import streamlit as st
import PyPDF2
import os
import random
import mysql.connector
import pickle

with open('./pkl_files/AutoTokenizer.pkl', 'rb') as file:
    tokenizer = pickle.load(file)
with open('./pkl_files/AutoModelForSeq2SeqLM.pkl', 'rb') as file:
    model = pickle.load(file)

session_state = st.session_state
session_state.page = "Login"
session_state.authenticated = False
actual_answers = []

# PDF to TEXT
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

def extract_text_from_pdf(pdf_file):
    with open(pdf_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text

# MYSQL Connection and Queries
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

def get_last_text_execute_query(connection=create_connection(),
                                 query="SELECT whole_text FROM Text ORDER BY id DESC LIMIT 1;"):
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


def insert_question_answer_pairs_query(questions, answers, identifier):
    connection = create_connection()

    if connection:
        try:
            # Create a cursor object
            cursor = connection.cursor()

            # SQL query to insert question-answer pairs into the database
            query = "INSERT INTO qa (question, answer, identifier) VALUES (%s, %s, %s);"

            # Check if the lengths of questions and answers are the same
            if len(questions) != len(answers):
                st.error("Number of questions and answers must be the same.")
                return

            # Execute the query for each question-answer pair
            for q, a in zip(questions, answers):
                cursor.execute(query, (q, a, identifier))

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


# Questions Page and its functions
if 'actual_answers' not in session_state:
    session_state.actual_answers = []
if 'loaded_data' not in session_state:
    session_state.loaded_data = False

def get_questions():
    data = ""
    st.header("Curated Questions")

    if st.button("Get Latest Questions"):
        data = get_last_text_execute_query()

    if data != "":
        questions = questions_generator_driver(data)
        display_questions(questions)

def questions_generator_driver(data):
    document = data
    # Split the document into smaller chunks for batch processing
    chunk_size = 800  # You may need to adjust this based on your document size

    if not session_state.loaded_data:
        session_state.document_chunks = [document[i:i + chunk_size] for i in range(0, len(document), chunk_size)]
        session_state.loaded_data = True

    num_broader_questions = 2
    num_niche_questions = 1

    broader_questions = generate_random_questions_batch(session_state.document_chunks, num_broader_questions)
    broader_final_questions = random.sample(broader_questions, k=2)
    niche_questions = generate_random_questions_batch(session_state.document_chunks, num_niche_questions)
    niche_final_questions = random.sample(niche_questions, k=1)
    questions = []
    for question in broader_final_questions:
        questions.append(question)
    for question in niche_final_questions:
        questions.append(question)
    return questions

def generate_random_questions_batch(documents, num_questions):
    questions = []

    for document in documents:
        if len(document.split()) <= 1:
            continue  # Skip empty or very short documents

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

        session_state.actual_answers.extend(temp_answers)

        input_ids_list = [tokenizer(input_text, return_tensors="pt").input_ids for input_text in input_texts]

        # Assuming model input limit is 512 tokens, you may need to adjust this based on your model
        max_tokens = 512

        for input_ids in input_ids_list:
            # Split input_ids into chunks of size max_tokens
            for i in range(0, len(input_ids[0]), max_tokens):
                input_ids_chunk = input_ids[:, i:i + max_tokens]

                # Generate output for each chunk
                output = model.generate(input_ids_chunk)

                # Decode the generated output
                generated_question = tokenizer.decode(output[0], skip_special_tokens=True)
                questions.append(generated_question)

    return questions

def display_questions(questions):
    answers = []  # Initialize empty list to store user responses

    # Display each question and input field
    for i, question in enumerate(questions, start=1):
        response = st.text_area(f"Question {i}: {question}")
        answers.append(response)

    if st.button("Submit"):
        insert_question_answer_pairs_query(session_state.actual_answers, answers, 0)

# Login Page
def login(username, password):
    return username == "neil" and password == "neil"


def login_page():
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
        else:
            st.error("Invalid username or password. Please try again.")


def main():
    page = st.sidebar.radio("Select Page", ["Login", "Upload", "Questions"])
    session_state.page = str(page)

    if session_state.page == "Upload":
        uploadpdf()
    elif session_state.page == "Login":
        login_page()
    elif session_state.page == "Questions":
        get_questions()


if __name__ == "__main__":
    main()
