import uuid
from django.db import models
from django.contrib.auth.models import User
from .avatars import AVATARS, DEFAULT_AVATAR, get_avatar_info

class PlayerProfile(models.Model):
    """
    Session-backed or User-linked profile for players.
    Guarantees a verified identity token for guest and logged-in players.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='player_profile')
    session_key = models.CharField(max_length=64, unique=True, db_index=True)
    nickname = models.CharField(max_length=30, default='Artist')
    avatar = models.CharField(max_length=50, default=DEFAULT_AVATAR)
    
    # Career Stats
    games_played = models.PositiveIntegerField(default=0)
    games_won = models.PositiveIntegerField(default=0)
    correct_guesses = models.PositiveIntegerField(default=0)
    total_score = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_score', '-games_won']

    def __str__(self):
        return f"{self.nickname} ({self.avatar})"

    @property
    def avatar_info(self):
        return get_avatar_info(self.avatar)

    @classmethod
    def get_for_request(cls, request):
        """
        Gets or creates a secure PlayerProfile tied to the current Django session.
        Ensures request.session has a session_key.
        """
        if not request.session.session_key:
            request.session.save()
        session_key = request.session.session_key

        profile, created = cls.objects.get_or_create(
            session_key=session_key,
            defaults={
                'nickname': f"Player_{session_key[:4].upper()}",
                'avatar': DEFAULT_AVATAR,
            }
        )
        if request.user.is_authenticated and not profile.user:
            profile.user = request.user
            if request.user.first_name:
                profile.nickname = request.user.first_name
            elif request.user.username:
                profile.nickname = request.user.username
            profile.save(update_fields=['user', 'nickname'])

        return profile
