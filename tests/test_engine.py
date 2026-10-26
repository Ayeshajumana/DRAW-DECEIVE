from django.test import TestCase
from accounts.models import PlayerProfile
from rooms.models import GameRoom, RoomPlayer
from words.models import Word
from game import engine
from game.models import GameMatch, GameTurn, Guess

class GameEngineUnitTests(TestCase):
    def setUp(self):
        Word.objects.create(text="guitar", category="objects", difficulty="medium", is_active=True)
        Word.objects.create(text="apple", category="food", difficulty="easy", is_active=True)

        self.p1 = PlayerProfile.objects.create(session_key="p1_session", nickname="HostFox", avatar="fox")
        self.p2 = PlayerProfile.objects.create(session_key="p2_session", nickname="GuessPanda", avatar="panda")
        self.p3 = PlayerProfile.objects.create(session_key="p3_session", nickname="GuessLion", avatar="lion")

        self.room = GameRoom.objects.create(
            code="TEST01",
            host=self.p1,
            num_rounds=1,
            draw_time=60,
        )

        self.rp1 = RoomPlayer.objects.create(room=self.room, player=self.p1, nickname="HostFox", avatar="fox", is_host=True)
        self.rp2 = RoomPlayer.objects.create(room=self.room, player=self.p2, nickname="GuessPanda", avatar="panda")
        self.rp3 = RoomPlayer.objects.create(room=self.room, player=self.p3, nickname="GuessLion", avatar="lion")

    def test_start_match_requires_host(self):
        with self.assertRaises(engine.GameEngineError):
            engine.start_match(self.room, self.rp2)

    def test_start_match_success(self):
        match, turn = engine.start_match(self.room, self.rp1)
        self.assertEqual(match.status, 'active')
        self.assertEqual(self.room.status, 'playing')
        self.assertEqual(len(match.turn_order), 3)
        self.assertEqual(turn.turn_number, 1)
        self.assertIn(turn.secret_word, ["guitar", "apple"])

    def test_drawer_cannot_guess(self):
        match, turn = engine.start_match(self.room, self.rp1)
        # Attempt guess as the drawer
        res = engine.process_guess(turn, turn.drawer, turn.secret_word)
        self.assertFalse(res['is_correct'])
        self.assertIn('Drawer cannot guess', res['rejected_reason'])

    def test_correct_guess_and_scoring(self):
        match, turn = engine.start_match(self.room, self.rp1)
        drawer_id = turn.drawer.id
        non_drawers = [p for p in [self.rp1, self.rp2, self.rp3] if p.id != drawer_id]
        guesser = non_drawers[0]

        # Submit correct guess with punctuation and spaces
        res = engine.process_guess(turn, guesser, f"  {turn.secret_word.upper()}!!  ")
        self.assertTrue(res['is_correct'])
        self.assertTrue(res['points'] >= 100)

        # Verify guesser score incremented
        guesser.refresh_from_db()
        self.assertEqual(guesser.match_score, res['points'])

        # Duplicate guess guard: submitting again should not re-award points
        res_repeat = engine.process_guess(turn, guesser, turn.secret_word)
        self.assertTrue(res_repeat['is_correct'])
        self.assertTrue(res_repeat['already_awarded'])
        guesser.refresh_from_db()
        self.assertEqual(guesser.match_score, res['points'])

    def test_turn_finish_and_advance(self):
        match, turn = engine.start_match(self.room, self.rp1)
        drawer = turn.drawer
        non_drawers = [p for p in [self.rp1, self.rp2, self.rp3] if p.id != drawer.id]

        # Guesser guesses correctly
        engine.process_guess(turn, non_drawers[0], turn.secret_word)

        # Finish turn
        summary = engine.finish_turn(turn)
        self.assertEqual(summary['secret_word'], turn.secret_word)
        self.assertTrue(turn.result_processed)

        # Drawer points awarded
        drawer.refresh_from_db()
        self.assertEqual(drawer.match_score, 50)
