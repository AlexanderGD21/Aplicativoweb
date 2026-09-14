(() => {
  'use strict';

  const categorySelect = document.getElementById('hub-category');
  const difficultySelect = document.getElementById('hub-difficulty');
  const updateHubLinks = () => {
    if (!categorySelect || !difficultySelect) return;
    const query = new URLSearchParams({ dificultad: difficultySelect.value });
    if (categorySelect.value) query.set('categoria', categorySelect.value);
    document.querySelectorAll('[data-game-url]').forEach((link) => {
      link.href = `${link.dataset.gameUrl}?${query.toString()}`;
    });
    const start = document.getElementById('start-learning');
    if (start) start.href = `${start.href.split('?')[0]}?${query.toString()}`;
  };
  categorySelect?.addEventListener('change', updateHubLinks);
  difficultySelect?.addEventListener('change', updateHubLinks);
  updateHubLinks();

  const root = document.querySelector('.game-session[data-game-type]');
  const dataNode = document.getElementById('game-data');
  if (!root || !dataNode) return;

  const words = JSON.parse(dataNode.textContent);
  const type = root.dataset.gameType;
  const stage = document.getElementById('game-stage');
  const feedback = document.getElementById('game-feedback');
  const nextButton = document.getElementById('game-next');
  const hintButton = document.getElementById('game-hint');
  const hintNotice = document.getElementById('game-hint-notice');
  const hintStatus = document.getElementById('game-hint-status');
  const skipButton = document.getElementById('game-skip');
  const completePanel = document.getElementById('game-complete');
  const actions = document.getElementById('game-actions');
  const soundButton = document.getElementById('game-sound-toggle');
  const exitPrompt = document.getElementById('game-exit-prompt');
  const stayButton = document.getElementById('game-stay');
  const confirmExitButton = document.getElementById('game-confirm-exit');
  const startedAt = Date.now();
  let current = 0;
  let correct = 0;
  let streak = 0;
  let sessionTotal = words.length;
  let finished = false;
  let questionLocked = false;
  let revealedLetters = new Set();
  let sessionDirty = false;
  let pendingExit = null;
  let audioContext = null;
  let pronunciationAudio = null;
  let soundEnabled = true;
  let promptPreviousFocus = null;
  let hintsBaseLeft = Number(root.dataset.hintBase) || 0;
  let hintsBonusLeft = Number(root.dataset.hintBonus) || 0;
  let hintRequestPending = false;
  let getHintOffer = () => null;
  const hintedWords = new Set();

  // El contenido principal tiene su propio contexto de apilamiento, debajo de la navegación.
  // El aviso debe vivir en el body para poder mostrarse completo por encima de ambos.
  if (exitPrompt) document.body.append(exitPrompt);

  try { soundEnabled = window.localStorage.getItem('kichwa-game-sound') !== 'off'; } catch (_) { /* La preferencia es opcional. */ }

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || '';
  const shuffle = (items) => {
    const result = [...items];
    for (let index = result.length - 1; index > 0; index -= 1) {
      const swap = Math.floor(Math.random() * (index + 1));
      [result[index], result[swap]] = [result[swap], result[index]];
    }
    return result;
  };
  const normalize = (value) => (value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es').replace(/[^a-z0-9ñ]+/g, ' ').trim();
  const elapsedSeconds = () => Math.max(0, Math.floor((Date.now() - startedAt) / 1000));
  const formatTime = (seconds) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;

  const ensureAudio = () => {
    if (!soundEnabled) return null;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return null;
    if (!audioContext) audioContext = new AudioContext();
    if (audioContext.state === 'suspended') audioContext.resume().catch(() => {});
    return audioContext;
  };

  const playTone = (frequency, delay, duration, volume = .035) => {
    const context = ensureAudio();
    if (!context) return;
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    const begins = context.currentTime + delay;
    oscillator.type = 'sine';
    oscillator.frequency.setValueAtTime(frequency, begins);
    gain.gain.setValueAtTime(.0001, begins);
    gain.gain.exponentialRampToValueAtTime(volume, begins + .012);
    gain.gain.exponentialRampToValueAtTime(.0001, begins + duration);
    oscillator.connect(gain); gain.connect(context.destination);
    oscillator.start(begins); oscillator.stop(begins + duration + .02);
  };

  const playSound = (kind) => {
    if (!soundEnabled) return;
    if (kind === 'correct') { playTone(659, 0, .13); playTone(880, .105, .18); }
    else if (kind === 'error') { playTone(247, 0, .16, .026); playTone(196, .11, .2, .024); }
    else if (kind === 'complete') { playTone(523, 0, .12); playTone(659, .1, .14); playTone(988, .22, .25); }
    else playTone(440, 0, .08, .018);
  };

  const markSessionActive = () => {
    if (!finished) sessionDirty = true;
    ensureAudio();
  };

  const updateSoundButton = () => {
    if (!soundButton) return;
    soundButton.setAttribute('aria-pressed', String(soundEnabled));
    soundButton.querySelector('i').className = `fas ${soundEnabled ? 'fa-volume-high' : 'fa-volume-xmark'}`;
    soundButton.querySelector('span').textContent = soundEnabled ? 'Efectos activados' : 'Efectos silenciados';
  };

  updateSoundButton();
  soundButton?.addEventListener('click', () => {
    soundEnabled = !soundEnabled;
    try { window.localStorage.setItem('kichwa-game-sound', soundEnabled ? 'on' : 'off'); } catch (_) { /* La partida sigue funcionando sin almacenamiento local. */ }
    updateSoundButton();
    if (soundEnabled) playSound('select');
  });

  const hideExitPrompt = () => {
    if (!exitPrompt) return;
    exitPrompt.hidden = true;
    pendingExit = null;
    window.bootstrap?.Tooltip?.getInstance(promptPreviousFocus)?.hide();
    stage.focus({ preventScroll: true });
    promptPreviousFocus = null;
  };

  const updateHintStatus = () => {
    if (!hintStatus) return;
    hintStatus.textContent = `${hintsBaseLeft} de partida${root.dataset.authenticated === 'true' ? ` · ${hintsBonusLeft} extra de cuenta` : ''}`;
  };
  updateHintStatus();

  const positionExitPrompt = () => {
    if (!exitPrompt || exitPrompt.hidden) return;
    const navigationBottom = document.querySelector('.navbar')?.getBoundingClientRect().bottom ?? 0;
    const preferredTop = Math.max(12, navigationBottom + 12);
    const lastVisibleTop = window.innerHeight - exitPrompt.offsetHeight - 12;
    exitPrompt.style.top = `${Math.max(12, Math.min(preferredTop, lastVisibleTop))}px`;
  };

  const requestExit = (action) => {
    if (!sessionDirty || finished || !exitPrompt) { action(); return; }
    pendingExit = action;
    promptPreviousFocus = document.activeElement;
    window.bootstrap?.Tooltip?.getInstance(promptPreviousFocus)?.hide();
    exitPrompt.hidden = false;
    positionExitPrompt();
    stayButton?.focus();
  };

  window.addEventListener('resize', positionExitPrompt);

  stayButton?.addEventListener('click', hideExitPrompt);
  confirmExitButton?.addEventListener('click', () => {
    const action = pendingExit;
    sessionDirty = false;
    exitPrompt.hidden = true;
    pendingExit = null;
    action?.();
  });

  exitPrompt?.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') { event.preventDefault(); hideExitPrompt(); return; }
    if (event.key !== 'Tab') return;
    const controls = [stayButton, confirmExitButton].filter(Boolean);
    const currentIndex = controls.indexOf(document.activeElement);
    const nextIndex = event.shiftKey ? (currentIndex <= 0 ? controls.length - 1 : currentIndex - 1) : (currentIndex + 1) % controls.length;
    event.preventDefault(); controls[nextIndex].focus();
  });

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href]');
    if (!link || link.closest('#game-exit-prompt') || link.target === '_blank' || !sessionDirty || finished) return;
    const destination = new URL(link.href, window.location.href);
    if (destination.href === window.location.href || destination.hash && destination.pathname === window.location.pathname && destination.search === window.location.search) return;
    event.preventDefault();
    requestExit(() => { window.location.href = destination.href; });
  }, true);

  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.closest('#game-stage') || form.closest('#game-exit-prompt') || !sessionDirty || finished) return;
    event.preventDefault();
    requestExit(() => form.submit());
  }, true);

  window.addEventListener('beforeunload', (event) => {
    if (!sessionDirty || finished) return;
    event.preventDefault();
    event.returnValue = '';
  });

  const timer = window.setInterval(() => {
    const time = document.getElementById('game-time');
    if (time && !finished) time.textContent = formatTime(elapsedSeconds());
  }, 1000);

  const setProgress = (done, total = words.length) => {
    const safeTotal = Math.max(total, 1);
    const percent = Math.round((done / safeTotal) * 100);
    document.getElementById('game-progress-fill').style.transform = `scaleX(${percent / 100})`;
    document.getElementById('game-progress-percent').textContent = `${percent}%`;
    document.getElementById('game-progress-label').textContent = done >= total ? `Completadas ${total} palabras` : `${done} de ${total} completadas`;
  };
  const updateStats = () => {
    document.getElementById('game-correct').textContent = String(correct);
    document.getElementById('game-streak').textContent = String(streak);
  };
  const showFeedback = (isCorrect, title, detail = '') => {
    feedback.hidden = false;
    feedback.className = `game-feedback ${isCorrect ? 'is-correct' : 'is-wrong'}`;
    feedback.replaceChildren();
    const strong = document.createElement('strong');
    strong.textContent = title;
    feedback.append(strong);
    if (detail) feedback.append(document.createTextNode(` ${detail}`));
  };
  const clearFeedback = () => {
    feedback.hidden = true;
    feedback.className = 'game-feedback';
    feedback.replaceChildren();
  };

  const registerAnswer = async (word, payload) => {
    markSessionActive();
    const response = await fetch(root.dataset.answerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
      body: JSON.stringify({ sesion_id: root.dataset.sessionId, tipo_juego: type, palabra_id: word.id, ...payload }),
    });
    if (!response.ok) throw new Error('No se pudo validar la respuesta.');
    return response.json();
  };

  const applyResult = (result) => {
    if (result.correcta) {
      correct += 1;
      streak += 1;
      const detail = result.puntos_ganados
        ? `¡Sumaste ${result.puntos_ganados} puntos por aprender esta palabra!`
        : (result.progreso_guardado ? 'Tu avance quedó guardado. Esta palabra ya sumó puntos antes.' : 'Puedes continuar con la siguiente.');
      showFeedback(true, 'Respuesta correcta.', detail);
      playSound('correct');
    } else {
      streak = 0;
      showFeedback(false, 'Todavía no.', `La respuesta esperada era “${result.respuesta_correcta}”.`);
      playSound('error');
    }
    updateStats();
  };

  const handleRequestError = () => {
    questionLocked = false;
    stage.querySelectorAll('button').forEach((item) => { item.disabled = false; });
    showFeedback(false, 'No pudimos comprobar la respuesta.', 'Revisa la conexión e inténtalo nuevamente.');
  };

  const revealListeningAnswer = () => {
    if (type !== 'escucha') return;
    pronunciationAudio?.pause();
    const transcript = stage.querySelector('.listening-transcript');
    if (transcript) transcript.open = true;
    const status = stage.querySelector('.listening-status');
    if (status) status.textContent = 'La palabra está escrita debajo.';
  };

  const finishGame = async () => {
    pronunciationAudio?.pause();
    finished = true;
    sessionDirty = false;
    window.clearInterval(timer);
    stage.hidden = true;
    feedback.hidden = true;
    actions.hidden = true;
    completePanel.hidden = false;
    const accuracy = Math.round((correct / Math.max(sessionTotal, 1)) * 100);
    document.getElementById('game-complete-copy').textContent = `Acertaste ${correct} de ${sessionTotal} palabras (${accuracy}%) en ${formatTime(elapsedSeconds())}.`;
    setProgress(sessionTotal, sessionTotal);
    playSound('complete');
    if (root.dataset.authenticated !== 'true') return;
    try {
      await fetch(root.dataset.statsUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({
          sesion_id: root.dataset.sessionId,
        }),
      });
    } catch (_) {
      // El progreso por palabra ya se guardó; el resumen agregado puede reintentarse en otra partida.
    }
  };

  const nextQuestion = () => {
    pronunciationAudio?.pause();
    pronunciationAudio = null;
    current += 1;
    questionLocked = false;
    revealedLetters = new Set();
    clearFeedback();
    nextButton.hidden = true;
    skipButton.hidden = false;
    if (current >= words.length) finishGame();
    else {
      renderSequential();
      stage.animate?.([
        { opacity: .55, clipPath: 'inset(0 0 18% 0 round 12px)' },
        { opacity: 1, clipPath: 'inset(0 0 0 0 round 12px)' },
      ], { duration: 260, easing: 'cubic-bezier(.16,1,.3,1)' });
    }
  };

  const makeOption = (label, wordId, correctId, direction) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'game-option';
    button.textContent = label;
    button.addEventListener('click', async () => {
      if (questionLocked) return;
      questionLocked = true;
      stage.querySelectorAll('button').forEach((item) => { item.disabled = true; });
      try {
        const result = await registerAnswer(words[current], { respuesta_id: wordId, direccion: direction });
        button.classList.add(result.correcta ? 'is-correct' : 'is-wrong');
        button.setAttribute('aria-pressed', 'true');
        if (!result.correcta) stage.querySelector(`[data-answer-id="${correctId}"]`)?.classList.add('is-correct');
        revealListeningAnswer();
        applyResult(result);
        nextButton.hidden = false;
        skipButton.hidden = true;
        setProgress(current + 1);
      } catch (_) { handleRequestError(); }
    });
    button.dataset.answerId = String(wordId);
    return button;
  };

  const renderTranslation = () => {
    const word = words[current];
    const reverse = current % 2 === 1;
    const question = document.createElement('div');
    question.className = 'game-question';
    const direction = document.createElement('p');
    direction.className = 'game-question__direction';
    direction.textContent = reverse ? 'Español → Kichwa' : 'Kichwa → Español';
    const prompt = document.createElement('h2');
    prompt.className = 'game-question__word';
    prompt.textContent = reverse ? word.espanol : word.kichwa;
    const support = document.createElement('p');
    support.className = 'game-question__support';
    support.textContent = word.pista || (reverse ? 'Elige la forma correspondiente en Kichwa.' : 'Elige el significado más preciso.');
    const options = document.createElement('div');
    options.className = 'game-options';
    const pool = shuffle([word, ...shuffle(words.filter((item) => item.id !== word.id)).slice(0, 3)]);
    const answerDirection = reverse ? 'espanol_kichwa' : 'kichwa_espanol';
    pool.forEach((item) => options.append(makeOption(reverse ? item.kichwa : item.espanol, item.id, word.id, answerDirection)));
    question.append(direction, prompt, support, options);
    stage.replaceChildren(question);
    getHintOffer = () => ({
      wordId: word.id,
      apply: () => {
        const wrong = [...options.querySelectorAll('.game-option')].find((item) => item.dataset.answerId !== String(word.id));
        if (wrong) {
          wrong.classList.add('is-hint-eliminated');
          wrong.disabled = true;
          showFeedback(true, 'Pista', 'Se descartó una opción que no corresponde a esta palabra.');
        } else {
          showFeedback(true, 'Pista', word.pronunciacion ? `Pronunciación: ${word.pronunciacion}` : `Tema: ${word.categoria}.`);
        }
      },
    });
  };

  const renderListening = () => {
    const word = words[current];
    const question = document.createElement('div');
    question.className = 'game-question game-question--listening';
    const direction = document.createElement('p');
    direction.className = 'game-question__direction';
    direction.textContent = 'Kichwa → Español';
    const prompt = document.createElement('h2');
    prompt.className = 'game-question__word';
    prompt.textContent = 'Escucha la palabra';
    const support = document.createElement('p');
    support.className = 'game-question__support';
    support.textContent = 'Reproduce la grabación y elige su significado en español.';
    const player = document.createElement('div');
    player.className = 'listening-player';
    const audio = document.createElement('audio');
    audio.preload = 'none';
    audio.src = word.audio;
    audio.hidden = true;
    pronunciationAudio = audio;
    const controls = document.createElement('div');
    controls.className = 'listening-controls';
    const normal = document.createElement('button');
    normal.type = 'button';
    normal.className = 'learning-primary';
    normal.textContent = 'Escuchar';
    normal.setAttribute('aria-label', 'Escuchar la palabra en Kichwa');
    const speed = document.createElement('button');
    speed.type = 'button';
    speed.className = 'learning-secondary';
    speed.textContent = 'Escuchar despacio';
    const status = document.createElement('p');
    status.className = 'listening-status';
    status.setAttribute('role', 'status');
    status.textContent = 'Pulsa escuchar para reproducir la grabación.';
    const playRecording = async (rate) => {
      audio.pause();
      audio.playbackRate = rate;
      try {
        audio.currentTime = 0;
        await audio.play();
        status.textContent = rate === 1 ? 'Reproduciendo la grabación.' : 'Reproduciendo más despacio.';
      }
      catch (_) { status.textContent = 'No se pudo reproducir. Puedes leer la palabra como alternativa.'; }
    };
    normal.addEventListener('click', () => playRecording(1));
    speed.addEventListener('click', () => playRecording(.8));
    audio.addEventListener('ended', () => { status.textContent = 'Grabación terminada. Puedes escucharla otra vez.'; });
    audio.addEventListener('error', () => {
      status.textContent = 'No se pudo cargar la grabación. Puedes leer la palabra como alternativa.';
      showFeedback(false, 'No se pudo cargar la grabación.', 'Puedes leer la palabra como alternativa y continuar.');
    });
    controls.append(normal, speed);
    player.append(audio, controls, status);
    const transcript = document.createElement('details');
    transcript.className = 'listening-transcript';
    const summary = document.createElement('summary');
    summary.textContent = 'Leer la palabra como alternativa al audio';
    const written = document.createElement('p');
    written.textContent = `Kichwa: ${word.kichwa}`;
    transcript.append(summary, written);
    const options = document.createElement('div');
    options.className = 'game-options';
    const pool = shuffle([word, ...shuffle(words.filter((item) => item.id !== word.id)).slice(0, 3)]);
    pool.forEach((item) => options.append(makeOption(item.espanol, item.id, word.id, 'kichwa_espanol')));
    question.append(direction, prompt, support, player, transcript, options);
    stage.replaceChildren(question);
    getHintOffer = () => ({
      wordId: word.id,
      apply: () => {
        const wrong = [...options.querySelectorAll('.game-option')].find((item) => item.dataset.answerId !== String(word.id) && !item.disabled);
        if (wrong) {
          wrong.disabled = true;
          wrong.classList.add('is-hint-eliminated');
          showFeedback(true, 'Pista', 'Se descartó una opción que no corresponde a la grabación.');
        }
      },
    });
  };

  const maskWord = (word) => [...word].map((character, index) => {
    if (!/[\p{L}]/u.test(character)) return character;
    const visible = index === 0 || index === word.length - 1 || revealedLetters.has(index) || index % 3 === 0;
    return visible ? character : '＿';
  }).join(' ');

  const renderCompletion = () => {
    const word = words[current];
    const question = document.createElement('div');
    question.className = 'game-question';
    const direction = document.createElement('p');
    direction.className = 'game-question__direction';
    direction.textContent = 'Español → Kichwa';
    const prompt = document.createElement('h2');
    prompt.className = 'game-question__word';
    prompt.textContent = word.espanol;
    const mask = document.createElement('p');
    mask.className = 'game-mask';
    mask.id = 'game-mask';
    mask.textContent = maskWord(word.kichwa);
    const row = document.createElement('form');
    row.className = 'game-input-row';
    const input = document.createElement('input');
    input.className = 'game-answer-input';
    input.autocomplete = 'off';
    input.spellcheck = false;
    input.placeholder = 'Escribe la palabra completa';
    input.setAttribute('aria-label', 'Respuesta en Kichwa');
    const submit = document.createElement('button');
    submit.type = 'submit';
    submit.className = 'learning-primary';
    submit.textContent = 'Comprobar';
    row.append(input, submit);
    row.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (questionLocked || !normalize(input.value)) return;
      questionLocked = true;
      input.disabled = true;
      submit.disabled = true;
      try {
        const result = await registerAnswer(word, { respuesta: input.value });
        applyResult(result);
        nextButton.hidden = false;
        skipButton.hidden = true;
        setProgress(current + 1);
      } catch (_) { input.disabled = false; submit.disabled = false; handleRequestError(); }
    });
    question.append(direction, prompt, mask, row);
    stage.replaceChildren(question);
    getHintOffer = () => {
      const letters = [...word.kichwa];
      const index = letters.findIndex((character, position) => /[\p{L}]/u.test(character) && position !== 0 && position !== letters.length - 1 && position % 3 !== 0 && !revealedLetters.has(position));
      if (index < 0) return null;
      return {
        wordId: word.id,
        apply: () => {
          revealedLetters.add(index);
          mask.textContent = maskWord(word.kichwa);
          showFeedback(true, 'Pista', 'Se reveló una letra de la palabra en Kichwa.');
        },
      };
    };
    input.focus();
  };

  const renderSequential = () => {
    setProgress(current);
    document.getElementById('game-progress-label').textContent = `Pregunta ${current + 1} de ${words.length}`;
    if (type === 'traduccion') renderTranslation();
    else if (type === 'escucha') renderListening();
    else renderCompletion();
  };

  const registerPair = async (word, selectedId) => {
    const result = await registerAnswer(word, { respuesta_id: selectedId });
    applyResult(result);
    return result.correcta;
  };

  const renderMemory = () => {
    hintButton.hidden = false;
    skipButton.hidden = true;
    const cards = shuffle(words.flatMap((word) => [
      { id: word.id, side: 'kichwa', label: word.kichwa },
      { id: word.id, side: 'espanol', label: word.espanol },
    ]));
    const board = document.createElement('div');
    board.className = 'memory-board';
    let openCards = [];
    let matched = 0;
    cards.forEach((card) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'memory-card';
      button.dataset.wordId = String(card.id);
      button.dataset.side = card.side;
      const closedLabel = `Carta sin revelar ${board.children.length + 1}`;
      button.setAttribute('aria-label', closedLabel);
      const label = document.createElement('span');
      label.textContent = card.label;
      button.append(label);
      button.addEventListener('click', async () => {
        if (button.classList.contains('is-open') || button.classList.contains('is-matched') || openCards.length === 2) return;
        markSessionActive();
        button.classList.add('is-open');
        button.setAttribute('aria-label', `${card.side === 'kichwa' ? 'Kichwa' : 'Español'}: ${card.label}`);
        openCards.push(button);
        if (openCards.length < 2) return;
        const [first, second] = openCards;
        const word = words.find((item) => item.id === Number(first.dataset.wordId));
        const isPair = first.dataset.wordId === second.dataset.wordId && first.dataset.side !== second.dataset.side;
        try {
          const accepted = await registerPair(word, isPair ? word.id : Number(second.dataset.wordId));
          if (accepted) {
            first.classList.add('is-matched'); second.classList.add('is-matched');
            matched += 1; setProgress(matched);
            openCards = [];
            if (matched === words.length) window.setTimeout(finishGame, 450);
          } else {
            window.setTimeout(() => {
              first.classList.remove('is-open'); second.classList.remove('is-open');
              first.setAttribute('aria-label', `Carta sin revelar ${[...board.children].indexOf(first) + 1}`);
              second.setAttribute('aria-label', `Carta sin revelar ${[...board.children].indexOf(second) + 1}`);
              openCards = []; clearFeedback();
            }, 850);
          }
        } catch (_) {
          first.classList.remove('is-open'); second.classList.remove('is-open');
          first.setAttribute('aria-label', `Carta sin revelar ${[...board.children].indexOf(first) + 1}`);
          second.setAttribute('aria-label', `Carta sin revelar ${[...board.children].indexOf(second) + 1}`);
          openCards = []; handleRequestError();
        }
      });
      board.append(button);
    });
    stage.replaceChildren(board);
    setProgress(0);
    getHintOffer = () => {
      if (openCards.length) return null;
      const pending = words.find((word) => !hintedWords.has(word.id) && board.querySelector(`[data-word-id="${word.id}"]:not(.is-matched)`));
      if (!pending) return null;
      return {
        wordId: pending.id,
        apply: () => {
          const pair = [...board.querySelectorAll(`[data-word-id="${pending.id}"]`)];
          pair.forEach((card) => card.classList.add('is-hint-preview'));
          showFeedback(true, 'Pista', `Observa esta pareja: ${pending.kichwa} y ${pending.espanol}.`);
          window.setTimeout(() => pair.forEach((card) => card.classList.remove('is-hint-preview')), 1500);
        },
      };
    };
  };

  const renderConnect = () => {
    hintButton.hidden = false;
    skipButton.hidden = true;
    const board = document.createElement('div');
    board.className = 'match-board';
    const left = document.createElement('div'); left.className = 'match-column';
    const right = document.createElement('div'); right.className = 'match-column';
    const leftTitle = document.createElement('h2'); leftTitle.textContent = 'Kichwa';
    const rightTitle = document.createElement('h2'); rightTitle.textContent = 'Español';
    left.append(leftTitle); right.append(rightTitle);
    let selected = null;
    let matched = 0;
    words.forEach((word) => {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'match-option'; button.textContent = word.kichwa; button.dataset.wordId = String(word.id);
      button.addEventListener('click', () => {
        if (button.classList.contains('is-matched')) return;
        markSessionActive();
        left.querySelectorAll('.is-selected').forEach((item) => item.classList.remove('is-selected'));
        selected = button; button.classList.add('is-selected'); clearFeedback();
      });
      left.append(button);
    });
    shuffle(words).forEach((word) => {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'match-option'; button.textContent = word.espanol; button.dataset.wordId = String(word.id);
      button.addEventListener('click', async () => {
        if (!selected || button.classList.contains('is-matched')) {
          showFeedback(false, 'Elige primero una palabra Kichwa.', 'Después selecciona su significado.'); return;
        }
        const question = words.find((item) => item.id === Number(selected.dataset.wordId));
        const chosenLeft = selected;
        try {
          const accepted = await registerPair(question, word.id);
          if (accepted) {
            chosenLeft.classList.remove('is-selected'); chosenLeft.classList.add('is-matched'); button.classList.add('is-matched');
            chosenLeft.disabled = true; button.disabled = true; matched += 1; setProgress(matched); selected = null;
            if (matched === words.length) window.setTimeout(finishGame, 450);
          } else {
            chosenLeft.classList.remove('is-selected'); selected = null;
          }
        } catch (_) { handleRequestError(); }
      });
      right.append(button);
    });
    board.append(left, right); stage.replaceChildren(board); setProgress(0);
    getHintOffer = () => {
      const first = [...left.querySelectorAll('.match-option:not(.is-matched)')].find((item) => !hintedWords.has(Number(item.dataset.wordId)));
      if (!first) return null;
      return {
        wordId: Number(first.dataset.wordId),
        apply: () => {
          const match = right.querySelector(`[data-word-id="${first.dataset.wordId}"]`);
          first.classList.add('is-hint-preview'); match?.classList.add('is-hint-preview');
          showFeedback(true, 'Pista', 'Se señaló una pareja Kichwa–español pendiente.');
          window.setTimeout(() => { first.classList.remove('is-hint-preview'); match?.classList.remove('is-hint-preview'); }, 1500);
        },
      };
    };
  };

  const boardWord = (word) => word.tablero || word.kichwa.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleUpperCase('es').replace(/[^A-ZÑ]/g, '');
  const renderWordSearch = () => {
    hintButton.hidden = false; skipButton.hidden = true;
    const size = 12;
    const grid = Array.from({ length: size }, () => Array(size).fill(''));
    const placements = [];
    const directions = [
      { row: 0, col: 1, name: 'horizontal' },
      { row: 1, col: 0, name: 'vertical' },
      { row: 1, col: 1, name: 'diagonal' },
      { row: 1, col: -1, name: 'diagonal' },
      { row: 0, col: -1, name: 'horizontal inversa' },
      { row: -1, col: 0, name: 'vertical inversa' },
      { row: -1, col: -1, name: 'diagonal inversa' },
      { row: -1, col: 1, name: 'diagonal inversa' },
    ];
    const placementCandidates = (letters, direction) => {
      const length = letters.length;
      const rowMinimum = direction.row < 0 ? length - 1 : 0;
      const rowMaximum = direction.row > 0 ? size - length : size - 1;
      const colMinimum = direction.col < 0 ? length - 1 : 0;
      const colMaximum = direction.col > 0 ? size - length : size - 1;
      if (rowMinimum > rowMaximum || colMinimum > colMaximum) return [];
      const candidates = [];
      for (let row = rowMinimum; row <= rowMaximum; row += 1) {
        for (let col = colMinimum; col <= colMaximum; col += 1) candidates.push([row, col]);
      }
      return shuffle(candidates);
    };
    const placeWord = (word, wordIndex) => {
      const letters = [...boardWord(word)];
      const preferred = directions[wordIndex % directions.length];
      const orderedDirections = [preferred, ...shuffle(directions.filter((direction) => direction !== preferred))];
      for (const direction of orderedDirections) {
        for (const [startRow, startCol] of placementCandidates(letters, direction)) {
          const cells = letters.map((_, index) => [startRow + (direction.row * index), startCol + (direction.col * index)]);
          const available = cells.every(([row, col], index) => !grid[row][col] || grid[row][col] === letters[index]);
          if (!available) continue;
          cells.forEach(([row, col], index) => { grid[row][col] = letters[index]; });
          return { word, letters: letters.join(''), cells, direction: direction.name };
        }
      }
      return null;
    };
    words.forEach((word, wordIndex) => {
      const placement = placeWord(word, wordIndex);
      if (placement) placements.push(placement);
    });
    const alphabet = 'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ';
    for (let row = 0; row < size; row += 1) for (let col = 0; col < size; col += 1) if (!grid[row][col]) grid[row][col] = alphabet[Math.floor(Math.random() * alphabet.length)];
    const layout = document.createElement('div'); layout.className = 'word-search-layout';
    const gridNode = document.createElement('div'); gridNode.className = 'word-grid'; gridNode.style.setProperty('--grid-size', size);
    const list = document.createElement('div'); list.className = 'word-list';
    const title = document.createElement('h2'); title.textContent = 'Palabras del reto'; list.append(title);
    placements.forEach(({ word }) => {
      const item = document.createElement('div'); item.className = 'word-list__item'; item.dataset.wordId = String(word.id);
      const kichwa = document.createElement('span'); kichwa.textContent = word.kichwa;
      const espanol = document.createElement('span'); espanol.textContent = word.espanol;
      item.append(kichwa, espanol); list.append(item);
    });
    sessionTotal = placements.length;
    let start = null; let found = 0; let dragStart = null; let dragEnd = null; let dragMoved = false; let suppressClick = false;
    const cellNodes = new Map();
    const clearPreview = () => gridNode.querySelectorAll('.is-preview').forEach((item) => item.classList.remove('is-preview'));
    const cellsInLine = (from, to) => {
      if (!from || !to) return null;
      const rowDistance = to[0] - from[0];
      const colDistance = to[1] - from[1];
      const isHorizontal = rowDistance === 0 && colDistance !== 0;
      const isVertical = colDistance === 0 && rowDistance !== 0;
      const isDiagonal = Math.abs(rowDistance) === Math.abs(colDistance) && rowDistance !== 0;
      if (!isHorizontal && !isVertical && !isDiagonal) return null;
      const length = Math.max(Math.abs(rowDistance), Math.abs(colDistance));
      const rowStep = Math.sign(rowDistance); const colStep = Math.sign(colDistance);
      return Array.from({ length: length + 1 }, (_, index) => [from[0] + (rowStep * index), from[1] + (colStep * index)]);
    };
    const previewLine = (from, to) => {
      clearPreview();
      const cells = cellsInLine(from, to);
      cells?.forEach(([row, col]) => cellNodes.get(`${row}:${col}`)?.classList.add('is-preview'));
    };
    const findMatch = (from, to) => placements.find((placement) => {
      if (placement.found) return false;
      const first = placement.cells[0]; const last = placement.cells[placement.cells.length - 1];
      return (first[0] === from[0] && first[1] === from[1] && last[0] === to[0] && last[1] === to[1]) || (last[0] === from[0] && last[1] === from[1] && first[0] === to[0] && first[1] === to[1]);
    });
    const submitLine = async (from, to) => {
      clearPreview();
      gridNode.querySelectorAll('.is-start').forEach((item) => item.classList.remove('is-start'));
      if (!cellsInLine(from, to)) {
        showFeedback(false, 'Traza una línea recta.', 'Puedes buscar en horizontal, vertical o diagonal, en ambos sentidos.');
        playSound('error'); streak = 0; updateStats(); return;
      }
      const match = findMatch(from, to);
      if (!match) {
        showFeedback(false, 'Esa línea no corresponde a una palabra pendiente.', 'Prueba con otro inicio y final.');
        playSound('error'); streak = 0; updateStats(); return;
      }
      try {
        const accepted = await registerPair(match.word, match.word.id);
        if (!accepted) return;
        match.found = true; found += 1;
        match.cells.forEach(([row, column]) => cellNodes.get(`${row}:${column}`)?.classList.add('is-found'));
        list.querySelector(`[data-word-id="${match.word.id}"]`)?.classList.add('is-found'); setProgress(found, placements.length);
        if (found === placements.length) window.setTimeout(finishGame, 450);
      } catch (_) { handleRequestError(); }
    };
    for (let row = 0; row < size; row += 1) for (let col = 0; col < size; col += 1) {
      const cell = document.createElement('button'); cell.type = 'button'; cell.className = 'word-cell'; cell.textContent = grid[row][col]; cell.dataset.row = row; cell.dataset.col = col;
      cell.setAttribute('aria-label', `Fila ${row + 1}, columna ${col + 1}: ${grid[row][col]}`);
      cellNodes.set(`${row}:${col}`, cell); gridNode.append(cell);
      cell.addEventListener('click', () => {
        if (suppressClick) { suppressClick = false; return; }
        markSessionActive();
        if (!start) { start = [row,col]; cell.classList.add('is-start'); playSound('select'); return; }
        const selectedStart = start; start = null; submitLine(selectedStart, [row,col]);
      });
    }
    gridNode.addEventListener('pointerdown', (event) => {
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      const cell = event.target.closest('.word-cell'); if (!cell) return;
      markSessionActive(); start = null; gridNode.querySelectorAll('.is-start').forEach((item) => item.classList.remove('is-start'));
      dragStart = [Number(cell.dataset.row), Number(cell.dataset.col)]; dragEnd = dragStart; dragMoved = false;
      gridNode.classList.add('is-dragging'); previewLine(dragStart, dragEnd);
    });
    gridNode.addEventListener('pointermove', (event) => {
      if (!dragStart) return;
      const target = document.elementFromPoint(event.clientX, event.clientY)?.closest('.word-cell'); if (!target || !gridNode.contains(target)) return;
      const next = [Number(target.dataset.row), Number(target.dataset.col)];
      if (next[0] !== dragEnd[0] || next[1] !== dragEnd[1]) dragMoved = true;
      dragEnd = next; previewLine(dragStart, dragEnd);
    });
    const finishDrag = (event) => {
      if (!dragStart) return;
      const from = dragStart; const to = dragEnd;
      dragStart = null; dragEnd = null; gridNode.classList.remove('is-dragging');
      if (!dragMoved) { clearPreview(); return; }
      event.preventDefault(); suppressClick = true; submitLine(from, to);
    };
    gridNode.addEventListener('pointerup', finishDrag);
    gridNode.addEventListener('pointercancel', () => { dragStart = null; dragEnd = null; dragMoved = false; clearPreview(); gridNode.classList.remove('is-dragging'); });
    layout.append(gridNode, list); stage.replaceChildren(layout); setProgress(0, placements.length);
    getHintOffer = () => {
      const pending = placements.find((item) => !item.found && !hintedWords.has(item.word.id));
      if (!pending) return null;
      return {
        wordId: pending.word.id,
        apply: () => {
          const [row,col] = pending.cells[0];
          const cell = cellNodes.get(`${row}:${col}`);
          cell?.classList.add('is-start');
          showFeedback(true, 'Pista', `${pending.word.kichwa} empieza en la fila ${row + 1}, columna ${col + 1}; dirección ${pending.direction}.`);
          window.setTimeout(() => cell?.classList.remove('is-start'), 1500);
        },
      };
    };
  };

  hintButton.addEventListener('click', async () => {
    if (hintRequestPending || questionLocked || finished) return;
    const offer = getHintOffer();
    if (!offer) {
      showFeedback(false, 'No hay una pista aplicable ahora.', 'Termina o cierra la selección actual y prueba con otra palabra.');
      return;
    }
    if (hintedWords.has(offer.wordId)) {
      showFeedback(false, 'Ya utilizaste la pista de esta palabra.', 'Continúa con otra palabra para usar una nueva pista.');
      return;
    }
    hintRequestPending = true;
    hintButton.disabled = true;
    try {
      const response = await fetch(root.dataset.hintUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({ sesion_id: root.dataset.sessionId, palabra_id: offer.wordId }),
      });
      const result = await response.json();
      if (!response.ok) {
        if (result.login_required) {
          hintNotice.hidden = false;
          showFeedback(false, 'Pistas de partida agotadas.', 'Puedes iniciar sesión o registrarte para usar dos pistas extra una sola vez por cuenta.');
        } else showFeedback(false, 'No hay más pistas disponibles.', result.message || 'Continúa sin pista o inicia otra partida.');
        return;
      }
      hintedWords.add(offer.wordId);
      hintsBaseLeft = result.pistas_base_restantes;
      hintsBonusLeft = result.pistas_extra_restantes;
      updateHintStatus();
      markSessionActive();
      offer.apply();
      playSound('select');
    } catch (_) {
      showFeedback(false, 'No se pudo cargar la pista.', 'Revisa la conexión e inténtalo nuevamente.');
    } finally {
      hintRequestPending = false;
      hintButton.disabled = false;
    }
  });
  skipButton.addEventListener('click', async () => {
    if (questionLocked || !['traduccion','escucha','completar'].includes(type)) return;
    questionLocked = true;
    try {
      const result = await registerAnswer(words[current], type === 'completar' ? { respuesta: '' } : { respuesta_id: 0 });
      revealListeningAnswer();
      applyResult(result);
      nextButton.hidden = false; skipButton.hidden = true; setProgress(current + 1);
    } catch (_) { handleRequestError(); }
  });
  nextButton.addEventListener('click', nextQuestion);
  document.getElementById('game-restart')?.addEventListener('click', () => window.location.reload());

  if (['traduccion', 'escucha', 'completar'].includes(type)) renderSequential();
  else if (type === 'memoria') renderMemory();
  else if (type === 'conectar') renderConnect();
  else renderWordSearch();
})();
