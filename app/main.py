from cProfile import label

import gradio as gr

from css import custom_css
from db import send_feedback
from chatbot import send_message, get_chat_history, delete_chat_room
from auth import authenticate_or_register_user

def get_first_key_value(json):
    if json and isinstance(json, dict):
        # Get the value of the first key in the dictionary
        return json[next(iter(json))]
    else:
        return [{"role": "assistant", "content": "Hi! How can I help you?"}]  # Handle this case appropriately

def gradio_auth(username, password):
    print("Authenticate user")
    # Wrap the authentication logic for Gradio
    success, user_id = authenticate_or_register_user(username, password)
    if success:
        session_user_id.value = str(user_id)
        print(f"User id: {session_user_id.value}")
        return True  # Gradio expects only a boolean here for login validation
    else:
        return False

def initialize_chat_interface():
    print("Init the web")
    user_id = session_user_id
    chat_history = get_chat_history(user_id.value)
    chat_rooms_ids = list(chat_history.keys())
    if len(chat_rooms_ids) == 0:
        chat_rooms_ids = ["Chat 1"]

    # Set states
    chat_room_state.value = chat_rooms_ids
    chat_history_states.value = chat_history
    return user_id, gr.update(choices=chat_rooms_ids, value=chat_rooms_ids[0]), get_first_key_value(chat_history)

# Function to add a new chat section
def add_new_section(sections):
    new_section_name = f"Chat {len(sections) + 1}"
    sections.append(new_section_name)
    return (gr.update(choices=sections, value=new_section_name),
            gr.update(value=[{"role": "assistant", "content": "Hi! How can I help you?"}]))

# Function to delete a chat section
def delete_section(selected_section, sections, chat_history_states):
    if selected_section == "Chat 1":
        return gr.update(choices=sections, value="Chat 1"), sections, chat_history_states, "Cannot delete the default section."

    # Safely attempt to delete the chat room in the database
    try:
        delete_chat_room(session_user_id.value, selected_section)  # External function to handle database deletion
    except Exception as e:
        return (
            gr.update(choices=sections, value=selected_section),  # Keep the selection unchanged
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

    # Check if the selected section exists, initialize if necessary
    if selected_section not in chat_history_states.keys():
        default_conversation = [{"role": "assistant", "content": "Welcome to the new conversation!"}]
        chat_history_states[selected_section] = default_conversation

    # Retrieve the chat history for the selected section
    current_conversation = chat_history_states[selected_section]

    return current_conversation

# Build the app
with gr.Blocks(css=custom_css) as app:
    session_user_id = gr.State(value=None)
    chat_room_state = gr.State(value=["Chat 1"])  # Initial sections
    chat_history_states = gr.State(value=[{"role": "assistant", "content": "Hi! How can I help you?"}])  # Chat histories for all sections

    # Title
    gr.Markdown("## UMMC Patient Enquiry Chatbot")

    with gr.Row():
        # Sidebar
        with gr.Column(scale=2, min_width=200):
            sections_radio = gr.Radio(label="Chat Rooms", choices=["Chat 1"], value="Chat 1")
            add_section_btn = gr.Button("Add New Section")
            delete_section_btn = gr.Button("Delete Selected Section")

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
                send_message,
                [session_user_id, sections_radio, msg, chatbot],
                [msg, chatbot])

    # Load event to fetch chat history dynamically
    app.load(
        initialize_chat_interface,
        inputs=None,  # No inputs required
        outputs=[session_user_id, sections_radio, chatbot],  # Set user ID and populate chat history
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
        outputs=chatbot,
    )

# Launch the app
app.launch(auth=gradio_auth)
# app.launch(share=True, auth=gradio_auth)
# app.launch()