import re
import random
from .models import Word, WordPack, WordPackEntry
from .data.default_words import INITIAL_WORDS

def seed_default_words():
    """
    Populates database with curated default words if table is empty.
    """
    if Word.objects.count() < len(INITIAL_WORDS):
        created_count = 0
        for item in INITIAL_WORDS:
            _, created = Word.objects.get_or_create(
                text=item["text"].strip().lower(),
                defaults={
                    "category": item["category"],
                    "difficulty": item["difficulty"],
                    "hint": item.get("hint", ""),
                    "is_active": True,
                }
            )
            if created:
                created_count += 1
        return created_count
    return 0

def normalize_guess(text: str) -> str:
    """
    Normalizes a guess string:
    - Strips whitespace
    - Lowercase
    - Removes punctuation
    - Collapses consecutive whitespaces
    """
    if not text:
        return ""
    text = text.strip().lower()
    # Remove punctuation except letters and spaces
    text = re.sub(r'[^\w\s]', '', text)
    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def get_word_for_turn(difficulty='mixed', category='all', pack_id=None, exclude_words=None):
    """
    Selects a random eligible word, avoiding recently used words in the current match.
    """
    exclude_words = exclude_words or []
    normalized_excludes = [normalize_guess(w) for w in exclude_words]

    # Custom word pack selected
    if pack_id:
        try:
            pack = WordPack.objects.get(id=pack_id)
            entries = pack.entries.all()
            eligible = [e for e in entries if normalize_guess(e.word_text) not in normalized_excludes]
            if not eligible and entries.exists():
                eligible = list(entries)  # reset if all exhausted
            if eligible:
                selected = random.choice(eligible)
                return {
                    'text': selected.word_text,
                    'category': selected.category,
                    'difficulty': selected.difficulty,
                    'hint': selected.hint,
                }
        except WordPack.DoesNotExist:
            pass

    # Built-in curated words
    qs = Word.objects.filter(is_active=True)

    if category and category != 'all':
        qs = qs.filter(category=category)

    if difficulty and difficulty != 'mixed':
        qs = qs.filter(difficulty=difficulty)

    eligible_words = [w for w in qs if normalize_guess(w.text) not in normalized_excludes]

    # If all eligible words in category/difficulty were used, fallback to any unused
    if not eligible_words:
        eligible_words = [w for w in Word.objects.filter(is_active=True) if normalize_guess(w.text) not in normalized_excludes]

    # If all words in entire database were used, fallback to full active set
    if not eligible_words:
        eligible_words = list(Word.objects.filter(is_active=True))

    if not eligible_words:
        # Fallback safety if database not seeded
        return {
            'text': 'star',
            'category': 'nature',
            'difficulty': 'easy',
            'hint': 'Twinkles in the night sky'
        }

    chosen = random.choice(eligible_words)
    return {
        'text': chosen.text,
        'category': chosen.category,
        'difficulty': chosen.difficulty,
        'hint': chosen.hint,
    }

def format_masked_hint(word_text: str, revealed_indices: set = None) -> str:
    """
    Returns masked representation of word for guessing players.
    Spaces are preserved as '   ' (3 spaces) so multi-word guesses are clear.
    Example: "apple" -> "_ _ _ _ _"
    With revealed indices {0, 3}: "A _ _ L _"
    """
    revealed_indices = revealed_indices or set()
    result = []
    for idx, char in enumerate(word_text):
        if char == ' ':
            result.append('  ')
        elif idx in revealed_indices:
            result.append(char.upper())
        else:
            result.append('_')
    return ' '.join(result)

def calculate_revealed_indices(word_text: str, hint_stage: int) -> set:
    """
    Calculates which character indices to reveal based on hint stage (0, 1, 2).
    Never reveals more than 40% of characters to keep game challenging.
    """
    letters = [i for i, c in enumerate(word_text) if c != ' ']
    total_letters = len(letters)
    if total_letters <= 2 or hint_stage <= 0:
        return set()

    revealed = set()
    # Stage 1: reveal 1st letter
    if hint_stage >= 1 and total_letters > 2:
        revealed.add(letters[0])

    # Stage 2: reveal a middle or last letter
    if hint_stage >= 2 and total_letters > 4:
        # Choose a middle letter
        mid_idx = letters[len(letters) // 2]
        revealed.add(mid_idx)

    return revealed
