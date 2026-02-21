# -*- coding: utf-8 -*-
"""
Database Manager for SysCRED
===========================
Handles connection to Supabase (PostgreSQL) and defines models.
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
            'created_at': self.created_at.isoformat(),
            'source_reputation': self.source_reputation
        }

def init_db(app):
    """Initialize the database with the Flask app."""
    # Fallback to sqlite for local dev if no DATABASE_URL
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///syscred.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    # Create tables if they don't exist (basic migration)
    with app.app_context():
        db.create_all()
        print("[SysCRED-DB] Database tables initialized.")
