import os
import streamlit as st
from streamlit_float import float_css_helper
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime
import pytz
from prompts import *
from recorder import record_audio, transcribe_audio
import sqlite3

# Initialize database connection
conn = sqlite3.connect('chat_history.db')
cursor = conn.cursor()

def init_db():
    conn = sqlite3.connect('chat_history.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

# Save chat message to database
def save_message_to_db(role, content):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_history (role, content)
        VALUES (?, ?)
    ''', (role, content))
    conn.commit()
    conn.close()

# Load chat history from database
def load_chat_history_from_db():
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('SELECT role, content, timestamp FROM chat_history ORDER BY timestamp')
    rows = cursor.fetchall()
    conn.close()
    return rows

# Delete chat message from database
def delete_message(timestamp):
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE timestamp = ?', (timestamp,))
    conn.commit()
    conn.close()

# Function to display chat history in the sidebar
def display_chat_history_sidebar():
    st.title("Chat History")
    specialist_avatar_url = specialist_id_caption[st.session_state.specialist]["avatar"]
    chat_history = load_chat_history_from_db()
    
    # Group messages by date
    grouped_history = {}
    for role, content, timestamp in chat_history:
        date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').date()
        if date not in grouped_history:
            grouped_history[date] = []
        grouped_history[date].append((role, content, timestamp))
    

    for date, messages in grouped_history.items():
        with st.expander(f"Chat on {date}"):
            for role, content, timestamp in messages:
                col1, col2, col3 = st.columns([1, 5, 1])
                
                with col1:
                    if role == "User":
                        st.image(user_avatar_url, width=20)
                    else:
                        st.image(specialist_id_caption[st.session_state.specialist]["avatar"], width=20)
                
                with col2:
                    st.write(f"{content}")
                
                with col3:
                    if st.button("🗑️", key=f"delete_{date}_{timestamp}"):
                        delete_message(timestamp)
                        st.rerun()

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("API Key not found! Please check your environment variables.")

client = OpenAI(api_key=api_key)

# Avatar URLs
user_avatar_url = "https://api.dicebear.com/8.x/pixel-art/svg?seed=Jasmine&beardProbability=0&clothing=variant01&clothingColor=ffd969&eyesColor=876658&glassesColor=191919,323232&hair=short04&hairColor=28150a&skinColor=b68655"

specialist_id_caption = {
  "Optimus Prime": {
    "assistant_id": "asst_IdOC7jNX9BdemhoOZqd0kmZ7",
    "caption": "role is multifaceted, encompassing elements of an assistant, AI journal, therapist, friend, and counselor.",
    "avatar": "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/0bd3c9c5-6f0d-4014-8eff-39e44d46eabb/depcapq-fb1672b3-f968-4be8-9943-d5284cdb2750.png/v1/fill/w_827,h_966/optimus_prime_head_by_drawinrook_depcapq-pre.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTQ5NSIsInBhdGgiOiJcL2ZcLzBiZDNjOWM1LTZmMGQtNDAxNC04ZWZmLTM5ZTQ0ZDQ2ZWFiYlwvZGVwY2FwcS1mYjE2NzJiMy1mOTY4LTRiZTgtOTk0My1kNTI4NGNkYjI3NTAucG5nIiwid2lkdGgiOiI8PTEyODAifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.dxxbGEB0k4WlyPz7uP3FBGwwdc7_t7HiyRXdEjRnChY"
  },
  "Mindfulness Teacher": {
    "assistant_id": "asst_ayrz6o4WCrbWF9Q0GrXUP0HJ",
    "caption": "Goes Deep",
    "avatar": "https://cdn.pixabay.com/photo/2013/07/12/19/30/enlightenment-154910_1280.png"
  },
  "Universal DDX Explorer": {
    "assistant_id": "asst_CFjyIpJwzSpIi1iQmtjduHtU",
    "caption": "Decision helper by clarifying multple outcomes",
    "avatar": "https://cdn.pixabay.com/photo/2013/07/12/19/30/enlightenment-154910_1280.png"
  },
  "Elon Musk": {
    "assistant_id": "asst_lNTHaP8rGWzTejWBKOmwB7EI",
    "caption": "1st principled innovator",
    "avatar": "https://media.craiyon.com/2023-06-14/cdc2eb7a87194630ac86b7c55d9d2760.webp"
  },
  "Richard Feynman": {
    "assistant_id": "asst_AdkSl7KnQVXyFllXIrA2yyt9",
    "caption": "1st principled innovator",
    "avatar": "https://images.nightcafe.studio/jobs/SMNkg4u4AR44tWZS9keI/SMNkg4u4AR44tWZS9keI--1--d1ryp.jpg?tr=w-1600,c-at_max"
  }
  
}

def initialize_session_state():
    primary_specialist = list(specialist_id_caption.keys())[0]
    primary_specialist_id = specialist_id_caption[primary_specialist]["assistant_id"]
    primary_specialist_avatar = specialist_id_caption[primary_specialist]["avatar"]
    state_keys_defaults = {
        "user_question": "",
        "json_data": {},
        "critical_actions": {},
        "sidebar_state": 1,
        "assistant_response": "",
        "specialist_input": "",
        "specialist": primary_specialist,
        "assistant_id": primary_specialist_id,
        "specialist_avatar": primary_specialist_avatar,
        "should_rerun": False        
    }
    for key, default in state_keys_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

def display_header():
    st.set_page_config(page_title="OP", page_icon="🤖", initial_sidebar_state="collapsed")
    specialist = st.session_state.specialist
    specialist_avatar = specialist_id_caption[st.session_state.specialist]["avatar"]
    st.markdown(
            f"""
            <div style="text-align: center;">
                <h1>
                    <img src="{specialist_avatar}" alt="Avatar" style="width:60px;height:60px;border-radius:50%;">
                    {specialist}
                </h1>
            </div>
            """, 
            unsafe_allow_html=True
        )

def generate_response_stream(stream):
    for response in stream:
        if response.event == 'thread.message.delta':
            for delta in response.data.delta.content:
                if delta.type == 'text':
                    yield delta.text.value


def get_response(user_question):
    try:
        client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=user_question)

        response_placeholder = st.empty()  # Placeholder for streaming response text
        response_text = ""  # To accumulate response text

        # Stream response from the assistant
        with client.beta.threads.runs.stream(thread_id=st.session_state.thread_id, assistant_id=st.session_state.assistant_id) as stream:
            for chunk in stream:
                if chunk.event == 'thread.message.delta':  # Check if it is the delta message
                    for delta in chunk.data.delta.content:
                        if delta.type == 'text':
                            response_text += delta.text.value  # Append new text fragment to response text
                            response_placeholder.markdown(response_text)  # Update the placeholder with new response text as markdown

        return response_text
    except Exception as e:
        print(f"DEBUG: API Error - {str(e)}")
        st.error("Oops! Something went wrong with the AI. Please try again.")
    

def display_chat_history():    
    for message in st.session_state.chat_history:
        if isinstance(message, HumanMessage):
            avatar_url = message.avatar
            with st.chat_message("user", avatar=user_avatar_url):                
                st.markdown(message.content, unsafe_allow_html=True)
        else:
            avatar_url = message.avatar
            with st.chat_message("AI", avatar=avatar_url):
                st.markdown(message.content, unsafe_allow_html=True)


def user_input():
    
    specialist_avatar = specialist_id_caption[st.session_state.specialist]["avatar"]
    specialist_name = st.session_state.specialist
    print(f"DEBUG: Specialist: {specialist_name}")
    input_container = st.container()
    input_container.float(float_css_helper(bottom="50px"))
    with input_container:
        col1, col2 = st.columns([4, 1])  # Adjust column widths for better appearance
        with col1:
            user_question = st.chat_input("How may I help you?")
        with col2:
            user_recording = record_audio()
            submit_button = st.button("Upload History")
        if submit_button:
            upload_history()
            
    if user_question is not None and user_question != "":

        st.session_state.chat_history.append(HumanMessage(user_question, avatar=user_avatar_url))
        save_message_to_db("User", user_question)

        with st.chat_message("user", avatar=user_avatar_url):
            st.markdown(user_question)
        
        with st.chat_message("AI", avatar=specialist_avatar):
            ai_response = get_response(user_question)
            assistant_response = ai_response
            save_message_to_db(specialist_name, assistant_response)
        
        st.session_state.chat_history.append(AIMessage(assistant_response, avatar=st.session_state.specialist_avatar))
    
    if user_recording is not None and user_recording != "":
        st.session_state.chat_history.append(HumanMessage(user_recording, avatar=user_avatar_url))
        save_message_to_db("User", user_recording)

        with st.chat_message("user", avatar=user_avatar_url):
            st.markdown(user_recording)
        
        with st.chat_message("AI", avatar=specialist_avatar):
            ai_response = get_response(user_recording)
            assistant_response = ai_response
            save_message_to_db("AI", assistant_response)
        
        st.session_state.chat_history.append(AIMessage(assistant_response, avatar=st.session_state.specialist_avatar))


def upload_history():
    chat = ''
    for index, message in enumerate(st.session_state.chat_history, start=1):
        if isinstance(message, dict) and 'content' in message:
            content = message['content']
        elif hasattr(message, 'content'):
            content = message.content
        else:
            content = str(message)
        
        prefix = 'User: ' if index % 2 != 0 else 'Assistant: '
        chat += f"{prefix}{content}\n"

    print(f"DEBUG chat_history:\n{chat}")
    #thread = client.beta.threads.retrieve(st.session_state.thread_id)
    # extract chat_history from thread
    all_messages = []
    limit = 100  # Maximum allowed limit per request 
    after = None

    while True:
        response = client.beta.threads.messages.list(thread_id=st.session_state.thread_id, limit=limit, after=after)
        messages = response.data
        if not messages:
            break
        all_messages.extend(messages)
        after = messages[-1].id      # Set the 'after' cursor to the ID of the last message
    # Reverse the messages to chronological order
    all_messages.reverse()
    # save to a list of dictionary
    extracted_messages = []
    for message in all_messages:
        # Initialize a dictionary for each message
        message_dict = {
            'role': message.role,
            'text': ''
        }

        message_content = message.content
        if isinstance(message_content, list):
            text_parts = [block.text.value for block in message_content if hasattr(block, 'text')]
            text = ' '.join(text_parts)
            message_dict['text'] = text
        
        extracted_messages.append(message_dict)
        # Now `extracted_messages` is a list of dictionaries containing the role and text of each message.
    # Convert the list of dictionaries to a plain text format
    plain_text = ""
    for msg in extracted_messages:
        plain_text += f"{msg['role']}: {msg['text']}\n"

    # Summarize chat history (plain_text)  
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": summary_prompt + chat,
            }
        ],
        model="gpt-3.5-turbo",
        temperature=0.5
    )
    summary = response.choices[0].message.content

    
    # print chat summary
    print("\nSummary compression:")
    print(summary)
    print(f'Size decrease: {(len(summary))/(len(plain_text))}')
    # update Global instructions of assistant with timestamp
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # extract assistant instructions
    assistant_info=client.beta.assistants.retrieve(assistant_id=st.session_state.assistant_id)
    assistant_instructions = assistant_info.instructions
    # upload new assistant instructions
    new_instructions = assistant_instructions + '\n' + current_time + '\n' + summary
    client.beta.assistants.update(assistant_id=st.session_state.assistant_id,instructions=new_instructions)

def display_sidebar():
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h2>                   
                    <img src="https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/0bd3c9c5-6f0d-4014-8eff-39e44d46eabb/depcapq-fb1672b3-f968-4be8-9943-d5284cdb2750.png/v1/fill/w_827,h_966/optimus_prime_head_by_drawinrook_depcapq-pre.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7ImhlaWdodCI6Ijw9MTQ5NSIsInBhdGgiOiJcL2ZcLzBiZDNjOWM1LTZmMGQtNDAxNC04ZWZmLTM5ZTQ0ZDQ2ZWFiYlwvZGVwY2FwcS1mYjE2NzJiMy1mOTY4LTRiZTgtOTk0My1kNTI4NGNkYjI3NTAucG5nIiwid2lkdGgiOiI8PTEyODAifV1dLCJhdWQiOlsidXJuOnNlcnZpY2U6aW1hZ2Uub3BlcmF0aW9ucyJdfQ.dxxbGEB0k4WlyPz7uP3FBGwwdc7_t7HiyRXdEjRnChY" alt="Avatar" style="width:80px;height:80px;border-radius:20%;"> 
                </h2>
            </div>
            """, 
            unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Functions", "Specialists", "Chat History"])
        
        with tab1:
            display_functions_tab()

        with tab2:
            
            choose_specialist_radio()
            
            st.subheader(':orange[Consult Recommnedations]')
            button1 = st.button("General Reccommendations")
            button2 = st.button("Diagnosis")
            button3 = st.button("Treatment Plan")
            button4 = st.button("Disposition Plan")
            


            # Ensure choose_specialist_radio is called here with a unique key
        with tab3:
            display_chat_history_sidebar()
        #container = st.container()
        #container.float(float_css_helper(bottom="10px"))
        #with container:
            #authenticate_user()

# Sidebar tabs and functions
def display_functions_tab():
    
    st.subheader('Process Management')
    col1, col2 = st.columns(2)
    with col1:
        button1 = st.button("button 1")
    with col2:
        button2 = st.button("button 2")

    # Process button actions
    process_buttons(button1, button2)

# Process the buttons
def process_buttons(button1, button2):
    if button1:
        specialist = "Optimus Prime"
        prompt = "test 1"
        st.session_state["specialist"] = specialist
        button_input(specialist, prompt)
    if button2:
        specialist = "Optimus Prime"
        prompt = "test 2"
        st.session_state["specialist"] = specialist
        button_input(specialist, prompt)
    
# process button inputs for quick bot responses
def button_input(specialist, prompt):
    st.session_state.button_clicked = True
    #call the specialist
    st.session_state.assistant_id = specialist_id_caption[specialist]["assistant_id"]
 
    # set st.sesssion_state.user_question_sidebar for process_other_queries() 
    user_question = prompt
    if user_question is not None and user_question != "":
        st.session_state.specialist = specialist
        specialist_avatar = specialist_id_caption[st.session_state.specialist]["avatar"]
        st.session_state.specialist_avatar = specialist_avatar
        timezone = pytz.timezone("America/Los_Angeles")
        current_datetime = datetime.now(timezone).strftime("%H:%M:%S")
        st.session_state.user_question_sidebar = user_question
        #refresh page
        st.rerun()
    st.session_state.button_clicked = False

# Choosing the specialty group
def choose_specialist_radio():
    specialities = list(specialist_id_caption.keys())
    captions = [specialist_id_caption[speciality]["caption"] for speciality in specialities]

    if 'specialist' in st.session_state:
        selected_specialist = st.session_state.specialist
    else:
        selected_specialist = specialities[0]

    # Assign a unique key to the st.radio widget
    specialist = st.radio("**:red[Choose Your Specialty Group]**", specialities, 
                          captions=captions, 
                          index=specialities.index(selected_specialist),
                          key="choose_specialist_radio")

    if 'button_clicked' not in st.session_state:
        st.session_state.button_clicked = False

    # Only update if the selected specialist is different
    if specialist and specialist != st.session_state.specialist:
    #if specialist and specialist != st.session_state.specialist and not st.session_state.button_clicked:
        print(f'DEBUG: Radio button changed specialist to {specialist}')
        st.session_state.specialist = specialist
        st.session_state.assistant_id = specialist_id_caption[specialist]["assistant_id"]
        st.session_state.specialist_avatar = specialist_id_caption[specialist]["avatar"]
        # No need to call st.rerun() here
        st.rerun()

def main():
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
        
    initialize_session_state()
    display_header()
    

    display_sidebar()
    display_chat_history()
    user_input()
    # display_chat_history_sidebar()
    
    print(st.session_state.thread_id)

if __name__ == '__main__':
    main()