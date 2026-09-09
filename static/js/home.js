// Variables globales
let currentPage = 1
let totalPages = 10
const wordsPerPage = 10
let allWords = []

// Datos de ejemplo de palabras
const sampleWords = [
  { kichwa: "Inti", spanish: "Sol", category: "Naturaleza" },
  { kichwa: "Mama", spanish: "Madre", category: "Familia" },
  { kichwa: "Wasi", spanish: "Casa", category: "Hogar" },
  { kichwa: "Yaku", spanish: "Agua", category: "Naturaleza" },
  { kichwa: "Runa", spanish: "Persona", category: "Familia" },
  { kichwa: "Allpa", spanish: "Tierra", category: "Naturaleza" },
  { kichwa: "Sumak", spanish: "Hermoso", category: "Adjetivos" },
  { kichwa: "Killa", spanish: "Luna", category: "Naturaleza" },
  { kichwa: "Ayni", spanish: "Reciprocidad", category: "Valores" },
  { kichwa: "Kawsay", spanish: "Vida", category: "Filosofía" },
  { kichwa: "Tayta", spanish: "Padre", category: "Familia" },
  { kichwa: "Warmi", spanish: "Mujer", category: "Familia" },
  { kichwa: "Kari", spanish: "Hombre", category: "Familia" },
  { kichwa: "Wawa", spanish: "Niño", category: "Familia" },
  { kichwa: "Atik", spanish: "Abuelo", category: "Familia" },
  { kichwa: "Apamama", spanish: "Abuela", category: "Familia" },
  { kichwa: "Turi", spanish: "Hermano", category: "Familia" },
  { kichwa: "Pani", spanish: "Hermana", category: "Familia" },
  { kichwa: "Mikuy", spanish: "Comida", category: "Alimentación" },
  { kichwa: "Upyay", spanish: "Beber", category: "Acciones" },
]

// Inicialización cuando se carga la página
document.addEventListener("DOMContentLoaded", () => {
  initializeCounters()
  initializeSearch()
  initializePagination()
  setupEventListeners()
})

// Contadores animados
function initializeCounters() {
  const counters = document.querySelectorAll(".stat-number")

  counters.forEach((counter) => {
    const target = Number.parseInt(counter.getAttribute("data-count")) || Number.parseInt(counter.textContent)
    const increment = target / 100
    let current = 0

    const updateCounter = () => {
      if (current < target) {
        current += increment
        counter.textContent = Math.ceil(current)
        requestAnimationFrame(updateCounter)
      } else {
        counter.textContent = target
      }
    }

    // Usar Intersection Observer para activar cuando sea visible
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          updateCounter()
          observer.unobserve(entry.target)
        }
      })
    })

    observer.observe(counter)
  })
}

// Inicializar búsqueda
function initializeSearch() {
  const searchInput = document.getElementById("searchInput")
  const searchSuggestions = document.getElementById("searchSuggestions")

  if (searchInput) {
    searchInput.addEventListener("input", function () {
      const query = this.value.toLowerCase()
      if (query.length > 1) {
        showSuggestions(query)
      } else {
        hideSuggestions()
      }
    })

    searchInput.addEventListener("focus", function () {
      if (this.value.length > 1) {
        showSuggestions(this.value.toLowerCase())
      }
    })

    // Cerrar sugerencias al hacer clic fuera
    document.addEventListener("click", (e) => {
      if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
        hideSuggestions()
      }
    })
  }
}

// Mostrar sugerencias de búsqueda
function showSuggestions(query) {
  const suggestions = document.getElementById("searchSuggestions")
  const filteredWords = sampleWords
    .filter((word) => word.kichwa.toLowerCase().includes(query) || word.spanish.toLowerCase().includes(query))
    .slice(0, 4)

  if (filteredWords.length > 0) {
    suggestions.innerHTML = filteredWords
      .map(
        (word) =>
          `<div class="suggestion-item" onclick="searchWord('${word.kichwa}')">${word.kichwa} (${word.spanish})</div>`,
      )
      .join("")
    suggestions.style.display = "block"
  } else {
    hideSuggestions()
  }
}

