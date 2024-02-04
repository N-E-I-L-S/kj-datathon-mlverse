import streamlit as st

def main():
    st.title("Simple Form Example")

    # Create a form using st.form context manager
    with st.form(key='my_form'):
        # Input fields
        name = st.text_input("Enter your name", max_chars=50)
        age = st.number_input("Enter your age", min_value=0, max_value=150, value=25)
        email = st.text_input("Enter your email", max_chars=100)

        # Submit button
        submitted = st.form_submit_button("Submit")

        # Handle form submission
        if submitted:
            # Process the form data
            st.success(f"Submitted: Name - {name}, Age - {age}, Email - {email}")

if __name__ == "__main__":
    main()
