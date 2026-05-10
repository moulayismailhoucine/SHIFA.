import sys
import getpass
import bcrypt

sys.path.insert(0, ".")

from app.database import SessionLocal
from app.models import User

def create_admin(username, email, name):
    db = SessionLocal()
    try:
        # Check if user exists
        existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            print(f"Error: User with username '{username}' or email '{email}' already exists.")
            sys.exit(1)

        password = getpass.getpass("Enter new admin password: ")
        confirm_password = getpass.getpass("Confirm password: ")

        if password != confirm_password:
            print("Error: Passwords do not match.")
            sys.exit(1)

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        new_admin = User(
            name=name,
            email=email,
            username=username,
            password_hash=hashed_password,
            role="admin"
        )
        db.add(new_admin)
        db.commit()
        print(f"Success: Admin account '{username}' created successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scripts/create_admin.py <username> <email> <full_name>")
        print("Example: python scripts/create_admin.py john_doe john@example.com \"John Doe\"")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    name = sys.argv[3]
    
    create_admin(username, email, name)
