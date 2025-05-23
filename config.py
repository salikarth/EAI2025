import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_PORT = os.getenv("MYSQL_PORT", 3306)
    
    MYSQL_DB_USER = os.getenv("MYSQL_DB_USER", "user_management_uts_db")
    MYSQL_DB_LOAN = os.getenv("MYSQL_DB_LOAN", "loan_management_uts_db")
    MYSQL_DB_BOOK = os.getenv("MYSQL_DB_BOOK", "book_management_uts_db")
    MYSQL_DB_PREDICT = os.getenv("MYSQL_DB_PREDICT", "predict_management_uts_db")
    
    BOOK_SERVICE_PORT = os.getenv("BOOK_SERVICE_PORT", 5000)
    USER_SERVICE_PORT = os.getenv("USER_SERVICE_PORT", 5002)
    LOAN_SERVICE_PORT = os.getenv("LOAN_SERVICE_PORT", 5001)
    AI_SERVICE_PORT = os.getenv("AI_SERVICE_PORT", 5003)
    PREDICT_SERVICE_PORT = os.getenv("PREDICT_SERVICE_PORT", 5004)
    
    GEMINI_API_KEY="AIzaSyAImlRgNLbrArrYlcS87EgEI_vr2D88HmA"
    

    URL = os.getenv("URL", 'http://localhost')
