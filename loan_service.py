from flask import Flask
from graphene import ObjectType, Int, String, List, Schema, Field, Argument
from flask_graphql import GraphQLView
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
        return connection
    except mysql.connector.Error as err:
        raise Exception(f"Database connection failed: {err}")

def update_book_availability(book_id, increment=True):
    response = requests.put(f'{Config.URL}:{Config.BOOK_SERVICE_PORT}/graphql', json={
        'query': f'mutation {{ updateBookAvailability(bookId: {book_id}, increment: {increment}) {{ message }} }}'
    })
    if response.status_code != 200:
        raise Exception(f"Failed to update book availability: {response.json().get('error', 'Unknown error')}")

class Loan(ObjectType):
    id = Int()
    user_id = Int()
    book_id = Int()
    loan_date = String()
    return_date = String()

class LoanQuery(ObjectType):
    loans = List(Loan, id=Argument(Int, required=False), user_id=Argument(Int, required=False))
    def resolve_loans(self, info, id=None, user_id=None):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM loans"
        params = []
        if id:
            query += " WHERE id = %s"
            params.append(id)
        elif user_id:
            query += " WHERE user_id = %s"
            params.append(user_id)
        cursor.execute(query, params)
        loans = cursor.fetchall()
        cursor.close()
        conn.close()
        return [Loan(id=l['id'], user_id=l['user_id'], book_id=l['book_id'], loan_date=l['loan_date'], return_date=l['return_date']) for l in loans]

class LoanMutation(ObjectType):
    create_loan = Field(Loan, user_id=Int(required=True), book_id=Int(required=True),
                        loan_date=String(), return_date=String())
    def resolve_create_loan(self, info, user_id, book_id, loan_date=None, return_date=None):
        book_response = requests.post(f'{Config.URL}:{Config.BOOK_SERVICE_PORT}/graphql', json={
            'query': f'query {{ book(id: {book_id}) {{ available_copies }} }}'
        })
        if book_response.status_code != 200 or book_response.json()['data']['book']['available_copies'] <= 0:
            raise Exception("Book is not available for loan")
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
        update_book_availability(book_id, increment=False)
        return Loan(id=loan_id, user_id=user_id, book_id=book_id, loan_date=loan_date, return_date=return_date)

schema = Schema(query=LoanQuery, mutation=LoanMutation)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.LOAN_SERVICE_PORT)