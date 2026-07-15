# Europack Flask Website

An original Flask recreation of the layout/UX of an industrial packaging
equipment supplier site, built with Bootstrap 5 utilities, GSAP, AOS, and
Swiper. All content is original wording; brand names in the carousel are
generic placeholders. All images are generated placeholders.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
flask --app app run             # or: python app.py
```

The app creates a local SQLite database (`europack.db`) on first run via
`db.create_all()`.

## Project Structure

```
app.py                  Flask application factory
config.py                Environment configuration classes
models/                  SQLAlchemy models (Service, StatCounter, BrandPartner,
                          Testimonial, ContactMessage, NewsletterSubscriber)
forms/                   Flask-WTF forms (ContactForm, NewsletterForm)
routes/main.py           Blueprint with all page routes
templates/               Jinja2 templates (base + pages + components + errors)
static/css/              style.css, responsive.css, animations.css
static/js/               main.js, navbar.js, animations.js, swiper.js
static/images/           Generated placeholder images (replace with real assets)
```

## Notes

- Contact form is CSRF-protected via Flask-WTF and validates server-side.
- Bootstrap's JS bundle is loaded for grid/utility support only; the
  navbar dropdown and mobile menu are implemented manually in `navbar.js`.
- Replace placeholder images in `static/images/` with real photography and
  licensed brand logos before deploying to production.
