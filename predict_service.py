import pandas as pd
import pickle
from datetime import datetime
import numpy as np
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.statespace.sarimax import SARIMAX
from flask import Flask, request, jsonify
from flask_graphql import GraphQLView
from graphene import ObjectType, Int, String, Float, List, Schema, Field, Argument, Boolean
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError
import json
import os

load_dotenv()
app = Flask(__name__)
CORS(app)

class Config:
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_PORT = os.getenv("MYSQL_PORT", 3306)
    PREDICT_SERVICE_PORT = os.getenv("PREDICT_SERVICE_PORT", 5003)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class Prediction(ObjectType):
    model_no = Int()
    prediction = Float()
    season_type = String()

class PredictQuery(ObjectType):
    predictions = List(Prediction,
                      model_no=Argument(Int, required=False),
                      date=Argument(String, required=False),
                      is_peak_season=Argument(Int, required=False),
                      is_low_season=Argument(Int, required=False))
    def resolve_predictions(self, info, model_no=None, date=None, is_peak_season=None, is_low_season=None):
        target_date = datetime.strptime(date, '%Y-%m-%d') if date else datetime.now()
        is_peak_season = is_peak_season if is_peak_season is not None else 0
        is_low_season = is_low_season if is_low_season is not None else 0
        results = []
        for m in range(1, 5) if not model_no else [model_no]:
            result = predict_future_borrowing(m, target_date, is_peak_season, is_low_season)
            if result.get("success"):
                results.append(Prediction(model_no=m, prediction=result["prediction"], season_type=f"peak_{is_peak_season}_low_{is_low_season}"))
        return results

class PredictAnalyze(ObjectType):
    success = Boolean()
    analysis = String()

class PredictMutation(ObjectType):
    predict_analyze = Field(PredictAnalyze, prompt=Argument(String, required=True))
    def resolve_predict_analyze(self, info, prompt):
        target_date = datetime(2025, 4, 30)
        results = {}
        season_combinations = [{"name": "peak_only", "is_peak": 1, "is_low": 0}, {"name": "low_only", "is_peak": 0, "is_low": 1}, {"name": "no_season", "is_peak": 0, "is_low": 0}]
        for model_no in range(1, 5):
            model_results = {}
            for combo in season_combinations:
                result = predict_future_borrowing(model_no, target_date, combo["is_peak"], combo["is_low"])
                if result.get("success"):
                    model_results[combo["name"]] = result["prediction"]
            results[f"model_{model_no}"] = model_results
        prediction_data = {"target_date": target_date.strftime('%Y-%m-%d'), "predictions": results}
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        full_prompt = f"User prompt: {prompt}\nPrediction data: {json.dumps(prediction_data, indent=2)}\nAnalyze this data."
        response = model.generate_content(full_prompt)
        return PredictAnalyze(success=True, analysis=response.text)

def predict_future_borrowing(model_no, target_date, is_peak_season, is_low_season):
    try:
        data_path = os.path.join(os.path.dirname(__file__), f'prediction_service/book_{model_no}_sirama_data.csv')
        df = pd.read_csv(data_path)
        df['date'] = pd.to_datetime(df['date'])
        df_ts = df.set_index('date')
        scaler = StandardScaler()
        borrowed_scaled = scaler.fit_transform(df_ts[['borrowed_count']])
        borrowed_scaled = pd.Series(borrowed_scaled.flatten(), index=df_ts.index)
        model_path = os.path.join(os.path.dirname(__file__), f'prediction_service/sarima_model_{model_no}.pkl')
        with open(model_path, 'rb') as pkl:
            loaded_model = pickle.load(pkl)
        future_data = pd.DataFrame({'is_peak_season': [is_peak_season], 'is_low_season': [is_low_season]})
        prediction = loaded_model['results'].predict(start=0, end=0, exog=future_data)
        prediction_unscaled = scaler.inverse_transform(prediction.values.reshape(-1, 1))[0][0]
        return {"success": True, "prediction": round(prediction_unscaled)}
    except Exception as e:
        return {"success": False, "error": str(e)}

schema = Schema(query=PredictQuery, mutation=PredictMutation)
app.add_url_rule('/graphql', view_func=GraphQLView.as_view('graphql', schema=schema, graphiql=True))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=Config.PREDICT_SERVICE_PORT)