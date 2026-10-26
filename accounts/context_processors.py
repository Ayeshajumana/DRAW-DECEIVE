from .models import PlayerProfile
from .avatars import AVATARS

def player_context(request):
    """
    Context processor providing current player info and avatar list to all templates.
    """
    try:
        player = PlayerProfile.get_for_request(request)
    except Exception:
        player = None

    return {
        'current_player': player,
        'available_avatars': AVATARS,
    }
