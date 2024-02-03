import streamlit as st
import PyPDF2
import os

def extract_text_from_pdf(pdf_file):
    with open(pdf_file, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        return text

def main():
    st.title("Simple PDF Text Extractor")

    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        with open("temp.pdf", "wb") as temp_file:
            temp_file.write(uploaded_file.getvalue())

        extracted_text = extract_text_from_pdf("temp.pdf")

        st.write(f"Text Extracted from PDF:")
        st.text(extracted_text)

        # Clean up temporary files
        os.remove("temp.pdf")

if __name__ == "__main__":
    main()
