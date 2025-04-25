import pandas as pd
import pickle
from datetime import datetime
import pandas as pd
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
import matplotlib.pyplot as plt
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
import requests  

# prediction_service/extract_predictions.py
import sys
import os

# # Add the parent directory (EAI2025) to sys.path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config')))

from config import Config

# # Path ke file .env di parent folder
# env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
# load_dotenv(dotenv_path=env_path)    
load_dotenv()

app = Flask(__name__)
CORS(app)

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB_PREDICT,
            port=Config.MYSQL_PORT,
        )
        app.logger.info("Database connection successful")
        return connection
    except mysql.connector.Error as err:
        app.logger.error(f"Database connection failed: {err}")
        raise Exception(f"Database connection failed: {err}")
    
def predict_future_borrowing(model_no, target_date, is_peak_season, is_low_season):
    try:
        # Get the absolute path to the data file
        data_path = os.path.join(os.path.dirname(__file__), f'prediction_service/book_{model_no}_sirama_data.csv')
        df = pd.read_csv(data_path)

        # Convert date to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Set date as index
        df_ts = df.set_index('date')

        scaler = StandardScaler()
        borrowed_scaled = scaler.fit_transform(df_ts[['borrowed_count']])
        borrowed_scaled = pd.Series(borrowed_scaled.flatten(), index=df_ts.index)
        
        # Load the saved model
        model_path = os.path.join(os.path.dirname(__file__), f'prediction_service/sarima_model_{model_no}.pkl')
        
        with open(model_path, 'rb') as pkl:
            loaded_model = pickle.load(pkl)
        
        # Create a DataFrame with the exogenous variables
        future_data = pd.DataFrame({
            'is_peak_season': [is_peak_season],
            'is_low_season': [is_low_season]
        })
        
        # Make prediction using the loaded model
        prediction = loaded_model['results'].predict(
            start=0, 
            end=0,
            exog=future_data
        )
        
        # Inverse transform the prediction (since our model was trained on scaled data)
        prediction_unscaled = scaler.inverse_transform(prediction.values.reshape(-1, 1))[0][0]
        
        return {"success": True, "prediction": round(prediction_unscaled)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# API Routes
@app.route('/predict/<int:model_no>', methods=['GET'])
def predict(model_no):
    """
    Endpoint to predict future borrowing for a specific book model
    
    Query parameters:
    - date: Target date in YYYY-MM-DD format
    - is_peak_season: 1 for peak season, 0 for not peak season
    - is_low_season: 1 for low season, 0 for not low season
    """
    try:
        target_date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        is_peak_season = int(request.args.get('is_peak_season', 0))
        is_low_season = int(request.args.get('is_low_season', 0))
        
        # Convert string date to datetime object
        target_date = datetime.strptime(target_date, '%Y-%m-%d')
        
        result = predict_future_borrowing(model_no, target_date, is_peak_season, is_low_season)
        
        if result.get("success", False):
            return jsonify({"success": True, "data": {"prediction": result["prediction"]}}), 200
        else:
            return jsonify({"success": False, "message": result.get("error", "Unknown error")}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/evaluate', methods=['GET'])
def evaluate():
    """
    Endpoint to fetch evaluation metrics from all SARIMA models (1-6)
    """
    try:
        all_metrics = {}
        
        # Loop through all 6 models
        for model_no in range(1, 5):
            try:
                # Load the saved model
                model_path = os.path.join(os.path.dirname(__file__), f'prediction_service/sarima_model_{model_no}.pkl')
                
                with open(model_path, 'rb') as pkl:
                    loaded_model = pickle.load(pkl)
                
                # Extract metrics from the model
                model_metrics = {
                    'mse': loaded_model.get('mse', 'N/A'),
                    'rmse': loaded_model.get('rmse', 'N/A'),
                    'mae': loaded_model.get('mae', 'N/A'),
                    'r2_score': loaded_model.get('r2_score', 'N/A')
                }
                
                all_metrics[f'model_{model_no}'] = model_metrics
                
            except Exception as e:
                all_metrics[f'model_{model_no}'] = {'error': str(e)}
        
        return jsonify({"success": True, "data": all_metrics}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/loans-total-data', methods=['GET'])
def get_all_loans_total():
    """
    Endpoint to fetch all loans total data from the loan service
    """
    try:
        # Make request to loan service
        response = requests.get('http://localhost:5001/loans-total')
        
        # Check if request was successful
        if response.status_code == 200:
            loans_total = response.json()
            return jsonify({"success": True, "data": loans_total}), 200
        else:
            return jsonify({"success": False, "message": "Failed to fetch loans data"}), response.status_code
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.PREDICT_SERVICE_PORT)