"""Primary site routes: home, about, services, products, contact."""
from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from forms.contact_form import ContactForm
from forms.newsletter_form import NewsletterForm
from models import db
from models.models import ContactMessage, NewsletterSubscriber

main = Blueprint("main", __name__)


@main.route("/")
def index():
    """Render the homepage with hero, stats, services, brands, CTA."""
    newsletter_form = NewsletterForm()
    return render_template("index.html", newsletter_form=newsletter_form)


@main.route("/about")
def about():
    """Render the Company / About page."""
    newsletter_form = NewsletterForm()
    return render_template("about.html", newsletter_form=newsletter_form)


@main.route("/services")
def services():
    """Render the Services page."""
    newsletter_form = NewsletterForm()
    return render_template("services.html", newsletter_form=newsletter_form)


@main.route("/products")
def products():
    """Render the Agencies / product categories page."""
    newsletter_form = NewsletterForm()
    return render_template("products.html", newsletter_form=newsletter_form)


@main.route("/contact", methods=["GET", "POST"])
def contact():
    """Render the contact page and process contact form submissions."""
    form = ContactForm()
    newsletter_form = NewsletterForm()

    if form.validate_on_submit():
        try:
            message = ContactMessage(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                subject=form.subject.data,
                message=form.message.data,
            )
            db.session.add(message)
            db.session.commit()
            flash("Message sent successfully! We will get back to you soon.", "success")
        except Exception as exc:  # noqa: BLE001
            db.session.rollback()
            current_app.logger.error("Failed to save contact message: %s", exc)
            flash("Something went wrong while sending your message.", "danger")
        return redirect(url_for("main.contact"))

    if form.errors:
        flash("Please correct the errors below and try again.", "danger")

    return render_template("contact.html", form=form, newsletter_form=newsletter_form)


@main.route("/newsletter", methods=["POST"])
def newsletter():
    """Handle newsletter subscription submissions from the footer form."""
    form = NewsletterForm()
    if form.validate_on_submit():
        existing = NewsletterSubscriber.query.filter_by(email=form.email.data).first()
        if not existing:
            db.session.add(NewsletterSubscriber(email=form.email.data))
            db.session.commit()
        flash("Thanks for subscribing to our newsletter!", "success")
    else:
        flash("Please enter a valid email address.", "danger")
    return redirect(url_for("main.index"))
