# reset_db.py
import os
import sys

# Add your project path
sys.path.insert(0, os.path.dirname(__file__))

from aivent import create_app, db
from aivent.models import CertificateRecord
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)
    
    # Check if certificate_record table exists
    if inspector.has_table('certificate_record'):
        print("Found existing certificate_record table...")
        print("Dropping certificate_record table...")
        CertificateRecord.__table__.drop(db.engine)
        print("Table dropped successfully!")
    
    print("Creating new certificate_record table...")
    CertificateRecord.__table__.create(db.engine)
    print("Table created successfully with correct schema!")
    
    # Verify the new table structure
    columns = inspector.get_columns('certificate_record')
    print("\nNew certificate_record table columns:")
    for col in columns:
        print(f"  - {col['name']} ({col['type']})")
    
    print("\n✅ Database fix completed! You can now run your Flask app.")