// Ocultar sugerencias
function hideSuggestions() {
  const suggestions = document.getElementById("searchSuggestions")
  suggestions.style.display = "none"
}

// Buscar palabra específica
function searchWord(word) {
  const searchInput = document.getElementById("searchInput")
  searchInput.value = word
  hideSuggestions()
  // Aquí podrías redirigir a la página de búsqueda
  window.location.href = `/buscar/?termino=${encodeURIComponent(word)}`
}

// Alternar filtros avanzados
function toggleFilters() {
  const filters = document.querySelector(".search-filters")
  const filterGroups = filters.querySelectorAll(".filter-group")

  filterGroups.forEach((group) => {
    if (group.style.display === "none" || group.style.display === "") {
      group.style.display = "flex"
    } else {
      group.style.display = "none"
    }
  })
}

// Inicializar paginación
function initializePagination() {
  allWords = sampleWords
  totalPages = Math.ceil(allWords.length / wordsPerPage)
  updateWordsList()
  updatePaginationInfo()
}

// Cambiar página
function changePage(direction) {
  const newPage = currentPage + direction

  if (newPage >= 1 && newPage <= totalPages) {
    currentPage = newPage
    updateWordsList()
    updatePaginationInfo()
  }
}

// Actualizar lista de palabras
function updateWordsList() {
  const wordsList = document.getElementById("wordsList")
  if (!wordsList) return

  const startIndex = (currentPage - 1) * wordsPerPage
  const endIndex = startIndex + wordsPerPage
  const currentWords = allWords.slice(startIndex, endIndex)

  wordsList.innerHTML = currentWords
    .map(
      (word) => `
        <a href="#" class="word-item">
            <div class="word-content">
                <div class="word-kichwa">${word.kichwa}</div>
                <div class="word-spanish">${word.spanish}</div>
                <div class="word-category">${word.category}</div>
            </div>
            <div class="word-arrow">→</div>
        </a>
    `,
    )
    .join("")
}

// Actualizar información de paginación
function updatePaginationInfo() {
  const pageInfo = document.getElementById("pageInfo")
  const prevBtn = document.getElementById("prevBtn")
  const nextBtn = document.getElementById("nextBtn")

  if (pageInfo) {
    pageInfo.textContent = `Página ${currentPage} de ${totalPages}`
  }

  if (prevBtn) {
    prevBtn.disabled = currentPage === 1
  }

  if (nextBtn) {
    nextBtn.disabled = currentPage === totalPages
  }
}

// Configurar event listeners
function setupEventListeners() {
  // Animaciones de scroll
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = "1"
        entry.target.style.transform = "translateY(0)"
      }
    })
  }, observerOptions)

  // Observar elementos para animaciones
  const animatedElements = document.querySelectorAll(".popular-word-card, .feature-card, .word-item")
  animatedElements.forEach((el) => {
    el.style.opacity = "0"
    el.style.transform = "translateY(30px)"
    el.style.transition = "opacity 0.6s ease, transform 0.6s ease"
    observer.observe(el)
  })

  // Efectos de hover mejorados
  const cards = document.querySelectorAll(".popular-word-card, .feature-card, .category-card")
  cards.forEach((card) => {
    card.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-10px) scale(1.02)"
    })

    card.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0) scale(1)"
    })
  })
}

// Función para manejar el formulario de búsqueda
function handleSearchForm(event) {
  event.preventDefault()
  const formData = new FormData(event.target)
  const searchParams = new URLSearchParams()

  for (const [key, value] of formData.entries()) {
    if (value) {
      searchParams.append(key, value)
    }
  }

  window.location.href = `/buscar/?${searchParams.toString()}`
}

