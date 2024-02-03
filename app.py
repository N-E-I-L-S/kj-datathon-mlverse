import streamlit as st
import PyPDF2
import os
from streamlit import session_state
import time
import random
import mysql.connector
import pickle

with open('./pkl_files/AutoTokenizer.pkl', 'rb') as file:
    tokenizer = pickle.load(file)
with open('./pkl_files/AutoModelForSeq2SeqLM.pkl', 'rb') as file:
    model = pickle.load(file)
session_state['page']="Login"
session_state.authenticated = False
loggedin = False
def extract_text_from_pdf(pdf_file):
    with open(pdf_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text

def create_connection():
    """Create a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="kj"
        )
        return connection
    except mysql.connector.Error as e:
        st.error(f"Error: {e}")
        return None


def get_last_text_execute_query(connection = create_connection(), query = "SELECT whole_text FROM Text ORDER BY id DESC LIMIT 1;"):
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result[0]["whole_text"]
def add_text_to_text_table(text_data):
    connection = create_connection()
    if connection:
        try:
            # Create a cursor object
            cursor = connection.cursor()

            # SQL query to insert text data into the text table
            query = "INSERT INTO Text (whole_text) VALUES (%s);"

            # Execute the query with the text data
            cursor.execute(query, (text_data,))

            # Commit the changes
            connection.commit()

            # Close the cursor (the connection remains open)
            cursor.close()

            st.success("Data added successfully.")
        except mysql.connector.Error as e:
            st.error(f"Error: {e}")
        finally:
            # Close the connection
            connection.close()

def GetQuestions():
        data = get_last_text_execute_query()
        if data:
            num_broader_questions = 3
            num_niche_questions = 2
            broader_questions = generate_random_questions(data, num_broader_questions)
            niche_questions = generate_random_questions(data, num_niche_questions)
            questions=[]
            for question in broader_questions:
                questions.append(question)
            for question in niche_questions:
                questions.append(question)
            display_questions(questions)

def display_questions(questions):
    # Initialize empty list to store user responses
    user_responses = []

    # Display each question and input field
    for i, question in enumerate(questions, start=1):
        response = st.text_input(f"Question {i}: {question}")
        user_responses.append(response)

    # Display the user responses
    st.subheader("Your Responses:")
    for i, response in enumerate(user_responses, start=1):
        st.write(f"Question {i}: {response}")


def main():
    st.title("Welcome to AI Powered Test")
    page = st.sidebar.radio("Select Page", ["Login", "Upload", "Questions"])
    session_state['page'] = str(page)
    if session_state['page'] == "Upload":
        uploadpdf()
    elif session_state['page'] == "Login":
        loginPage()
    elif session_state['page'] == "Questions":
        GetQuestions()

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
        add_text_to_text_table(extracted_text)
    


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
                loggedin =True

            else:
                st.error("Invalid username or password. Please try again.")
    else:
        # Redirect to another page if authenticated
        st.experimental_set_query_params(authenticated=True)
        st.experimental_rerun()

        # Display content for authenticated users
        st.subheader(f"Welcome, {session_state.username}!")
        st.write("This is the authenticated content.")
def generate_random_questions(document, num_questions):
    questions = []

    for _ in range(num_questions):
        # Ensure the document has enough words for the range
        if len(document.split()) <= 1:
            break

        # Randomly choose the lengths of text between [HL] tags
        text_lengths = [random.randint(1, min(len(document.split()) - 1, 10)) for _ in range(2)]

        # Randomly choose the starting indices for [HL] tags
        start_indices = [random.randint(0, len(document.split()) - text_length - 1) for text_length in text_lengths]

        # Construct input text with randomized tags
        input_text = " ".join([
            document.split()[i] if i < start_index or i >= start_index + text_length else "[HL]" 
            for start_index, text_length in zip(start_indices, text_lengths)
            for i in range(len(document.split()))
        ])
        # Tokenize the input text
        input_ids = tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True).input_ids

        # Generate output
        output = model.generate(input_ids)

        # Decode the generated output
        generated_question = tokenizer.decode(output[0], skip_special_tokens=True)

        questions.append(generated_question)

    return questions


if __name__ == "__main__":
    main()
