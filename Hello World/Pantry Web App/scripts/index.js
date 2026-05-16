// Footer
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('year').textContent = new Date().getFullYear();
  document.getElementById('lastMod').textContent = document.lastModified;
});

// Hamburger
document.addEventListener('DOMContentLoaded', () => {
  const hamburger = document.querySelector('.hamburger');
  const nav = document.getElementById('mainNav');

  if (hamburger && nav) {
    hamburger.addEventListener('click', () => {
      const expanded = hamburger.getAttribute('aria-expanded') === 'true';
      hamburger.setAttribute('aria-expanded', !expanded);
      nav.classList.toggle('nav-open');
    });
  }
});

// Carousel 
const track = document.querySelector('.carousel-track');
const slides = Array.from(track.children);
const nextButton = document.querySelector('.carousel-next');
const prevButton = document.querySelector('.carousel-prev');
const dotsContainer = document.querySelector('.carousel-dots');

let currentSlide = 0;

// Nav
slides.forEach((_, i) => {
  const dot = document.createElement('button');
  dot.classList.add('dot');
  dot.setAttribute('aria-label', `Go to slide ${i + 1}`);
  dot.setAttribute('role', 'tab');
  if (i === 0) dot.classList.add('active');
  dot.addEventListener('click', () => goToSlide(i));
  dotsContainer.appendChild(dot);
});

const dots = document.querySelectorAll('.dot');

const goToSlide = (index) => {
  track.style.transform = `translateX(-${index * 100}%)`;
  dots.forEach(d => d.classList.remove('active'));
  dots[index].classList.add('active');
  currentSlide = index;
};

// Next & Back
nextButton.addEventListener('click', () => {
  currentSlide = (currentSlide + 1) % slides.length;
  goToSlide(currentSlide);
});

prevButton.addEventListener('click', () => {
  currentSlide = currentSlide === 0 ? slides.length - 1 : currentSlide - 1;
  goToSlide(currentSlide);
});

// Auto-play
setInterval(() => {
  currentSlide = (currentSlide + 1) % slides.length;
  goToSlide(currentSlide);
}, 10000);

// Smart Pantry IndexedDB Database
const dbName = "SmartPantryDB";
const storeName = "ingredients";

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(dbName, 1);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      if (!db.objectStoreNames.contains(storeName)) {
        db.createObjectStore(storeName, {
          keyPath: "id",
          autoIncrement: true
        });
      }
    };

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject("Database failed to open.");
  });
}