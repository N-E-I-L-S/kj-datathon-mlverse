from flask import Flask, request, jsonify
import mysql.connector

app = Flask(__name__)
conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="kj"
        )

cursor = conn.cursor()

@app.route('/insert_qa', methods=['POST'])
def insert_qa():
        try:
            ques = request.json.get('questions')
            ans = request.json.get('answers')
            for a in ans:
                    cursor.execute("INSERT INTO qa (answers) VALUES (%s);", (a,))
            conn.commit()
            return jsonify({'response': 1, 'message': 'success'}), 200
        except Exception as e:
            return jsonify({'response': 0, 'message': f'Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
               


