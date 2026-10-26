from django.db import transaction
from .models import GameRoom, RoomPlayer, generate_unique_room_code
from words.models import WordPack

class RoomJoinError(Exception):
    pass

def create_game_room(host_player, name='', num_rounds=3, draw_time=60, difficulty='mixed', category='all', word_pack_id=None, is_private=False):
    """
    Creates a new GameRoom and automatically assigns the host as the first RoomPlayer.
    """
    word_pack = None
    if word_pack_id:
        word_pack = WordPack.objects.filter(id=word_pack_id).first()

    # Validate boundaries
    num_rounds = max(1, min(10, int(num_rounds or 3)))
    draw_time = max(30, min(120, int(draw_time or 60)))
    if difficulty not in ['easy', 'medium', 'hard', 'mixed']:
        difficulty = 'mixed'

    with transaction.atomic():
        room = GameRoom.objects.create(
            code=generate_unique_room_code(),
            name=name.strip() or f"{host_player.nickname}'s Room",
            host=host_player,
            num_rounds=num_rounds,
            draw_time=draw_time,
            difficulty=difficulty,
            category=category,
            word_pack=word_pack,
            is_private=is_private,
        )

        RoomPlayer.objects.create(
            room=room,
            player=host_player,
            nickname=host_player.nickname,
            avatar=host_player.avatar,
            is_host=True,
            is_ready=True,
            is_connected=True,
        )

    return room

def join_game_room(room_code: str, player, nickname=None, avatar=None):
    """
    Adds a player to a room or updates their existing membership.
    Raises RoomJoinError if room not found, full, or closed.
    """
    room_code = room_code.strip().upper()
    try:
        room = GameRoom.objects.get(code=room_code)
    except GameRoom.DoesNotExist:
        raise RoomJoinError("Room code not found. Please verify the 6-character code.")

    # Check existing membership
    existing_member = RoomPlayer.objects.filter(room=room, player=player).first()
    if existing_member:
        # Re-joining or updating profile
        if nickname:
            existing_member.nickname = nickname.strip()[:30]
        if avatar:
            existing_member.avatar = avatar
        existing_member.is_connected = True
        existing_member.save()
        return room, existing_member

    # Check room status
    if room.status == 'finished':
        raise RoomJoinError("This match has already ended.")

    if room.status == 'playing':
        raise RoomJoinError("Game is currently in progress. Please wait for the next game or join another room.")

    if room.is_full:
        raise RoomJoinError(f"Room is full (maximum {room.max_players} players).")

    nickname = (nickname or player.nickname or 'Player').strip()[:30]
    avatar = avatar or player.avatar

    with transaction.atomic():
        room_player = RoomPlayer.objects.create(
            room=room,
            player=player,
            nickname=nickname,
            avatar=avatar,
            is_host=(room.players.count() == 0),
            is_ready=False,
            is_connected=True,
        )

    return room, room_player

def get_room_snapshot(room):
    """
    Serializes current room state for lobby and WebSocket synchronization.
    """
    players = [p.to_dict() for p in room.players.all()]
    return {
        'code': room.code,
        'name': room.name,
        'status': room.status,
        'host_id': str(room.host.id),
        'min_players': room.min_players,
        'max_players': room.max_players,
        'num_rounds': room.num_rounds,
        'draw_time': room.draw_time,
        'difficulty': room.difficulty,
        'category': room.category,
        'word_pack_name': room.word_pack.name if room.word_pack else None,
        'players': players,
        'player_count': len(players),
        'can_start': room.can_start,
    }
