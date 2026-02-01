/**
 * Dakota Country Home - Hero Slideshow
 */

(function() {
  let currentSlide = 0;
  let slides, totalSlides;
  let autoplayInterval = null;
  let progressBar = null;
  let currentIndicator = null;
  const AUTOPLAY_DELAY = 5000; // 5 seconds per slide

  function init() {
    slides = document.querySelectorAll('.slide');
    totalSlides = slides.length;
    progressBar = document.querySelector('.slide-progress-bar');
    currentIndicator = document.querySelector('.slide-current');

    // Update total count in indicator
    const totalIndicator = document.querySelector('.slide-total');
    if (totalIndicator) {
      totalIndicator.textContent = totalSlides;
    }

    // Navigation buttons
    document.querySelector('.slide-nav.prev')?.addEventListener('click', () => {
      prevSlide();
      resetAutoplay();
    });
    document.querySelector('.slide-nav.next')?.addEventListener('click', () => {
      nextSlide();
      resetAutoplay();
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') {
        prevSlide();
        resetAutoplay();
      }
      if (e.key === 'ArrowRight') {
        nextSlide();
        resetAutoplay();
      }
    });

    // Touch/swipe support
    let touchStartX = 0;
    const slideshow = document.querySelector('.hero-slideshow');

    slideshow?.addEventListener('touchstart', (e) => {
      touchStartX = e.touches[0].clientX;
      pauseAutoplay();
    }, { passive: true });

    slideshow?.addEventListener('touchend', (e) => {
      const touchEndX = e.changedTouches[0].clientX;
      const diff = touchStartX - touchEndX;
      if (Math.abs(diff) > 50) {
        if (diff > 0) nextSlide();
        else prevSlide();
      }
      resetAutoplay();
    }, { passive: true });

    // Pause on hover
    slideshow?.addEventListener('mouseenter', pauseAutoplay);
    slideshow?.addEventListener('mouseleave', startAutoplay);

    // Start autoplay
    updateIndicator();
    startAutoplay();
  }

  function goToSlide(index) {
    slides[currentSlide].classList.remove('active');

    currentSlide = index;
    if (currentSlide >= totalSlides) currentSlide = 0;
    if (currentSlide < 0) currentSlide = totalSlides - 1;

    slides[currentSlide].classList.add('active');
    updateIndicator();
  }

  function updateIndicator() {
    if (currentIndicator) {
      currentIndicator.textContent = currentSlide + 1;
    }
    if (progressBar) {
      const progress = ((currentSlide + 1) / totalSlides) * 100;
      progressBar.style.width = progress + '%';
    }
  }

  function nextSlide() {
    goToSlide(currentSlide + 1);
  }

  function prevSlide() {
    goToSlide(currentSlide - 1);
  }

  function startAutoplay() {
    if (autoplayInterval) return;
    autoplayInterval = setInterval(nextSlide, AUTOPLAY_DELAY);
  }

  function pauseAutoplay() {
    if (autoplayInterval) {
      clearInterval(autoplayInterval);
      autoplayInterval = null;
    }
  }

  function resetAutoplay() {
    pauseAutoplay();
    startAutoplay();
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
