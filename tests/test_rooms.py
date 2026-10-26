from django.test import TestCase
from accounts.models import PlayerProfile
from rooms.models import GameRoom, RoomPlayer, generate_unique_room_code
from rooms.services import create_game_room, join_game_room, RoomJoinError

class RoomsUnitTests(TestCase):
    def setUp(self):
        self.host = PlayerProfile.objects.create(session_key="host_session_123", nickname="HostFox", avatar="fox")
        self.player2 = PlayerProfile.objects.create(session_key="player2_session_456", nickname="PlayerPanda", avatar="panda")
        self.player3 = PlayerProfile.objects.create(session_key="player3_session_789", nickname="PlayerLion", avatar="lion")

    def test_room_code_uniqueness_and_format(self):
        codes = {generate_unique_room_code() for _ in range(50)}
        self.assertEqual(len(codes), 50)
        for code in codes:
            self.assertEqual(len(code), 6)
            self.assertTrue(code.isalnum())
            self.assertTrue(code.isupper())

    def test_create_game_room_assigns_host(self):
        room = create_game_room(
            host_player=self.host,
            name="Party Room",
            num_rounds=4,
            draw_time=45,
            difficulty="easy",
            category="animals",
        )
        self.assertEqual(room.players.count(), 1)
        host_member = room.players.first()
        self.assertTrue(host_member.is_host)
        self.assertTrue(host_member.is_ready)
        self.assertEqual(host_member.player, self.host)
        self.assertEqual(room.status, 'waiting')

    def test_join_room_success(self):
        room = create_game_room(host_player=self.host)
        room, member = join_game_room(room.code, self.player2)
        self.assertEqual(room.players.count(), 2)
        self.assertFalse(member.is_host)
        self.assertEqual(member.nickname, "PlayerPanda")

    def test_duplicate_membership_idempotent(self):
        room = create_game_room(host_player=self.host)
        room, m1 = join_game_room(room.code, self.player2)
        room, m2 = join_game_room(room.code, self.player2)
        self.assertEqual(m1.id, m2.id)
        self.assertEqual(room.players.count(), 2)

    def test_room_capacity_enforcement(self):
        room = create_game_room(host_player=self.host)
        room.max_players = 2
        room.save()

        # Join 2nd player
        join_game_room(room.code, self.player2)

        # 3rd player should raise RoomJoinError
        with self.assertRaises(RoomJoinError):
            join_game_room(room.code, self.player3)

    def test_cannot_join_playing_room(self):
        room = create_game_room(host_player=self.host)
        room.status = 'playing'
        room.save()

        with self.assertRaises(RoomJoinError):
            join_game_room(room.code, self.player2)
