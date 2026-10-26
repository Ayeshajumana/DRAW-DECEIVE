import random
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from rooms.models import GameRoom, RoomPlayer
from words.services import get_word_for_turn, normalize_guess, format_masked_hint, calculate_revealed_indices
from .models import GameMatch, GameTurn, DrawingStroke, Guess, RoundResult, ChatMessage
from .scoring import calculate_guesser_points, calculate_drawer_points

class GameEngineError(Exception):
    pass

def start_match(room: GameRoom, host_player: RoomPlayer):
    """
    Initializes a match with server-side randomized turn order.
    Requires at least 2 players in the room.
    """
    if not host_player.is_host:
        raise GameEngineError("Only the room host can start the game.")

    eligible_players = list(room.players.filter(is_connected=True))
    if len(eligible_players) < room.min_players:
        # If testing with disconnected or fewer, allow all players in room
        eligible_players = list(room.players.all())

    if len(eligible_players) < 2:
        raise GameEngineError(f"At least 2 players are required to start (currently {len(eligible_players)}).")

    # Server-side turn order randomization
    player_ids = [str(p.id) for p in eligible_players]
    random.shuffle(player_ids)

    # Reset player match scores
    for p in eligible_players:
        p.match_score = 0
        p.save(update_fields=['match_score'])

    with transaction.atomic():
        room.status = 'playing'
        room.save(update_fields=['status'])

        match = GameMatch.objects.create(
            room=room,
            status='active',
            turn_order=player_ids,
            current_turn_index=0,
            round_number=1,
            total_rounds=room.num_rounds,
            used_words=[],
        )

        turn = start_new_turn(match)

    return match, turn

def start_new_turn(match: GameMatch) -> GameTurn:
    """
    Starts a new turn in the match:
    - Selects drawer based on turn_order and current_turn_index
    - Chooses secret word avoiding match.used_words
    - Sets timezone-aware deadline
    """
    room = match.room
    turn_order = match.turn_order
    if not turn_order:
        turn_order = [str(p.id) for p in room.players.all()]
        match.turn_order = turn_order
        match.save(update_fields=['turn_order'])

    drawer_id = turn_order[match.current_turn_index % len(turn_order)]
    drawer = RoomPlayer.objects.filter(id=drawer_id).first()
    if not drawer:
        # Fallback to first available room player
        drawer = room.players.first()

    word_info = get_word_for_turn(
        difficulty=room.difficulty,
        category=room.category,
        pack_id=room.word_pack_id,
        exclude_words=match.used_words or [],
    )

    used_words = match.used_words or []
    used_words.append(word_info['text'])
    match.used_words = used_words
    match.save(update_fields=['used_words'])

    now = timezone.now()
    deadline = now + timedelta(seconds=room.draw_time)
    turn_number = match.turns.count() + 1

    turn = GameTurn.objects.create(
        match=match,
        turn_number=turn_number,
        round_number=match.round_number,
        drawer=drawer,
        secret_word=word_info['text'],
        category=word_info['category'],
        difficulty=word_info['difficulty'],
        hint=word_info['hint'],
        phase='drawing',
        deadline=deadline,
        turn_duration=room.draw_time,
        hint_stage=0,
    )

    return turn

def process_guess(turn: GameTurn, player: RoomPlayer, guess_text: str):
    """
    Validates and processes a player's guess:
    - Rejects guess from active drawer
    - Rejects if turn is expired or not in drawing phase
    - Guards against duplicate correct guesses
    - Awards speed bonus and base score
    - Checks if all eligible guessers have guessed
    """
    if turn.phase != 'drawing' or turn.is_expired:
        return {'is_correct': False, 'rejected_reason': 'Round is not in drawing phase'}

    if player.id == turn.drawer.id:
        return {'is_correct': False, 'rejected_reason': 'Drawer cannot guess the word'}

    # Check if this player already guessed correctly in this turn
    already_correct = Guess.objects.filter(turn=turn, player=player, is_correct=True).exists()
    if already_correct:
        return {'is_correct': True, 'already_awarded': True}

    normalized_input = normalize_guess(guess_text)
    normalized_target = normalize_guess(turn.secret_word)

    if not normalized_input:
        return {'is_correct': False}

    if normalized_input == normalized_target:
        # Correct guess!
        remaining = turn.remaining_seconds
        base_points, speed_bonus = calculate_guesser_points(remaining, turn.turn_duration)
        total_points = base_points + speed_bonus

        with transaction.atomic():
            Guess.objects.create(
                turn=turn,
                player=player,
                text=guess_text,
                is_correct=True,
                points_awarded=total_points,
                speed_bonus=speed_bonus,
                remaining_seconds=remaining,
            )

            # Update match score
            player.match_score += total_points
            player.save(update_fields=['match_score'])

            # Update career stats
            profile = player.player
            profile.correct_guesses += 1
            profile.total_score += total_points
            profile.save(update_fields=['correct_guesses', 'total_score'])

        # Check if all eligible opponents have guessed correctly
        room = turn.match.room
        eligible_opponents = room.players.exclude(id=turn.drawer.id).count()
        correct_count = Guess.objects.filter(turn=turn, is_correct=True).values('player').distinct().count()
        all_guessed = (correct_count >= eligible_opponents) and (eligible_opponents > 0)

        return {
            'is_correct': True,
            'points': total_points,
            'speed_bonus': speed_bonus,
            'remaining_seconds': remaining,
            'all_guessed': all_guessed,
            'player_nickname': player.nickname,
            'player_id': str(player.id),
        }

    # Incorrect guess - log it
    Guess.objects.create(
        turn=turn,
        player=player,
        text=guess_text[:150],
        is_correct=False,
        points_awarded=0,
    )
    return {'is_correct': False}

