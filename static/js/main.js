// Funciones principales del sitio
document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("surface-ready")
  // Importar Bootstrap
  const bootstrap = window.bootstrap

  // Inicializar tooltips de Bootstrap
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))

  // Inicializar popovers de Bootstrap
  var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
  var popoverList = popoverTriggerList.map((popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl))

  // Smooth scrolling para enlaces internos
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault()
      const target = document.querySelector(this.getAttribute("href"))
      if (target) {
        target.scrollIntoView({
          behavior: "smooth",
          block: "start",
        })
      }
    })
  })

  // Auto-hide alerts después de 5 segundos
  setTimeout(() => {
    const alerts = document.querySelectorAll(".alert")
    alerts.forEach((alert) => {
      if (alert.classList.contains("alert-success") || alert.classList.contains("alert-info")) {
        const bsAlert = new bootstrap.Alert(alert)
        bsAlert.close()
      }
    })
  }, 5000)

  // Animación de entrada para cards
  const observerOptions = {
    threshold: 0.1,
    rootMargin: "0px 0px -50px 0px",
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("fade-in-up")
        observer.unobserve(entry.target)
      }
    })
  }, observerOptions)

  // Observar todas las cards
  document.querySelectorAll(".card").forEach((card) => {
    observer.observe(card)
  })

  // Actualizar puntos del usuario periódicamente
  const updateUserPoints = window.updateUserPoints
  if (typeof updateUserPoints === "function") {
    setInterval(updateUserPoints, 30000) // Cada 30 segundos
  }
})

// Función para copiar texto al portapapeles
function copyToClipboard(text) {
  navigator.clipboard
    .writeText(text)
    .then(() => {
      showNotification("Texto copiado al portapapeles", "success")
    })
    .catch((err) => {
      console.error("Error al copiar: ", err)
      showNotification("Error al copiar texto", "error")
    })
}

// Función para compartir contenido
function shareContent(title, text, url) {
  if (navigator.share) {
    navigator
      .share({
        title: title,
        text: text,
        url: url,
      })
      .catch(console.error)
  } else {
    // Fallback: copiar URL al portapapeles
    copyToClipboard(url)
  }
}

// Función para lazy loading de imágenes
function lazyLoadImages() {
  const images = document.querySelectorAll("img[data-src]")
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target
        img.src = img.dataset.src
        img.classList.remove("lazy")
        imageObserver.unobserve(img)
      }
    })
  })

  images.forEach((img) => imageObserver.observe(img))
}

// Función para validar formularios
function validateForm(formId) {
  const form = document.getElementById(formId)
  if (!form) return false

  const inputs = form.querySelectorAll("input[required], textarea[required], select[required]")
  let isValid = true

  inputs.forEach((input) => {
    if (!input.value.trim()) {
      input.classList.add("is-invalid")
      isValid = false
    } else {
      input.classList.remove("is-invalid")
      input.classList.add("is-valid")
    }
  })

  return isValid
}

// Función para formatear números
function formatNumber(num) {
  return new Intl.NumberFormat("es-ES").format(num)
}

// Función para formatear fechas
function formatDate(date) {
  return new Intl.DateTimeFormat("es-ES", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(date))
}

// Función para debounce (útil para búsquedas)
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

// Función para throttle (útil para scroll events)
function throttle(func, limit) {
  let inThrottle
  return function () {
    const args = arguments
    
    if (!inThrottle) {
      func.apply(this, args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

// Configurar CSRF token para requests AJAX
function getCSRFToken() {
  return (
    document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
    document.querySelector('meta[name="csrf-token"]')?.content ||
    ""
  )
}

// Configuración global para fetch requests
const defaultFetchOptions = {
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": getCSRFToken(),
  },
}

// Función helper para hacer requests
async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      ...defaultFetchOptions,
      ...options,
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    return await response.json()
  } catch (error) {
    console.error("API request failed:", error)
    showNotification("Error en la conexión", "error")
    throw error
  }
}

// Función para mostrar notificaciones
function showNotification(message, type) {
  const notification = document.createElement("div")
  notification.classList.add("alert", `alert-${type}`, "alert-dismissible", "fade", "show")
  notification.setAttribute("role", "alert")
  notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `
  document.body.appendChild(notification)
}
