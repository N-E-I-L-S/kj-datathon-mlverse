import streamlit as st
import mysql.connector

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

def execute_query(connection, query):
    """Execute a SQL query and return the results."""
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    return result

def main():
    st.title("Streamlit MySQL Connection Example")

    # Connect to MySQL
    connection = create_connection()

    if connection:
        # Display data from the database
        st.subheader("Display Data from MySQL")

        query = "SELECT whole_text FROM Text ORDER BY id DESC LIMIT 1;"
        data = execute_query(connection, query)

        if data:
            st.write("Data from MySQL:")
            st.write(data[0]["whole_text"])
        else:
            st.warning("No data available.")

        # Close the MySQL connection
        connection.close()
    else:
        st.error("Failed to connect to MySQL.")

if __name__ == "__main__":
    main()
