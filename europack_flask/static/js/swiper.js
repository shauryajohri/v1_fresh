/**
 * swiper.js — Swiper.js initialisation for the brands/partners carousel.
 */
document.addEventListener('DOMContentLoaded', function () {
  if (typeof Swiper === 'undefined') return;

  var brandsEl = document.querySelector('.brands-swiper');
  if (!brandsEl) return;

  new Swiper('.brands-swiper', {
    loop: true,
    autoplay: { delay: 2200, disableOnInteraction: false },
    slidesPerView: 2,
    spaceBetween: 30,
    breakpoints: {
      576: { slidesPerView: 3 },
      768: { slidesPerView: 4 },
      1024: { slidesPerView: 6 }
    }
  });
});
