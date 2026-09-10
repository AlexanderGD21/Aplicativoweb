document.addEventListener("DOMContentLoaded", () => {
  const links = [...document.querySelectorAll("[data-legal-index] a[href^='#']")]
  const sections = links
    .map((link) => document.querySelector(link.getAttribute("href")))
    .filter(Boolean)

  if (!links.length || !sections.length || !("IntersectionObserver" in window)) return

  const activate = (section) => {
    links.forEach((link) => {
      const active = link.getAttribute("href") === `#${section.id}`
      link.classList.toggle("is-active", active)
      if (active) link.setAttribute("aria-current", "location")
      else link.removeAttribute("aria-current")
    })
  }

  const observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
    if (visible) activate(visible.target)
  }, { rootMargin: "-18% 0px -64%", threshold: [0.05, 0.25, 0.6] })

  sections.forEach((section) => observer.observe(section))
})
