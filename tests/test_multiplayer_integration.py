import asyncio
from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from django.contrib.sessions.backends.db import SessionStore
from config.asgi import application
from accounts.models import PlayerProfile
from rooms.models import GameRoom, RoomPlayer
from words.models import Word
from game.models import GameMatch, GameTurn, Guess

class MultiplayerIntegrationTests(TransactionTestCase):
    def setUp(self):
        # Seed test words
        Word.objects.create(text="rocket", category="tech", difficulty="easy", is_active=True)
        Word.objects.create(text="submarine", category="tech", difficulty="medium", is_active=True)
        Word.objects.create(text="telescope", category="tech", difficulty="hard", is_active=True)

        # Create 3 player sessions
        self.sessions = []
        self.profiles = []
        names = ["Alice", "Bob", "Charlie"]
        avatars = ["fox", "panda", "lion"]

        for i in range(3):
            s = SessionStore()
            s.save()
            self.sessions.append(s)
            p = PlayerProfile.objects.create(
                session_key=s.session_key,
                nickname=names[i],
                avatar=avatars[i],
            )
            self.profiles.append(p)

        # Host Alice creates room
        self.room = GameRoom.objects.create(
            code="MULTI1",
            host=self.profiles[0],
            num_rounds=1,
            draw_time=30,
        )

        # 3 Room players
        self.room_players = []
        for i in range(3):
            rp = RoomPlayer.objects.create(
                room=self.room,
                player=self.profiles[i],
                nickname=names[i],
                avatar=avatars[i],
                is_host=(i == 0),
                is_ready=True,
            )
            self.room_players.append(rp)

    async def test_full_3_player_game_cycle(self):
        # 1. Connect all 3 players via WebSocket
        communicators = []
        for i in range(3):
            comm = WebsocketCommunicator(
                application,
                f"/ws/room/{self.room.code}/",
                headers=[
                    (b"cookie", f"sessionid={self.sessions[i].session_key}".encode("latin1")),
                ]
            )
            connected, _ = await comm.connect()
            self.assertTrue(connected, f"Player {i} failed to connect")
            communicators.append(comm)

        # Drain initial connect messages from all 3 communicators
        for comm in communicators:
            while await comm.receive_nothing(timeout=0.1) is False:
                await comm.receive_json_from()

        # 2. Host (communicators[0]) starts match
        await communicators[0].send_json_to({'type': 'game.start', 'data': {}})

        # Collect turn_started from all 3 communicators
        turn_start_events = []
        secret_word_data = None
        drawer_index = None

        for idx, comm in enumerate(communicators):
            msg = await comm.receive_json_from()
            self.assertEqual(msg['type'], 'game.turn_started')
            turn_start_events.append(msg['data'])

            # Drawer also receives private game.secret_word directly
            if not await comm.receive_nothing(timeout=0.2):
                extra = await comm.receive_json_from()
                if extra['type'] == 'game.secret_word':
                    secret_word_data = extra['data']
                    drawer_index = idx

        self.assertIsNotNone(secret_word_data, "Drawer did not receive secret word")
        secret_word = secret_word_data['secret_word']
        self.assertIn(secret_word, ["rocket", "submarine", "telescope"])

        # Guessers must NOT see the unrevealed secret word in public turn_started payload!
        public_data = turn_start_events[0]
        self.assertNotIn(secret_word, public_data['masked_word'])
        self.assertIn('_', public_data['masked_word'])

        # 3. Drawer draws on canvas
        drawer_comm = communicators[drawer_index]
        stroke_id = "test_stroke_123"
        await drawer_comm.send_json_to({
            'type': 'drawing.stroke',
            'data': {
                'stroke_id': stroke_id,
                'tool_type': 'brush',
                'color': '#ff0000',
                'brush_size': 6,
                'points': [{'x': 100, 'y': 150}, {'x': 105, 'y': 155}],
            }
        })

        # Other 2 guessers must receive the drawing.stroke event
        guesser_indices = [i for i in range(3) if i != drawer_index]
        for g_idx in guesser_indices:
            stroke_event = await communicators[g_idx].receive_json_from()
            self.assertEqual(stroke_event['type'], 'drawing.stroke')
            self.assertEqual(stroke_event['data']['stroke_id'], stroke_id)

        # 4. Guesser submits an incorrect guess
        first_guesser = communicators[guesser_indices[0]]
        await first_guesser.send_json_to({
            'type': 'game.guess',
            'data': {'text': 'totally_wrong_guess'}
        })

        # Chat message broadcasted
        chat_event = await first_guesser.receive_json_from()
        self.assertEqual(chat_event['type'], 'game.chat_message')
        self.assertEqual(chat_event['data']['text'], 'totally_wrong_guess')

        # 5. Guesser submits the correct secret word!
        await first_guesser.send_json_to({
            'type': 'game.guess',
            'data': {'text': secret_word}
        })

        # Correct guess broadcasted
        correct_event = await first_guesser.receive_json_from()
        self.assertEqual(correct_event['type'], 'game.guess_correct')
        self.assertTrue(correct_event['data']['points'] >= 100)

        # Clean disconnect
        for comm in communicators:
            await comm.disconnect()
