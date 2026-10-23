/* Bit Flip — build the target number by flipping bits.
   The server issues a round token and computes the final score; this file only runs the round. */
(function () {
  'use strict';

  var root = document.getElementById('game');
  if (!root) return;

  var ROUND = parseInt(root.dataset.seconds, 10) || 60;
  var LEVELS = JSON.parse(document.getElementById('game-levels').textContent); // [[startIndex, label, points], ...]
  var PLACES = [128, 64, 32, 16, 8, 4, 2, 1];

  var el = {
    time: document.getElementById('hud-time'),
    score: document.getElementById('hud-score'),
    level: document.getElementById('hud-level'),
    target: document.getElementById('target'),
    targetLabel: document.getElementById('target-label'),
    current: document.getElementById('current'),
    bits: Array.prototype.slice.call(document.querySelectorAll('.bit')),
    start: document.getElementById('screen-start'),
    end: document.getElementById('screen-end'),
    btnStart: document.getElementById('btn-start'),
    btnAgain: document.getElementById('btn-again'),
    endScore: document.getElementById('end-score'),
    endSolved: document.getElementById('end-solved'),
    form: document.getElementById('save-form'),
    name: document.getElementById('player-name'),
    status: document.getElementById('save-status'),
    board: document.getElementById('lb-list')
  };

  var state = { bits: [0, 0, 0, 0, 0, 0, 0, 0], target: 0, solved: 0, score: 0, token: null, endsAt: 0, timer: null, running: false };

  el.bits.forEach(function (b, i) { b.querySelector('.bit-place').textContent = PLACES[i]; });

  function csrf() {
    var i = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return i ? i.value : '';
  }

  function api(url, body) {
    return fetch(url, {
      method: body === undefined ? 'GET' : 'POST',
      headers: { 'X-CSRFToken': csrf(), 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: body === undefined ? undefined : JSON.stringify(body)
    }).then(function (r) {
      return r.json().then(function (d) {
        if (!r.ok) throw new Error(d.error || 'Something went wrong.');
        return d;
      });
    });
  }

  function level() {
    var current = LEVELS[0];
    LEVELS.forEach(function (l) { if (state.solved >= l[0]) current = l; });
    return current;
  }
  function activeBits() { return level()[1] === '4-bit' ? 4 : 8; }
  function value() { return state.bits.reduce(function (acc, b, i) { return acc + b * PLACES[i]; }, 0); }

  function render() {
    var lv = level();
    var active = activeBits();
    el.level.textContent = lv[1];
    el.score.textContent = state.score;
    el.current.textContent = value();
    el.bits.forEach(function (b, i) {
      var on = state.bits[i] === 1;
      var locked = i < 8 - active;
      b.querySelector('.bit-value').textContent = on ? '1' : '0';
      b.setAttribute('aria-pressed', String(on));
      b.setAttribute('aria-label', 'Bit worth ' + PLACES[i] + ', ' + (on ? 'on' : 'off'));
      b.classList.toggle('locked', locked);
      b.disabled = !state.running || locked;
    });
  }

  function nextTarget() {
    var max = Math.pow(2, activeBits()) - 1;
    var t;
    do { t = 1 + Math.floor(Math.random() * max); } while (t === state.target);
    state.target = t;
    state.bits = [0, 0, 0, 0, 0, 0, 0, 0];
    var hex = level()[1] === 'Hex';
    el.targetLabel.textContent = hex ? 'Make this hex number' : 'Make this number';
    el.target.textContent = hex ? '0x' + t.toString(16).toUpperCase().padStart(2, '0') : String(t);
    el.target.classList.remove('hit');
    void el.target.offsetWidth;
    el.target.classList.add('hit');
  }

  function flip(i) {
    if (!state.running || i < 8 - activeBits()) return;
    state.bits[i] ^= 1;
    if (value() === state.target) {
      state.score += level()[2];
      state.solved += 1;
      nextTarget();
    }
    render();
  }

  function tick() {
    var left = Math.max(0, Math.ceil((state.endsAt - Date.now()) / 1000));
    el.time.textContent = left;
    root.classList.toggle('hurry', left <= 10 && left > 0);
    if (left <= 0) finish();
  }

  function start() {
    el.btnStart.disabled = true;
    el.btnAgain.disabled = true;
    state.token = null;
    api(root.dataset.startUrl, {})
      .then(function (d) { state.token = d.token; })
      .catch(function () { state.token = null; }) // still playable, just can't save
      .then(function () {
        state.solved = 0; state.score = 0; state.target = 0; state.running = true;
        state.endsAt = Date.now() + ROUND * 1000;
        el.start.hidden = true; el.end.hidden = true;
        el.btnStart.disabled = false; el.btnAgain.disabled = false;
        root.classList.add('playing');
        nextTarget(); render(); tick();
        state.timer = setInterval(tick, 200);
        var first = el.bits.filter(function (b) { return !b.disabled; })[0];
        if (first) first.focus();
      });
  }

  function finish() {
    clearInterval(state.timer);
    state.running = false;
    root.classList.remove('playing', 'hurry');
    render();
    el.endScore.textContent = state.score;
    el.endSolved.textContent = state.solved;
    el.status.textContent = state.token ? '' : "Scores can't be saved right now, but thanks for playing.";
    el.form.hidden = !state.token || state.solved === 0;
    el.end.hidden = false;
    try { el.name.value = localStorage.getItem('bitflip-name') || ''; } catch (e) {}
    (el.form.hidden ? el.btnAgain : el.name).focus();
  }

  function renderBoard(rows) {
    el.board.innerHTML = '';
    if (!rows.length) {
      var empty = document.createElement('li');
      empty.className = 'lb-empty';
      empty.textContent = 'No scores yet. Be the first.';
      el.board.appendChild(empty);
      return;
    }
    rows.forEach(function (r) {
      var li = document.createElement('li');
      var name = document.createElement('span'); name.className = 'lb-name'; name.textContent = r.name; // textContent: no HTML injection
      var pts = document.createElement('span'); pts.className = 'lb-score'; pts.textContent = r.score;
      li.appendChild(name); li.appendChild(pts);
      el.board.appendChild(li);
    });
  }

  function loadBoard() {
    api(root.dataset.boardUrl)
      .then(function (d) { renderBoard(d.leaderboard); })
      .catch(function () { el.board.innerHTML = '<li class="lb-empty">Leaderboard is unavailable right now.</li>'; });
  }

  el.form.addEventListener('submit', function (e) {
    e.preventDefault();
    var name = el.name.value.trim();
    if (!/^[A-Za-z0-9 _.\-]{1,20}$/.test(name)) {
      el.status.textContent = 'Use 1–20 letters, numbers, spaces, dots, dashes or underscores.';
      return;
    }
    try { localStorage.setItem('bitflip-name', name); } catch (err) {}
    var btn = el.form.querySelector('button');
    btn.disabled = true;
    el.status.textContent = 'Saving…';
    api(root.dataset.submitUrl, { token: state.token, solved: state.solved, name: name })
      .then(function (d) {
        el.status.textContent = 'Saved. You are #' + d.rank + ' on the leaderboard.';
        state.token = null;
        renderBoard(d.leaderboard);
        el.form.hidden = true;
        el.btnAgain.focus();
      })
      .catch(function (err) { el.status.textContent = err.message; })
      .then(function () { btn.disabled = false; });
  });

  el.bits.forEach(function (b, i) { b.addEventListener('click', function () { flip(i); }); });
  document.addEventListener('keydown', function (e) {
    if (!state.running || e.target.tagName === 'INPUT') return;
    var n = parseInt(e.key, 10);
    if (n >= 1 && n <= 8) { e.preventDefault(); flip(n - 1); }
  });
  el.btnStart.addEventListener('click', start);
  el.btnAgain.addEventListener('click', start);

  render();
  loadBoard();
})();
