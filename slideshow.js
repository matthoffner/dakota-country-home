/**
 * Dakota Country Home - Hero Slideshow
 */

(function() {
  let currentSlide = 0;
  let slides, dots, totalSlides;

  function init() {
    slides = document.querySelectorAll('.slide');
    dots = document.querySelectorAll('.dot');
    totalSlides = slides.length;

    // Navigation buttons
    document.querySelector('.slide-nav.prev')?.addEventListener('click', prevSlide);
    document.querySelector('.slide-nav.next')?.addEventListener('click', nextSlide);

    // Dot navigation
    dots.forEach((dot, index) => {
      dot.addEventListener('click', () => goToSlide(index));
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') prevSlide();
      if (e.key === 'ArrowRight') nextSlide();
    });

    // Touch/swipe support
    let touchStartX = 0;
    const slideshow = document.querySelector('.hero-slideshow');

    slideshow?.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
    }, { passive: true });

    slideshow?.addEventListener('touchend', (e) => {
      const touchEndX = e.changedTouches[0].clientX;
      const diff = touchStartX - touchEndX;
      if (Math.abs(diff) > 50) {
        if (diff > 0) nextSlide();
        else prevSlide();
      }
    }, { passive: true });
  }

  function goToSlide(index) {
    slides[currentSlide].classList.remove('active');
    dots[currentSlide].classList.remove('active');

    currentSlide = index;
    if (currentSlide >= totalSlides) currentSlide = 0;
    if (currentSlide < 0) currentSlide = totalSlides - 1;

    slides[currentSlide].classList.add('active');
    dots[currentSlide].classList.add('active');
  }

  function nextSlide() {
    goToSlide(currentSlide + 1);
  }

  function prevSlide() {
    goToSlide(currentSlide - 1);
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
