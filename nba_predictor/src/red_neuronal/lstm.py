#!pip -q install torch pandas scikit-learn


import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#device


PATH = "/content/regular_season_limpio.csv"
df = pd.read_csv(PATH)




#Usamos Game_date como indice para nuestra LSTM.

df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
#df.set_index("GAME_DATE", inplace=True)


#Al estar ya el dato como índice podemos quitar la temporada y el game_id 
df.drop(columns=["GAME_ID", "SEASON"], inplace=True)

#Vamos a dividir el dataset en 2 filas por cada partido, una del local y otra del visitante

home = df.copy()
away = df.copy()


home['TEAM_ID'] = df['ID_TEAM_home']
away['TEAM_ID'] = df['ID_TEAM_away']

home['OPPONENT_ID'] = df['ID_TEAM_away']
away['OPPONENT_ID'] = df['ID_TEAM_home']

home['FGM'] = df['FGM_home']
home['FGA'] = df['FGA_home']
home['FG_PCT'] = df['FG_PCT_home']
home['FG3M'] = df['FG3M_home']
home['FG3A'] = df['FG3A_home']
home['FG3_PCT'] = df['FG3_PCT_home']
home['FTM'] = df['FTM_home']
home['FTA'] = df['FTA_home']
home['FT_PCT'] = df['FT_PCT_home']

home['OREB'] = df['OREB_home']
home['DREB'] = df['DREB_home']
home['AST'] = df['AST_home']
home['STL'] = df['STL_home']
home['BLK'] = df['BLK_home']
home['TOV'] = df['TOV_home']
home['PF'] = df['PF_home']
home['PTS'] = df['PTS_home']


away['FGM'] = df['FGM_away']
away['FGA'] = df['FGA_away']
away['FG_PCT'] = df['FG_PCT_away']
away['FG3M'] = df['FG3M_away']
away['FG3A'] = df['FG3A_away']
away['FG3_PCT'] = df['FG3_PCT_away']
away['FTM'] = df['FTM_away']
away['FTA'] = df['FTA_away']
away['FT_PCT'] = df['FT_PCT_away']

away['OREB'] = df['OREB_away']
away['DREB'] = df['DREB_away']
away['AST'] = df['AST_away']
away['STL'] = df['STL_away']
away['BLK'] = df['BLK_away']
away['TOV'] = df['TOV_away']
away['PF'] = df['PF_away']
away['PTS'] = df['PTS_away']


#Se necesita usar numpy para modificar la Series entera de la columna ganador

home['WINNER'] = np.where(df['WINNER'] == "HOME", 1, 0)
away['WINNER'] = np.where(df['WINNER'] == "AWAY", 1, 0)


df = pd.concat([home, away], ignore_index=True)


# Eliminar las columnas antiguas con sufijos "_home" y "_away"
columnass_to_drop = [c for c in df.columns if c.endswith('_home') or c.endswith('_away')]
df = df.drop(columns=columnass_to_drop)


#Primero ordena por equipo y luego por fecha(índice)
#Volvemos con el indice numerico y vuelve game_date a columna, se ordena por equipo
# y fecha del partido 
df = df.sort_values(["TEAM_ID", "GAME_DATE"]).reset_index(drop=True)


#Target binario:
#Ganador o perdedor 1 o 0

#df["WINNER"] = (df["WINNER"] == "HOME").astype(int)

print(df.head())
print(df.tail())


# Quitamos columnas que no usaremos como features
#cols_drop = ["GAME_DATE", "SEASON", "GAME_ID"]  # simple
#X_df = df.drop(columns=cols_drop)

# X (todas menos WINNER), y (WINNER)
# y vector binario de si gano
# X dataframe pasado numpy para el LSTM, tensor, con todas las columnas menos WINNER

y = df["WINNER"].values.astype(np.float32)

# X = solo columnas numéricas (descarta GAME_DATE y otros tipos)
X_df = df.drop(columns=["WINNER"]).select_dtypes(include=[np.number])
X = X_df.values.astype(np.float32)


#n_samples = nº total de filas, n_features = nº total de columnas
n_samples, n_features = X.shape
n_samples, n_features



# Seleccionamos solo columnas numéricas (para escalar)
feature_cols = [c for c in df.columns if c not in ['WINNER', 'TEAM_ID', 'OPPONENT_ID', 'GAME_DATE']]

input_size = len(feature_cols)

# Asumimos que df está ordenado por ['TEAM_ID', 'GAME_DATE']

# Splits 70/15/15 por tiempo
n_samples = len(df)
n_train = int(0.70 * n_samples) #70% de datos para entrenamiento
n_val   = int(0.85 * n_samples) # 15% para validación y el otro 15% para test


