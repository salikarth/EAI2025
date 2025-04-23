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
            database=Config.MYSQL_DB_USER,
            port=Config.MYSQL_PORT,
        )
        app.logger.info("Database connection successful")
        return connection
    except mysql.connector.Error as err:
        app.logger.error(f"Database connection failed: {err}")
        raise Exception(f"Database connection failed: {err}")

@app.route('/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        # Ambil jumlah loan untuk setiap user dari loan_service
        for user in users:
            loan_response = requests.get(f'{Config.URL}:{Config.LOAN_SERVICE_PORT}/loans/user/{user["id"]}')
            if loan_response.status_code == 200:
                loans = loan_response.json()
                user['loan_history'] = len(loans)  # Jumlah loan untuk user ini
            else:
                user['loan_history'] = 0

        app.logger.info(f"Fetched {len(users)} users")
        return jsonify(users), 200
    except Exception as e:
        app.logger.error(f"Error fetching users: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Ambil jumlah loan untuk user ini
        loan_response = requests.get(f'{Config.URL}:{Config.LOAN_SERVICE_PORT}/loans/user/{user_id}')
        if loan_response.status_code == 200:
            loans = loan_response.json()
            user['loan_history'] = len(loans)
        else:
            user['loan_history'] = 0

        app.logger.info(f"Fetched user with ID: {user_id}")
        return jsonify(user), 200
    except Exception as e:
        app.logger.error(f"Error fetching user with ID {user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        name = data['name']
        email = data['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (name, email)
            VALUES (%s, %s)
        """, (name, email))
        conn.commit()
        user_id = cursor.lastrowid
        cursor.close()
        conn.close()

        app.logger.info(f"User created successfully with ID: {user_id}")
        return jsonify({"message": "User created successfully", "user_id": user_id}), 201
    except Exception as e:
        app.logger.error(f"Error creating user: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        data = request.get_json()
        name = data['name']
        email = data['email']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET name = %s, email = %s
            WHERE id = %s
        """, (name, email, user_id))
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()

        if affected_rows == 0:
            return jsonify({"error": "User not found"}), 404

        app.logger.info(f"User updated successfully with ID: {user_id}")
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error updating user with ID {user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        affected_rows = cursor.rowcount
        cursor.close()
        conn.close()

        if affected_rows == 0:
            return jsonify({"error": "User not found"}), 404

        app.logger.info(f"User deleted successfully with ID: {user_id}")
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error deleting user with ID {user_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.USER_SERVICE_PORT)