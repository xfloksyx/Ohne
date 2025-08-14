// Tab functionality (removed since no longer needed for installation)
document.addEventListener("DOMContentLoaded", () => {
  // Smooth scrolling for navigation links
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

  // Enhanced PDF Generation functionality
  const pdfButton = document.getElementById("generatePdfBtn")
  const html2pdf = window.html2pdf // Declare the variable here

  pdfButton.addEventListener("click", async () => {
    // Add loading state
    pdfButton.classList.add("loading")
    pdfButton.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinning">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14,2 14,8 20,8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10,9 9,9 8,9"/>
            </svg>
            Generating PDF...
        `

    try {
      // Load html2pdf library dynamically
      if (!html2pdf) {
        const script = document.createElement("script")
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"
        document.head.appendChild(script)

        // Wait for script to load
        await new Promise((resolve) => {
          script.onload = resolve
        })
      }

      // Configure PDF options
      const opt = {
        margin: [0.5, 0.5, 0.5, 0.5],
        filename: "Ohne_Documentation.pdf",
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: {
          scale: 2,
          useCORS: true,
          letterRendering: true,
        },
        jsPDF: {
          unit: "in",
          format: "a4",
          orientation: "portrait",
        },
      }

      // Hide elements that shouldn't appear in PDF
      const elementsToHide = document.querySelectorAll(".header, .sidebar, .footer, .pdf-button")
      elementsToHide.forEach((el) => (el.style.display = "none"))

      // Adjust content for PDF
      const content = document.querySelector(".content")
      const originalStyle = content.style.cssText
      content.style.cssText = `
        box-shadow: none !important;
        border: none !important;
        margin: 0 !important;
        padding: 20px !important;
        max-width: none !important;
      `

      // Generate PDF
      await window.html2pdf().set(opt).from(content).save()

      // Restore original styles
      content.style.cssText = originalStyle
      elementsToHide.forEach((el) => (el.style.display = ""))
    } catch (error) {
      console.error("PDF generation failed:", error)

      // Fallback to browser print
      window.print()
    }

    // Reset button state
    setTimeout(() => {
      pdfButton.classList.remove("loading")
      pdfButton.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14,2 14,8 20,8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10,9 9,9 8,9"/>
                </svg>
                Generate PDF
            `
    }, 2000)
  })

  // Highlight current section in navigation
  const observerOptions = {
    root: null,
    rootMargin: "-20% 0px -80% 0px",
    threshold: 0,
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute("id")
        const navLink = document.querySelector(`.toc a[href="#${id}"]`)

        // Remove active class from all nav links
        document.querySelectorAll(".toc a").forEach((link) => {
          link.style.background = ""
          link.style.color = ""
        })

        // Add active class to current nav link
        if (navLink) {
          navLink.style.background = "#667eea"
          navLink.style.color = "white"
        }
      }
    })
  }, observerOptions)

  // Observe all sections
  document.querySelectorAll("section[id]").forEach((section) => {
    observer.observe(section)
  })
})
