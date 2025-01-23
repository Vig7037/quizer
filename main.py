import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import (
    CredentialsError, ForgotError, LoginError, RegisterError, ResetError, UpdateError
)
from dotenv import load_dotenv
load_dotenv()  # Load all the environment variables
import os
import google.generativeai as genai

# Configure GenAI Key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to Load Google Gemini Model and Provide Queries as Response
def get_gemini_response(question, number):
    prompt = f"""
    You are an expert in creating quizzes based on the context.
    Provide four options for each question.
    Context: {question}
    Number of Questions: {number}
    """
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([prompt])
    return response.text

# --- Load and Save Config ---
def load_config():
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            return yaml.load(file, Loader=SafeLoader)
    except FileNotFoundError:
        st.error("Config file not found. Please create a valid `config.yaml` file.")
        return None
    except yaml.YAMLError as e:
        st.error(f"Error in YAML format: {e}")
        return None

def save_config(config):
    try:
        with open('config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False)
    except Exception as e:
        st.error(f"Error saving config file: {e}")

# --- Authentication ---
def create_authenticator(config):
    return stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

# --- Quiz Page ---
def quiz_page():
    st.title("Quizzer")
    st.write("### A platform where you can create quizzes easily.")

    question = st.text_input("On which context do you want the quiz? Please explain!")
    number = st.number_input("Number of questions:", min_value=1, step=1, value=1)
    if st.button("Generate Quiz"):
        if question and number:
            with st.spinner("Generating quiz..."):
                response = get_gemini_response(question, number)
                st.write(f"Generated quiz: \n\n{response}")
        else:
            st.warning("Please provide the context and number of questions.")

# --- Create Account Page ---
def create_account_page():
    st.title("Create Your Account")
    config = load_config()
    if config:
        authenticator = create_authenticator(config)
        try:
            email, username, name = authenticator.register_user()
            if email:
                st.success("User registered successfully!")
                save_config(config)
        except RegisterError as e:
            st.error(e)

# --- Manage Account Page ---
def manage_account_page():
    config = load_config()
    if config:
        authenticator = create_authenticator(config)
        try:
            authenticator.login()
            authenticator.experimental_guest_login(
                'Login with Google', provider='google', oauth2=config['oauth2']
            )
        except LoginError as e:
            st.error(f"Login Error: {e}")

        # Authentication Status
        if st.session_state.get("authentication_status"):
            st.success(f"Welcome, {st.session_state['name']}!")
            quiz_page()
            authenticator.logout("Logout", "sidebar")

        elif st.session_state.get("authentication_status") is False:
            st.error("Invalid username or password.")
        elif st.session_state.get("authentication_status") is None:
            st.warning("Please log in.")

# --- Navigation Menu ---
pages = {
    "Create Your Account": create_account_page,
    "Sign In": manage_account_page,
}

# --- Sidebar for Navigation ---
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(pages.keys()))

# --- Run the Selected Page ---
if selection in pages:
    pages[selection]()
