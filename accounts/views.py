import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import PlayerProfile
from .avatars import AVATARS, AVATAR_MAP

def profile_view(request):
    player = PlayerProfile.get_for_request(request)
    top_players = PlayerProfile.objects.order_by('-total_score')[:10]
    return render(request, 'profile.html', {
        'player': player,
        'top_players': top_players,
        'avatars': AVATARS,
    })

@require_POST
def update_profile(request):
    player = PlayerProfile.get_for_request(request)
    
    # Handle either JSON or form POST
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            nickname = data.get('nickname', '').strip()
            avatar = data.get('avatar', '').strip()
        except Exception:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    else:
        nickname = request.POST.get('nickname', '').strip()
        avatar = request.POST.get('avatar', '').strip()

    if nickname:
        if len(nickname) > 25:
            nickname = nickname[:25]
        player.nickname = nickname

    if avatar in AVATAR_MAP:
        player.avatar = avatar

    player.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'nickname': player.nickname,
            'avatar': player.avatar,
            'avatar_info': player.avatar_info,
        })

    messages.success(request, 'Profile updated successfully!')
    return redirect('profile')
