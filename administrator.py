from user import User
from db import db

class Administrator(User):
	def __init__(self, user: User):
		if user.role != 'administrator':
			raise ValueError("User is not a administrator")
		self.user = user

	def grant_privileges(self, user_id, new_role):
		target_user = User.query.get(user_id)
		if not target_user:
			raise ValueError("Target user not found.")

		if target_user.role == new_role:
			raise ValueError("User already has this role.")

		target_user.role = new_role
		db.session.commit()
		print(f"Privileges updated: {target_user.name} is now a {new_role}.")

	def add_user(self, **kwargs):
		user = User(**kwargs)
		db.session.add(user)
		db.session.commit()
		print(f"User '{user.name}' added successfully.")

	def delete_user(self, userId):
		user = User.query.get(userId)
		if user:
			db.session.delete(user)
			db.session.commit()
			print(f"User ID {userId} deleted successfully.")
		else:
			print("User not found.")

	def update_user(self, userId, **kwargs):
		user = User.query.get(userId)
		if not User:
			print("Product not found.")
			return
		for key, value in kwargs.items():
			if hasattr(user, key):
				setattr(user, key, value)
		db.session.commit()
		print(f"User ID {userId} updated successfully.")

