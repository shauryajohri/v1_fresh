"""Contact page form definition."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional


class ContactForm(FlaskForm):
    """Public contact form: name, email, phone, subject, message."""

    name = StringField(
        "Full Name", validators=[DataRequired(), Length(min=2, max=120)]
    )
    email = StringField(
        "Email Address", validators=[DataRequired(), Email(), Length(max=120)]
    )
    phone = StringField("Phone Number", validators=[Optional(), Length(max=40)])
    subject = StringField("Subject", validators=[Optional(), Length(max=200)])
    message = TextAreaField(
        "Message", validators=[DataRequired(), Length(min=10, max=2000)]
    )
