import os
import streamlit as st

from streamlit_float import float_css_helper
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime, timedelta
import pytz
from prompts import *
from recorder import record_audio, transcribe_audio
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow
import json
import oauthlib.oauth2.rfc6749.errors

st.set_page_config(page_title="OP", page_icon="🤖", initial_sidebar_state="collapsed")

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
        "chat_history": [],
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

def display_header():
    
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

        with st.chat_message("user", avatar=user_avatar_url):
            st.markdown(user_question)
        
        with st.chat_message("AI", avatar=specialist_avatar):
            ai_response = get_response(user_question)
            assistant_response = ai_response
        
        st.session_state.chat_history.append(AIMessage(assistant_response, avatar=st.session_state.specialist_avatar))
    
    if user_recording is not None and user_recording != "":
        st.session_state.chat_history.append(HumanMessage(user_recording, avatar=user_avatar_url))

        with st.chat_message("user", avatar=user_avatar_url):
            st.markdown(user_recording)
        
        with st.chat_message("AI", avatar=specialist_avatar):
            ai_response = get_response(user_recording)
            assistant_response = ai_response
        
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
        
        tab1, tab2, = st.tabs(["Functions", "Specialists"])
        
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

# Google Calendar API

def setup_google_calendar():
    client_secret_json = os.getenv("CLIENT_SECRET_JSON")
    
    if not client_secret_json:
        st.warning("Google Calendar integration is not set up. CLIENT_SECRET_JSON is missing in .env file.")
        return None

    try:
        client_config = json.loads(client_secret_json)
    except json.JSONDecodeError:
        st.error("Invalid CLIENT_SECRET_JSON format in .env file.")
        return None

    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri="http://localhost:8501/"
    )
    
    if 'code' not in st.query_params:
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.markdown(f"[Click here to authorize]({auth_url})")
        return None
    
    try:
        flow.fetch_token(code=st.query_params['code'])
        st.session_state.calendar_credentials = flow.credentials
        return build('calendar', 'v3', credentials=flow.credentials)
    except oauthlib.oauth2.rfc6749.errors.InvalidGrantError:
        st.error("Invalid or expired authorization code. Please try authenticating again.")
        # Clear the query parameters to allow re-authentication
        st.experimental_set_query_params()
        return None

# In your main function:
if 'calendar_credentials' not in st.session_state:
    calendar_service = setup_google_calendar()
    if calendar_service:
        st.success("Successfully authenticated with Google Calendar!")
        st.rerun()
elif 'calendar_credentials' in st.session_state:
    calendar_service = build('calendar', 'v3', credentials=st.session_state.calendar_credentials)
else:
    st.warning("Google Calendar is not authenticated. Please complete the authentication process.")

# In your main function:
if 'calendar_credentials' not in st.session_state:
    calendar_service = setup_google_calendar()
    if calendar_service:
        st.success("Successfully authenticated with Google Calendar!")
        st.rerun()
else:
    calendar_service = build('calendar', 'v3', credentials=st.session_state.calendar_credentials)

def create_appointment(service, summary, description, start_time, end_time):
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': end_time.isoformat(),
            'timeZone': 'America/Los_Angeles',
        },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    st.success(f"Event created: {event.get('htmlLink')}")

# Modify your main function to include Google Calendar setup
def main():
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    
    initialize_session_state()
    display_header()
    display_chat_history()
    user_input()
    display_sidebar()
    print(st.session_state.thread_id)

    # Set up Google Calendar
    if 'calendar_credentials' not in st.session_state:
        calendar_service = setup_google_calendar()
        if calendar_service:
            st.success("Successfully authenticated with Google Calendar!")
            st.rerun()
    else:
        calendar_service = build('calendar', 'v3', credentials=st.session_state.calendar_credentials)

    # Example of creating an appointment (you can trigger this based on user input)
    if calendar_service and st.button("Create Test Appointment"):
        create_appointment(
            calendar_service,
            "Test Appointment",
            "This is a test appointment created by the app",
            datetime.now(),
            datetime.now() + timedelta(hours=1)
        )
    elif not calendar_service:
        st.warning("Google Calendar integration is not available.")



if __name__ == '__main__':
    main()