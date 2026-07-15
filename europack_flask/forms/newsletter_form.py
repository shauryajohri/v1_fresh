"""Footer newsletter subscription form."""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Email


class NewsletterForm(FlaskForm):
    """Simple single-field newsletter subscription form."""

    email = StringField("Email Address", validators=[DataRequired(), Email()])
