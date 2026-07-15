/**
 * navbar.js — mobile hamburger toggle and dropdown handling.
 * Bootstrap JS components are intentionally not used for the nav.
 */
document.addEventListener('DOMContentLoaded', function () {
  var toggle = document.getElementById('navbarToggle');
  var navWrapper = document.getElementById('navbarNavWrapper');

  if (toggle && navWrapper) {
    toggle.addEventListener('click', function () {
      navWrapper.classList.toggle('open');
      toggle.classList.toggle('open');
    });
  }

  document.querySelectorAll('.nav-dropdown').forEach(function (dropdown) {
    var toggleLink = dropdown.querySelector('.dropdown-toggle');
    if (!toggleLink) return;

    toggleLink.addEventListener('click', function (e) {
      if (window.innerWidth <= 992) {
        e.preventDefault();
        dropdown.classList.toggle('open');
      }
    });
  });

  // Close mobile menu when a nav link is clicked
  document.querySelectorAll('.navbar-nav a').forEach(function (link) {
    link.addEventListener('click', function () {
      if (window.innerWidth <= 992 && navWrapper) {
        navWrapper.classList.remove('open');
      }
    });
  });
});
