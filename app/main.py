import gradio as gr

from chatbot import get_chat_scores
from css import custom_css
from db import send_feedback
from chatbot import send_message, get_chat_history, delete_chat_room
from auth import authenticate_or_register_user

def gradio_auth(username, password):
    print("Authenticate user")
    if not username.strip():
        gr.Warning("Username cannot be empty.", duration=3)
    if not password.strip():
        gr.Warning("Password cannot be empty.", duration=3)

    # Wrap the authentication logic for Gradio
    success, user_id = authenticate_or_register_user(username, password)
    if success:
        session_user_id.value = str(user_id)
        print(f"User id: {session_user_id.value}")
        return True  # Gradio expects only a boolean here for login validation
    else:
        return False

def get_first_key_value(json):
    if json and isinstance(json, dict):
        # Get the value of the first key in the dictionary
        first_key = next(iter(json))
        return first_key, json[first_key]
    else:
        return "Chat 1", [{"role": "assistant", "content": "Hi! How can I help you?"}]

def initialize_chat_interface():
    print("Init the web")
    user_id = session_user_id
    chat_history = get_chat_history(user_id.value)
    chat_rooms_ids = list(chat_history.keys())
    if len(chat_rooms_ids) == 0:
        chat_rooms_ids = ["Chat 1"]
    chat_metrics = get_chat_scores(user_id.value)

    # Set states
    chat_room_state.value = chat_rooms_ids
    chat_history_states.value = chat_history
    chat_metrics_state.value = chat_metrics
    #TODO: Enhance state of selected radio button
    first_key, first_key_chat = get_first_key_value(chat_history)
    first_key_chat_metrics = next((
        chat_metric["metrics"]
        for chat_metric in chat_metrics
        if chat_metric["chat_room_id"] == first_key), None)

    if first_key_chat_metrics is None:
        relevancy_score = 0
        relevancy_reason = "Evaluating..."
        completeness_score = 0
        completeness_reason = "Evaluating..."
        role_adherence_score = 0
        role_adherence_reason = "Evaluating..."
    else:
        # Extract relevant values from first_key_chat_metrics with safe access
        relevancy_score = first_key_chat_metrics.get("relevancy_metric_score", 0)
        relevancy_reason = first_key_chat_metrics.get("relevancy_metric_reason", "Evaluating...")
        completeness_score = first_key_chat_metrics.get("completeness_metric_score", 0)
        completeness_reason = first_key_chat_metrics.get("completeness_metric_reason", "Evaluating...")
        role_adherence_score = first_key_chat_metrics.get("role_adherence_metric_score", 0)
        role_adherence_reason = first_key_chat_metrics.get("role_adherence_metric_reason", "Evaluating...")

    # Return the desired values
    return (
        user_id,  # User ID or first key identifier
        gr.update(choices=chat_rooms_ids, value=chat_rooms_ids[0] if chat_rooms_ids else None),
        first_key_chat,  # The full chat
        relevancy_score,  # Relevancy metric score
        relevancy_reason,  # Relevancy metric reason
        completeness_score,  # Completeness metric score
        completeness_reason,  # Completeness metric reason
        role_adherence_score,  # Knowledge retention metric score
        role_adherence_reason  # Knowledge retention metric reason
    )

# Function to add a new chat section
def add_new_section(sections):
    new_section_name = f"Chat {len(sections) + 1}"
    sections.append(new_section_name)
    print(f"Added sections: {sections}")
    return (gr.update(choices=sections, value=new_section_name),
            gr.update(value=[{"role": "assistant", "content": "Hi! How can I help you?"}]))

# Function to delete a chat section
def delete_section(selected_section, sections, chat_history_states):
    if selected_section == "Chat 1":
        gr.Info("Cannot delete the default section.", duration=3)
        return gr.update(choices=sections, value="Chat 1"), sections, chat_history_states

    # Safely attempt to delete the chat room in the database
    try:
        delete_chat_room(session_user_id.value, selected_section)  # External function to handle database deletion
    except Exception as e:
        if selected_section in sections:
            sections.remove(selected_section)
        return (
            gr.update(choices=sections, value=sections[0]),  # Keep the selection unchanged
            sections,
            chat_history_states)

    # Remove the section from the UI list
    if selected_section in sections:
        sections.remove(selected_section)

    # Remove the corresponding key from the JSON chat history
    if selected_section in chat_history_states.keys():
        del chat_history_states[selected_section]

    new_selection = sections[0] if sections else "Chat 1"
    return gr.update(choices=sections,
                     value=new_selection), sections, chat_history_states

