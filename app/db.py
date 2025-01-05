# MongoDB setup
import os

import gradio
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

from constant import BACKEND_URL

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client[os.getenv("MONGO_DB_NAME")]  # Database name
users_collection = db["users"]  # Collection name

def send_feedback(user_id, message):
    if not message.strip():
        gradio.Warning("Feedback is empty", duration=3)
        return None

    try:
        url = f"{BACKEND_URL}/feedback/"
        header = {"user-id": user_id.value}
        json = {
            "message": message
        }
        resp = requests.post(url, headers=header, json=json)

        if resp is None or resp.status_code != 200:
            gradio.Error("Failed to upload feedback", duration=3)
            return None

        gradio.Info("Successfully uploaded feedback!", duration=3)
        return None
    except Exception as e:
        print(f"Error upload feedback: {e}")
        gradio.Error("Unexpected error when upload feedback", duration=3)
        return None