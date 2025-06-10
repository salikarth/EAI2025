from flask import Flask
from flask_graphql import GraphQLView
from graphene import ObjectType, String, Int, List, Schema, Field, Argument, Boolean
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
from config import Config
import logging

logging.basicConfig(level=logging.DEBUG)
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
        return connection
    except mysql.connector.Error as err:
        raise Exception(f"Database connection failed: {err}")

class Book(ObjectType):
    id = Int()
    title = String()
    author = String()
    isbn = String()
    total_copies = Int()
    available_copies = Int()  # Snake case for consistency
    cover_url = String()

class BookQuery(ObjectType):
    books = List(Book, id=Argument(Int, required=False), title=Argument(String, required=False))
    book = Field(Book, id=Int(required=True))
    search_books = List(Book, q=String(required=True))

    def resolve_books(self, info, id=None, title=None):
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT * FROM books"
            params = []
            if id:
                query += " WHERE id = %s"
                params.append(id)
            elif title:
                query += " WHERE LOWER(title) LIKE %s"
                params.append(f'%{title.lower()}%')
            cursor.execute(query, params)
            books = cursor.fetchall()
            return [Book(id=b['id'], title=b['title'], author=b['author'], isbn=b['isbn'],
                         total_copies=b['total_copies'], available_copies=b['available_copies'],
                         cover_url=b['cover_url']) for b in books]
        finally:
            cursor.close()
            conn.close()

    def resolve_book(self, info, id):
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM books WHERE id = %s", (id,))
            book = cursor.fetchone()
            if not book:
                raise Exception("Book not found")
            return Book(id=book['id'], title=book['title'], author=book['author'], isbn=book['isbn'],
                        total_copies=book['total_copies'], available_copies=book['available_copies'],
                        cover_url=book['cover_url'])
        finally:
            cursor.close()
            conn.close()

    def resolve_search_books(self, info, q):
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT * FROM books 
                WHERE LOWER(title) LIKE %s OR LOWER(author) LIKE %s
            """, (f'%{q.lower()}%', f'%{q.lower()}%'))
            books = cursor.fetchall()
            return [Book(id=b['id'], title=b['title'], author=b['author'], isbn=b['isbn'],
                         total_copies=b['total_copies'], available_copies=b['available_copies'],
                         cover_url=b['cover_url']) for b in books]
        finally:
            cursor.close()
            conn.close()

class BookMutation(ObjectType):
    create_book = Field(Book, title=String(required=True), author=String(required=True),
                        isbn=String(required=True), total_copies=Int(required=True),
                        available_copies=Int(required=True), cover_url=String())
    update_book = Field(Book, id=Int(required=True), title=String(), author=String(),
                        isbn=String(), total_copies=Int(), available_copies=Int(), cover_url=String())
    update_book_availability = Field(Book, id=Int(required=True), increment=Boolean(required=True))
    delete_book = Field(Boolean, id=Int(required=True))

    def resolve_create_book(self, info, title, author, isbn, total_copies, available_copies, cover_url=''):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO books (title, author, isbn, total_copies, available_copies, cover_url)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (title, author, isbn, total_copies, available_copies, cover_url))
            conn.commit()
            book_id = cursor.lastrowid
            return Book(id=book_id, title=title, author=author, isbn=isbn,
                        total_copies=total_copies, available_copies=available_copies, cover_url=cover_url)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def resolve_update_book(self, info, id, title=None, author=None, isbn=None, total_copies=None, available_copies=None, cover_url=None):
        logging.debug(f"Updating book id: {id}, inputs: {locals()}")
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM books WHERE id = %s", (id,))
            book = cursor.fetchone()
            if not book:
                raise Exception("Book not found")
            
            allowed_fields = ['title', 'author', 'isbn', 'total_copies', 'available_copies', 'cover_url']
            updates = {k: v for k, v in locals().items() if v is not None and k in allowed_fields}
            logging.debug(f"Updates: {updates}")
            
            if not updates:
                raise Exception("No fields provided to update")
            
            set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
            values = list(updates.values()) + [id]
            cursor.execute(f"UPDATE books SET {set_clause} WHERE id = %s", values)
            conn.commit()
            
            cursor.execute("SELECT * FROM books WHERE id = %s", (id,))
            updated_book = cursor.fetchone()
            logging.debug(f"Updated book: {updated_book}")
            
            return Book(id=updated_book['id'], title=updated_book['title'], author=updated_book['author'], isbn=updated_book['isbn'],
                        total_copies=updated_book['total_copies'], available_copies=updated_book['available_copies'],
                        cover_url=updated_book['cover_url'])
        except Exception as e:
            conn.rollback()
            logging.error(f"Error in update_book: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def resolve_update_book_availability(self, info, id, increment):
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT available_copies, total_copies FROM books WHERE id = %s", (id,))
            book = cursor.fetchone()
            if not book:
                raise Exception("Book not found")
            available_copies = book['available_copies']
            total_copies = book['total_copies']
            if increment:
                if available_copies >= total_copies:
                    raise Exception("Available copies cannot exceed total copies")
                available_copies += 1
            else:
                if available_copies <= 0:
                    raise Exception("No available copies to loan")
                available_copies -= 1
            cursor.execute("UPDATE books SET available_copies = %s WHERE id = %s", (available_copies, id))
            conn.commit()
            cursor.execute("SELECT * FROM books WHERE id = %s", (id,))
            updated_book = cursor.fetchone()
            return Book(id=updated_book['id'], title=updated_book['title'], author=updated_book['author'], isbn=updated_book['isbn'],
                        total_copies=updated_book['total_copies'], available_copies=updated_book['available_copies'],
                        cover_url=updated_book['cover_url'])
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def resolve_delete_book(self, info, id):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE id = %s", (id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

schema = Schema(query=BookQuery, mutation=BookMutation)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.BOOK_SERVICE_PORT)