import requests

BACKEND_URL = "http://localhost:8000"

def get_chat_history(user_id, chat_room_id):
    if not user_id:
        print("Get chat with user id empty")
        return [{"role": "assistant", "content": "Hi! How can I help you?"}]

    url = f"{BACKEND_URL}/chat/chat-room/{chat_room_id}"
    header = {"user-id": user_id}
    resp = requests.get(url, headers=header)

    if resp.status_code != 200:
        raise Exception("Failed to retrieve chat history")

    chat_data = resp.json()

    if len(chat_data["messages"]) == 0:
        return []

    # Format the messages to match {role: "", content: ""}
    return [
        {"role": message["sender_type"].lower(), "content": message["message"]}
        for message in chat_data.get("messages", [])
    ]

def send_message(session_user_id, message, history):
    if not session_user_id:
        return "", [{"role": "assistant", "content": "You must log in before sending a message."}]

    url = f"{BACKEND_URL}/chat/"
    json_payload = {
        "user_id": session_user_id.value,
        "chat_room_id": "room_2",
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