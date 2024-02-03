import streamlit as st
import PyPDF2
import os
from streamlit import session_state
import time

session_state['page']="login"
session_state.authenticated = False
st.experimental_set_query_params(authenticated = False)
def extract_text_from_pdf(pdf_file):
    with open(pdf_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text

def main():
    st.title("Welcome to AI Powered Test")
    page = st.sidebar.radio("Select Page", ["Login", "Contact","Upload", ])
    session_state['page'] = str(page)
    if session_state['page'] == "Upload":
        uploadpdf()
    elif session_state['page'] == "Login":
        loginPage()
    elif session_state['page'] == "Contact":
        show_contact()

def uploadpdf():
    st.title("Simple PDF Text Extractor")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    if uploaded_file is not None:
        with open("temp.pdf", "wb") as temp_file:
            temp_file.write(uploaded_file.getvalue())
        extracted_text = extract_text_from_pdf("temp.pdf")
        st.write(f"Text Extracted from PDF:")
        st.text(extracted_text)
        os.remove("temp.pdf")

def login(username, password):
    return username == "neil" and password == "neil"
def loginPage():

    # Create a session_state state to store user authentication status
    session_state.username=""

    if not session_state.authenticated:
        # Display login form if not authenticated
        st.subheader("Login")

        # User input for username and password
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        # Login button
        if st.button("Login"):
            if login(username, password):
                # Update session_state state on successful login
                session_state.username = username
                session_state.authenticated = True
                st.experimental_set_query_params(authenticated=True)
                st.success("Login successful! Redirecting...")
                session_state.page = "Upload"

            else:
                st.error("Invalid username or password. Please try again.")
    else:
        # Redirect to another page if authenticated
        st.experimental_set_query_params(authenticated=True)
        st.experimental_rerun()

        # Display content for authenticated users
        st.subheader(f"Welcome, {session_state.username}!")
        st.write("This is the authenticated content.")


if __name__ == "__main__":
    main()
