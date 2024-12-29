import datetime
import os

import bcrypt
import jwt
from dotenv import load_dotenv

from db import users_collection

# Load environment variables
load_dotenv()
SECRET_KEY = os.getenv("PW_ENCRYPT_KEY")

def authenticate_or_register_user(username, password):
    if not username.strip():
        return False, None
    if not password.strip():
        return False, None

    # Check if the username already exists in the database
    user = users_collection.find_one({"username": username})

    if user:
        # If user exists, validate the password
        stored_hashed_password = user["password"]
        if bcrypt.checkpw(password.encode(), stored_hashed_password):
            return True, user["_id"]  # Successful login, return the user ID
        else:
            return False, None  # Incorrect password
    else:
        # If user does not exist, register them
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user_id = users_collection.insert_one({"username": username, "password": hashed_password}).inserted_id
        print(f"User '{username}' registered successfully.")
        return True, user_id  # Auto-login after registration, return the new user ID

# JWT token generation and validation
def generate_token(username):
    payload = {
        "username": username,
        "exp": datetime.datetime.now() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def validate_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["username"]
    except jwt.ExpiredSignatureError:
        return "Token expired"
    except jwt.InvalidTokenError:
        return "Invalid token"