import requests

from constant import BACKEND_URL

def get_chat_history(user_id):
    if not user_id:
        print("Get chat with user id empty")
        return [{"role": "assistant", "content": "Hi! How can I help you?"}]

    url = f"{BACKEND_URL}/chat/chat-room"
    header = {"user-id": user_id}
    resp = requests.get(url, headers=header)

    if resp.status_code != 200:
        raise Exception("Failed to retrieve chat history")

    chat_data = resp.json()

    if len(chat_data) == 0:
        return {}

    return format_chat_history(chat_data)

def delete_chat_room(user_id, chat_room_id):
    url = f"{BACKEND_URL}/chat/{chat_room_id}"
    header = {"user-id": user_id}
    resp = requests.delete(url, headers=header)

    if resp.status_code != 200:
        raise Exception(f"Failed to delete chat room id: {chat_room_id}")

def format_chat_history(chat_data):
    chat_history = {}

    for chat in chat_data:
        # Initialize the list of messages for the current chat room ID
        chat_room_id = chat["chat_room_id"]
        if chat_room_id not in chat_history:
            chat_history[chat_room_id] = []

        # Append formatted messages to the list
        for message in chat["messages"]:
            chat_history[chat_room_id].append({
                "role": message["sender_type"].lower(),
                "content": message["message"]
            })

    return chat_history

def send_message(session_user_id, chat_room_id, message, history):
    if not session_user_id:
        return "", [{"role": "assistant", "content": "You must log in before sending a message."}]

    url = f"{BACKEND_URL}/chat/"
    json_payload = {
        "user_id": session_user_id.value,
        "chat_room_id": chat_room_id,
        "prompt": message
    }
    try:
        resp = requests.post(url, json=json_payload)

        # If backend fails, append a failure message to history
        if resp is None or resp.status_code != 200:
            history.append(
                {"role": "assistant", "content": "Sorry, the chatbot service is unavailable. Please try again later."})
            return "", history

        # Append user and assistant messages to the history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": resp.json().get("message", "No response from chatbot.")})

    except Exception as e:
        # Catch network or other errors and log them
        print(f"Error: {e}")
        history.append({"role": "assistant", "content": "An error occurred. Please try again later."})

        # Return the updated history
    return "", history