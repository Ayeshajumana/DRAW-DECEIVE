from django.test import TestCase
from words.models import Word
from words.services import (
    normalize_guess,
    format_masked_hint,
    calculate_revealed_indices,
    get_word_for_turn,
)

class WordsUnitTests(TestCase):
    def setUp(self):
        Word.objects.create(text="apple", category="food", difficulty="easy", hint="Keeps doctor away", is_active=True)
        Word.objects.create(text="banana", category="food", difficulty="easy", hint="Yellow fruit", is_active=True)
        Word.objects.create(text="elephant", category="animals", difficulty="medium", hint="Large ears", is_active=True)
        Word.objects.create(text="space station", category="tech", difficulty="hard", hint="Orbital lab", is_active=True)

    def test_normalize_guess(self):
        self.assertEqual(normalize_guess("  Apple  "), "apple")
        self.assertEqual(normalize_guess("APPLE!!!"), "apple")
        self.assertEqual(normalize_guess("Space   Station..."), "space station")
        self.assertEqual(normalize_guess("what? elephant!"), "what elephant")
        self.assertEqual(normalize_guess(""), "")

    def test_format_masked_hint_stage_zero(self):
        masked = format_masked_hint("apple", set())
        self.assertEqual(masked, "_ _ _ _ _")

    def test_format_masked_hint_multi_word(self):
        masked = format_masked_hint("hot dog", set())
        # Two words with spaces preserved
        self.assertIn("  ", masked)

    def test_format_masked_hint_with_reveals(self):
        revealed = {0, 3}  # 'a' and 'l' in apple
        masked = format_masked_hint("apple", revealed)
        self.assertEqual(masked, "A _ _ L _")

    def test_calculate_revealed_indices(self):
        # Stage 0: empty
        self.assertEqual(calculate_revealed_indices("elephant", 0), set())
        
        # Stage 1: first letter revealed (index 0)
        stage_1 = calculate_revealed_indices("elephant", 1)
        self.assertEqual(stage_1, {0})

        # Stage 2: first letter + middle letter revealed
        stage_2 = calculate_revealed_indices("elephant", 2)
        self.assertIn(0, stage_2)
        self.assertTrue(len(stage_2) >= 2)

    def test_word_selection_avoid_used(self):
        # Exclude 'apple'
        word = get_word_for_turn(category="food", exclude_words=["apple"])
        self.assertEqual(word['text'], "banana")
