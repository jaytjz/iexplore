// ===================================
// Smooth Scrolling for Anchor Links
// ===================================

document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute("href"));

    if (target) {
      const navHeight = document.querySelector(".navbar").offsetHeight;
      const targetPosition = target.offsetTop - navHeight;

      window.scrollTo({
        top: targetPosition,
        behavior: "smooth",
      });
    }
  });
});

// ===================================
// Navbar Background on Scroll
// ===================================

const navbar = document.querySelector(".navbar");
let lastScroll = 0;

window.addEventListener("scroll", () => {
  const currentScroll = window.pageYOffset;

  // Add shadow when scrolled
  if (currentScroll > 100) {
    navbar.style.boxShadow = "0 4px 6px -1px rgba(0, 0, 0, 0.1)";
  } else {
    navbar.style.boxShadow = "0 1px 2px 0 rgba(0, 0, 0, 0.05)";
  }

  lastScroll = currentScroll;
});

// ===================================
// Animate Confidence Bars on Scroll
// ===================================

function animateConfidenceBars() {
  const confidenceBars = document.querySelectorAll(".confidence-fill");

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const width = entry.target.style.width;
          entry.target.style.width = "0";
          setTimeout(() => {
            entry.target.style.width = width;
          }, 100);
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.5,
    }
  );

  confidenceBars.forEach((bar) => observer.observe(bar));
}

// Initialize on DOM load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", animateConfidenceBars);
} else {
  animateConfidenceBars();
}

// ===================================
// Animate Numbers (Counter Effect)
// ===================================

function animateNumbers() {
  const metricValues = document.querySelectorAll(".metric-value");
  const statNumbers = document.querySelectorAll(".stat-number");

  const animateValue = (element, start, end, duration) => {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
      current += increment;
      if (current >= end) {
        element.textContent = end + "%";
        clearInterval(timer);
      } else {
        element.textContent = Math.floor(current) + "%";
      }
    }, 16);
  };

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const target = entry.target;
          const endValue = parseInt(target.textContent);
          animateValue(target, 0, endValue, 1500);
          observer.unobserve(target);
        }
      });
    },
    {
      threshold: 0.5,
    }
  );

  metricValues.forEach((value) => observer.observe(value));
  statNumbers.forEach((num) => {
    if (num.textContent.includes("%")) {
      observer.observe(num);
    }
  });
}

// Initialize number animations
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", animateNumbers);
} else {
  animateNumbers();
}

// ===================================
// Active Navigation Highlight
// ===================================

function highlightActiveSection() {
  const sections = document.querySelectorAll("section[id]");
  const navLinks = document.querySelectorAll('.nav-menu a[href^="#"]');

  window.addEventListener("scroll", () => {
    const scrollPosition = window.pageYOffset + 100;

    sections.forEach((section) => {
      const sectionTop = section.offsetTop;
      const sectionHeight = section.offsetHeight;
      const sectionId = section.getAttribute("id");

      if (
        scrollPosition >= sectionTop &&
        scrollPosition < sectionTop + sectionHeight
      ) {
        navLinks.forEach((link) => {
          link.classList.remove("active");
          if (link.getAttribute("href") === `#${sectionId}`) {
            link.classList.add("active");
          }
        });
      }
    });
  });
}

highlightActiveSection();

// ===================================
// Form Validation (if you add a contact form)
// ===================================

function setupFormValidation() {
  const forms = document.querySelectorAll("form");

  forms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();

      const inputs = form.querySelectorAll(
        "input[required], textarea[required]"
      );
      let isValid = true;

      inputs.forEach((input) => {
        if (!input.value.trim()) {
          isValid = false;
          input.classList.add("error");
        } else {
          input.classList.remove("error");
        }
      });

      if (isValid) {
        // Handle form submission
        console.log("Form is valid, ready to submit");
        // You can add your form submission logic here
      }
    });
  });
}

setupFormValidation();

// ===================================
// Lazy Loading Images
// ===================================

function lazyLoadImages() {
  const images = document.querySelectorAll("img[data-src]");

  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute("data-src");
        imageObserver.unobserve(img);
      }
    });
  });

  images.forEach((img) => imageObserver.observe(img));
}

lazyLoadImages();

// ===================================
// Back to Top Button (Optional)
// ===================================

function createBackToTopButton() {
  // Create button element
  const backToTop = document.createElement("button");
  backToTop.innerHTML = "↑";
  backToTop.className = "back-to-top";
  backToTop.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background: var(--primary-color);
        color: white;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 999;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    `;

  document.body.appendChild(backToTop);

  // Show/hide based on scroll position
  window.addEventListener("scroll", () => {
    if (window.pageYOffset > 300) {
      backToTop.style.opacity = "1";
      backToTop.style.visibility = "visible";
    } else {
      backToTop.style.opacity = "0";
      backToTop.style.visibility = "hidden";
    }
  });

  // Scroll to top on click
  backToTop.addEventListener("click", () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  });
}

createBackToTopButton();

// ===================================
// Console Welcome Message
// ===================================

console.log(
  "%c AI Image Detector ",
  "background: #6366f1; color: white; font-size: 20px; padding: 10px;"
);
console.log("%c Demystifying ML Project ", "font-size: 14px; color: #6b7280;");
console.log(
  "%c Interested in the code? Check out our GitHub! ",
  "font-size: 12px; color: #10b981;"
);
