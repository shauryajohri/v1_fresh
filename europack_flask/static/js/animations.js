/**
 * animations.js — GSAP hero timeline, ScrollTrigger reveals, and
 * counter animation using IntersectionObserver.
 */
document.addEventListener('DOMContentLoaded', function () {
  if (typeof AOS !== 'undefined') {
    AOS.init({ duration: 800, once: true, offset: 60 });
  }

  if (typeof gsap !== 'undefined') {
    var heroTitle = document.querySelector('.hero-title');
    var heroSubtitle = document.querySelector('.hero-subtitle');
    var heroActions = document.querySelector('.hero-actions');
    var heroEyebrow = document.querySelector('.hero-eyebrow');

    if (heroTitle) {
      var tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
      tl.from(heroEyebrow, { opacity: 0, y: 20, duration: 0.6 })
        .from(heroTitle, { opacity: 0, y: 40, duration: 0.8 }, '-=0.3')
        .from(heroSubtitle, { opacity: 0, y: 30, duration: 0.7 }, '-=0.4')
        .from(heroActions, { opacity: 0, y: 20, duration: 0.6 }, '-=0.3');
    }

    if (typeof ScrollTrigger !== 'undefined') {
      gsap.registerPlugin(ScrollTrigger);
      document.querySelectorAll('.service-card, .agency-card').forEach(function (card) {
        gsap.from(card, {
          opacity: 0,
          y: 40,
          duration: 0.6,
          scrollTrigger: { trigger: card, start: 'top 85%' }
        });
      });
    }
  }

  // Counter animation for stats section
  var counters = document.querySelectorAll('.stat-number');
  if (counters.length && 'IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    counters.forEach(function (counter) { observer.observe(counter); });
  }

  function animateCounter(el) {
    var target = parseInt(el.getAttribute('data-target'), 10) || 0;
    var current = 0;
    var duration = 1500;
    var startTime = null;

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      current = Math.floor(progress * target);
      el.textContent = current;
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target;
      }
    }
    requestAnimationFrame(step);
  }
});
