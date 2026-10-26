from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import PlayerProfile
from accounts.avatars import AVATARS, AVATAR_MAP
from words.models import WordPack, CATEGORY_CHOICES, DIFFICULTY_CHOICES
from .models import GameRoom, RoomPlayer
from .services import create_game_room, join_game_room, RoomJoinError, get_room_snapshot

def home_view(request):
    player = PlayerProfile.get_for_request(request)
    recent_rooms = GameRoom.objects.filter(status='waiting', is_private=False)[:6]
    return render(request, 'home.html', {
        'player': player,
        'recent_rooms': recent_rooms,
        'avatars': AVATARS,
    })

def create_room_view(request):
    player = PlayerProfile.get_for_request(request)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        num_rounds = request.POST.get('num_rounds', 3)
        draw_time = request.POST.get('draw_time', 60)
        difficulty = request.POST.get('difficulty', 'mixed')
        category = request.POST.get('category', 'all')
        word_pack_id = request.POST.get('word_pack_id') or None
        is_private = request.POST.get('is_private') == 'on'

        # Update player nickname / avatar if submitted on this form
        nickname = request.POST.get('nickname', '').strip()
        avatar = request.POST.get('avatar', '').strip()
        if nickname:
            player.nickname = nickname[:25]
        if avatar in AVATAR_MAP:
            player.avatar = avatar
        player.save()

        try:
            room = create_game_room(
                host_player=player,
                name=name,
                num_rounds=num_rounds,
                draw_time=draw_time,
                difficulty=difficulty,
                category=category,
                word_pack_id=word_pack_id,
                is_private=is_private,
            )
            return redirect('room_view', code=room.code)
        except Exception as e:
            messages.error(request, f"Could not create room: {str(e)}")

    word_packs = WordPack.objects.filter(is_public=True) | WordPack.objects.filter(owner=player)
    return render(request, 'create_room.html', {
        'player': player,
        'categories': CATEGORY_CHOICES,
        'difficulties': DIFFICULTY_CHOICES,
        'word_packs': word_packs.distinct(),
        'avatars': AVATARS,
    })

def join_room_view(request, code=''):
    player = PlayerProfile.get_for_request(request)
    target_code = (code or request.GET.get('code', '')).strip().upper()

    if request.method == 'POST':
        target_code = request.POST.get('code', '').strip().upper()
        nickname = request.POST.get('nickname', '').strip()
        avatar = request.POST.get('avatar', '').strip()

        if nickname:
            player.nickname = nickname[:25]
        if avatar in AVATAR_MAP:
            player.avatar = avatar
        player.save()

        try:
            room, _ = join_game_room(target_code, player, nickname=player.nickname, avatar=player.avatar)
            return redirect('room_view', code=room.code)
        except RoomJoinError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error joining room: {str(e)}")

    return render(request, 'join_room.html', {
        'player': player,
        'target_code': target_code,
        'avatars': AVATARS,
    })

def room_view(request, code):
    player = PlayerProfile.get_for_request(request)
    room = get_object_or_404(GameRoom, code=code.upper())

    # Ensure player has joined the room
    membership = RoomPlayer.objects.filter(room=room, player=player).first()
    if not membership:
        # Prompt to join with nickname & avatar
        if room.status != 'waiting' and room.status != 'playing':
            messages.error(request, "This room is no longer active.")
            return redirect('join_room_with_code', code=room.code)
        
        # If room not full, auto-join player
        if not room.is_full:
            try:
                room, membership = join_game_room(room.code, player)
            except RoomJoinError as e:
                messages.error(request, str(e))
                return redirect('join_room_with_code', code=room.code)
        else:
            messages.error(request, "Room is full.")
            return redirect('join_room')

    # Pass room snapshot and context
    return render(request, 'game.html', {
        'room': room,
        'player': player,
        'membership': membership,
        'is_host': membership.is_host,
        'share_url': room.get_share_url(request),
        'avatars': AVATARS,
    })

def leave_room_view(request, code):
    player = PlayerProfile.get_for_request(request)
    room = GameRoom.objects.filter(code=code.upper()).first()
    if room:
        RoomPlayer.objects.filter(room=room, player=player).delete()
        if room.host == player:
            next_host = room.players.first()
            if next_host:
                room.host = next_host.player
                next_host.is_host = True
                next_host.save()
                room.save()
            else:
                room.status = 'finished'
                room.save()
    return redirect('home')
