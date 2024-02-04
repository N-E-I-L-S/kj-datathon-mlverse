import streamlit as st
import PyPDF2
import os
import random
import mysql.connector
import pickle
from streamlit import session_state

with open('./pkl_files/AutoTokenizer.pkl', 'rb') as file:
    tokenizer = pickle.load(file)
with open('./pkl_files/AutoModelForSeq2SeqLM.pkl', 'rb') as file:
    model = pickle.load(file)

# Define session_state variables
session_state.authenticated = False
session_state.username = ""
session_state.questions_page_loaded = False

# MySQL Connection function
def create_connection():
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

# Extract text from PDF and add to the Text table
def add_text_to_text_table(text_data):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO Text (whole_text) VALUES (%s);"
            cursor.execute(query, (text_data,))
            connection.commit()
            cursor.close()
            st.success("Data added successfully.")
        except mysql.connector.Error as e:
            st.error(f"Error: {e}")
        finally:
            connection.close()

# Insert question-answer pairs into the QA table
def insert_question_answer_pairs_query(questions, answers, identifier):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            query = "INSERT INTO qa (question, answer, identifier) VALUES (%s, %s, %s);"
            if len(questions) != len(answers):
                st.error("Number of questions and answers must be the same.")
                return
            for q, a in zip(questions, answers):
                cursor.execute(query, (q, a, identifier))
            connection.commit()
            cursor.close()
            st.success("Data added successfully.")
        except mysql.connector.Error as e:
            st.error(f"Error: {e}")
        finally:
            connection.close()

# Display questions on the Questions page
def display_questions(questions):
    user_responses = []

    for i, question in enumerate(questions, start=1):
        response = st.text_area(f"Question {i}: {question}")
        user_responses.append(response)

    if st.button("Submit"):
        insert_question_answer_pairs_query(questions, user_responses, 0)

# PDF Upload function
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

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    with open(pdf_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text

# Curated Questions Generator
def questions_generator_driver(data):
    document = data
    chunk_size = 800
    document_chunks = [document[i:i + chunk_size] for i in range(0, len(document), chunk_size)]

    num_broader_questions = 2
    num_niche_questions = 1

    broader_questions = generate_random_questions_batch(document_chunks, num_broader_questions)
    broader_final_questions = random.sample(broader_questions, k=2)
    niche_questions = generate_random_questions_batch(document_chunks, num_niche_questions)
    niche_final_questions = random.sample(niche_questions, k=1)
    questions = []
    for question in broader_final_questions:
        questions.append(question)
    for question in niche_final_questions:
        questions.append(question)
    return questions

# Generate random questions from document chunks
def generate_random_questions_batch(documents, num_questions):
    questions = []

    for document in documents:
        if len(document.split()) <= 1:
            continue
        text_lengths = [random.randint(1, min(len(document.split()) - 1, 10)) for _ in range(2)]
        start_indices = [random.randint(0, len(document.split()) - text_length - 1) for text_length in text_lengths]

        input_texts = [
            " ".join([
                document.split()[i] if i < start_index or i >= start_index + text_length else "[HL]"
                for i in range(len(document.split()))
            ]) for start_index, text_length in zip(start_indices, text_lengths)
        ]

        temp_answers = []

        for input_text in input_texts:
            temp = input_text.split()
            while "[HL]" in temp:
                temp.remove("[HL]")
            string = " ".join(temp)
            temp_answers.append(string)

        input_ids_list = [tokenizer(input_text, return_tensors="pt").input_ids for input_text in input_texts]

        max_tokens = 512

        for input_ids in input_ids_list:
            for i in range(0, len(input_ids[0]), max_tokens):
                input_ids_chunk = input_ids[:, i:i + max_tokens]
                output = model.generate(input_ids_chunk)
                generated_question = tokenizer.decode(output[0], skip_special_tokens=True)
                questions.append(generated_question)

    return questions

# Login function
def login(username, password):
    return username == "neil" and password == "neil"

# Login Page
def loginPage():
    if not session_state.authenticated:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if login(username, password):
                session_state.username = username
                session_state.authenticated = True
                st.experimental_set_query_params(authenticated=True)
                st.success("Login successful! Redirecting...")
            else:
                st.error("Invalid username or password. Please try again.")
    else:
        st.experimental_set_query_params(authenticated=True)
        st.experimental_rerun()
        st.subheader(f"Welcome, {session_state.username}!")
        st.write("This is the authenticated content.")

# Main function
def main():
    st.sidebar.title("Navigation")
    pages = ["Login", "Upload", "Questions"]
    selected_page = st.sidebar.radio("Select Page", pages)

    if selected_page == "Upload":
        uploadpdf()
    elif selected_page == "Login":
        loginPage()
    elif selected_page == "Questions":
        if not session_state.questions_page_loaded:
            data = get_last_text_execute_query()
            if data:
                questions = questions_generator_driver(data)
                display_questions(questions)
                session_state.questions_page_loaded = True

# Get the last text from the Text table
def get_last_text_execute_query(connection=create_connection(),
                                query="SELECT whole_text FROM Text ORDER BY id DESC LIMIT 1;"):
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result[0]["whole_text"]

if __name__ == "__main__":
    main()
