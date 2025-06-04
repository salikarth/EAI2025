from flask import Flask
from graphene import ObjectType, String, Int, List, Schema, Field, Argument
from flask_graphql import GraphQLView
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
        return connection
    except mysql.connector.Error as err:
        raise Exception(f"Database connection failed: {err}")

class Book(ObjectType):
    id = Int()
    title = String()
    author = String()
    isbn = String()
    total_copies = Int()
    available_copies = Int()
    cover_url = String()

class BookQuery(ObjectType):
    books = List(Book, id=Argument(Int, required=False), title=Argument(String, required=False))
    def resolve_books(self, info, id=None, title=None):
        conn = get_db_connection()
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
        cursor.close()
        conn.close()
        return [Book(id=b['id'], title=b['title'], author=b['author'], isbn=b['isbn'],
                     total_copies=b['total_copies'], available_copies=b['available_copies'],
                     cover_url=b['cover_url']) for b in books]

class BookMutation(ObjectType):
    create_book = Field(Book, title=String(required=True), author=String(required=True),
                        isbn=String(required=True), total_copies=Int(required=True),
                        available_copies=Int(required=True), cover_url=String())
    def resolve_create_book(self, info, title, author, isbn, total_copies, available_copies, cover_url=''):
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
        return Book(id=book_id, title=title, author=author, isbn=isbn,
                    total_copies=total_copies, available_copies=available_copies, cover_url=cover_url)

schema = Schema(query=BookQuery, mutation=BookMutation)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.BOOK_SERVICE_PORT)