// Funcionalidad de autenticación mejorada
document.addEventListener("DOMContentLoaded", () => {
  // Elementos del formulario
  const form = document.querySelector("form")
  const usernameField = document.getElementById("id_username")
  const emailField = document.getElementById("id_email")
  const password1Field = document.getElementById("id_password1")
  const password2Field = document.getElementById("id_password2")
  const firstNameField = document.getElementById("id_first_name")
  const lastNameField = document.getElementById("id_last_name")
  const termsCheckbox = document.getElementById("id_acepto_terminos")
  const matchDiv = document.getElementById("passwordMatch") // Declare matchDiv here

  // Inicializar animaciones de entrada
  initPageAnimations()

  // Configurar toggles de contraseña
  setupPasswordToggles()

  // Configurar validaciones en tiempo real
  if (usernameField) setupUsernameValidation()
  if (emailField) setupEmailValidation()
  if (password1Field) setupPasswordValidation()
  if (password2Field) setupPasswordConfirmation()
  if (firstNameField) setupNameValidation(firstNameField, "firstNameError")
  if (lastNameField) setupNameValidation(lastNameField, "lastNameError")
  if (termsCheckbox) setupTermsValidation()

  // Configurar envío del formulario
  if (form) setupFormSubmission()

  // Configurar efectos de partículas
  setupFloatingParticles()

  // NUEVO: Configurar restricción de solo letras para nombres
  setupLettersOnlyValidation()
})

// Animaciones de entrada de página
function initPageAnimations() {
  const authCard = document.querySelector(".auth-card")
  const formGroups = document.querySelectorAll(".form-group")

  if (authCard) {
    authCard.classList.add("fade-in")
  }

  // Animar campos del formulario secuencialmente
  formGroups.forEach((group, index) => {
    group.style.animationDelay = `${0.1 + index * 0.1}s`
  })
}

// Configurar toggles de contraseña
function setupPasswordToggles() {
  const toggles = document.querySelectorAll(".password-toggle")

  toggles.forEach((toggle) => {
    const targetId = toggle.getAttribute("data-target")
    const targetField = document.getElementById(targetId)
    const icon = toggle.querySelector(".toggle-icon")

    if (targetField && icon) {
      toggle.addEventListener("click", (e) => {
        e.preventDefault()

        if (targetField.type === "password") {
          targetField.type = "text"
          toggle.setAttribute("data-visible", "true")
          toggle.setAttribute("title", "Ocultar contraseña")
        } else {
          targetField.type = "password"
          toggle.setAttribute("data-visible", "false")
          toggle.setAttribute("title", "Mostrar contraseña")
        }

        // Animación del botón
        toggle.style.transform = "translateY(-50%) scale(0.9)"
        setTimeout(() => {
          toggle.style.transform = "translateY(-50%) scale(1)"
        }, 150)
      })
    }
  })
}

// NUEVO: Configurar restricción de solo letras para nombres
function setupLettersOnlyValidation() {
  const nameFields = [document.getElementById("id_first_name"), document.getElementById("id_last_name")]

  nameFields.forEach((field) => {
    if (field) {
      // Prevenir entrada de números y caracteres especiales
      field.addEventListener("keypress", function (e) {
        const char = String.fromCharCode(e.which)
        // Permitir solo letras (incluyendo acentos), espacios y teclas de control
        if (!/[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/.test(char) && e.which !== 8 && e.which !== 0) {
          e.preventDefault()

          // Mostrar feedback visual
          this.classList.add("invalid")
          setTimeout(() => {
            this.classList.remove("invalid")
          }, 500)
        }
      })

      // Limpiar caracteres no válidos al pegar
      field.addEventListener("paste", function (e) {
        setTimeout(() => {
          const value = this.value
          const cleanValue = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, "")
          if (value !== cleanValue) {
            this.value = cleanValue
            this.classList.add("invalid")
            setTimeout(() => {
              this.classList.remove("invalid")
            }, 500)
          }
        }, 10)
      })

      // Validación en tiempo real
      field.addEventListener("input", function () {
        const value = this.value
        const cleanValue = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]/g, "")
        if (value !== cleanValue) {
          this.value = cleanValue
        }
      })
    }
  })
}

// Validación de nombre de usuario
function setupUsernameValidation() {
  const usernameField = document.getElementById("id_username")
  const errorDiv = document.getElementById("usernameError")

  usernameField.addEventListener("input", function () {
    const value = this.value.trim()
    const isValid = validateUsername(value)

    updateFieldValidation(
      this,
      errorDiv,
      isValid,
      isValid ? "" : "El nombre de usuario debe tener al menos 3 caracteres y solo contener letras, números y guiones.",
    )
  })

  usernameField.addEventListener("blur", function () {
    if (this.value.trim()) {
      checkUsernameAvailability(this.value.trim())
    }
  })
}

