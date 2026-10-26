from django.test import SimpleTestCase
from game.scoring import calculate_speed_bonus, calculate_guesser_points, calculate_drawer_points

class ScoringUnitTests(SimpleTestCase):
    def test_speed_bonus_max_at_start(self):
        # 60s remaining out of 60s total should be 50 points
        bonus = calculate_speed_bonus(remaining_seconds=60, total_turn_seconds=60)
        self.assertEqual(bonus, 50)

    def test_speed_bonus_halfway(self):
        # 30s remaining out of 60s total should be 25 points
        bonus = calculate_speed_bonus(remaining_seconds=30, total_turn_seconds=60)
        self.assertEqual(bonus, 25)

    def test_speed_bonus_zero_at_expiry(self):
        # 0s remaining should be 0 points
        bonus = calculate_speed_bonus(remaining_seconds=0, total_turn_seconds=60)
        self.assertEqual(bonus, 0)

    def test_speed_bonus_negative_clamped(self):
        # Negative remaining clamped to 0
        bonus = calculate_speed_bonus(remaining_seconds=-5, total_turn_seconds=60)
        self.assertEqual(bonus, 0)

    def test_speed_bonus_exceeding_clamped(self):
        # Remaining greater than total clamped to 50
        bonus = calculate_speed_bonus(remaining_seconds=120, total_turn_seconds=60)
        self.assertEqual(bonus, 50)

    def test_guesser_total_points(self):
        base, speed = calculate_guesser_points(remaining_seconds=45, total_turn_seconds=60)
        self.assertEqual(base, 100)
        self.assertEqual(speed, 37)
        self.assertEqual(base + speed, 137)

    def test_drawer_points_calculation(self):
        # 0 guessers = 0 points
        points = calculate_drawer_points(num_correct_guessers=0, total_eligible_guessers=3)
        self.assertEqual(points, 0)

        # 2 out of 3 guessers = 100 points
        points = calculate_drawer_points(num_correct_guessers=2, total_eligible_guessers=3)
        self.assertEqual(points, 100)

        # All 3 guessers = 150 points + 50 completion bonus = 200 points
        points = calculate_drawer_points(num_correct_guessers=3, total_eligible_guessers=3)
        self.assertEqual(points, 200)
