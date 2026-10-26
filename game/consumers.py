import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from accounts.models import PlayerProfile
from rooms.models import GameRoom, RoomPlayer
from rooms.services import get_room_snapshot
from words.services import format_masked_hint, calculate_revealed_indices
from .models import GameMatch, GameTurn, DrawingStroke, Guess, ChatMessage, RoundResult
from . import engine

# Global active turn timers tracked by room code to prevent duplicate loops
ACTIVE_TIMERS = {}

class DrawAndDeceiveConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code'].upper()
        self.room_group_name = f"room_{self.room_code}"
        self.session = self.scope.get('session')

        if not self.session or not self.session.session_key:
            await self.close(code=4001)
            return

        # Fetch authenticated player & membership
        self.player, self.room, self.room_player = await self.get_player_and_room()

        if not self.room or not self.room_player:
            await self.close(code=4004)
            return

        # Accept connection and join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        self.player_group_name = f"player_{self.room_player.id}"
        await self.channel_layer.group_add(self.player_group_name, self.channel_name)
        await self.accept()

        # Mark player connected
        await self.set_player_connected(True)
        player_dict = await self.get_room_player_dict()

        # Notify room of player arrival
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_event',
                'event': 'room.player_joined',
                'data': {
                    'player': player_dict,
                    'message': f"{self.room_player.nickname} joined the game!",
                }
            }
        )

        # Send initial full state snapshot to the connecting client
        await self.send_room_snapshot()

    async def disconnect(self, close_code):
        if hasattr(self, 'player_group_name'):
            await self.channel_layer.group_discard(self.player_group_name, self.channel_name)
        if hasattr(self, 'room_group_name'):
            await self.set_player_connected(False)
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_event',
                    'event': 'room.player_left',
                    'data': {
                        'player_id': str(self.room_player.id) if self.room_player else None,
                        'nickname': self.room_player.nickname if self.room_player else 'Player',
                    }
                }
            )

    async def receive(self, text_data):
        try:
            payload = json.loads(text_data)
        except Exception:
            await self.send_error("Invalid JSON payload.")
            return

        event_type = payload.get('type')
        data = payload.get('data', {})

        if event_type == 'game.request_state':
            await self.handle_request_state()

        elif event_type == 'room.ready':
            await self.handle_room_ready(data)

        elif event_type == 'game.start':
            await self.handle_game_start()

        elif event_type == 'drawing.stroke':
            await self.handle_drawing_stroke(data)

        elif event_type == 'drawing.undo':
            await self.handle_drawing_undo()

        elif event_type == 'drawing.clear':
            await self.handle_drawing_clear()

        elif event_type == 'game.guess':
            await self.handle_game_guess(data)

        elif event_type == 'game.chat':
            await self.handle_game_chat(data)

        elif event_type == 'game.play_again':
            await self.handle_play_again()

        else:
            await self.send_error(f"Unknown event type '{event_type}'.")

    # -------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------

    async def handle_request_state(self):
        """
        Sends full current state for reconnection / recovery.
        """
        state = await self.get_full_game_state()
        await self.send_json({
            'type': 'game.state_recovery',
            'data': state,
        })

    async def handle_room_ready(self, data):
        """
        Toggles or sets readiness for current player.
        """
        is_ready = bool(data.get('is_ready', not self.room_player.is_ready))
        await self.set_player_ready(is_ready)
        snapshot = await self.get_snapshot()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_event',
                'event': 'room.snapshot',
                'data': snapshot,
            }
        )

    async def handle_game_start(self):
        """
        Starts match and initial turn. Authorized for host only.
        """
        is_host = await self.check_is_host()
        if not is_host:
            await self.send_error("Only the room host can start the game.")
            return

        try:
            match, turn = await database_sync_to_async(engine.start_match)(self.room, self.room_player)
        except engine.GameEngineError as e:
            await self.send_error(str(e))
            return

        # Broadcast turn start
        await self.broadcast_turn_start(turn)

        # Start server-side timer task for this room
        self.start_timer_task(turn.id)

    async def handle_drawing_stroke(self, data):
        """
        Validates drawer authority, saves stroke, broadcasts to other clients.
        """
        current_turn = await self.get_active_drawing_turn()
        if not current_turn:
            return

        if current_turn.drawer_id != self.room_player.id:
            await self.send_error("Only the active drawer can draw.")
            return

        # Validate stroke fields
        stroke_id = str(data.get('stroke_id', ''))
        tool_type = str(data.get('tool_type', 'brush'))[:20]
        color = str(data.get('color', '#000000'))[:30]
        brush_size = max(1, min(60, int(data.get('brush_size', 4))))
        points = data.get('points', [])

        if not points or not isinstance(points, list):
            return

        # Cap stroke points to prevent unbounded payload abuse
        points = points[:500]

        # Persist stroke in DB
        await self.save_drawing_stroke(current_turn, stroke_id, tool_type, color, brush_size, points)

        # Broadcast to room (exclude drawer sender to prevent duplicate rendering)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_drawing_stroke',
                'sender_channel': self.channel_name,
                'data': {
                    'stroke_id': stroke_id,
                    'tool_type': tool_type,
                    'color': color,
                    'brush_size': brush_size,
                    'points': points,
                }
            }
        )

    async def handle_drawing_undo(self):
        """
        Removes the last stroke by the active drawer.
        """
        current_turn = await self.get_active_drawing_turn()
        if not current_turn or current_turn.drawer_id != self.room_player.id:
            return

        undone_id = await self.undo_last_stroke(current_turn)
        if undone_id:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_event',
                    'event': 'drawing.undo',
                    'data': {'stroke_id': undone_id}
                }
            )

    async def handle_drawing_clear(self):
        """
        Clears all active strokes for current turn.
        """
        current_turn = await self.get_active_drawing_turn()
        if not current_turn or current_turn.drawer_id != self.room_player.id:
            return

        await self.clear_turn_strokes(current_turn)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_event',
                'event': 'drawing.cleared',
                'data': {'cleared_by': self.room_player.nickname}
            }
        )

    async def handle_game_guess(self, data):
        """
        Processes a guess from a non-drawing player.
        """
        guess_text = str(data.get('text', '')).strip()[:150]
        if not guess_text:
            return

        current_turn = await self.get_active_drawing_turn()
        if not current_turn:
            await self.handle_game_chat({'text': guess_text})
            return

        if current_turn.drawer_id == self.room_player.id:
            # Drawer chatting, not guessing
            await self.handle_game_chat({'text': guess_text})
            return

        # Process guess against secret word
        result = await database_sync_to_async(engine.process_guess)(current_turn, self.room_player, guess_text)

        if result.get('is_correct'):
            if result.get('already_awarded'):
                await self.send_json({
                    'type': 'game.chat_message',
                    'data': {
                        'text': "You already guessed the word! Shh, let others guess!",
                        'sender': "Game System",
                        'is_system': True,
                        'msg_type': 'system',
                    }
                })
                return

            # Public celebration notice
            leaderboard = await self.get_leaderboard()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'broadcast_event',
                    'event': 'game.guess_correct',
                    'data': {
                        'player_id': str(self.room_player.id),
                        'nickname': self.room_player.nickname,
                        'avatar': self.room_player.avatar,
                        'avatar_info': self.room_player.avatar_info,
                        'points': result['points'],
                        'speed_bonus': result['speed_bonus'],
                        'leaderboard': leaderboard,
                        'message': f"🎉 {self.room_player.nickname} guessed the secret word! (+{result['points']} pts)",
                    }
                }
            )

            # If all eligible players guessed, end the turn early
            if result.get('all_guessed'):
                # Cancel timer and trigger finish turn
                self.trigger_early_finish(current_turn.id)
        else:
            # Broadcast as chat message
            await self.handle_game_chat({'text': guess_text, 'msg_type': 'guess'})

    async def handle_game_chat(self, data):
        """
        Broadcasts a regular chat message.
        """
        text = str(data.get('text', '')).strip()[:200]
        if not text:
            return

        msg_type = data.get('msg_type', 'chat')
        chat_msg = await self.save_chat_message(text, msg_type)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_event',
                'event': 'game.chat_message',
                'data': chat_msg.to_dict(),
            }
        )

    async def handle_play_again(self):
        """
        Restarts match for another round series.
        """
        is_host = await self.check_is_host()
        if not is_host:
            await self.send_error("Only the host can start a new match.")
            return

        try:
            match, turn = await database_sync_to_async(engine.start_match)(self.room, self.room_player)
        except engine.GameEngineError as e:
            await self.send_error(str(e))
            return

        await self.broadcast_turn_start(turn)
        self.start_timer_task(turn.id)

    # -------------------------------------------------------------
    # Broadcast / Event Handlers
    # -------------------------------------------------------------

    async def broadcast_event(self, event):
        """
        Relays public broadcast events to this client.
        """
        await self.send_json({
            'type': event['event'],
            'data': event['data'],
        })

    async def broadcast_drawing_stroke(self, event):
        """
        Sends drawing stroke to all clients except the sender.
        """
        if event.get('sender_channel') != self.channel_name:
            await self.send_json({
                'type': 'drawing.stroke',
                'data': event['data'],
            })

    async def broadcast_secret_word(self, event):
        """
        Receives private secret word intended only for this drawer.
        """
        await self.send_json({
            'type': 'game.secret_word',
            'data': event['data'],
        })

    async def broadcast_turn_start(self, turn):
        """
        Broadcasts turn start:
        - Sends public masked word and category to the room group.
        - Sends secret word privately to the drawer's personal group.
        """
        turn_data = await self.get_turn_data(turn)

        # Public broadcast (secret word masked!)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_event',
                'event': 'game.turn_started',
                'data': turn_data['public'],
            }
        )

        # Secret word sent privately to the drawer's personal player group!
        await self.channel_layer.group_send(
            f"player_{turn.drawer_id}",
            {
                'type': 'broadcast_secret_word',
                'data': turn_data['private'],
            }
        )

    # -------------------------------------------------------------
    # Timers and Phase Progression
    # -------------------------------------------------------------

    def start_timer_task(self, turn_id):
        """
        Spawns server-side asyncio timer loop for active turn.
        """
        room_code = self.room_code
        if room_code in ACTIVE_TIMERS:
            ACTIVE_TIMERS[room_code].cancel()

        task = asyncio.create_task(self.run_turn_timer(turn_id, room_code))
        ACTIVE_TIMERS[room_code] = task

    def trigger_early_finish(self, turn_id):
        """
        Interrupts timer when all players have guessed.
        """
        room_code = self.room_code
        if room_code in ACTIVE_TIMERS:
            ACTIVE_TIMERS[room_code].cancel()

        task = asyncio.create_task(self.conclude_turn_early(turn_id, room_code))
        ACTIVE_TIMERS[room_code] = task

    async def conclude_turn_early(self, turn_id, room_code):
        """
        Finishes turn immediately when all guessers got it right.
        """
        turn = await database_sync_to_async(GameTurn.objects.select_related('match', 'match__room', 'drawer').filter(id=turn_id).first)()
        if turn:
            await self.finish_and_advance_turn(turn, room_code)

    async def run_turn_timer(self, turn_id, room_code):
        """
        Authoritative countdown loop:
        - Emits second ticks
        - Reveals hints at 50% and 75% time elapsed
        - Finishes turn on timeout
        """
        try:
            turn = await database_sync_to_async(GameTurn.objects.select_related('match', 'match__room', 'drawer').filter(id=turn_id).first)()
            if not turn:
                return

            total_seconds = turn.turn_duration
            half_mark = total_seconds // 2
            quarter_mark = total_seconds // 4

            while True:
                now = timezone.now()
                remaining = max(0, int((turn.deadline - now).total_seconds()))

                # Broadcast timer tick every second
                await self.channel_layer.group_send(
                    f"room_{room_code}",
                    {
                        'type': 'broadcast_event',
                        'event': 'game.timer_update',
                        'data': {'remaining_seconds': remaining}
                    }
                )

                # Progressive Hints
                if remaining <= half_mark and turn.hint_stage < 1:
                    await self.update_hint_stage(turn, 1, room_code)

                if remaining <= quarter_mark and turn.hint_stage < 2:
                    await self.update_hint_stage(turn, 2, room_code)

                if remaining <= 0:
                    break

                await asyncio.sleep(1)

            # Turn expired! Complete turn
            await self.finish_and_advance_turn(turn, room_code)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in turn timer: {e}")

    async def update_hint_stage(self, turn, stage, room_code):
        """
        Reveals letters in the masked word as time passes.
        """
        turn.hint_stage = stage
        await database_sync_to_async(turn.save)(update_fields=['hint_stage'])

        revealed = calculate_revealed_indices(turn.secret_word, stage)
        masked = format_masked_hint(turn.secret_word, revealed)

        await self.channel_layer.group_send(
            f"room_{room_code}",
            {
                'type': 'broadcast_event',
                'event': 'game.hint_update',
                'data': {
                    'hint_stage': stage,
                    'masked_word': masked,
                    'category': turn.category,
                    'hint_text': turn.hint if stage >= 2 and turn.hint else "",
                }
            }
        )

    async def finish_and_advance_turn(self, turn, room_code):
        """
        Finishes current turn, reveals round results, waits for review, then advances to next turn.
        """
        # Calculate results and reveal secret word
        results_summary = await database_sync_to_async(engine.finish_turn)(turn)

        await self.channel_layer.group_send(
            f"room_{room_code}",
            {
                'type': 'broadcast_event',
                'event': 'game.round_results',
                'data': results_summary,
            }
        )

        # Wait 7 seconds for round results screen
        await asyncio.sleep(7)

        # Advance state
        match = await database_sync_to_async(GameMatch.objects.select_related('room').filter(id=turn.match_id).first)()
        if not match:
            return

        advance_result = await database_sync_to_async(engine.advance_to_next_turn)(match)

        if advance_result['status'] == 'match_finished':
            await self.channel_layer.group_send(
                f"room_{room_code}",
                {
                    'type': 'broadcast_event',
                    'event': 'game.match_results',
                    'data': {
                        'leaderboard': advance_result['leaderboard'],
                        'winner': advance_result['winner'],
                        'message': "Match finished! Celebrate the champion!",
                    }
                }
            )
        else:
            new_turn = advance_result['turn']
            turn_data = await self.get_turn_data(new_turn)

            await self.channel_layer.group_send(
                f"room_{room_code}",
                {
                    'type': 'broadcast_event',
                    'event': 'game.turn_started',
                    'data': turn_data['public'],
                }
            )

            # Send secret word privately to new drawer
            await self.channel_layer.group_send(
                f"player_{new_turn.drawer_id}",
                {
                    'type': 'broadcast_secret_word',
                    'data': turn_data['private'],
                }
            )

            # Start timer for new turn
            self.start_timer_task(new_turn.id)

    # -------------------------------------------------------------
    # Database helpers (sync_to_async)
    # -------------------------------------------------------------

    @database_sync_to_async
    def get_player_and_room(self):
        try:
            player = PlayerProfile.objects.get(session_key=self.session.session_key)
            room = GameRoom.objects.get(code=self.room_code)
            room_player = RoomPlayer.objects.select_related('player', 'room').filter(room=room, player=player).first()
            return player, room, room_player
        except Exception:
            return None, None, None

    @database_sync_to_async
    def get_room_player_dict(self):
        return self.room_player.to_dict() if self.room_player else {}

    @database_sync_to_async
    def set_player_connected(self, connected: bool):
        if self.room_player:
            self.room_player.is_connected = connected
            self.room_player.save(update_fields=['is_connected'])

    @database_sync_to_async
    def set_player_ready(self, ready: bool):
        if self.room_player:
            self.room_player.is_ready = ready
            self.room_player.save(update_fields=['is_ready'])

    @database_sync_to_async
    def check_is_host(self):
        if not self.room_player:
            return False
        return self.room_player.is_host or self.room.host_id == self.player.id

    @database_sync_to_async
    def get_snapshot(self):
        return get_room_snapshot(self.room)

    @database_sync_to_async
    def get_active_drawing_turn(self):
        match = GameMatch.objects.filter(room=self.room, status='active').first()
        if not match:
            return None
        return match.turns.filter(phase='drawing').order_by('-created_at').first()

    @database_sync_to_async
    def save_drawing_stroke(self, turn, stroke_id, tool_type, color, brush_size, points):
        seq = turn.strokes.count() + 1
        return DrawingStroke.objects.create(
            turn=turn,
            stroke_id=stroke_id,
            sequence_number=seq,
            player=self.room_player,
            tool_type=tool_type,
            color=color,
            brush_size=brush_size,
            points=points,
        )

    @database_sync_to_async
    def undo_last_stroke(self, turn):
        last_stroke = turn.strokes.filter(is_undone=False, player=self.room_player).order_by('-sequence_number').first()
        if last_stroke:
            last_stroke.is_undone = True
            last_stroke.save(update_fields=['is_undone'])
            return last_stroke.stroke_id
        return None

    @database_sync_to_async
    def clear_turn_strokes(self, turn):
        turn.strokes.filter(is_undone=False).update(is_undone=True)

    @database_sync_to_async
    def save_chat_message(self, text, msg_type='chat'):
        return ChatMessage.objects.create(
            room=self.room,
            player=self.room_player,
            text=text,
            is_system=False,
            msg_type=msg_type,
        )

    @database_sync_to_async
    def get_leaderboard(self):
        return [p.to_dict() for p in self.room.players.order_by('-match_score')]

    @database_sync_to_async
    def get_turn_data(self, turn):
        revealed = calculate_revealed_indices(turn.secret_word, turn.hint_stage)
        masked = format_masked_hint(turn.secret_word, revealed)
        leaderboard = [p.to_dict() for p in turn.match.room.players.order_by('-match_score')]

        public_data = {
            'turn_id': str(turn.id),
            'turn_number': turn.turn_number,
            'round_number': turn.round_number,
            'total_rounds': turn.match.total_rounds,
            'drawer_id': str(turn.drawer_id),
            'drawer_nickname': turn.drawer.nickname,
            'drawer_avatar': turn.drawer.avatar,
            'category': turn.category,
            'difficulty': turn.difficulty,
            'turn_duration': turn.turn_duration,
            'remaining_seconds': turn.remaining_seconds,
            'masked_word': masked,
            'word_length': len(turn.secret_word),
            'hint_stage': turn.hint_stage,
            'leaderboard': leaderboard,
        }

        private_data = {
            'secret_word': turn.secret_word,
            'category': turn.category,
            'hint': turn.hint,
        }

        return {'public': public_data, 'private': private_data}

    @database_sync_to_async
    def get_full_game_state(self):
        room_snap = get_room_snapshot(self.room)
        match = GameMatch.objects.filter(room=self.room, status='active').first()
        
        state = {
            'room': room_snap,
            'current_player': self.room_player.to_dict() if self.room_player else None,
            'match_active': match is not None,
        }

        if match:
            turn = match.current_turn
            if turn:
                revealed = calculate_revealed_indices(turn.secret_word, turn.hint_stage)
                masked = format_masked_hint(turn.secret_word, revealed)
                strokes = [s.to_dict() for s in turn.strokes.filter(is_undone=False)]
                is_drawer = (self.room_player and self.room_player.id == turn.drawer_id)

                state['turn'] = {
                    'turn_id': str(turn.id),
                    'turn_number': turn.turn_number,
                    'round_number': turn.round_number,
                    'total_rounds': match.total_rounds,
                    'phase': turn.phase,
                    'drawer_id': str(turn.drawer_id),
                    'drawer_nickname': turn.drawer.nickname,
                    'category': turn.category,
                    'difficulty': turn.difficulty,
                    'turn_duration': turn.turn_duration,
                    'remaining_seconds': turn.remaining_seconds,
                    'masked_word': masked,
                    'secret_word': turn.secret_word if is_drawer else None,
                    'is_drawer': is_drawer,
                    'strokes': strokes,
                    'leaderboard': [p.to_dict() for p in self.room.players.order_by('-match_score')],
                }

        # Recent chat messages
        chats = [c.to_dict() for c in self.room.chat_messages.order_by('-created_at')[:40]]
        chats.reverse()
        state['recent_chats'] = chats

        return state

    # -------------------------------------------------------------
    # Low-level network utilities
    # -------------------------------------------------------------

    async def send_room_snapshot(self):
        snapshot = await self.get_snapshot()
        await self.send_json({
            'type': 'room.snapshot',
            'data': snapshot,
        })

    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))

    async def send_error(self, message):
        await self.send_json({
            'type': 'error',
            'data': {'message': message}
        })
