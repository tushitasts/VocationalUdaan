# set_password_for_user.py
from app import app, db
from models import User

EMAIL = "abc@gmail.com"
NEW_PWD = "YourNewPass123"   # change this to the password you want

with app.app_context():
    user = User.query.filter_by(email=EMAIL).first()
    if not user:
        print("User not found:", EMAIL)
    else:
        print("Before:", user.email, "password_hash is", user.password_hash)
        # Use model helper to set password
        if hasattr(user, "set_password"):
            user.set_password(NEW_PWD)
        else:
            # fallback - rarely needed if models are correct
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(NEW_PWD)
        db.session.add(user)
        db.session.commit()
        print("After:", user.email, "password_hash is", user.password_hash)