def finish_turn(turn: GameTurn) -> dict:
    """
    Completes a turn, calculates drawer score, reveals results.
    Guaranteed idempotent with result_processed flag.
    """
    if turn.result_processed:
        return get_turn_results_summary(turn)

    with transaction.atomic():
        room = turn.match.room
        eligible_opponents = room.players.exclude(id=turn.drawer.id).count()
        correct_guesses = Guess.objects.filter(turn=turn, is_correct=True).select_related('player')
        correct_player_ids = set(g.player_id for g in correct_guesses)
        num_correct = len(correct_player_ids)

        # Drawer scoring
        drawer_points = calculate_drawer_points(num_correct, eligible_opponents)
        drawer = turn.drawer
        drawer.match_score += drawer_points
        drawer.save(update_fields=['match_score'])

        drawer_profile = drawer.player
        drawer_profile.total_score += drawer_points
        drawer_profile.save(update_fields=['total_score'])

        # Create RoundResult records
        RoundResult.objects.get_or_create(
            turn=turn,
            player=drawer,
            defaults={
                'role': 'drawer',
                'points_awarded': drawer_points,
                'guessed_correctly': num_correct > 0,
            }
        )

        for guess in correct_guesses:
            RoundResult.objects.get_or_create(
                turn=turn,
                player=guess.player,
                defaults={
                    'role': 'guesser',
                    'points_awarded': guess.points_awarded,
                    'speed_bonus': guess.speed_bonus,
                    'guessed_correctly': True,
                }
            )

        turn.phase = 'round_results'
        turn.result_processed = True
        turn.save(update_fields=['phase', 'result_processed'])

    return get_turn_results_summary(turn)

def get_turn_results_summary(turn: GameTurn) -> dict:
    """
    Returns complete breakdown of the completed turn.
    """
    results = RoundResult.objects.filter(turn=turn).select_related('player')
    leaderboard = [p.to_dict() for p in turn.match.room.players.order_by('-match_score')]

    return {
        'turn_number': turn.turn_number,
        'round_number': turn.round_number,
        'secret_word': turn.secret_word,
        'category': turn.category,
        'drawer_nickname': turn.drawer.nickname,
        'drawer_id': str(turn.drawer.id),
        'results': [
            {
                'player_id': str(r.player.id),
                'nickname': r.player.nickname,
                'avatar': r.player.avatar,
                'avatar_info': r.player.avatar_info,
                'role': r.role,
                'points_awarded': r.points_awarded,
                'speed_bonus': r.speed_bonus,
                'guessed_correctly': r.guessed_correctly,
            }
            for r in results
        ],
        'leaderboard': leaderboard,
    }

def advance_to_next_turn(match: GameMatch) -> dict:
    """
    Advances turn index. If round is complete, increments round.
    If all rounds complete, marks match finished and calculates final standings.
    """
    num_players = len(match.turn_order)
    next_index = match.current_turn_index + 1

    if next_index >= num_players:
        # Full rotation complete! Next round
        next_round = match.round_number + 1
        if next_round > match.total_rounds:
            # Match is finished!
            with transaction.atomic():
                match.status = 'finished'
                match.finished_at = timezone.now()
                match.save(update_fields=['status', 'finished_at'])

                room = match.room
                room.status = 'finished'
                room.save(update_fields=['status'])

                # Update player career win counts
                players = list(room.players.order_by('-match_score'))
                if players:
                    winner = players[0]
                    winner_profile = winner.player
                    winner_profile.games_won += 1
                    winner_profile.save(update_fields=['games_won'])

                for p in players:
                    prof = p.player
                    prof.games_played += 1
                    prof.save(update_fields=['games_played'])

            return {
                'status': 'match_finished',
                'leaderboard': [p.to_dict() for p in room.players.order_by('-match_score')],
                'winner': players[0].to_dict() if players else None,
            }
        else:
            match.round_number = next_round
            match.current_turn_index = 0
            match.save(update_fields=['round_number', 'current_turn_index'])
    else:
        match.current_turn_index = next_index
        match.save(update_fields=['current_turn_index'])

    new_turn = start_new_turn(match)
    return {
        'status': 'turn_started',
        'turn': new_turn,
    }
