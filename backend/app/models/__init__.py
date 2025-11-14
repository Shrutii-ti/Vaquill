"""
SQLAlchemy models package.
Import all models here for easy access and Alembic discovery.
"""

from app.models.user import User
from app.models.case import Case
from app.models.document import Document
from app.models.argument import Argument
from app.models.verdict import Verdict

__all__ = [
    "User",
    "Case",
    "Document",
    "Argument",
    "Verdict",
]
