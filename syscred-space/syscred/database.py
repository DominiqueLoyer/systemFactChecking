# -*- coding: utf-8 -*-
"""
Database Manager for SysCRED
===========================
Handles connection to Supabase (PostgreSQL) and defines models.
Falls back to SQLite if PostgreSQL is unavailable.
"""

import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy
db = SQLAlchemy()

class AnalysisResult(db.Model):
    """Stores the result of a credibility analysis."""
    __tablename__ = 'analysis_results'

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    credibility_score = db.Column(db.Float, nullable=False)
    summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Metadata stored as JSON if supported, or simplified columns
    source_reputation = db.Column(db.String(50))
    fact_check_count = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'score': self.credibility_score,
            'summary': self.summary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'source_reputation': self.source_reputation
        }

def init_db(app):
    """Initialize the database with the Flask app."""
    # Use SYSCRED_DATABASE_URL first (from .env), fallback to DATABASE_URL (from Render/HF)
    db_url = os.environ.get('SYSCRED_DATABASE_URL') or os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    # Test PostgreSQL reachability before committing to it
    if db_url and 'postgresql' in db_url:
        try:
            import socket
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            socket.getaddrinfo(parsed.hostname, parsed.port or 5432)
        except (socket.gaierror, Exception) as e:
            print(f"[SysCRED-DB] PostgreSQL host unreachable ({parsed.hostname}): {e}")
            print("[SysCRED-DB] Falling back to SQLite...")
            db_url = None  # Force SQLite fallback
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///syscred.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            db.create_all()
            db_type = 'PostgreSQL (Supabase)' if db_url else 'SQLite (local)'
            print(f"[SysCRED-DB] Database initialized: {db_type}")
        except Exception as e:
            print(f"[SysCRED-DB] Database init error: {e}")
