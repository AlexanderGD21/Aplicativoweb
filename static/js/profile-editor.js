document.addEventListener('DOMContentLoaded', () => {
  const english = document.documentElement.lang.toLowerCase().startsWith('en')
  const copy = english ? {
    chooseBirthDate: 'Your age will appear after you choose your birth date.',
    invalidBirthDate: 'Choose a valid birth date.',
    currentAge: (age) => `Current age: ${age} ${age === 1 ? 'year' : 'years'}`,
  } : {
    chooseBirthDate: 'La edad aparecerá al elegir tu fecha de nacimiento.',
    invalidBirthDate: 'Selecciona una fecha de nacimiento válida.',
    currentAge: (age) => `Edad actual: ${age} ${age === 1 ? 'año' : 'años'}`,
  }
  const phone = document.getElementById('id_telefono')
  if (phone) {
    phone.addEventListener('beforeinput', (event) => {
      if (event.isComposing || !event.inputType.startsWith('insert') || !event.data) return
      if (/[^0-9]/.test(event.data)) {
        event.preventDefault()
        const digits = event.data.replace(/[^0-9]/g, '')
        if (digits) {
          phone.setRangeText(digits, phone.selectionStart, phone.selectionEnd, 'end')
          phone.dispatchEvent(new Event('input', { bubbles: true }))
        }
      }
    })
    phone.addEventListener('input', () => {
      const clean = phone.value.replace(/[^0-9]/g, '').slice(0, 10)
      if (phone.value !== clean) phone.value = clean
    })
  }

  const birthDate = document.getElementById('id_fecha_nacimiento')
  const agePreview = document.getElementById('profile-age-preview')
  if (!birthDate || !agePreview) return

  const updateAge = () => {
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(birthDate.value)
    if (!match) {
      agePreview.textContent = copy.chooseBirthDate
      return
    }
    const year = Number(match[1])
    const month = Number(match[2])
    const day = Number(match[3])
    const validDate = new Date(Date.UTC(year, month - 1, day))
    const today = new Date()
    if (validDate.getUTCFullYear() !== year || validDate.getUTCMonth() + 1 !== month || validDate.getUTCDate() !== day || validDate > today) {
      agePreview.textContent = copy.invalidBirthDate
      return
    }
    const age = today.getFullYear() - year - (today.getMonth() + 1 < month || (today.getMonth() + 1 === month && today.getDate() < day) ? 1 : 0)
    agePreview.textContent = copy.currentAge(age)
  }
  birthDate.addEventListener('input', updateAge)
  birthDate.addEventListener('change', updateAge)
  if (birthDate.value) updateAge()
})