# Function to handle switching between chat sections
def switch_section(selected_section, chat_history_states):
    # Initialize chat states dictionary if not already done
    if chat_history_states is None:
        chat_history_states = {}

        # Validate or convert selected_section
    if isinstance(selected_section, list):
        selected_section = selected_section[0]

    chat_metrics = chat_metrics_state.value
    first_key_chat_metrics = next((
        chat_metric["metrics"]
        for chat_metric in chat_metrics
        if chat_metric["chat_room_id"] == selected_section), None)

    if first_key_chat_metrics is None:
        relevancy_score = 0
        relevancy_reason = "Evaluating..."
        completeness_score = 0
        completeness_reason = "Evaluating..."
        role_adherence_score = 0
        role_adherence_reason = "Evaluating..."
    else:
        # Extract relevant values from first_key_chat_metrics with safe access
        relevancy_score = first_key_chat_metrics.get("relevancy_metric_score", 0)
        relevancy_reason = first_key_chat_metrics.get("relevancy_metric_reason", "Evaluating...")
        completeness_score = first_key_chat_metrics.get("completeness_metric_score", 0)
        completeness_reason = first_key_chat_metrics.get("completeness_metric_reason", "Evaluating...")
        role_adherence_score = first_key_chat_metrics.get("role_adherence_metric_score", 0)
        role_adherence_reason = first_key_chat_metrics.get("role_adherence_metric_reason", "Evaluating...")

    # Check if the selected section exists, initialize if necessary
    if selected_section not in chat_history_states.keys():
        default_conversation = [{"role": "assistant", "content": "Welcome to the new conversation!"}]
        chat_history_states[selected_section] = default_conversation

    # Retrieve the chat history for the selected section
    current_conversation = chat_history_states[selected_section]

    return [
        current_conversation,
        relevancy_score,
        relevancy_reason,
        completeness_score,
        completeness_reason,
        role_adherence_score,
        role_adherence_reason
    ]

def send_message_and_handle_chat_history(session_user_id, chat_room_id, message, history):
    if not message.strip():
        return None, history, chat_history_states.value

    chat_history = send_message(session_user_id, chat_room_id, message, history)

    # Handle chat history state
    cur_chat_history_state = chat_history_states.value
    cur_chat_history_state[chat_room_id] = chat_history
    chat_history_states.value = cur_chat_history_state
    return None, chat_history, chat_history_states.value

# Build the app
with gr.Blocks(css=custom_css) as app:
    app.title = "UMMC Chatbot"

    session_user_id = gr.State(value=None)
    chat_room_state = gr.State(value=["Chat 1"])  # Initial sections
    chat_history_states = gr.State(value=[{"role": "assistant", "content": "Hi! How can I help you?"}])  # Chat histories for all sections
    chat_metrics_state = gr.State(value=[])

    # Title
    gr.Markdown("## UMMC Patient Enquiry Chatbot")

    with gr.Row():
        # Sidebar
        with gr.Column(scale=2):
            sections_radio = gr.Radio(label="Chat Rooms", choices=["Chat 1"], value="Chat 1")
            add_section_btn = gr.Button("Add New Chat")
            delete_section_btn = gr.Button("Delete Selected Chat")

            feedback = gr.Textbox(
                label="Feedback",
                placeholder="Give us feedback",
                interactive=True, lines=1)
            feedback.submit(
                send_feedback,
                inputs = [session_user_id, feedback],
                outputs=[feedback])

        # Main Chat Interface
        with gr.Column(scale=5):
            chatbot = gr.Chatbot(
                value=[{"role": "assistant", "content": "Hi! How can I help you?"}],
                type="messages",
                elem_id="chatbot")
            msg = gr.Textbox(show_label=False, placeholder="Type a message and press enter...")
            msg.submit(
                send_message_and_handle_chat_history,
                [session_user_id, sections_radio, msg, chatbot],
                [msg, chatbot, chat_history_states])

    # Metric score
    with gr.Row():
        with gr.Column():
            relevancy_metric = gr.Textbox(label="Conversation Relevancy Metric", interactive=False)
            relevancy_metric_reason = gr.Textbox(label="Reason", interactive=False)
        with gr.Column():
            completeness_metric = gr.Textbox(label="Conversation Completeness Metric", interactive=False)
            completeness_metric_reason = gr.Textbox(label="Reason", interactive=False)
        with gr.Column():
            role_adherence_metric = gr.Textbox(label="Role adherence Metric", interactive=False)
            role_adherence_metric_reason = gr.Textbox(label="Reason", interactive=False)

    # Load event to fetch chat history dynamically
    app.load(
        initialize_chat_interface,
        inputs=None,  # No inputs required
        outputs=[
            session_user_id,
            sections_radio,
            chatbot,
            relevancy_metric,
            relevancy_metric_reason,
            completeness_metric,
            completeness_metric_reason,
            role_adherence_metric,
            role_adherence_metric_reason
        ]
    )

    # Add a new chat section
    add_section_btn.click(
        add_new_section,
        inputs=[chat_room_state],
        outputs=[sections_radio, chatbot],
    )

    # Delete a chat section
    delete_section_btn.click(
        delete_section,
        inputs=[sections_radio, chat_room_state, chat_history_states],
        outputs=[sections_radio, chat_room_state, chat_history_states],
    )

    # Switch between sections
    sections_radio.change(
        switch_section,
        inputs=[sections_radio, chat_history_states],
        outputs=[
            chatbot,
            relevancy_metric,
            relevancy_metric_reason,
            completeness_metric,
            completeness_metric_reason,
            role_adherence_metric,
            role_adherence_metric_reason
        ],
    )

# Launch the app
# app.launch(auth=gradio_auth)
app.launch(share=True, auth=gradio_auth)
# app.launch()