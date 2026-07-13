"""Vercel serverless entry point.

Vercel's @vercel/python builder looks for a module-level WSGI callable named
`app`. We import the already-created Flask app and expose it here.
"""
import os
import sys

# Make the project root importable (api/ is one level down).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402  (WSGI app Vercel will serve)
