// Sistema de notificaciones
class NotificationSystem {
  constructor() {
    this.container = this.createContainer()
    this.welcomeShown = localStorage.getItem("welcomeShown") === "true"
    this.registrationPromptShown = false
    this.startTime = Date.now()

    this.init()
  }

  createContainer() {
    let container = document.getElementById("notifications-container")
    if (!container) {
      container = document.createElement("div")
      container.id = "notifications-container"
      container.style.cssText = `
                position: fixed;
                top: 80px;
                right: 20px;
                z-index: 9999;
                max-width: 350px;
            `
      document.body.appendChild(container)
    }
    return container
  }

  init() {
    // Mostrar bienvenida solo una vez
    if (!this.welcomeShown) {
      setTimeout(() => {
        this.showWelcome()
        localStorage.setItem("welcomeShown", "true")
      }, 1000)
    }

    // Configurar prompt de registro para usuarios anónimos
    this.setupRegistrationPrompt()
  }

  showWelcome() {
    this.show({
      title: "¡Bienvenido al Diccionario Kichwa!",
      message: "Explora palabras, aprende y gana puntos por cada nueva palabra que descubras.",
      type: "welcome",
      duration: 6000,
      icon: "fas fa-hand-wave",
    })
  }

  showWordLearned(points = 10) {
    this.show({
      title: "¡Palabra nueva aprendida!",
      message: `Has ganado ${points} puntos. ¡Sigue explorando!`,
      type: "success",
      duration: 4000,
      icon: "fas fa-star",
    })

    // Actualizar contador de puntos
    this.updatePointsDisplay()
  }

  setupRegistrationPrompt() {
    // Solo para usuarios no autenticados
    if (document.body.dataset.userAuthenticated === "false") {
      setTimeout(() => {
        if (!this.registrationPromptShown) {
          this.showRegistrationPrompt()
          this.registrationPromptShown = true
        }
      }, 180000) // 3 minutos
    }
  }

  showRegistrationPrompt() {
    this.show({
      title: "¿Quieres guardar tus puntos?",
      message: "Regístrate para guardar tu progreso y competir con otros usuarios.",
      type: "info",
      duration: 8000,
      icon: "fas fa-user-plus",
      actions: [
        {
          text: "Registrarme",
          class: "btn-primary",
          action: () => (window.location.href = "/usuarios/registro/"),
        },
        {
          text: "Más tarde",
          class: "btn-secondary",
          action: () => {},
        },
      ],
    })
  }

  show(options) {
    const notification = this.createNotification(options)
    this.container.appendChild(notification)

    // Animación de entrada
    setTimeout(() => {
      notification.classList.add("show")
    }, 100)

    // Auto-remove
    if (options.duration) {
      setTimeout(() => {
        this.remove(notification)
      }, options.duration)
    }

    return notification
  }

  createNotification(options) {
    const notification = document.createElement("div")
    notification.className = `notification notification-${options.type}`

    const typeColors = {
      success: "#28a745",
      error: "#dc3545",
      warning: "#ffc107",
      info: "#17a2b8",
      welcome: "#6f42c1",
    }

    notification.style.cssText = `
            background: white;
            border-left: 4px solid ${typeColors[options.type] || "#17a2b8"};
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            margin-bottom: 10px;
            padding: 16px;
            transform: translateX(100%);
            transition: all 0.3s ease;
            opacity: 0;
            max-width: 100%;
            position: relative;
        `

    let actionsHtml = ""
    if (options.actions) {
      actionsHtml = `
                <div style="margin-top: 12px; display: flex; gap: 8px;">
                    ${options.actions
                      .map(
                        (action) =>
                          `<button class="btn btn-sm ${action.class}" onclick="this.parentElement.parentElement.remove(); (${action.action})()">${action.text}</button>`,
                      )
                      .join("")}
                </div>
            `
    }

    notification.innerHTML = `
            <div style="display: flex; align-items: flex-start;">
                <div style="margin-right: 12px; color: ${typeColors[options.type]};">
                    <i class="${options.icon || "fas fa-info-circle"}" style="font-size: 20px;"></i>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight: 600; color: #333; margin-bottom: 4px;">
                        ${options.title}
                    </div>
                    <div style="color: #666; font-size: 14px; line-height: 1.4;">
                        ${options.message}
                    </div>
                    ${actionsHtml}
                </div>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; color: #999; cursor: pointer; font-size: 18px; padding: 0; margin-left: 8px;">
                    ×
                </button>
            </div>
        `

    // Clase para animación
    notification.classList.add("notification-enter")

    return notification
  }

  remove(notification) {
    notification.style.transform = "translateX(100%)"
    notification.style.opacity = "0"
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification)
      }
    }, 300)
  }

  updatePointsDisplay() {
    fetch("/api/puntos-usuario/")
      .then((response) => response.json())
      .then((data) => {
        const puntosElement = document.getElementById("puntos-usuario")
        if (puntosElement) {
          puntosElement.textContent = data.puntos
        }
      })
      .catch((error) => console.error("Error updating points:", error))
  }
}

// Inicializar sistema de notificaciones
let notificationSystem
document.addEventListener("DOMContentLoaded", () => {
  notificationSystem = new NotificationSystem()
})

// Funciones globales para usar desde otros scripts
function showNotification(message, type = "info", title = null) {
  if (notificationSystem) {
    notificationSystem.show({
      title: title || (type === "success" ? "¡Éxito!" : type === "error" ? "Error" : "Información"),
      message: message,
      type: type,
      duration: 4000,
      icon:
        type === "success"
          ? "fas fa-check-circle"
          : type === "error"
            ? "fas fa-exclamation-circle"
            : type === "warning"
              ? "fas fa-exclamation-triangle"
              : "fas fa-info-circle",
    })
  }
}

function updateUserPoints() {
  if (notificationSystem) {
    notificationSystem.updatePointsDisplay()
  }
}
