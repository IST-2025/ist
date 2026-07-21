from flask_login import UserMixin
from . import db
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    username = db.Column(db.String(100), unique=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)


# Add this below your existing User and Contact models
class ProjectRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    college = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)



# Add this below your existing models
class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    resume_filename = db.Column(db.String(200), nullable=False) # Stores the file path
    message = db.Column(db.Text, nullable=True) # Cover letter (optional)
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)



# Add this below your existing models
class InternshipApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    college = db.Column(db.String(200), nullable=False)
    resume_filename = db.Column(db.String(200), nullable=False) # Stores the file path
    date_submitted = db.Column(db.DateTime, default=datetime.utcnow)

class CertificateRecord(db.Model):
    __tablename__ = 'certificate_record'
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    certificate_id = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CertificateRecord {self.student_name} - {self.certificate_id}>"