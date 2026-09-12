document.addEventListener("DOMContentLoaded", () => {
  const cleanPersonName = (value) => [...value.normalize("NFC").replace(/\s/gu, " ")]
    .filter((character) => /[\p{L} ]/u.test(character)).join("")

  document.querySelectorAll("#id_first_name, #id_last_name").forEach((field) => {
    const cleanCurrentValue = () => {
      const original = field.value
      const cleaned = cleanPersonName(original)
      if (cleaned === original) return
      const start = field.selectionStart ?? original.length
      const end = field.selectionEnd ?? start
      field.value = cleaned
      field.setSelectionRange(cleanPersonName(original.slice(0, start)).length,
        cleanPersonName(original.slice(0, end)).length)
    }

    field.addEventListener("beforeinput", (event) => {
      if (event.isComposing || !event.inputType.startsWith("insert") || !event.data) return
      const cleaned = cleanPersonName(event.data)
      if (cleaned === event.data.normalize("NFC") || !event.cancelable) return
      event.preventDefault()
      if (cleaned) {
        field.setRangeText(cleaned, field.selectionStart, field.selectionEnd, "end")
        field.dispatchEvent(new Event("input", { bubbles: true }))
      }
    })
    field.addEventListener("paste", (event) => {
      const pasted = event.clipboardData?.getData("text")
      if (pasted == null) return
      const cleaned = cleanPersonName(pasted)
      if (cleaned === pasted) return
      event.preventDefault()
      field.setRangeText(cleaned, field.selectionStart, field.selectionEnd, "end")
      field.dispatchEvent(new Event("input", { bubbles: true }))
    })
    field.addEventListener("input", (event) => {
      if (!event.isComposing) cleanCurrentValue()
    })
    field.addEventListener("compositionend", cleanCurrentValue)
  })

  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    const field = document.getElementById(button.dataset.passwordToggle)
    if (!field) return

    button.addEventListener("click", () => {
      const visible = field.type === "text"
      field.type = visible ? "password" : "text"
      button.setAttribute("aria-pressed", String(!visible))
      button.setAttribute("aria-label", visible ? "Mostrar contraseña" : "Ocultar contraseña")
      const icon = button.querySelector("i")
      if (icon) {
        icon.classList.toggle("fa-eye", visible)
        icon.classList.toggle("fa-eye-slash", !visible)
      }
      field.focus({ preventScroll: true })
    })
  })

  const password = document.getElementById("id_password1") || document.getElementById("id_new_password1")
  const confirmation = document.getElementById("id_password2") || document.getElementById("id_new_password2")
  const meter = document.querySelector("[data-password-meter]")
  const feedback = document.querySelector("[data-password-feedback]")

  const updatePasswordFeedback = () => {
    if (!password || !meter || !feedback) return
    const value = password.value
    let score = 0
    if (value.length >= 8) score += 1
    if (value.length >= 12) score += 1
    if (/[A-Za-z]/.test(value) && /\d/.test(value)) score += 1
    if (/[^A-Za-z0-9]/.test(value)) score += 1
    meter.dataset.score = String(value ? Math.max(1, score) : 0)
    feedback.textContent = value
      ? (score >= 3 ? "Buena longitud y variedad. La validación final se realiza de forma segura al enviar." : "Usa una frase larga y única; evita datos personales y contraseñas conocidas.")
      : "Usa al menos 8 caracteres y evita contraseñas comunes."
  }

  if (password) {
    password.addEventListener("input", updatePasswordFeedback)
    updatePasswordFeedback()
  }

  if (password && confirmation) {
    const match = document.querySelector("[data-password-match]")
    const updateMatch = () => {
      if (!match) return
      if (!confirmation.value) {
        match.textContent = ""
        return
      }
      const matches = password.value === confirmation.value
      match.textContent = matches ? "Las contraseñas coinciden." : "Las contraseñas todavía no coinciden."
      match.classList.toggle("auth-error", !matches)
      match.classList.toggle("auth-help", matches)
    }
    password.addEventListener("input", updateMatch)
    confirmation.addEventListener("input", updateMatch)
  }

  document.querySelectorAll("form[data-auth-form]").forEach((form) => {
    form.addEventListener("submit", () => {
      if (!form.checkValidity()) return
      const button = form.querySelector('button[type="submit"]')
      if (!button || button.disabled) return
      button.disabled = true
      button.dataset.originalText = button.textContent.trim()
      button.textContent = button.dataset.loadingText || "Procesando…"
    })
  })
})
