(function () {
  'use strict';

  const button = document.querySelector('#favorite-button');
  if (!button) return;

  const icon = button.querySelector('#heart-icon');
  const label = button.querySelector('span');
  const csrf = document.querySelector('[name="csrfmiddlewaretoken"]')?.value || document.querySelector('meta[name="csrf-token"]')?.content || '';

  button.addEventListener('click', function () {
    button.disabled = true;
    icon.className = 'fas fa-spinner fa-spin';

    fetch(button.dataset.toggleUrl, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/json' },
    })
      .then(function (response) {
        if (!response.ok) throw new Error('No se pudo actualizar la palabra favorita.');
        return response.json();
      })
      .then(function (data) {
        if (data.login_required) {
          window.bootstrap.Modal.getOrCreateInstance(document.querySelector('#loginModal')).show();
          return;
        }
        if (!data.success) throw new Error(data.message || 'No se pudo actualizar la palabra favorita.');
        button.classList.toggle('is-favorite', data.es_favorita);
        button.setAttribute('aria-pressed', String(data.es_favorita));
        icon.className = (data.es_favorita ? 'fas' : 'far') + ' fa-heart';
        label.textContent = data.es_favorita ? 'Guardada en favoritas' : 'Guardar en favoritas';
        if (typeof window.showNotification === 'function') window.showNotification(data.message, 'success');
      })
      .catch(function (error) {
        if (typeof window.showNotification === 'function') window.showNotification(error.message, 'danger');
      })
      .finally(function () {
        if (icon.classList.contains('fa-spinner')) {
          const active = button.classList.contains('is-favorite');
          icon.className = (active ? 'fas' : 'far') + ' fa-heart';
        }
        button.disabled = false;
      });
  });
}());
