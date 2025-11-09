# app/models/user.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    """Modèle utilisateur"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100))
    is_premium = db.Column(db.Boolean, default=False)
    premium_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sessions = db.relationship('Session', backref='user', lazy=True)
    
    def get_plan_limits(self):
        if self.is_premium and (not self.premium_expires or self.premium_expires > datetime.utcnow()):
            return {
                'exercises': 15,
                'questions_per_session': 20,
                'daily_sessions': 10,
                'voice_response': True,
                'advanced_analysis': True,
                'emergency_alert': True,
                'personalized_treatment': True
            }
        else:
            return {
                'exercises': 3,
                'questions_per_session': 5,
                'daily_sessions': 2,
                'voice_response': False,
                'advanced_analysis': False,
                'emergency_alert': True,
                'personalized_treatment': False
            }
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'is_premium': self.is_premium,
            'plan_limits': self.get_plan_limits(),
            'created_at': self.created_at.isoformat()
        }


class Session(db.Model):
    """Session thérapeutique"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    emotion_detected = db.Column(db.String(50))
    confidence = db.Column(db.Float)
    transcription = db.Column(db.Text)
    danger_level = db.Column(db.Integer, default=0)
    
    conversation_history = db.Column(db.JSON)
    
    diagnosis = db.Column(db.String(200))
    treatment_plan = db.Column(db.JSON)
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'emotion': self.emotion_detected,
            'confidence': self.confidence,
            'transcription': self.transcription,
            'danger_level': self.danger_level,
            'diagnosis': self.diagnosis,
            'started_at': self.started_at.isoformat(),
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }
