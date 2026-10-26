/**
 * DRAW & DECEIVE - Game Orchestration & UI Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  const roomCode = window.ROOM_CODE;
  const currentUserId = window.CURRENT_PLAYER_ID;
  const isHostInitial = window.IS_HOST;

  if (!roomCode) return;

  // Initialize socket
  const socket = new RoomSocket(roomCode);
  window.appSocket = socket;

  // Initialize canvas
  const canvasEl = document.getElementById('drawing-canvas');
  let drawingEngine = null;
  if (canvasEl) {
    drawingEngine = new DrawingEngine(canvasEl, socket, { canDraw: false });
    window.drawingEngine = drawingEngine;
  }

  // UI Element References
  const lobbyContainer = document.getElementById('lobby-container');
  const gameArenaContainer = document.getElementById('game-arena-container');
  const roundResultsModal = document.getElementById('round-results-modal');
  const matchResultsModal = document.getElementById('match-results-modal');

  // Top Bar elements
  const roundPillText = document.getElementById('game-round-text');
  const drawerNameText = document.getElementById('game-drawer-name');
  const drawerAvatarBox = document.getElementById('game-drawer-avatar');
  const wordDisplay = document.getElementById('game-word-display');
  const categoryTag = document.getElementById('game-category-tag');
  const timerDisplay = document.getElementById('game-timer');

  // Drawing toolbar
  const drawingToolbar = document.getElementById('drawing-toolbar');
  const spectatorBadge = document.getElementById('spectator-badge');

  // Leaderboard & Chat
  const leaderboardList = document.getElementById('leaderboard-list');
  const chatMessages = document.getElementById('chat-messages');
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');

  // Lobby elements
  const lobbyPlayersGrid = document.getElementById('lobby-players-grid');
  const lobbyPlayerCount = document.getElementById('lobby-player-count');
  const btnStartMatch = document.getElementById('btn-start-match');
  const btnToggleReady = document.getElementById('btn-toggle-ready');
  const copyInviteBtn = document.getElementById('btn-copy-invite');

  let currentTurnData = null;
  let isCurrentDrawer = false;

  // -------------------------------------------------------------
  // Copy Invite Link Handler
  // -------------------------------------------------------------
  if (copyInviteBtn) {
    copyInviteBtn.addEventListener('click', () => {
      const inviteUrl = window.location.href;
      navigator.clipboard.writeText(inviteUrl).then(() => {
        showToast("Invite link copied to clipboard! 📋", "success");
        if (window.soundFx) window.soundFx.playPop();
      }).catch(() => {
        showToast("Failed to copy link.", "error");
      });
    });
  }

  // -------------------------------------------------------------
  // Ready & Start Game Buttons
  // -------------------------------------------------------------
  if (btnToggleReady) {
    btnToggleReady.addEventListener('click', () => {
      socket.send('room.ready', {});
      if (window.soundFx) window.soundFx.playPop();
    });
  }

  if (btnStartMatch) {
    btnStartMatch.addEventListener('click', () => {
      socket.send('game.start', {});
      if (window.soundFx) window.soundFx.playPop();
    });
  }

  // -------------------------------------------------------------
  // Chat & Guess Submission
  // -------------------------------------------------------------
  if (chatForm && chatInput) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;

      if (isCurrentDrawer) {
        // Drawer chats
        socket.send('game.chat', { text });
      } else {
        // Guesser submits guess
        socket.send('game.guess', { text });
      }

      chatInput.value = '';
      if (window.soundFx) window.soundFx.playPop();
    });
  }

  // -------------------------------------------------------------
  // Toolbar Tool Handlers
  // -------------------------------------------------------------
  setupDrawingToolbar(drawingEngine);

  // -------------------------------------------------------------
  // WebSocket Event Listeners
  // -------------------------------------------------------------

  socket.on('room.snapshot', (data) => {
    updateLobbyUI(data);
  });

  socket.on('room.player_joined', (data) => {
    showToast(data.message, 'info');
    socket.send('game.request_state', {});
  });

  socket.on('room.player_left', (data) => {
    showToast(`${data.nickname} left the room.`, 'info');
    socket.send('game.request_state', {});
  });

  socket.on('game.turn_started', (data) => {
    onTurnStarted(data);
  });

  socket.on('game.secret_word', (data) => {
    onSecretWordReceived(data);
  });

  socket.on('drawing.stroke', (data) => {
    if (drawingEngine) {
      drawingEngine.renderRemoteStroke(data);
    }
  });

  socket.on('drawing.undo', (data) => {
    if (drawingEngine) {
      drawingEngine.undoStroke(data.stroke_id);
    }
  });

  socket.on('drawing.cleared', () => {
    if (drawingEngine) {
      drawingEngine.clearCanvas();
      showToast("Canvas cleared", "info");
    }
  });

  socket.on('game.timer_update', (data) => {
    updateTimer(data.remaining_seconds);
  });

  socket.on('game.hint_update', (data) => {
    onHintUpdate(data);
  });

  socket.on('game.guess_correct', (data) => {
    onCorrectGuess(data);
  });

  socket.on('game.chat_message', (data) => {
    appendChatMessage(data);
  });

  socket.on('game.round_results', (data) => {
    onRoundResults(data);
  });

  socket.on('game.match_results', (data) => {
    onMatchResults(data);
  });

  socket.on('game.state_recovery', (data) => {
    onStateRecovery(data);
  });

  socket.on('error', (data) => {
    showToast(data.message || 'An error occurred', 'error');
  });

  // Start connection
  socket.connect();

  // -------------------------------------------------------------
  // Core Game Event Handlers
  // -------------------------------------------------------------

  function onTurnStarted(data) {
    currentTurnData = data;
    closeModals();

    // Switch view to active game
    if (lobbyContainer) lobbyContainer.style.display = 'none';
    if (gameArenaContainer) gameArenaContainer.style.display = 'flex';

    if (drawingEngine) {
      drawingEngine.clearCanvas();
    }

    // Determine if current player is the drawer
    isCurrentDrawer = (String(data.drawer_id) === String(currentUserId));
    if (drawingEngine) {
      drawingEngine.setCanDraw(isCurrentDrawer);
    }

    // Toggle drawer toolbar vs spectator badge
    if (drawingToolbar) drawingToolbar.style.display = isCurrentDrawer ? 'flex' : 'none';
    if (spectatorBadge) spectatorBadge.style.display = isCurrentDrawer ? 'none' : 'flex';

    // Update Header
    if (roundPillText) roundPillText.textContent = `Round ${data.round_number} / ${data.total_rounds}`;
    if (drawerNameText) drawerNameText.textContent = data.drawer_nickname + (isCurrentDrawer ? " (You!)" : "");
    if (categoryTag) categoryTag.textContent = data.category || 'General';

    // Word display for guessers (masked)
    if (!isCurrentDrawer && wordDisplay) {
      wordDisplay.textContent = data.masked_word;
      wordDisplay.classList.remove('drawer-word');
    }

    updateTimer(data.turn_duration);
    updateLeaderboard(data.leaderboard, data.drawer_id);

    appendChatMessage({
      text: isCurrentDrawer 
        ? "🎨 It's your turn to draw! Check your secret word above."
        : `✏️ ${data.drawer_nickname} is now drawing! Guess the word in chat!`,
      is_system: true,
      msg_type: 'system',
    });

    if (window.soundFx) window.soundFx.playPop();
  }

  function onSecretWordReceived(data) {
    // Secret word delivered privately to the drawer
    if (wordDisplay) {
      wordDisplay.textContent = data.secret_word;
      wordDisplay.classList.add('drawer-word');
    }
    if (categoryTag) {
      categoryTag.textContent = data.category + (data.hint ? ` • Hint: ${data.hint}` : "");
    }
  }

  function onHintUpdate(data) {
    if (!isCurrentDrawer && wordDisplay) {
      wordDisplay.textContent = data.masked_word;
      if (data.hint_text && categoryTag) {
        categoryTag.textContent = `${data.category} • Hint: ${data.hint_text}`;
      }
      showToast("💡 A letter was revealed!", "info");
      if (window.soundFx) window.soundFx.playPop();
    }
  }

  function onCorrectGuess(data) {
    if (window.soundFx) window.soundFx.playSuccess();
    appendChatMessage({
      text: data.message,
      is_system: true,
      msg_type: 'correct-guess',
    });
    updateLeaderboard(data.leaderboard);
  }

  function updateTimer(seconds) {
    if (!timerDisplay) return;
    timerDisplay.textContent = seconds;
    timerDisplay.classList.remove('warning', 'danger');

    if (seconds <= 10 && seconds > 0) {
      timerDisplay.classList.add('danger');
      if (window.soundFx) window.soundFx.playTick();
    } else if (seconds <= 20) {
      timerDisplay.classList.add('warning');
    }
  }

  function onRoundResults(data) {
    if (drawingEngine) drawingEngine.setCanDraw(false);
    if (roundResultsModal) {
      document.getElementById('result-secret-word').textContent = data.secret_word;
      
      const tbody = document.getElementById('round-results-tbody');
      tbody.innerHTML = '';
      (data.results || []).forEach((r) => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td><strong>${escapeHtml(r.nickname)}</strong> ${r.role === 'drawer' ? '🎨' : ''}</td>
          <td>${r.role === 'drawer' ? 'Drawer' : (r.guessed_correctly ? '✓ Guessed' : '—')}</td>
          <td><span style="color:var(--accent-green);font-weight:800;">+${r.points_awarded}</span></td>
        `;
        tbody.appendChild(row);
      });

      roundResultsModal.classList.add('active');
    }
    updateLeaderboard(data.leaderboard);
  }

  function onMatchResults(data) {
    if (roundResultsModal) roundResultsModal.classList.remove('active');
    if (drawingEngine) drawingEngine.setCanDraw(false);

    if (matchResultsModal) {
      const winners = data.leaderboard || [];
      const winner = winners[0];

      if (winner) {
        document.getElementById('winner-nickname').textContent = winner.nickname;
        document.getElementById('winner-score').textContent = `${winner.match_score} pts`;
      }

      const matchTbody = document.getElementById('match-results-tbody');
      if (matchTbody) {
        matchTbody.innerHTML = '';
        winners.forEach((p, idx) => {
          const row = document.createElement('tr');
          row.innerHTML = `
            <td>#${idx + 1}</td>
            <td><strong>${escapeHtml(p.nickname)}</strong></td>
            <td><strong style="color:var(--accent-amber);">${p.match_score}</strong></td>
          `;
          matchTbody.appendChild(row);
        });
      }

      matchResultsModal.classList.add('active');
      if (window.soundFx) window.soundFx.playFanfare();
    }
  }

  function onStateRecovery(data) {
    if (data.match_active && data.turn) {
      if (lobbyContainer) lobbyContainer.style.display = 'none';
      if (gameArenaContainer) gameArenaContainer.style.display = 'flex';

      const turn = data.turn;
      isCurrentDrawer = turn.is_drawer;
      if (drawingEngine) {
        drawingEngine.setCanDraw(isCurrentDrawer);
        drawingEngine.loadStrokes(turn.strokes || []);
      }

      if (drawingToolbar) drawingToolbar.style.display = isCurrentDrawer ? 'flex' : 'none';
      if (spectatorBadge) spectatorBadge.style.display = isCurrentDrawer ? 'none' : 'flex';

      if (roundPillText) roundPillText.textContent = `Round ${turn.round_number} / ${turn.total_rounds}`;
      if (drawerNameText) drawerNameText.textContent = turn.drawer_nickname + (isCurrentDrawer ? " (You!)" : "");
      if (categoryTag) categoryTag.textContent = turn.category;

      if (wordDisplay) {
        wordDisplay.textContent = isCurrentDrawer ? turn.secret_word : turn.masked_word;
        if (isCurrentDrawer) wordDisplay.classList.add('drawer-word');
      }

      updateTimer(turn.remaining_seconds);
      updateLeaderboard(turn.leaderboard, turn.drawer_id);
    } else {
      updateLobbyUI(data.room);
    }

    // Load recent chats
    if (chatMessages && data.recent_chats) {
      chatMessages.innerHTML = '';
      data.recent_chats.forEach(appendChatMessage);
    }
  }

  // -------------------------------------------------------------
  // UI Helpers
  // -------------------------------------------------------------

  function updateLobbyUI(room) {
    if (!room) return;
    if (lobbyPlayerCount) {
      lobbyPlayerCount.textContent = `(${room.player_count}/${room.max_players} Players)`;
    }

    if (lobbyPlayersGrid) {
      lobbyPlayersGrid.innerHTML = '';
      (room.players || []).forEach((player) => {
        const card = document.createElement('div');
        card.className = 'lobby-player-card';
        card.innerHTML = `
          <div class="player-avatar-large" style="background:${player.avatar_info.bg};">
            ${player.avatar_info.emoji}
            ${player.is_host ? '<div class="host-badge-icon" title="Host">★</div>' : ''}
          </div>
          <div class="player-card-name">${escapeHtml(player.nickname)}</div>
          <div class="player-status-tag ${player.is_ready ? 'ready' : 'waiting'}">
            ${player.is_ready ? 'READY ✓' : 'WAITING'}
          </div>
        `;
        lobbyPlayersGrid.appendChild(card);
      });

      // Show empty slots
      const emptySlots = room.max_players - room.player_count;
      for (let i = 0; i < Math.min(emptySlots, 4); i++) {
        const slot = document.createElement('div');
        slot.className = 'lobby-slot-empty';
        slot.innerHTML = `<span>➕</span><span>Open Slot</span>`;
        lobbyPlayersGrid.appendChild(slot);
      }
    }

    if (btnStartMatch) {
      btnStartMatch.disabled = !room.can_start;
      const warningText = document.getElementById('lobby-min-players-note');
      if (warningText) {
        warningText.style.display = room.can_start ? 'none' : 'block';
      }
    }
  }

  function updateLeaderboard(players, activeDrawerId) {
    if (!leaderboardList || !players) return;
    leaderboardList.innerHTML = '';

    players.forEach((p, idx) => {
      const item = document.createElement('div');
      const isMe = String(p.player_id) === String(currentUserId);
      const isDrawing = activeDrawerId && String(p.id) === String(activeDrawerId);

      item.className = `leaderboard-item ${isMe ? 'is-me' : ''} ${isDrawing ? 'is-drawing' : ''}`;
      item.innerHTML = `
        <div class="player-meta-left">
          <span class="rank-number">#${idx + 1}</span>
          <div class="player-avatar-small" style="background:${p.avatar_info.bg};">
            ${p.avatar_info.emoji}
          </div>
          <div class="player-name-col">
            <span class="lb-player-name">${escapeHtml(p.nickname)} ${isMe ? '(You)' : ''}</span>
            <span class="lb-status-text ${isDrawing ? 'drawing' : ''}">
              ${isDrawing ? '✏️ Drawing' : ''}
            </span>
          </div>
        </div>
        <span class="lb-score-value">${p.match_score}</span>
      `;
      leaderboardList.appendChild(item);
    });
  }

  function appendChatMessage(msg) {
    if (!chatMessages) return;
    const el = document.createElement('div');
    const isSystem = msg.is_system;
    const msgType = msg.msg_type || (isSystem ? 'system' : 'chat');

    el.className = `chat-msg ${msgType}`;
    if (isSystem) {
      el.textContent = msg.text;
    } else {
      el.innerHTML = `
        <span class="sender">${escapeHtml(msg.sender || 'Player')}:</span>
        <span class="text">${escapeHtml(msg.text)}</span>
      `;
    }

    chatMessages.appendChild(el);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function closeModals() {
    if (roundResultsModal) roundResultsModal.classList.remove('active');
    if (matchResultsModal) matchResultsModal.classList.remove('active');
  }

  function setupDrawingToolbar(engine) {
    if (!engine) return;

    // Tool buttons
    document.querySelectorAll('.tool-btn[data-tool]').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tool-btn[data-tool]').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        engine.currentTool = btn.dataset.tool;
      });
    });

    // Swatches
    document.querySelectorAll('.color-swatch').forEach((swatch) => {
      swatch.addEventListener('click', () => {
        document.querySelectorAll('.color-swatch').forEach((s) => s.classList.remove('active'));
        swatch.classList.add('active');
        engine.currentColor = swatch.dataset.color;
      });
    });

    // Custom Color Input
    const colorPicker = document.getElementById('custom-color-picker');
    if (colorPicker) {
      colorPicker.addEventListener('input', (e) => {
        engine.currentColor = e.target.value;
      });
    }

    // Brush Sizes
    document.querySelectorAll('.size-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.size-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        engine.brushSize = parseInt(btn.dataset.size, 10);
      });
    });

    // Undo & Clear
    const btnUndo = document.getElementById('btn-undo');
    if (btnUndo) {
      btnUndo.addEventListener('click', () => engine.triggerUndo());
    }

    const btnClear = document.getElementById('btn-clear');
    if (btnClear) {
      btnClear.addEventListener('click', () => engine.triggerClear());
    }

    // Play again
    const btnPlayAgain = document.getElementById('btn-play-again');
    if (btnPlayAgain) {
      btnPlayAgain.addEventListener('click', () => {
        socket.send('game.play_again', {});
      });
    }
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3200);
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
});
