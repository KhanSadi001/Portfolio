(function () {
  'use strict';

  function csrfToken() {
    var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  // ---- Project filter ----
  var filters = document.querySelectorAll('.filter');
  var projects = document.querySelectorAll('.project');
  filters.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var f = btn.dataset.filter;
      filters.forEach(function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
      projects.forEach(function (p) { p.hidden = !(f === 'all' || p.dataset.cat === f); });
    });
  });

  // ---- Likes (stored on the server; one per visitor) ----
  document.querySelectorAll('.like-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      if (btn.classList.contains('is-liked') || btn.disabled) return;
      btn.disabled = true;
      fetch(btn.dataset.likeUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken() },
        credentials: 'same-origin'
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
          if (!res.ok) throw new Error(res.data.error || 'Like failed');
          btn.querySelector('.like-count').textContent = res.data.count;
          btn.querySelector('.heart').textContent = '♥';
          btn.classList.add('is-liked', 'pop');
          btn.setAttribute('aria-pressed', 'true');
        })
        .catch(function (err) {
          btn.disabled = false;
          btn.title = err.message;
        });
    });
  });
})();
