import random
import string
from django.db import models
from accounts.models import PlayerProfile
from accounts.avatars import get_avatar_info
from words.models import WordPack

ROOM_STATUS_CHOICES = [
    ('waiting', 'In Lobby'),
    ('playing', 'Match in Progress'),
    ('finished', 'Match Finished'),
]

SAFE_CODE_CHARS = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'  # Excludes 0, O, 1, I to avoid look-alikes

def generate_unique_room_code():
    for _ in range(50):
        code = ''.join(random.choices(SAFE_CODE_CHARS, k=6))
        if not GameRoom.objects.filter(code=code).exists():
            return code
    # Fallback with length 8 if high room volume
    return ''.join(random.choices(SAFE_CODE_CHARS, k=8))

class GameRoom(models.Model):
    code = models.CharField(max_length=8, unique=True, db_index=True)
    name = models.CharField(max_length=100, blank=True)
    host = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='hosted_rooms')
    status = models.CharField(max_length=20, choices=ROOM_STATUS_CHOICES, default='waiting', db_index=True)
    
    # Settings
    min_players = models.PositiveSmallIntegerField(default=2)
    max_players = models.PositiveSmallIntegerField(default=8)
    num_rounds = models.PositiveSmallIntegerField(default=3)
    draw_time = models.PositiveSmallIntegerField(default=60)  # seconds
    difficulty = models.CharField(max_length=20, default='mixed')
    category = models.CharField(max_length=50, default='all')
    word_pack = models.ForeignKey(WordPack, null=True, blank=True, on_delete=models.SET_NULL)
    is_private = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Room {self.code} ({self.status}) - Host: {self.host.nickname}"

    @property
    def player_count(self):
        return self.players.count()

    @property
    def is_full(self):
        return self.player_count >= self.max_players

    @property
    def can_start(self):
        return self.status == 'waiting' and self.player_count >= self.min_players

    def get_share_url(self, request=None):
        if request:
            return request.build_absolute_uri(f"/room/{self.code}/")
        return f"/room/{self.code}/"

class RoomPlayer(models.Model):
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='players')
    player = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='room_memberships')
    nickname = models.CharField(max_length=30)
    avatar = models.CharField(max_length=50)
    
    is_host = models.BooleanField(default=False)
    is_ready = models.BooleanField(default=False)
    is_connected = models.BooleanField(default=True)
    match_score = models.PositiveIntegerField(default=0)
    
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('room', 'player')
        ordering = ['-match_score', 'joined_at']

    def __str__(self):
        return f"{self.nickname} in {self.room.code} (Score: {self.match_score})"

    @property
    def avatar_info(self):
        return get_avatar_info(self.avatar)

    def to_dict(self):
        return {
            'id': str(self.id),
            'player_id': str(self.player.id),
            'nickname': self.nickname,
            'avatar': self.avatar,
            'avatar_info': self.avatar_info,
            'is_host': self.is_host,
            'is_ready': self.is_ready,
            'is_connected': self.is_connected,
            'match_score': self.match_score,
        }
