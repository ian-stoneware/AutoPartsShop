from sqlalchemy import or_
from db import db


class User(db.Model):
    __tablename__ = 'User'

    userId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50))

    def __repr__(self):
        return f'<User {self.name} ({self.email})>'

    def register(name, email, password):
        if User.query.filter((User.email == email) | (User.name == name)).first():
            print("User already exists.")
            return False

        user = User(name=name, email=email, password=password, role='customer')
        db.session.add(user)
        db.session.commit()
        print("Registration successful!")
        return True

    def login(identifier, password):
        user = User.query.filter(
            or_(User.name == identifier, User.email == identifier)
        ).first()

        if user and user.password == password:
            print("Login successful!")
            return user
        else:
            print("Login failed!")
            return None

    def reset_password(name, email, new_password):
        user = User.query.filter_by(name=name, email=email).first()
        if user:
            if new_password == user.password:
                print("Failed! Please use a new password different from your current password.")
                return False
            user.password = new_password
            db.session.commit()
            print("Password reset successful!")
            return True
        else:
            print("User not found.")
            return False

    def manage_profile(userId):
        user = User.query.get(userId)
        if user:
            print(f"Profile - ID: {user.userId}, Name: {user.name}, Email: {user.email}")
        else:
            print("User not found.")
