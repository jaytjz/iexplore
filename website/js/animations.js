// ===================================
// Scroll Reveal Animations
// ===================================

function scrollReveal() {
  const reveals = document.querySelectorAll(
    ".solution-card, .demo-card, .team-card, .resource-card, .stat-card, .metric-card"
  );

  // Add reveal class to elements
  reveals.forEach((el) => {
    if (!el.classList.contains("reveal")) {
      el.classList.add("reveal");
    }
  });

  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          // Add stagger delay for cards
          setTimeout(() => {
            entry.target.classList.add("active");
          }, index * 100);
          revealObserver.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.15,
      rootMargin: "0px 0px -50px 0px",
    }
  );

  reveals.forEach((el) => revealObserver.observe(el));
}

// Initialize scroll reveal on DOM load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", scrollReveal);
} else {
  scrollReveal();
}

// ===================================
// Parallax Effect for Hero Background
// ===================================

function parallaxEffect() {
  const heroBg = document.querySelector(".hero-bg");

  if (heroBg) {
    window.addEventListener("scroll", () => {
      const scrolled = window.pageYOffset;
      const rate = scrolled * 0.5;
      heroBg.style.transform = `translateY(${rate}px)`;
    });
  }
}

parallaxEffect();

// ===================================
// Typing Effect for Hero Title (Optional)
// ===================================

function typingEffect(element, text, speed = 100) {
  let i = 0;
  element.textContent = "";

  function type() {
    if (i < text.length) {
      element.textContent += text.charAt(i);
      i++;
      setTimeout(type, speed);
    }
  }

  type();
}

// Uncomment to enable typing effect
// const heroTitle = document.querySelector('.hero-title');
// if (heroTitle) {
//     const originalText = heroTitle.textContent;
//     window.addEventListener('load', () => {
//         typingEffect(heroTitle, originalText, 50);
//     });
// }

// ===================================
// Card Tilt Effect on Hover
// ===================================

function cardTiltEffect() {
  const cards = document.querySelectorAll(
    ".solution-card, .team-card, .resource-card"
  );

  cards.forEach((card) => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      const rotateX = (y - centerY) / 10;
      const rotateY = (centerX - x) / 10;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform =
        "perspective(1000px) rotateX(0) rotateY(0) scale(1)";
    });
  });
}

// Initialize card tilt effect
cardTiltEffect();

// ===================================
// Progress Bar for Page Scroll
// ===================================

function createProgressBar() {
  // Create progress bar element
  const progressBar = document.createElement("div");
  progressBar.className = "scroll-progress";
  progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 0%;
        height: 3px;
        background: linear-gradient(90deg, var(--primary-color), var(--primary-light));
        z-index: 9999;
        transition: width 0.1s ease;
    `;

  document.body.appendChild(progressBar);

  // Update progress on scroll
  window.addEventListener("scroll", () => {
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight - windowHeight;
    const scrolled = window.pageYOffset;
    const progress = (scrolled / documentHeight) * 100;

    progressBar.style.width = `${progress}%`;
  });
}

createProgressBar();

// ===================================
// Animate Elements on Scroll
// ===================================

function animateOnScroll() {
  const animatedElements = document.querySelectorAll(
    ".section-title, .section-intro, .problem-text, .how-it-works"
  );

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "0";
          entry.target.style.transform = "translateY(30px)";

          setTimeout(() => {
            entry.target.style.transition = "all 0.8s ease";
            entry.target.style.opacity = "1";
            entry.target.style.transform = "translateY(0)";
          }, 100);

          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.1,
    }
  );

  animatedElements.forEach((el) => observer.observe(el));
}

animateOnScroll();

// ===================================
// Gradient Animation for Hero
// ===================================

function animateHeroGradient() {
  const heroBg = document.querySelector(".hero-bg");

  if (heroBg) {
    let hue = 250;

    setInterval(() => {
      hue = (hue + 1) % 360;
      heroBg.style.background = `linear-gradient(135deg, 
                hsl(${hue}, 70%, 65%) 0%, 
                hsl(${(hue + 30) % 360}, 70%, 55%) 100%)`;
    }, 50);
  }
}

// Uncomment to enable animated gradient (performance intensive)
// animateHeroGradient();

// ===================================
// Floating Animation for Icons
// ===================================

function floatingAnimation() {
  const icons = document.querySelectorAll(".card-icon, .resource-icon");

  icons.forEach((icon, index) => {
    icon.style.animation = `float 3s ease-in-out ${index * 0.2}s infinite`;
  });

  // Add keyframes if not in CSS
  if (!document.querySelector("#float-keyframes")) {
    const style = document.createElement("style");
    style.id = "float-keyframes";
    style.textContent = `
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
            }
        `;
    document.head.appendChild(style);
  }
}

floatingAnimation();

// ===================================
// Cursor Trail Effect (Optional - Fun!)
// ===================================

function cursorTrail() {
  let particles = [];

  class Particle {
    constructor(x, y) {
      this.x = x;
      this.y = y;
      this.size = Math.random() * 3 + 1;
      this.speedX = Math.random() * 2 - 1;
      this.speedY = Math.random() * 2 - 1;
      this.life = 30;
    }

    update() {
      this.x += this.speedX;
      this.y += this.speedY;
      this.life--;
      if (this.size > 0.1) this.size -= 0.1;
    }

    draw(ctx) {
      ctx.fillStyle = `rgba(99, 102, 241, ${this.life / 30})`;
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const canvas = document.createElement("canvas");
  canvas.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 9998;
    `;
  document.body.appendChild(canvas);

  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  window.addEventListener("resize", () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  });

  document.addEventListener("mousemove", (e) => {
    particles.push(new Particle(e.clientX, e.clientY));
  });

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    particles.forEach((particle, index) => {
      particle.update();
      particle.draw(ctx);

      if (particle.life <= 0) {
        particles.splice(index, 1);
      }
    });

    requestAnimationFrame(animate);
  }

  animate();
}

// Uncomment to enable cursor trail
// cursorTrail();

// ===================================
// Section Fade In on Load
// ===================================

window.addEventListener("load", () => {
  document.querySelectorAll(".section").forEach((section, index) => {
    section.style.opacity = "0";
    setTimeout(() => {
      section.style.transition = "opacity 0.5s ease";
      section.style.opacity = "1";
    }, index * 100);
  });
});

// ===================================
// Performance Optimization
// ===================================

// Debounce function for scroll events
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Apply debounce to intensive scroll handlers
const debouncedScroll = debounce(() => {
  // Any intensive scroll operations can go here
}, 100);

window.addEventListener("scroll", debouncedScroll);
