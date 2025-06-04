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
    def resolve_users(self, info, id=None):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT id, name, email FROM users"
        params = []
        if id:
            query += " WHERE id = %s"
            params.append(id)
        cursor.execute(query, params)
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        for user in users:
            loan_response = requests.get(f'{Config.URL}:{Config.LOAN_SERVICE_PORT}/graphql', json={
                'query': f'query {{ loans(userId: {user["id"]}) {{ id }} }}'
            })
            if loan_response.status_code == 200:
                loans = loan_response.json()['data']['loans']
                user['loan_history'] = len(loans)
            else:
                user['loan_history'] = 0
        return [User(id=u['id'], name=u['name'], email=u['email'], loan_history=u['loan_history']) for u in users]

class UserMutation(ObjectType):
    create_user = Field(User, name=String(required=True), email=String(required=True))
    def resolve_create_user(self, info, name, email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return User(id=user_id, name=name, email=email, loan_history=0)

schema = Schema(query=UserQuery, mutation=UserMutation)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.USER_SERVICE_PORT)