// Validación de email
function setupEmailValidation() {
  const emailField = document.getElementById("id_email")
  const validationDiv = document.getElementById("emailValidation")
  const errorDiv = document.getElementById("emailError")

  emailField.addEventListener("input", function () {
    const value = this.value.trim()
    const isValid = validateEmail(value)

    if (value) {
      if (isValid) {
        showValidationMessage(validationDiv, "✓ Email válido", "valid")
        updateFieldValidation(this, errorDiv, true, "")
      } else {
        showValidationMessage(validationDiv, "✗ Formato de email inválido", "invalid")
        updateFieldValidation(this, errorDiv, false, "Por favor ingresa un email válido.")
      }
    } else {
      hideValidationMessage(validationDiv)
      updateFieldValidation(this, errorDiv, false, "")
    }
  })
}

// Validación de contraseña
function setupPasswordValidation() {
  const password1Field = document.getElementById("id_password1")
  const strengthDiv = document.getElementById("passwordStrength")
  const errorDiv = document.getElementById("password1Error")

  password1Field.addEventListener("input", function () {
    const value = this.value
    const strength = calculatePasswordStrength(value)

    if (value) {
      showPasswordStrength(strengthDiv, strength)
      const isValid = strength.score >= 2
      updateFieldValidation(this, errorDiv, isValid, isValid ? "" : "La contraseña debe ser más segura.")
    } else {
      hidePasswordStrength(strengthDiv)
      updateFieldValidation(this, errorDiv, false, "")
    }

    // Revalidar confirmación si existe
    const password2Field = document.getElementById("id_password2")
    if (password2Field && password2Field.value) {
      validatePasswordConfirmation(password2Field)
    }
  })
}

// Validación de confirmación de contraseña
function setupPasswordConfirmation() {
  const password2Field = document.getElementById("id_password2")
  const matchDiv = document.getElementById("passwordMatch")
  const errorDiv = document.getElementById("password2Error")

  password2Field.addEventListener("input", function () {
    validatePasswordConfirmation(this, errorDiv, matchDiv)
  })
}

function validatePasswordConfirmation(password2Field, errorDiv, matchDiv) {
  const password1 = document.getElementById("id_password1").value
  const password2 = password2Field.value

  if (password2) {
    const matches = password1 === password2

    if (matches) {
      showValidationMessage(matchDiv, "✓ Las contraseñas coinciden", "match")
      updateFieldValidation(password2Field, errorDiv, true, "")
    } else {
      showValidationMessage(matchDiv, "✗ Las contraseñas no coinciden", "no-match")
      updateFieldValidation(password2Field, errorDiv, false, "Las contraseñas deben coincidir.")
    }
  } else {
    hideValidationMessage(matchDiv)
    updateFieldValidation(password2Field, errorDiv, false, "")
  }
}

// Validación de nombres
function setupNameValidation(field, errorId) {
  const errorDiv = document.getElementById(errorId)

  field.addEventListener("input", function () {
    const value = this.value.trim()
    const isValid = validateName(value)

    updateFieldValidation(this, errorDiv, isValid, isValid ? "" : "Solo se permiten letras y espacios.")
  })
}

// Validación de términos
function setupTermsValidation() {
  const termsCheckbox = document.getElementById("id_acepto_terminos")
  const tooltipDiv = document.getElementById("termsTooltip")

  termsCheckbox.addEventListener("change", function () {
    console.log("Checkbox changed:", this.checked) // Debug
    if (this.checked) {
      hideValidationMessage(tooltipDiv)
      this.classList.remove("invalid")
    } else {
      this.classList.add("invalid")
    }
  })
}

// Configurar envío del formulario
function setupFormSubmission() {
  const form = document.querySelector("form")
  const submitBtn = form.querySelector('button[type="submit"]')

  form.addEventListener("submit", (e) => {
    console.log("Form submitted") // Debug

    if (!validateForm()) {
      e.preventDefault()
      showFormErrors()
      return false
    }

    // Mostrar estado de carga
    if (submitBtn) {
      const originalText = submitBtn.textContent
      submitBtn.textContent = "Creando cuenta..."
      submitBtn.disabled = true

      // Restaurar después de 5 segundos si no hay redirección
      setTimeout(() => {
        submitBtn.textContent = originalText
        submitBtn.disabled = false
      }, 5000)
    }
  })
}

// Funciones de validación
function validateUsername(username) {
  return username.length >= 3 && /^[a-zA-Z0-9_-]+$/.test(username)
}

function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function validateName(name) {
  return name.length > 0 && /^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$/.test(name)
}

