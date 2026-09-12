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
  const skipButton = document.getElementById('game-skip');
  const completePanel = document.getElementById('game-complete');
  const actions = document.getElementById('game-actions');
  const startedAt = Date.now();
  let current = 0;
  let correct = 0;
  let streak = 0;
  let sessionTotal = words.length;
  let finished = false;
  let questionLocked = false;
  let revealedLetters = new Set();

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
      showFeedback(true, 'Respuesta correcta.', result.progreso_guardado ? 'El avance de esta palabra quedó guardado.' : 'Puedes continuar con la siguiente.');
    } else {
      streak = 0;
      showFeedback(false, 'Todavía no.', `La respuesta esperada era “${result.respuesta_correcta}”.`);
    }
    updateStats();
  };

  const handleRequestError = () => {
    questionLocked = false;
    stage.querySelectorAll('button').forEach((item) => { item.disabled = false; });
    showFeedback(false, 'No pudimos comprobar la respuesta.', 'Revisa la conexión e inténtalo nuevamente.');
  };

  const finishGame = async () => {
    finished = true;
    window.clearInterval(timer);
    stage.hidden = true;
    feedback.hidden = true;
    actions.hidden = true;
    completePanel.hidden = false;
    const accuracy = Math.round((correct / Math.max(sessionTotal, 1)) * 100);
    document.getElementById('game-complete-copy').textContent = `Acertaste ${correct} de ${sessionTotal} palabras (${accuracy}%) en ${formatTime(elapsedSeconds())}.`;
    setProgress(sessionTotal, sessionTotal);
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
    current += 1;
    questionLocked = false;
    revealedLetters = new Set();
    clearFeedback();
    nextButton.hidden = true;
    skipButton.hidden = false;
    if (current >= words.length) finishGame();
    else renderSequential();
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
    input.focus();
  };

  const renderSequential = () => {
    setProgress(current);
    document.getElementById('game-progress-label').textContent = `Pregunta ${current + 1} de ${words.length}`;
    if (type === 'traduccion') renderTranslation();
    else renderCompletion();
  };

  const registerPair = async (word, selectedId) => {
    const result = await registerAnswer(word, { respuesta_id: selectedId });
    applyResult(result);
    return result.correcta;
  };

  const renderMemory = () => {
    hintButton.hidden = true;
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
    hintButton.onclick = () => {
      const first = left.querySelector('.match-option:not(.is-matched)');
      if (!first) return;
      const match = right.querySelector(`[data-word-id="${first.dataset.wordId}"]`);
      first.classList.add('is-selected'); match?.classList.add('is-selected');
      window.setTimeout(() => { first.classList.remove('is-selected'); match?.classList.remove('is-selected'); }, 900);
    };
  };

  const boardWord = (word) => word.tablero || word.kichwa.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleUpperCase('es').replace(/[^A-ZÑ]/g, '');
  const renderWordSearch = () => {
    hintButton.hidden = false; skipButton.hidden = true;
    const size = 12;
    const grid = Array.from({ length: size }, () => Array(size).fill(''));
    const placements = [];
    const availableRows = shuffle(Array.from({ length: size }, (_, index) => index));
    words.forEach((word, wordIndex) => {
      const original = boardWord(word);
      const letters = wordIndex % 2 ? [...original].reverse().join('') : original;
      const row = availableRows[wordIndex];
      const startColumn = Math.floor(Math.random() * (size - letters.length + 1));
      const cells = [...letters].map((_, index) => [row, startColumn + index]);
      cells.forEach(([r,c], index) => { grid[r][c] = letters[index]; });
      placements.push({ word, letters: original, cells });
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
    let start = null; let found = 0;
    const cellNodes = new Map();
    for (let row = 0; row < size; row += 1) for (let col = 0; col < size; col += 1) {
      const cell = document.createElement('button'); cell.type = 'button'; cell.className = 'word-cell'; cell.textContent = grid[row][col]; cell.dataset.row = row; cell.dataset.col = col;
      cellNodes.set(`${row}:${col}`, cell); gridNode.append(cell);
      cell.addEventListener('click', async () => {
        if (!start) { start = [row,col]; cell.classList.add('is-start'); return; }
        const selectedStart = start; start = null; gridNode.querySelectorAll('.is-start').forEach((item) => item.classList.remove('is-start'));
        const match = placements.find((placement) => {
          if (placement.found) return false;
          const first = placement.cells[0]; const last = placement.cells[placement.cells.length - 1];
          return (first[0] === selectedStart[0] && first[1] === selectedStart[1] && last[0] === row && last[1] === col) || (last[0] === selectedStart[0] && last[1] === selectedStart[1] && first[0] === row && first[1] === col);
        });
        if (!match) { showFeedback(false, 'Esa línea no corresponde a una palabra pendiente.', 'Prueba con otro inicio y final.'); streak = 0; updateStats(); return; }
        try {
          const accepted = await registerPair(match.word, match.word.id);
          if (!accepted) return;
          match.found = true; found += 1; match.cells.forEach(([r,c]) => cellNodes.get(`${r}:${c}`)?.classList.add('is-found'));
          list.querySelector(`[data-word-id="${match.word.id}"]`)?.classList.add('is-found'); setProgress(found, placements.length);
          if (found === placements.length) window.setTimeout(finishGame, 450);
        } catch (_) { handleRequestError(); }
      });
    }
    layout.append(gridNode, list); stage.replaceChildren(layout); setProgress(0, placements.length);
    hintButton.onclick = () => {
      const pending = placements.find((item) => !item.found); if (!pending) return;
      const [row,col] = pending.cells[0]; const cell = cellNodes.get(`${row}:${col}`); cell?.classList.add('is-start');
      window.setTimeout(() => cell?.classList.remove('is-start'), 900);
    };
  };

  hintButton.addEventListener('click', () => {
    if (type === 'completar' && !questionLocked) {
      const candidates = [...words[current].kichwa].map((character, index) => /[\p{L}]/u.test(character) && index !== 0 && index !== words[current].kichwa.length - 1 ? index : -1).filter((index) => index >= 0 && !revealedLetters.has(index));
      if (candidates.length) { revealedLetters.add(candidates[0]); document.getElementById('game-mask').textContent = maskWord(words[current].kichwa); }
    } else if (type === 'traduccion' && !questionLocked) {
      const word = words[current]; showFeedback(true, 'Pista', word.pronunciacion ? `Pronunciación: ${word.pronunciacion}` : `Tema: ${word.categoria}.`);
    }
  });
  skipButton.addEventListener('click', async () => {
    if (questionLocked || !['traduccion','completar'].includes(type)) return;
    questionLocked = true;
    try {
      const result = await registerAnswer(words[current], type === 'completar' ? { respuesta: '' } : { respuesta_id: 0 });
      applyResult(result); nextButton.hidden = false; skipButton.hidden = true; setProgress(current + 1);
    } catch (_) { handleRequestError(); }
  });
  nextButton.addEventListener('click', nextQuestion);
  document.getElementById('game-restart')?.addEventListener('click', () => window.location.reload());

  if (type === 'traduccion' || type === 'completar') renderSequential();
  else if (type === 'memoria') renderMemory();
  else if (type === 'conectar') renderConnect();
  else renderWordSearch();
})();
