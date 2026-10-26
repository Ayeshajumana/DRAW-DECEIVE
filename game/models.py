import uuid
from django.db import models
from django.utils import timezone
from rooms.models import GameRoom, RoomPlayer

MATCH_STATUS_CHOICES = [
    ('waiting', 'Waiting to Start'),
    ('active', 'Match Active'),
    ('finished', 'Match Finished'),
]

TURN_PHASE_CHOICES = [
    ('round_start', 'Round Starting'),
    ('drawing', 'Drawing Phase'),
    ('round_results', 'Round Results'),
    ('match_results', 'Match Finished'),
]

class GameMatch(models.Model):
    """
    Represents an active or completed game match in a room.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='matches')
    status = models.CharField(max_length=20, choices=MATCH_STATUS_CHOICES, default='waiting', db_index=True)
    
    # Serialized list of RoomPlayer IDs in server-randomized turn order
    turn_order = models.JSONField(default=list)
    current_turn_index = models.PositiveIntegerField(default=0)
    round_number = models.PositiveSmallIntegerField(default=1)
    total_rounds = models.PositiveSmallIntegerField(default=3)
    
    # Track words used in this match to prevent repetition
    used_words = models.JSONField(default=list)
    
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Match {self.id} for Room {self.room.code} (Round {self.round_number}/{self.total_rounds})"

    @property
    def current_turn(self):
        return self.turns.order_by('-created_at').first()

class GameTurn(models.Model):
    """
    An individual drawing turn within a match.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.ForeignKey(GameMatch, on_delete=models.CASCADE, related_name='turns')
    turn_number = models.PositiveIntegerField(default=1)
    round_number = models.PositiveSmallIntegerField(default=1)
    
    drawer = models.ForeignKey(RoomPlayer, on_delete=models.CASCADE, related_name='drawn_turns')
    secret_word = models.CharField(max_length=80)
    category = models.CharField(max_length=50, default='General')
    difficulty = models.CharField(max_length=20, default='medium')
    hint = models.CharField(max_length=200, blank=True)
    
    phase = models.CharField(max_length=20, choices=TURN_PHASE_CHOICES, default='drawing', db_index=True)
    deadline = models.DateTimeField(db_index=True)
    turn_duration = models.PositiveSmallIntegerField(default=60)
    hint_stage = models.PositiveSmallIntegerField(default=0)  # 0: fully masked, 1: 1 letter, 2: 2 letters
    
    result_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Turn {self.turn_number} (Round {self.round_number}): Drawer {self.drawer.nickname} - Word '{self.secret_word}'"

    @property
    def remaining_seconds(self):
        now = timezone.now()
        if now >= self.deadline:
            return 0
        return max(0, int((self.deadline - now).total_seconds()))

    @property
    def is_expired(self):
        return timezone.now() >= self.deadline

class DrawingStroke(models.Model):
    """
    Stores an individual stroke for real-time synchronization and canvas replay on reconnect.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turn = models.ForeignKey(GameTurn, on_delete=models.CASCADE, related_name='strokes')
    stroke_id = models.CharField(max_length=64, db_index=True)
    sequence_number = models.PositiveIntegerField(default=0)
    player = models.ForeignKey(RoomPlayer, on_delete=models.CASCADE)
    
    tool_type = models.CharField(max_length=20, default='brush')  # brush, eraser, line, rect, circle
    color = models.CharField(max_length=30, default='#000000')
    brush_size = models.PositiveSmallIntegerField(default=4)
    points = models.JSONField(default=list)  # list of {x, y} normalized 0..800, 0..600
    
    is_undone = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sequence_number', 'created_at']
        indexes = [
            models.Index(fields=['turn', 'is_undone']),
        ]

    def to_dict(self):
        return {
            'stroke_id': self.stroke_id,
            'tool_type': self.tool_type,
            'color': self.color,
            'brush_size': self.brush_size,
            'points': self.points,
            'is_undone': self.is_undone,
        }

class Guess(models.Model):
    """
    A submitted guess from a player.
    Guarantees that a player only receives correct-guess points once per turn.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turn = models.ForeignKey(GameTurn, on_delete=models.CASCADE, related_name='guesses')
    player = models.ForeignKey(RoomPlayer, on_delete=models.CASCADE)
    text = models.CharField(max_length=150)
    is_correct = models.BooleanField(default=False)
    points_awarded = models.PositiveIntegerField(default=0)
    speed_bonus = models.PositiveIntegerField(default=0)
    remaining_seconds = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['turn', 'player', 'is_correct']),
        ]

class RoundResult(models.Model):
    """
    Score delta summary for a player in a turn.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    turn = models.ForeignKey(GameTurn, on_delete=models.CASCADE, related_name='results')
    player = models.ForeignKey(RoomPlayer, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, default='guesser')  # drawer, guesser
    points_awarded = models.PositiveIntegerField(default=0)
    speed_bonus = models.PositiveIntegerField(default=0)
    guessed_correctly = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('turn', 'player')

class ChatMessage(models.Model):
    """
    Chat or system message in a room.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='chat_messages')
    turn = models.ForeignKey(GameTurn, null=True, blank=True, on_delete=models.SET_NULL)
    player = models.ForeignKey(RoomPlayer, null=True, blank=True, on_delete=models.SET_NULL)
    text = models.CharField(max_length=250)
    is_system = models.BooleanField(default=False)
    msg_type = models.CharField(max_length=20, default='chat')  # chat, guess, correct, system
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def to_dict(self):
        return {
            'id': str(self.id),
            'text': self.text,
            'sender': self.player.nickname if self.player else 'Game System',
            'avatar': self.player.avatar if self.player else 'robot',
            'is_system': self.is_system,
            'msg_type': self.msg_type,
            'time': self.created_at.strftime('%H:%M:%S'),
        }