function calculatePasswordStrength(password) {
  let score = 0
  const feedback = []

  if (password.length >= 8) score++
  else feedback.push("al menos 8 caracteres")

  if (/[a-z]/.test(password)) score++
  else feedback.push("letras minúsculas")

  if (/[A-Z]/.test(password)) score++
  else feedback.push("letras mayúsculas")

  if (/[0-9]/.test(password)) score++
  else feedback.push("números")

  if (/[^a-zA-Z0-9]/.test(password)) score++
  else feedback.push("símbolos especiales")

  const strength = score <= 2 ? "weak" : score <= 3 ? "medium" : "strong"
  const strengthText = score <= 2 ? "Débil" : score <= 3 ? "Media" : "Fuerte"

  return {
    score,
    strength,
    strengthText,
    feedback: feedback.length > 0 ? `Necesita: ${feedback.join(", ")}` : "Contraseña segura",
  }
}

// Funciones de UI
function updateFieldValidation(field, errorDiv, isValid, errorMessage) {
  if (isValid) {
    field.classList.remove("invalid")
    field.classList.add("valid")
    if (errorDiv) hideValidationMessage(errorDiv)
  } else {
    field.classList.remove("valid")
    if (errorMessage) {
      field.classList.add("invalid")
      if (errorDiv) showValidationMessage(errorDiv, errorMessage, "show")
    }
  }
}

function showValidationMessage(element, message, className) {
  if (element) {
    element.textContent = message
    element.className = element.className.split(" ")[0] + " " + className
  }
}

function hideValidationMessage(element) {
  if (element) {
    element.className = element.className.split(" ")[0]
  }
}

function showPasswordStrength(strengthDiv, strength) {
  if (strengthDiv) {
    strengthDiv.innerHTML = `
            <div class="strength-bar">
                <div class="strength-fill"></div>
            </div>
            <div class="strength-text">${strength.strengthText}</div>
            <div class="strength-message">${strength.feedback}</div>
        `
    strengthDiv.className = `password-strength show strength-${strength.strength}`
  }
}

function hidePasswordStrength(strengthDiv) {
  if (strengthDiv) {
    strengthDiv.className = "password-strength"
  }
}

// Validación completa del formulario
function validateForm() {
  let isValid = true

  // Validar todos los campos requeridos
  const requiredFields = document.querySelectorAll("input[required]")
  requiredFields.forEach((field) => {
    if (!field.value.trim()) {
      isValid = false
      field.classList.add("invalid")
    }
  })

  // Validar términos específicamente
  const termsCheckbox = document.getElementById("id_acepto_terminos")
  if (termsCheckbox && !termsCheckbox.checked) {
    console.log("Terms not accepted") // Debug
    isValid = false
    termsCheckbox.classList.add("invalid")
    const tooltipDiv = document.getElementById("termsTooltip")
    showValidationMessage(tooltipDiv, "⚠️ Debes aceptar los términos y condiciones", "show")
  }

  console.log("Form validation result:", isValid) // Debug
  return isValid
}

function showFormErrors() {
  // Scroll al primer campo con error
  const firstError = document.querySelector(".invalid")
  if (firstError) {
    firstError.scrollIntoView({ behavior: "smooth", block: "center" })
    firstError.focus()
  }
}

// Verificar disponibilidad de nombre de usuario (simulado)
function checkUsernameAvailability(username) {
  // Simulación de verificación
  setTimeout(() => {
    const isAvailable = !["admin", "test", "user"].includes(username.toLowerCase())
    const errorDiv = document.getElementById("usernameError")
    const usernameField = document.getElementById("id_username")

    if (!isAvailable) {
      updateFieldValidation(usernameField, errorDiv, false, "Este nombre de usuario no está disponible.")
    }
  }, 500)
}

// Efectos de partículas flotantes
function setupFloatingParticles() {
  setInterval(createFloatingParticle, 2000)
}

function createFloatingParticle() {
  const particle = document.createElement("div")
  particle.className = "floating-particle"

  // Colores que combinan con el fondo
  const colors = [
    "rgba(102, 126, 234, 0.6)",
    "rgba(118, 75, 162, 0.6)",
    "rgba(240, 147, 251, 0.6)",
    "rgba(245, 87, 108, 0.6)",
  ]
  const color = colors[Math.floor(Math.random() * colors.length)]

  const size = Math.random() * 8 + 4
  const startX = Math.random() * window.innerWidth

  particle.style.cssText = `
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        left: ${startX}px;
        bottom: -10px;
        opacity: ${Math.random() * 0.5 + 0.3};
    `

  document.body.appendChild(particle)

  // Remover después de la animación
  setTimeout(() => {
    if (particle.parentNode) {
      particle.parentNode.removeChild(particle)
    }
  }, 4000)
}

// Interceptar navegación para animaciones de transición
document.addEventListener("click", (e) => {
  const link = e.target.closest("a[href]")
  if (link && (link.href.includes("/login") || link.href.includes("/registro"))) {
    e.preventDefault()

    const authCard = document.querySelector(".auth-card")
    if (authCard) {
      authCard.classList.add("fade-out")

      setTimeout(() => {
        window.location.href = link.href
      }, 300)
    } else {
      window.location.href = link.href
    }
  }
})
