(function () {
  'use strict';
  const english = document.documentElement.lang === 'en';
  const text = (spanish, translated) => english ? translated : spanish;

  const input = document.querySelector('#id_termino');
  const wrapper = input ? input.closest('.search-control') : null;
  const list = document.querySelector('#search-suggestions');
  if (!input || !wrapper || !list) return;

  const endpoint = wrapper.dataset.suggestionsUrl;
  const status = document.querySelector('#search-suggestions-status');
  let timer;
  let controller;
  let activeIndex = -1;

  function options() {
    return Array.from(list.querySelectorAll('.suggestion-item'));
  }

  function announce(message) {
    if (status) status.textContent = message;
  }

  function setActive(index) {
    const items = options();
    if (!items.length) return;
    activeIndex = (index + items.length) % items.length;
    items.forEach(function (item, itemIndex) {
      const active = itemIndex === activeIndex;
      item.classList.toggle('is-active', active);
      item.setAttribute('aria-selected', active ? 'true' : 'false');
    });
    input.setAttribute('aria-activedescendant', items[activeIndex].id);
  }

  function closeSuggestions() {
    list.hidden = true;
    list.replaceChildren();
    activeIndex = -1;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
  }

  function renderSuggestions(items) {
    list.replaceChildren();
    activeIndex = -1;
    items.forEach(function (item, index) {
      const link = document.createElement('a');
      const words = document.createElement('span');
      const kichwa = document.createElement('strong');
      const spanish = document.createElement('small');
      const category = document.createElement('span');

      link.className = 'suggestion-item';
      link.id = 'search-suggestion-' + index;
      link.href = item.url;
      link.setAttribute('role', 'option');
      link.setAttribute('aria-selected', 'false');
      kichwa.textContent = item.palabra_kichwa;
      spanish.textContent = item.traduccion_espanol;
      category.className = 'suggestion-category';
      category.textContent = item.categoria;
      words.append(kichwa, spanish);
      link.append(words, category);
      list.append(link);
    });
    list.hidden = items.length === 0;
    input.setAttribute('aria-expanded', items.length ? 'true' : 'false');
    announce(items.length
      ? items.length + text(' sugerencias disponibles.', ' suggestions available.')
      : text('No hay sugerencias.', 'No suggestions available.'));
  }

  input.addEventListener('input', function () {
    window.clearTimeout(timer);
    const query = input.value.trim();
    if (controller) controller.abort();
    if (query.length < 2) {
      closeSuggestions();
      return;
    }

    timer = window.setTimeout(function () {
      controller = new AbortController();
      wrapper.setAttribute('aria-busy', 'true');
      announce(text('Buscando sugerencias.', 'Searching for suggestions.'));
      fetch(endpoint + '?q=' + encodeURIComponent(query), { signal: controller.signal })
        .then(function (response) {
          if (!response.ok) throw new Error(text('No se pudieron cargar las sugerencias.', 'Suggestions could not be loaded.'));
          return response.json();
        })
        .then(function (data) { renderSuggestions(data.palabras || []); })
        .catch(function (error) {
          if (error.name !== 'AbortError') {
            closeSuggestions();
            announce(text('No se pudieron cargar las sugerencias. Puedes continuar con el botón Buscar.', 'Suggestions could not be loaded. You can continue with the Search button.'));
          }
        })
        .finally(function () { wrapper.removeAttribute('aria-busy'); });
    }, 180);
  });

  input.addEventListener('keydown', function (event) {
    if (event.key === 'ArrowDown' && !list.hidden) {
      event.preventDefault();
      setActive(activeIndex + 1);
    } else if (event.key === 'ArrowUp' && !list.hidden) {
      event.preventDefault();
      setActive(activeIndex - 1);
    } else if (event.key === 'Enter' && activeIndex >= 0) {
      event.preventDefault();
      window.location.assign(options()[activeIndex].href);
    } else if (event.key === 'Escape') {
      closeSuggestions();
      announce('Sugerencias cerradas.');
    }
  });

  document.addEventListener('click', function (event) {
    if (!wrapper.contains(event.target)) closeSuggestions();
  });
}());
