import math

def calculate_speed_bonus(remaining_seconds: int, total_turn_seconds: int) -> int:
    """
    Calculates speed bonus for guessers:
    speed_bonus = floor(50 * remaining_seconds / total_turn_seconds)
    Clamped strictly to 0..50.
    """
    if total_turn_seconds <= 0 or remaining_seconds <= 0:
        return 0
    ratio = min(1.0, max(0.0, float(remaining_seconds) / float(total_turn_seconds)))
    bonus = math.floor(50.0 * ratio)
    return max(0, min(50, int(bonus)))

def calculate_guesser_points(remaining_seconds: int, total_turn_seconds: int) -> tuple[int, int]:
    """
    Returns (base_points, speed_bonus)
    Base: 100
    Speed: 0..50
    """
    speed_bonus = calculate_speed_bonus(remaining_seconds, total_turn_seconds)
    base_points = 100
    return base_points, speed_bonus

def calculate_drawer_points(num_correct_guessers: int, total_eligible_guessers: int) -> int:
    """
    Drawer gets 50 points per opponent who correctly guessed.
    If all eligible opponents guessed, bonus 50 points awarded.
    """
    if num_correct_guessers <= 0:
        return 0
    points = num_correct_guessers * 50
    if total_eligible_guessers > 0 and num_correct_guessers >= total_eligible_guessers:
        points += 50  # full round completion bonus
    return points
