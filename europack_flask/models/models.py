"""SQLAlchemy models for the Europack site.

All fields are kept nullable-friendly since this is demo/placeholder
data intended to make the site runnable out of the box.
"""
from datetime import datetime

from models import db


class Service(db.Model):
    """A service offered by Europack (Design, Support, Maintenance...)."""

    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(4), nullable=True)
    title = db.Column(db.String(120), nullable=True)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(120), nullable=True)


class StatCounter(db.Model):
    """A single "X+ Something" statistic shown in the About section."""

    __tablename__ = "stat_counters"

    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=True)
    suffix = db.Column(db.String(10), nullable=True, default="+")
    label = db.Column(db.String(120), nullable=True)


class BrandPartner(db.Model):
    """A manufacturing brand/partner shown in the logo carousel."""

    __tablename__ = "brand_partners"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=True)
    logo = db.Column(db.String(200), nullable=True)


class Testimonial(db.Model):
    """A quote from a company representative (e.g. the CEO)."""

    __tablename__ = "testimonials"

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(120), nullable=True)
    role = db.Column(db.String(120), nullable=True)
    quote = db.Column(db.Text, nullable=True)
    photo = db.Column(db.String(200), nullable=True)


class ContactMessage(db.Model):
    """A message submitted through the public contact form."""

    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(40), nullable=True)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NewsletterSubscriber(db.Model):
    """An email address collected from the footer newsletter form."""

    __tablename__ = "newsletter_subscribers"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
