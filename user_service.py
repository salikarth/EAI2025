from flask import Flask
from graphene import ObjectType, Int, String, List, Schema, Field, Argument, Boolean
from flask_graphql import GraphQLView
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import requests
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
            database=Config.MYSQL_DB_USER,
            port=Config.MYSQL_PORT,
        )
        return connection
    except mysql.connector.Error as err:
        raise Exception(f"Database connection failed: {err}")

class User(ObjectType):
    id = Int()
    name = String()
    email = String()
    loan_history = Int()

class UserQuery(ObjectType):
    users = List(User, id=Argument(Int, required=False))
    user = Field(User, id=Int(required=True))

    def resolve_users(self, info, id=None):
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            query = "SELECT id, name, email FROM users"
            params = []
            if id:
                query += " WHERE id = %s"
                params.append(id)
            cursor.execute(query, params)
            users = cursor.fetchall()
            for user in users:
                loan_response = requests.get(f'{Config.LOAN_SERVICE_URL}/graphql', json={
                    'query': f'query {{ loansByUser(userId: {user["id"]}) {{ id }} }}'
                })
                if loan_response.status_code == 200:
                    loans = loan_response.json()['data']['loansByUser']
                    user['loan_history'] = len(loans)
                else:
                    user['loan_history'] = 0
            return [User(id=u['id'], name=u['name'], email=u['email'], loan_history=u['loan_history']) for u in users]
        finally:
            cursor.close()
            conn.close()

    def resolve_user(self, info, id):
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (id,))
            user = cursor.fetchone()
            if not user:
                raise Exception("User not found")
            loan_response = requests.get(f'{Config.LOAN_SERVICE_URL}/graphql', json={
                'query': f'query {{ loansByUser(userId: {id}) {{ id }} }}'  # Fixed query name to match loan_service
            })
            loan_history = len(loan_response.json()['data']['loansByUser']) if loan_response.status_code == 200 else 0
            return User(id=user['id'], name=user['name'], email=user['email'], loan_history=loan_history)
        finally:
            cursor.close()
            conn.close()

class UserMutation(ObjectType):
    create_user = Field(User, name=String(required=True), email=String(required=True))
    update_user = Field(User, id=Int(required=True), name=String(), email=String())
    delete_user = Field(Boolean, id=Int(required=True))

    def resolve_create_user(self, info, name, email):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
            conn.commit()
            user_id = cursor.lastrowid
            return User(id=user_id, name=name, email=email, loan_history=0)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

    def resolve_update_user(self, info, id, name=None, email=None):
        logging.debug(f"Updating user id: {id}, inputs: {{name: {name}, email: {email}}}")
        conn = get_db_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (id,))
            user = cursor.fetchone()
            if not user:
                raise Exception("User not found")
            
            allowed_fields = ['name', 'email']
            updates = {k: v for k, v in locals().items() if v is not None and k in allowed_fields}
            logging.debug(f"Updates: {updates}")
            
            if not updates:
                raise Exception("No fields provided to update")
            
            set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
            values = list(updates.values()) + [id]
            cursor.execute(f"UPDATE users SET {set_clause} WHERE id = %s", values)
            conn.commit()
            
            cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (id,))
            updated_user = cursor.fetchone()
            logging.debug(f"Updated user: {updated_user}")
            
            loan_response = requests.get(f'{Config.LOAN_SERVICE_URL}/graphql', json={
                'query': f'query {{ loansByUser(userId: {id}) {{ id }} }}'
            })
            loan_history = len(loan_response.json()['data']['loansByUser']) if loan_response.status_code == 200 else 0
            
            return User(id=updated_user['id'], name=updated_user['name'], email=updated_user['email'], loan_history=loan_history)
        except Exception as e:
            conn.rollback()
            logging.error(f"Error in update_user: {str(e)}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def resolve_delete_user(self, info, id):
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()

schema = Schema(query=UserQuery, mutation=UserMutation)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.USER_SERVICE_PORT)