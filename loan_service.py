from flask import Flask
from graphene import ObjectType, Int, String, List, Schema, Field, Argument, Boolean
from flask_graphql import GraphQLView
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import requests
from config import Config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/graphql": {"origins": "*"}})

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB_LOAN,
            port=Config.MYSQL_PORT,
        )
        logging.debug(f"Connected to database: {Config.MYSQL_DB_LOAN}")
        return connection
    except mysql.connector.Error as e:
        logging.error(f"Database connection failed: {str(e)}")
        raise Exception(f"Database connection failed: {str(e)}")

def update_book_availability(book_id, increment=True):
    query = f'mutation {{ updateBookAvailability(id: {book_id}, increment: {"true" if increment else "false"}) {{ id availableCopies }} }}'
    logging.info(f"Sending mutation to book_service: {query}")
    try:
        response = requests.post(
            f'{Config.BOOK_SERVICE_URL}/graphql',
            json={'query': query},
            timeout=5
        )
        logging.info(f"Book service response: status={response.status_code}, body={response.text}")
        if response.status_code != 200:
            error_msg = response.json().get('errors', [{'message': 'Unknown error'}])[0]['message']
            raise Exception(f"Failed to update book availability: {error_msg}")
        response_data = response.json()
        if 'errors' in response_data:
            raise Exception(f"Book service error: {response_data['errors'][0]['message']}")
    #     # if not response_data.get('data', {}).get('updateBookAvailability'):
    #     #     raise Exception(f"Book availability update failed for book_id: {book_id}")
    #     return response_data['data']['updateBookAvailability']
    except requests.RequestException as e:
        logging.error(f"Book service mutation failed: {str(e)}")
        raise Exception(f"Failed to update book availability: {str(e)}")

class Loan(ObjectType):
    id = Int()
    user_id = Int()
    book_id = Int()
    loan_date = String()
    return_date = String()

class LoanQuery(ObjectType):
    loans = List(Loan, id=Argument(Int, required=False), user_id=Argument(Int, required=False))
    loan = Field(Loan, id=Int(required=True))
    loans_by_user = List(Loan, user_id=Int(required=True))
    loans_total = List(Loan)

    def resolve_loans(self, info, id=None, user_id=None):
        conn = get_db_connection()
        try:
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
            return [Loan(id=l['id'], user_id=l['user_id'], book_id=l['book_id'], loan_date=l['loan_date'], return_date=l['return_date']) for l in loans]
        finally:
            cursor.close()
            conn.close()

    def resolve_loan(self, info, id):
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM loans WHERE id = %s", (id,))
            loan = cursor.fetchone()
            if not loan:
                raise Exception("Loan not found")
            return Loan(id=loan['id'], user_id=loan['user_id'], book_id=loan['book_id'], loan_date=loan['loan_date'], return_date=loan['return_date'])
        finally:
            cursor.close()
            conn.close()

    def resolve_loans_by_user(self, info, user_id):
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM loans WHERE user_id = %s", (user_id,))
            loans = cursor.fetchall()
            return [Loan(id=l['id'], user_id=l['user_id'], book_id=l['book_id'], loan_date=l['loan_date'], return_date=l['return_date']) for l in loans]
        finally:
            cursor.close()
            conn.close()

    def resolve_loans_total(self, info):
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM loans")
            loans_total = cursor.fetchall()
            return [Loan(id=l['id'], user_id=l['user_id'], book_id=l['book_id'], loan_date=l['loan_date'], return_date=l['return_date']) for l in loans_total]
        finally:
            cursor.close()
            conn.close()

