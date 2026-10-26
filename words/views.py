import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from accounts.models import PlayerProfile
from .models import WordPack, WordPackEntry, Word, CATEGORY_CHOICES, DIFFICULTY_CHOICES

def word_packs_view(request):
    player = PlayerProfile.get_for_request(request)
    public_packs = WordPack.objects.filter(is_public=True).prefetch_related('entries')
    user_packs = WordPack.objects.filter(owner=player).prefetch_related('entries')
    
    total_curated_words = Word.objects.filter(is_active=True).count()

    return render(request, 'word_packs.html', {
        'public_packs': public_packs,
        'user_packs': user_packs,
        'categories': CATEGORY_CHOICES,
        'difficulties': DIFFICULTY_CHOICES,
        'total_curated_words': total_curated_words,
    })

@require_POST
def create_word_pack(request):
    player = PlayerProfile.get_for_request(request)
    
    name = request.POST.get('name', '').strip()
    description = request.POST.get('description', '').strip()
    is_public = request.POST.get('is_public') == 'on'
    raw_words = request.POST.get('words', '').strip()

    if not name:
        messages.error(request, 'Please provide a name for your word pack.')
        return redirect('word_packs')

    word_lines = [w.strip() for w in raw_words.splitlines() if w.strip()]
    if len(word_lines) < 5:
        messages.error(request, 'Please include at least 5 words in your pack (one per line).')
        return redirect('word_packs')

    pack = WordPack.objects.create(
        name=name,
        description=description,
        owner=player,
        is_public=is_public,
    )

    created_count = 0
    for line in word_lines:
        parts = [p.strip() for p in line.split(',') if p.strip()]
        word_text = parts[0]
        hint = parts[1] if len(parts) > 1 else ''
        if word_text:
            WordPackEntry.objects.create(
                pack=pack,
                word_text=word_text,
                hint=hint,
            )
            created_count += 1

    messages.success(request, f'Word pack "{pack.name}" created with {created_count} words!')
    return redirect('word_packs')
