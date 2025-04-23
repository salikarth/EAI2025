from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
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
            database=Config.MYSQL_DB_BOOK,
            port=Config.MYSQL_PORT,
        )
        app.logger.info("Database connection successful")
        return connection
    except mysql.connector.Error as err:
        app.logger.error(f"Database connection failed: {err}")
        raise Exception(f"Database connection failed: {err}")

@app.route('/books', methods=['GET'])
def get_books():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books")
        books = cursor.fetchall()
        cursor.close()
        conn.close()
        app.logger.info(f"Fetched {len(books)} books")
        return jsonify(books), 200
    except Exception as e:
        app.logger.error(f"Error fetching books: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        cursor.close()
        conn.close()
        if not book:
            return jsonify({"error": "Book not found"}), 404
        app.logger.info(f"Fetched book with ID: {book_id}")
        return jsonify(book), 200
    except Exception as e:
        app.logger.error(f"Error fetching book with ID {book_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/books', methods=['POST'])
def create_book():
    try:
        data = request.get_json()
        title = data['title']
        author = data['author']
        isbn = data['isbn']
        total_copies = data['total_copies']
        available_copies = data['available_copies']
        cover_url = data.get('cover_url', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO books (title, author, isbn, total_copies, available_copies, cover_url)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (title, author, isbn, total_copies, available_copies, cover_url))
        conn.commit()
        book_id = cursor.lastrowid
        cursor.close()
        conn.close()

        app.logger.info(f"Book created successfully with ID: {book_id}")
        return jsonify({"message": "Book created successfully", "book_id": book_id}), 201
    except Exception as e:
        app.logger.error(f"Error creating book: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    try:
        data = request.get_json()
        title = data['title']
        author = data['author']
        isbn = data['isbn']
        total_copies = data['total_copies']
        available_copies = data['available_copies']
        cover_url = data.get('cover_url', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE books
            SET title = %s, author = %s, isbn = %s, total_copies = %s, available_copies = %s, cover_url = %s
            WHERE id = %s
        """, (title, author, isbn, total_copies, available_copies, cover_url, book_id))
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()

        if affected_rows == 0:
            return jsonify({"error": "Book not found"}), 404

        app.logger.info(f"Book updated successfully with ID: {book_id}")
        return jsonify({"message": "Book updated successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error updating book with ID {book_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/books/<int:book_id>/availability', methods=['PUT'])
def update_book_availability(book_id):
    try:
        data = request.get_json()
        increment = data['increment']  

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT available_copies, total_copies FROM books WHERE id = %s", (book_id,))
        book = cursor.fetchone()
        if not book:
            cursor.close()
            conn.close()
            return jsonify({"error": "Book not found"}), 404

        available_copies = book['available_copies']
        total_copies = book['total_copies']

        if increment:
            if available_copies >= total_copies:
                cursor.close()
                conn.close()
                return jsonify({"error": "Available copies cannot exceed total copies"}), 400
            available_copies += 1
        else:
            if available_copies <= 0:
                cursor.close()
                conn.close()
                return jsonify({"error": "No available copies to loan"}), 400
            available_copies -= 1

        cursor.execute("""
            UPDATE books
            SET available_copies = %s
            WHERE id = %s
        """, (available_copies, book_id))
        conn.commit()
        cursor.close()
        conn.close()

        app.logger.info(f"Book ID {book_id} availability updated to {available_copies}")
        return jsonify({"message": "Book availability updated", "available_copies": available_copies}), 200
    except Exception as e:
        app.logger.error(f"Error updating availability for book ID {book_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()

        if affected_rows == 0:
            return jsonify({"error": "Book not found"}), 404

        app.logger.info(f"Book deleted successfully with ID: {book_id}")
        return jsonify({"message": "Book deleted successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error deleting book with ID {book_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/books/search', methods=['GET'])
def search_books():
    try:
        query = request.args.get('q', '').lower()  # Ambil query parameter 'q'
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Cari buku berdasarkan judul atau penulis (case-insensitive)
        cursor.execute("""
            SELECT * FROM books 
            WHERE LOWER(title) LIKE %s OR LOWER(author) LIKE %s
        """, (f'%{query}%', f'%{query}%'))
        books = cursor.fetchall()
        cursor.close()
        conn.close()

        app.logger.info(f"Found {len(books)} books for query: {query}")
        return jsonify(books), 200
    except Exception as e:
        app.logger.error(f"Error searching books: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.BOOK_SERVICE_PORT)