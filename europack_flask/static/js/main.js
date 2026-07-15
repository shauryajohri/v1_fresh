/**
 * main.js — global site behaviours: sticky navbar, mobile menu toggle,
 * smooth scroll, back-to-top button, and lazy loading fallback.
 */
document.addEventListener('DOMContentLoaded', function () {
  var navbar = document.getElementById('siteNavbar');
  var backToTop = document.getElementById('backToTop');

  function handleScroll() {
    if (window.scrollY > 60) {
      navbar && navbar.classList.add('scrolled');
    } else {
      navbar && navbar.classList.remove('scrolled');
    }
    if (backToTop) {
      if (window.scrollY > 400) {
        backToTop.classList.add('visible');
      } else {
        backToTop.classList.remove('visible');
      }
    }
  }

  window.addEventListener('scroll', handleScroll);
  handleScroll();

  if (backToTop) {
    backToTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // Smooth scroll for in-page anchor links
  document.querySelectorAll('a[href*="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var url = link.getAttribute('href');
      var hashIndex = url.indexOf('#');
      if (hashIndex === -1) return;
      var hash = url.substring(hashIndex);
      var samePage = url.substring(0, hashIndex) === window.location.pathname ||
        url.substring(0, hashIndex) === '';
      if (samePage && hash.length > 1) {
        var target = document.querySelector(hash);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  });

  // Dismiss flash messages
  document.querySelectorAll('.flash-close').forEach(function (btn) {
    btn.addEventListener('click', function () {
      btn.closest('.flash-message').remove();
    });
  });
  setTimeout(function () {
    document.querySelectorAll('.flash-message').forEach(function (el) { el.remove(); });
  }, 6000);

  // Basic lazy-load fallback for browsers without native support
  if (!('loading' in HTMLImageElement.prototype)) {
    document.querySelectorAll('img[loading="lazy"]').forEach(function (img) {
      img.setAttribute('loading', 'eager');
    });
  }
});
