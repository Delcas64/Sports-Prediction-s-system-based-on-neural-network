import torch
import torch.nn as nn
import xgboost as xgb
import numpy as np
import os
from pathlib import Path
import app.ml.features as features

ruta_archivo = os.path.dirname(os.path.abspath(__file__))


LSTM = os.path.join(ruta_archivo,"../models/best_model.pt")
XGBBOOST = os.path.join(ruta_archivo,"../models/xgboost_model.ubj")

class LSTMPredictor(nn.Module):
    def __init__(self, model_path = LSTM, device="cpu"):
        super().__init__()
        self.device = torch.device(device)
               
        self.lstm = nn.LSTM(input_size = 11, hidden_size = 32, num_layers=2, 
                           batch_first=True, dropout=0.4)
        
        self.fc = nn.Linear(32, 1)  # salida 1 -> prob de que gane el HOME

        # 2. CARGA PESOS en esta instancia
        checkpoint = torch.load(model_path, map_location=self.device)
        self.load_state_dict(checkpoint)  # ← CLAVE: carga en self
        
        self.to(self.device)
        self.eval()
    
    def forward(self, x):
        out, _ = self.lstm(x) # x: (batch, seq_len, input_dim)

        # Nos quedamos con la salida del último paso temporal
        last_hidden = out[:, -1, :]  # (batch, hidden_dim), El partido predicho tras ver la secuencia completa
        logits = self.fc(last_hidden) # (batch, 1)
        return logits # sin sigmoide, usaremos BCEWithLogitsLoss
      
    def predict_match(self, home_name, away_name):
        return features.predecir_partido(home_name=home_name, away_name=away_name, model=self, seq_len=10)


class XGBPredictor:
    def __init__(self, model_path):
        self.model = xgb.Booster()
        self.model.load_model(model_path)

    def predict_match(self,home_name, away_name):
        return features.predecir_partido_xgb(homename=home_name,awayname=away_name,model=self.model)    



