import json
from django.test import TransactionTestCase
from channels.testing import WebsocketCommunicator
from django.contrib.sessions.backends.db import SessionStore
from config.asgi import application
from accounts.models import PlayerProfile
from rooms.models import GameRoom, RoomPlayer
from words.models import Word

class GameConsumerTests(TransactionTestCase):
    def setUp(self):
        Word.objects.create(text="sun", category="nature", difficulty="easy", is_active=True)
        Word.objects.create(text="tree", category="nature", difficulty="easy", is_active=True)

        # Create sessions
        self.session1 = SessionStore()
        self.session1.save()

        self.session2 = SessionStore()
        self.session2.save()

        # Profiles
        self.host_profile = PlayerProfile.objects.create(session_key=self.session1.session_key, nickname="Host", avatar="fox")
        self.guest_profile = PlayerProfile.objects.create(session_key=self.session2.session_key, nickname="Guest", avatar="panda")

        # Room
        self.room = GameRoom.objects.create(code="WSROOM", host=self.host_profile, num_rounds=2, draw_time=60)
        self.rp1 = RoomPlayer.objects.create(room=self.room, player=self.host_profile, nickname="Host", avatar="fox", is_host=True, is_ready=True)
        self.rp2 = RoomPlayer.objects.create(room=self.room, player=self.guest_profile, nickname="Guest", avatar="panda", is_ready=False)

    async def test_websocket_connect_and_snapshot(self):
        # Connect host with valid session cookie
        communicator = WebsocketCommunicator(
            application,
            f"/ws/room/{self.room.code}/",
            headers=[
                (b"cookie", f"sessionid={self.session1.session_key}".encode("latin1")),
            ]
        )

        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)

        # Receive initial connect messages (snapshot and player_joined broadcast)
        initial_types = set()
        for _ in range(2):
            msg = await communicator.receive_json_from()
            initial_types.add(msg['type'])
        self.assertIn('room.snapshot', initial_types)
        self.assertIn('room.player_joined', initial_types)

        # Send room.ready toggle
        await communicator.send_json_to({
            'type': 'room.ready',
            'data': {'is_ready': True}
        })

        # Receive broadcasted room.snapshot
        broadcast_response = await communicator.receive_json_from()
        self.assertEqual(broadcast_response['type'], 'room.snapshot')

        await communicator.disconnect()

    async def test_websocket_reject_invalid_room(self):
        communicator = WebsocketCommunicator(
            application,
            "/ws/room/INVALID/",
            headers=[
                (b"cookie", f"sessionid={self.session1.session_key}".encode("latin1")),
            ]
        )
        connected, _ = await communicator.connect()
        # Should be rejected
        self.assertFalse(connected)
