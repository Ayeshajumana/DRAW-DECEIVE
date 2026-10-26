import uuid
from django.db import models
from accounts.models import PlayerProfile

CATEGORY_CHOICES = [
    ('animals', 'Animals'),
    ('food', 'Food & Drinks'),
    ('objects', 'Objects & Tools'),
    ('nature', 'Nature & Weather'),
    ('sports', 'Sports & Games'),
    ('entertainment', 'Movies & Pop Culture'),
    ('tech', 'Technology & Science'),
    ('activities', 'Everyday Activities'),
]

DIFFICULTY_CHOICES = [
    ('easy', 'Easy'),
    ('medium', 'Medium'),
    ('hard', 'Hard'),
]

class Word(models.Model):
    """
    Curated word dataset for games.
    """
    text = models.CharField(max_length=50, unique=True, db_index=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium', db_index=True)
    hint = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['text']
        indexes = [
            models.Index(fields=['category', 'difficulty', 'is_active']),
        ]

    def __str__(self):
        return f"{self.text} ({self.category} - {self.difficulty})"

class WordPack(models.Model):
    """
    Custom word packs created by hosts/players.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(PlayerProfile, null=True, blank=True, on_delete=models.CASCADE, related_name='word_packs')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def word_count(self):
        return self.entries.count()

class WordPackEntry(models.Model):
    """
    Individual word within a custom word pack.
    """
    pack = models.ForeignKey(WordPack, on_delete=models.CASCADE, related_name='entries')
    word_text = models.CharField(max_length=50)
    category = models.CharField(max_length=50, default='Custom')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    hint = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['word_text']
        unique_together = ('pack', 'word_text')

    def __str__(self):
        return f"{self.word_text} in {self.pack.name}"
