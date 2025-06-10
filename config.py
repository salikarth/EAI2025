import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql_db")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    
    MYSQL_DB_BOOK = os.getenv("MYSQL_DB_BOOK", "book_management_uts_db")
    MYSQL_DB_LOAN = os.getenv("MYSQL_DB_LOAN", "loan_management_uts_db")
    MYSQL_DB_USER = os.getenv("MYSQL_DB_USER", "user_management_uts_db")
    
    BOOK_SERVICE_PORT = int(os.getenv("BOOK_SERVICE_PORT", "5000"))
    LOAN_SERVICE_PORT = int(os.getenv("LOAN_SERVICE_PORT", "5001"))
    USER_SERVICE_PORT = int(os.getenv("USER_SERVICE_PORT", "5002"))
    PREDICT_SERVICE_PORT = int(os.getenv("PREDICT_SERVICE_PORT", "5003"))
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    BOOK_SERVICE_URL = os.getenv("BOOK_SERVICE_URL", "http://book-service:5000")
    LOAN_SERVICE_URL = os.getenv("LOAN_SERVICE_URL", "http://loan-service:5001")
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5002")
    PREDICT_SERVICE_URL = os.getenv("PREDICT_SERVICE_URL", "http://predict-service:5003")