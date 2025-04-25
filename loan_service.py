from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import requests
from config import Config

load_dotenv()    

app = Flask(__name__)
CORS(app)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB_LOAN,
            port=Config.MYSQL_PORT,
        )
        app.logger.info("Database connection successful")
        return connection
    except mysql.connector.Error as err:
        app.logger.error(f"Database connection failed: {err}")
        raise Exception(f"Database connection failed: {err}")

def update_book_availability(book_id, increment=True):
    try:
        # Panggil endpoint di book_service.py untuk memperbarui available_copies
        response = requests.put(f'{Config.URL}:{Config.BOOK_SERVICE_PORT}/books/{book_id}/availability', json={
            'increment': increment
        })
        if response.status_code != 200:
            raise Exception(f"Failed to update book availability: {response.json().get('error', 'Unknown error')}")
        app.logger.info(f"Book ID {book_id} availability updated: {'incremented' if increment else 'decremented'}")
    except Exception as e:
        app.logger.error(f"Error updating book availability for book ID {book_id}: {str(e)}")
        raise e

@app.route('/loans', methods=['GET'])
def get_loans():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM loans")
        loans = cursor.fetchall()
        cursor.close()
        conn.close()
        app.logger.info(f"Fetched {len(loans)} loans")
        return jsonify(loans), 200
    except Exception as e:
        app.logger.error(f"Error fetching loans: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/loans/<int:loan_id>', methods=['GET'])
def get_loan(loan_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM loans WHERE id = %s", (loan_id,))
        loan = cursor.fetchone()
        cursor.close()
        conn.close()
        if not loan:
            return jsonify({"error": "Loan not found"}), 404
        app.logger.info(f"Fetched loan with ID: {loan_id}")
        return jsonify(loan), 200
    except Exception as e:
        app.logger.error(f"Error fetching loan with ID {loan_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/loans', methods=['POST'])
def create_loan():
    try:
        data = request.get_json()
        user_id = data['user_id']
        book_id = data['book_id']
        loan_date = data.get('loan_date')
        return_date = data.get('return_date')

        # Cek apakah buku tersedia (available_copies > 0)
        book_response = requests.get(f'{Config.URL}:{Config.BOOK_SERVICE_PORT}/books/{book_id}')
        if book_response.status_code != 200:
            return jsonify({"error": "Book not found"}), 404
        book = book_response.json()
        if book['available_copies'] <= 0:
            return jsonify({"error": "Book is not available for loan"}), 400

        # Simpan data loan
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO loans (user_id, book_id, loan_date, return_date)
            VALUES (%s, %s, %s, %s)
        """, (user_id, book_id, loan_date, return_date))
        conn.commit()
        loan_id = cursor.lastrowid
        cursor.close()
        conn.close()

        # Kurangi available_copies di tabel books
        update_book_availability(book_id, increment=False)

        app.logger.info(f"Loan created successfully with ID: {loan_id}")
        return jsonify({"message": "Loan created successfully", "loan_id": loan_id}), 201
    except Exception as e:
        app.logger.error(f"Error creating loan: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/loans/<int:loan_id>', methods=['PUT'])
def update_loan(loan_id):
    try:
        data = request.get_json()
        user_id = data['user_id']
        book_id = data['book_id']
        loan_date = data['loan_date']
        return_date = data.get('return_date')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE loans
            SET user_id = %s, book_id = %s, loan_date = %s, return_date = %s
            WHERE id = %s
        """, (user_id, book_id, loan_date, return_date, loan_id))
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()

        if affected_rows == 0:
            return jsonify({"error": "Loan not found"}), 404

        app.logger.info(f"Loan updated successfully with ID: {loan_id}")
        return jsonify({"message": "Loan updated successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error updating loan with ID {loan_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/loans/<int:loan_id>', methods=['DELETE'])
def delete_loan(loan_id):
    try:
        # Ambil book_id sebelum menghapus loan
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT book_id FROM loans WHERE id = %s", (loan_id,))
        loan = cursor.fetchone()
        if not loan:
            cursor.close()
            conn.close()
            return jsonify({"error": "Loan not found"}), 404
        book_id = loan['book_id']

        # Hapus loan
        cursor.execute("DELETE FROM loans WHERE id = %s", (loan_id,))
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()

        if affected_rows == 0:
            return jsonify({"error": "Loan not found"}), 404

        # Tambah kembali available_copies di tabel books
        update_book_availability(book_id, increment=True)

        app.logger.info(f"Loan deleted successfully with ID: {loan_id}")
        return jsonify({"message": "Loan deleted successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error deleting loan with ID {loan_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/loans/user/<int:user_id>', methods=['GET'])
def get_loans_by_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM loans WHERE user_id = %s", (user_id,))
        loans = cursor.fetchall()
        cursor.close()
        conn.close()
        app.logger.info(f"Fetched {len(loans)} loans for user ID: {user_id}")
        return jsonify(loans), 200
    except Exception as e:
        app.logger.error(f"Error fetching loans for user ID {user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/loans-total', methods=['GET'])
def get_all_loans_total():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM loans_total")
        loans_total = cursor.fetchall()
        cursor.close()
        conn.close()
        app.logger.info(f"Fetched {len(loans_total)} records from loans_total table")
        return jsonify(loans_total), 200
    except Exception as e:
        app.logger.error(f"Error fetching loans_total data: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.LOAN_SERVICE_PORT)