#Con el copy() evitamoes el warning de que train_df es solo una vista del df original
train_df = df.iloc[:n_train].copy()
val_df   = df.iloc[n_train:n_val].copy()
test_df  = df.iloc[n_val:].copy()


# Entrenar scaler solo con el conjunto de entrenamiento
scaler = StandardScaler().fit(train_df[feature_cols])

# Aplicar el mismo escalado a todos
train_df[feature_cols] = scaler.transform(train_df[feature_cols])
val_df[feature_cols]   = scaler.transform(val_df[feature_cols])
test_df[feature_cols]  = scaler.transform(test_df[feature_cols])


train_df.shape, val_df.shape, test_df.shape


#Agrupar por equipo y fecha las sequencias

def build_team_sequences(df, seq_len=10, feature_cols=None, target_col='WINNER'):
    X_all, y_all = [], []
    teams = df['TEAM_ID'].unique() #Lista id equipos

    for team in teams:
        df_team = df[df['TEAM_ID'] == team].sort_values('GAME_DATE')
        X_rows = df_team[feature_cols].values
        y_rows = df_team[target_col].values

        # Crear secuencias deslizantes
        for i in range(len(df_team) - seq_len):
            X_all.append(X_rows[i:i+seq_len])
            y_all.append(y_rows[i+seq_len])

    return np.array(X_all, dtype=np.float32), np.array(y_all, dtype=np.float32)


seq_len = 10  # Probar con más seq_len 

X_train, y_train = build_team_sequences(train_df, seq_len, feature_cols)
X_val,   y_val   = build_team_sequences(val_df,   seq_len, feature_cols)
X_test,  y_test  = build_team_sequences(test_df,  seq_len, feature_cols)

print("Shapes →")
print("Train:", X_train.shape, y_train.shape)
print("Val:",   X_val.shape, y_val.shape)
print("Test:",  X_test.shape, y_test.shape)


#COnvierto mis numpy arrayes en tensores para la red

train_ds = TensorDataset(torch.tensor(X_train), torch.tensor(y_train))
val_ds   = TensorDataset(torch.tensor(X_val),   torch.tensor(y_val))
test_ds  = TensorDataset(torch.tensor(X_test),  torch.tensor(y_test))

train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
val_loader   = DataLoader(val_ds, batch_size=64, shuffle=False)
test_loader  = DataLoader(test_ds, batch_size=64, shuffle=False)



#Probar con mas num_layers y distintas hidden_size
class NBA_Predictor(nn.Module):
    def __init__(self, input_size, hidden_size=64, num_layers=1):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc   = nn.Linear(hidden_size, 1)

    def forward(self, x):
        # x: [Batch, seq_len, hidden_size]
        out, _ = self.lstm(x)
        last = out[:, -1, :]#último partido de la secuencia
        logits = self.fc(last).squeeze(1)  # [B]  <-- SIN sigmoid
        return logits
    


model = NBA_Predictor(input_size=input_size, hidden_size=64).to(device)

# Usamos BCEWithLogitsLoss porque el modelo devuelve logits
criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)



from sklearn.metrics import accuracy_score

def evaluate(loader):
    model.eval()
    total_loss = 0.0
    all_probs, all_targets = [], []
    with torch.no_grad():                       # usa el import global
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device).float()          # asegúrate de float 0/1
            logits = model(xb)                  # logits
            loss = criterion(logits, yb)
            total_loss += loss.item()

            probs = torch.sigmoid(logits)       # [0,1] solo para métricas
            all_probs.append(probs.detach().cpu())
            all_targets.append(yb.detach().cpu())

    probs = torch.cat(all_probs)
    targets = torch.cat(all_targets)
    pred_cls = (probs >= 0.5).float()
    acc = (pred_cls == targets).float().mean().item()
    return total_loss/len(loader), acc


epochs = 5  # empieza corto, luego ajusta
for ep in range(1, epochs+1):
    model.train()
    running = 0.0
    for xb, yb in train_loader:
        xb = xb.to(device)
        yb = yb.to(device).float()          # <- float 0/1
        optimizer.zero_grad()
        logits = model(xb)                  # logits
        loss = criterion(logits, yb)        # OK con logits
        loss.backward()
        optimizer.step()
        running += loss.item()

    val_loss, val_acc = evaluate(val_loader)
    print(f"Epoch {ep:02d} | train_loss={running/len(train_loader):.4f} | val_loss={val_loss:.4f} | val_acc={val_acc:.3f}")


test_loss, test_acc = evaluate(test_loader)
print(f"TEST | loss={test_loss:.4f} | acc={test_acc:.3f}")