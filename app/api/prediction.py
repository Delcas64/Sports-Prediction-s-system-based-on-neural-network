from fastapi import APIRouter, Request
from datetime import datetime
import os
import pandas as pd
from pydantic import BaseModel


from app.ml.predictors import LSTMPredictor, XGBPredictor
import app.ml.teams as teams

router = APIRouter(prefix="/prediction")

ruta_archivo = os.path.dirname(os.path.abspath(__file__))
LSTM = os.path.join(ruta_archivo,"../models/best_model.pt")
XGB = os.path.join(ruta_archivo,"../models/xgboost_model.ubj")

lstm = LSTMPredictor(LSTM)  # ← Global
xgb  = XGBPredictor(XGB)

class PredictionRequest(BaseModel):
    home_team: str
    away_team: str



@router.post("/predict_lstm")
def predict_lstm(request: PredictionRequest):
   
    home = request.home_team
    away = request.away_team
    
   
    
    # Llama al método de predicción de LSTM (ajusta según la firma real del método)
    prediction = lstm.predict_match(home, away)     
    return prediction
    
@router.post("/predict_xgb")
def predict_xgb(request: PredictionRequest):
    
    home = request.home_team
    away = request.away_team
    
            
    # Llama al método de predicción de XGBoost (ajusta según la firma real del método)
    prediction = xgb.predict_match(home,away)  # Asume que tiene un método predict
    
    return  prediction
    



    