// Efectos de parallax suaves
function initParallax() {
  window.addEventListener("scroll", () => {
    const scrolled = window.pageYOffset
    const parallaxElements = document.querySelectorAll(".hero-pattern")

    parallaxElements.forEach((element) => {
      const speed = 0.5
      element.style.transform = `translateY(${scrolled * speed}px)`
    })
  })
}

// Inicializar parallax
initParallax()

// Función para mostrar/ocultar elementos según el scroll
function handleScrollEffects() {
  const navbar = document.querySelector(".navbar")
  const scrollTop = window.pageYOffset

  if (scrollTop > 100) {
    navbar?.classList.add("scrolled")
  } else {
    navbar?.classList.remove("scrolled")
  }
}

window.addEventListener("scroll", handleScrollEffects)

// Función para copiar texto al portapapeles
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showNotification("Texto copiado al portapapeles")
  })
}

// Mostrar notificaciones
function showNotification(message, type = "success") {
  const notification = document.createElement("div")
  notification.className = `notification notification-${type}`
  notification.textContent = message

  notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === "success" ? "#10b981" : "#ef4444"};
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `

  document.body.appendChild(notification)

  setTimeout(() => {
    notification.style.transform = "translateX(0)"
  }, 100)

  setTimeout(() => {
    notification.style.transform = "translateX(100%)"
    setTimeout(() => {
      document.body.removeChild(notification)
    }, 300)
  }, 3000)
}

// Función para manejar favoritos
function toggleFavorite(wordId) {
  // Aquí se haría la petición AJAX al servidor
  fetch(`/toggle-favorito/${wordId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification(data.mensaje)
        updateFavoriteButton(wordId, data.es_favorito)
      }
    })
    .catch((error) => {
      showNotification("Error al actualizar favorito", "error")
    })
}

// Obtener cookie CSRF
function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

// Actualizar botón de favorito
function updateFavoriteButton(wordId, isFavorite) {
  const button = document.querySelector(`[data-word-id="${wordId}"]`)
  if (button) {
    button.innerHTML = isFavorite ? "❤️" : "🤍"
    button.classList.toggle("is-favorite", isFavorite)
  }
}

// Función para lazy loading de imágenes
function initLazyLoading() {
  const images = document.querySelectorAll("img[data-src]")

  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target
        img.src = img.dataset.src
        img.removeAttribute("data-src")
        imageObserver.unobserve(img)
      }
    })
  })

  images.forEach((img) => imageObserver.observe(img))
}

// Inicializar lazy loading
initLazyLoading()

// Función para manejar el modo oscuro (si se implementa)
function toggleDarkMode() {
  document.body.classList.toggle("dark-mode")
  localStorage.setItem("darkMode", document.body.classList.contains("dark-mode"))
}

// Cargar preferencia de modo oscuro
if (localStorage.getItem("darkMode") === "true") {
  document.body.classList.add("dark-mode")
}

// Función para optimizar rendimiento en móviles
function optimizeForMobile() {
  if (window.innerWidth <= 768) {
    // Reducir animaciones en móviles
    document.documentElement.style.setProperty("--animation-duration", "0.3s")

    // Deshabilitar parallax en móviles
    const parallaxElements = document.querySelectorAll(".hero-pattern")
    parallaxElements.forEach((el) => {
      el.style.transform = "none"
    })
  }
}

// Ejecutar optimizaciones móviles
optimizeForMobile()
window.addEventListener("resize", optimizeForMobile)

// Precargar páginas importantes
function preloadPages() {
  const importantLinks = ["/buscar/", "/categorias/", "/juegos/"]

  importantLinks.forEach((url) => {
    const link = document.createElement("link")
    link.rel = "prefetch"
    link.href = url
    document.head.appendChild(link)
  })
}

// Precargar después de que la página esté completamente cargada
window.addEventListener("load", preloadPages)
