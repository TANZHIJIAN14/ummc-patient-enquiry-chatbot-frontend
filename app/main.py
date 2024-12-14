import gradio as gr
from tomlkit import value

from chatbot import send_message, get_chat_history
from auth import authenticate_or_register_user

def gradio_auth(username, password):
    print("Authenticate user")
    # Wrap the authentication logic for Gradio
    success, user_id = authenticate_or_register_user(username, password)
    if success:
        session_user_id.value = str(user_id)
        chat_states.value = get_chat_history(session_user_id.value, "room_2")
        print(f"User id: {session_user_id.value}")
        return True  # Gradio expects only a boolean here for login validation
    else:
        return False

def initialize_chat_interface():
    print("Init the web")
    user_id = session_user_id
    chat_history = get_chat_history(user_id.value, "room_2")
    return user_id, chat_history

# Function to add a new chat section
def add_new_section(sections, chat_states):
    new_section_name = f"Chat {len(sections) + 1}"
    sections.append(new_section_name)
    chat_states[new_section_name] = []  # Initialize chat history for the new section
    return gr.update(choices=sections, value=new_section_name), sections, chat_states

# Function to delete a chat section
def delete_section(selected_section, sections, chat_states):
    if selected_section == "Chat 1":
        return gr.update(choices=sections, value="Chat 1"), sections, chat_states, "Cannot delete the default section."

    sections.remove(selected_section)
    chat_states.pop(selected_section, None)

    new_selection = sections[0] if sections else "Chat 1"
    return gr.update(choices=sections,
                     value=new_selection), sections, chat_states, f"Deleted section: {selected_section}"

# Function to handle switching between chat sections
def switch_section(selected_section, chat_states):
    if selected_section not in chat_states:
        chat_states[selected_section] = []  # Ensure the selected section has a history
    # Reset to a new conversation
    new_conversation = [("Bot", "Welcome to the new conversation!")]
    chat_states[selected_section] = new_conversation
    return new_conversation

# Build the app
with gr.Blocks(fill_height=True) as app:
    session_user_id = gr.State(value=None)
    sections_state = gr.State(["Chat 1"])  # Initial sections
    chat_states = gr.State(value=None)  # Chat histories for all sections

    # Title
    gr.Markdown("## UMMC Patient Enquiry Chatbot")

    with gr.Row(equal_height=True):
        # Sidebar
        with gr.Column(scale=1, min_width=200):
            sections_radio = gr.Radio(label="Chat Rooms", choices=["Chat 1"], value="Chat 1")
            add_section_btn = gr.Button("Add New Section")
            delete_section_btn = gr.Button("Delete Selected Section")

        # Main Chat Interface
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                value=chat_states.value,
                type="messages",
                elem_id="chatbot")
            msg = gr.Textbox(show_label=False, placeholder="Type a message and press enter...")
            msg.submit(
                send_message,
                [session_user_id, msg, chatbot],
                [msg, chatbot])

        # Feedback display for deletion
        feedback = gr.Textbox(label="Feedback", interactive=True, lines=1)

    # Load event to fetch chat history dynamically
    app.load(
        initialize_chat_interface,
        inputs=None,  # No inputs required
        outputs=[session_user_id, chatbot],  # Set user ID and populate chat history
    )

    # Add a new chat section
    add_section_btn.click(
        add_new_section,
        inputs=[sections_state, chat_states],
        outputs=[sections_radio, sections_state, chat_states],
    )

    # Delete a chat section
    delete_section_btn.click(
        delete_section,
        inputs=[sections_radio, sections_state, chat_states],
        outputs=[sections_radio, sections_state, chat_states, feedback],
    )

    # Switch between sections
    sections_radio.change(
        switch_section,
        inputs=[sections_radio, chat_states],
        outputs=chatbot,
    )

# Launch the app
app.launch(share=True, auth=gradio_auth)
# app.launch()