import streamlit as st
from streamlit_float import float_css_helper
from openai import OpenAI
import os
from dotenv import load_dotenv
from prompts import *
from utils import *
from langchain_core.messages import HumanMessage, AIMessage


# Load variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("API Key not found! Please check your environment variables.")
client = OpenAI(api_key=api_key)

# Define the avatar URLs
user_avatar_url = "https://cdn.pixabay.com/photo/2016/12/21/07/36/profession-1922360_1280.png"

specialist_id_caption = {
  "Sunny's Assistant": {
    "assistant_id": "asst_IdOC7jNX9BdemhoOZqd0kmZ7",
    "caption": "role is multifaceted, encompassing elements of an assistant, AI journal, therapist, friend, and counselor.",
    "avatar": "https://cdn.pixabay.com/photo/2017/03/31/23/11/robot-2192617_1280.png"
  },
  "Mindfulness Teacher": {
    "assistant_id": "asst_bnFm27eqedaYK9Ulekh8Yjd9",
    "caption": "Goes Deep",
    "avatar": "https://cdn.pixabay.com/photo/2013/07/12/19/30/enlightenment-154910_1280.png"
  }
}

# Initialize session_state variables
def initialize_session_state():
    primary_specialist = list(specialist_id_caption.keys())[0]
    primary_specialist_id = specialist_id_caption[primary_specialist]["assistant_id"]
    state_keys_defaults = {
        "chat_history": [],
        "user_question": "",
        "json_data": {},
        "critical_actions": {},
        "sidebar_state": 1,
        "assistant_response": "",
        "specialist_input": "",
        "specialist": primary_specialist,
        "assistant_id": primary_specialist_id,  # Initialize 'assistant_id' here
        "should_rerun": False
    }
    for key, default in state_keys_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

# Setup the main page display and header
def display_header():
    st.set_page_config(page_title="DA", page_icon="🫡")
    st.header("Optimus Prime 🤖")

# User input container
def handle_user_input_container():
    input_container = st.container()
    input_container.float(float_css_helper(bottom="50px"))
    with input_container:
        specialist = st.session_state.specialist
        #obtain specialist avatar
        specialist_avatar = specialist_id_caption[st.session_state.specialist]["avatar"]
         # Replace with your avatar URL
        st.markdown(
            f"""
            <div style="text-align: center;">
                <h6>
                    <img src="{specialist_avatar}" alt="Avatar" style="width:30px;height:30px;border-radius:50%;">
                    <span style="color:teal;">{specialist}</span>
                </h6>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        user_question = st.chat_input("How may I help you?", key="widget2")
        if user_question:
            handle_userinput(user_question)

# Chat history display
def display_chat_history():
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            avatar_url = message.get("avatar", user_avatar_url)
            with st.chat_message(message["role"], avatar=avatar_url):
                st.markdown(message["content"], unsafe_allow_html=True)


# Processing queries
def process_queries():
    if st.session_state["user_question"]:
        handle_userinput(st.session_state["user_question"])


# Create a thread where the conversation will happen and keep Streamlit from initiating a new session state
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# Create new thread
def new_thread():
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.chat_history = []
    st.rerun()

# Function to generate the response stream
def generate_response_stream(stream):
    for response in stream:
        if response.event == 'thread.message.delta':
            for delta in response.data.delta.content:
                if delta.type == 'text':
                    yield delta.text.value

#@st.cache_data
def handle_userinput(user_question):    
    # Append user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_question, "avatar": user_avatar_url})
        
    client.beta.threads.messages.create(thread_id=st.session_state.thread_id, role="user", content=user_question)

    with client.beta.threads.runs.stream(thread_id=st.session_state.thread_id, assistant_id=st.session_state.assistant_id) as stream:
        assistant_response = "".join(generate_response_stream(stream))
        st.write_stream(generate_response_stream(stream))
    specialist_avatar = specialist_id_caption[st.session_state.specialist]["avatar"]
    parse_json(assistant_response)
    st.session_state.chat_history.append({"role": "assistant", "content": st.session_state.assistant_response, "avatar": specialist_avatar})  # Add assistant response to chat history
    



def main():
    initialize_session_state()
    display_header()
    handle_user_input_container()
    #display_sidebar()
    process_queries()    
    display_chat_history()
       
if __name__ == '__main__':
    main()