class LoanMutation(ObjectType):
    create_loan = Field(Loan, user_id=Int(required=True), book_id=Int(required=True),
                        loan_date=String(), return_date=String())
    update_loan = Field(Loan, id=Int(required=True), user_id=Int(), book_id=Int(),
                        loan_date=String(), return_date=String())
    delete_loan = Field(Boolean, id=Int(required=True))

    def resolve_create_loan(self, info, user_id, book_id, loan_date=None, return_date=None):
        logging.info(f"Creating loan for user_id: {user_id}, book_id: {book_id}")
        try:
            # Validate user existence
            user_response = requests.post(
                f'{Config.USER_SERVICE_URL}/graphql',
                json={'query': f'query {{ user(id: {user_id}) {{ id }} }}'},
                timeout=5
            )
            logging.debug(f"User query response: status={user_response.status_code}, body={user_response.text}")
            user_data = user_response.json().get('data', {}).get('user')
            if user_data is None:
                raise Exception(f"User not found in user_service (id: {user_id})")

            # Validate book existence and availability
            book_response = requests.post(
                f'{Config.BOOK_SERVICE_URL}/graphql',
                json={'query': f'query {{ book(id: {book_id}) {{ id availableCopies }} }}'},
                timeout=5
            )
            logging.info(f"Book query response: status={book_response.status_code}, body={book_response.text}")
            response_data = book_response.json()
            if 'errors' in response_data:
                raise Exception(f"Book service error: {response_data['errors'][0]['message']}")
            book_data = response_data.get('data', {}).get('book')
            logging.debug(f"Book data: {book_data}")
            if book_data is None:
                raise Exception(f"Book not found in book_service (id: {book_id})")
            if book_data.get('availableCopies', 0) <= 0:
                raise Exception(f"Book is not available for loan (id: {book_id})")

            # Perform loan creation and book availability update atomically
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO loans (user_id, book_id, loan_date, return_date)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, book_id, loan_date, return_date))
                conn.commit()
                loan_id = cursor.lastrowid
                logging.info(f"Loan created with id: {loan_id}")
                
                # Update book availability after loan creation
                update_book_availability(book_id, increment=False)
                
                return Loan(id=loan_id, user_id=user_id, book_id=book_id, loan_date=loan_date, return_date=return_date)
            except Exception as e:
                conn.rollback()
                logging.error(f"Error in create_loan: {str(e)}")
                raise e
            finally:
                cursor.close()
                conn.close()
        except requests.RequestException as e:
            logging.error(f"Service request failed: {str(e)}")
            raise Exception(f"Failed to query services: {str(e)}")

    def resolve_update_loan(self, info, id, user_id=None, book_id=None, loan_date=None, return_date=None):
        logging.info(f"Updating loan id: {id}, inputs: {{user_id: {user_id}, book_id: {book_id}, loan_date: {loan_date}, return_date: {return_date}}}")
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM loans WHERE id = %s", (id,))
            loan = cursor.fetchone()
            if not loan:
                raise Exception("Loan not found")
            
            allowed_fields = ['user_id', 'book_id', 'loan_date', 'return_date']
            updates = {k: v for k, v in locals().items() if v is not None and k in allowed_fields}
            logging.debug(f"Updates: {updates}")
            
            if not updates:
                raise Exception("No fields provided to update")
            
            if user_id and user_id != loan['user_id']:
                user_response = requests.post(
                    f'{Config.USER_SERVICE_URL}/graphql',
                    json={'query': f'query {{ user(id: {user_id}) {{ id }} }}'},
                    timeout=5
                )
                logging.debug(f"User query response: status={user_response.status_code}, body={user_response.text}")
                user_data = user_response.json().get('data', {}).get('user')
                if user_data is None:
                    raise Exception(f"New user not found in user_service (id: {user_id})")
            
            if book_id and book_id != loan['book_id']:
                book_response = requests.post(
                    f'{Config.BOOK_SERVICE_URL}/graphql',
                    json={'query': f'query {{ book(id: {book_id}) {{ id availableCopies }} }}'},
                    timeout=5
                )
                logging.debug(f"Book query response for update: status={book_response.status_code}, body={book_response.text}")
                book_data = book_response.json().get('data', {}).get('book')
                if book_data is None or book_data.get('availableCopies', 0) <= 0:
                    raise Exception(f"New book is not available for loan (id: {book_id})")
                update_book_availability(loan['book_id'], increment=True)  # Return old book
                update_book_availability(book_id, increment=False)  # Loan new book
            
            set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
            values = list(updates.values()) + [id]
            cursor.execute(f"UPDATE loans SET {set_clause} WHERE id = %s", values)
            conn.commit()
            
            cursor.execute("SELECT * FROM loans WHERE id = %s", (id,))
            updated_loan = cursor.fetchone()
            logging.info(f"Updated loan: {updated_loan}")
            
            return Loan(id=updated_loan['id'], user_id=updated_loan['user_id'], book_id=updated_loan['book_id'],
                        loan_date=updated_loan['loan_date'], return_date=updated_loan['return_date'])
        except Exception as e:
            conn.rollback()
            logging.error(f"Error in update_loan: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def resolve_delete_loan(self, info, id):
        logging.info(f"Deleting loan id: {id}")
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT book_id FROM loans WHERE id = %s", (id,))
            loan = cursor.fetchone()
            if not loan:
                raise Exception(f"Loan not found (id: {id})")
            
            # Update book availability before deleting loan
            update_book_availability(loan['book_id'], increment=True)
            
            cursor.execute("DELETE FROM loans WHERE id = %s", (id,))
            conn.commit()
            rows_affected = cursor.rowcount
            if rows_affected == 0:
                raise Exception(f"Failed to delete loan (id: {id})")
            logging.info(f"Loan deleted successfully: {id}")
            return True
        except Exception as e:
            conn.rollback()
            logging.error(f"Error in delete_loan: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

schema = Schema(query=LoanQuery, mutation=LoanMutation)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    logging.info(f"Starting loan_service on port {Config.LOAN_SERVICE_PORT}")
    app.run(debug=True, host='0.0.0.0', port=Config.LOAN_SERVICE_PORT)