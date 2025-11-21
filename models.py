# models.py (update the VocationalTrack model only; keep rest of file as-is)

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
#from models import db  
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model,UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    age = db.Column(db.Integer)
    #pincode = db.Column(db.String(10))
    email=db.Column(db.String(255))
    phone_number=db.Column(db.String(20))
    education = db.Column(db.String(100))
    #language = db.Column(db.String(20))
    interests = db.Column(db.String(255))  # comma-separated tags
    skill_level = db.Column(db.String(20))  # Beginner/Intermediate/Advanced
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    password_hash = db.Column(db.String(255), nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

class CentreCourse(db.Model):
    __tablename__ = "centre_courses"
    id = db.Column(db.Integer, primary_key=True)
    centre_id = db.Column(db.Integer, db.ForeignKey("centres.id"))
    career_id = db.Column(db.Integer, db.ForeignKey("careers.id"))


class VocationalTrack(db.Model):
    __tablename__ = "careers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)    # already used by templates
    sector = db.Column(db.String(255), nullable=True)
    attributes = db.Column(db.Text, default="")
    key_learnings = db.Column(ARRAY(db.Text)) 
    #min_education = db.Column(db.String(50))
    earning_low = db.Column(db.Integer)
    earning_high = db.Column(db.Integer)
    # NEW optional fields:
    # career_path = db.Column(db.String(500))  # e.g., "Beautician Assistant > Cosmetology > Salon Manager"
    recommended_skill_level = db.Column(db.String(20))  # "Beginner"/"Intermediate"/"Advanced"

class TrainingCentre(db.Model):
    __tablename__ = "centres"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, default="")
    # pincode = db.Column(db.String(10))
    contact = db.Column(db.String(50))
    sector = db.Column(ARRAY(db.Text))   # primary sector tag
    source_url = db.Column(ARRAY(db.Text)) # comma-separated course titles
