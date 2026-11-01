import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import pickle

df = pd.read_csv("data/metrics.csv")
cpu = df['cpu'].values
network = df['network_traffic'].values
memory = df['memory'].values
WINDOW = 3
X, y = [], []
for i in range(WINDOW, len(memory)):
    features = [
        memory[i-1],      # memory_t-1
        memory[i-2],      # memory_t-2
        memory[i-3],      # memory_t-3
        cpu[i],           # current cpu
        network[i],       # current network
    ]
    X.append(features)
    y.append(memory[i])
X = np.array(X)
y = np.array(y)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print(f"R² Score: {r2_score(y_test, y_pred):.4f}")
print(f"MAE: {mean_absolute_error(y_test, y_pred):.4f}")
print(f"RMSE: {np.sqrt(mean_squared_error(y_test, y_pred)):.4f}")
with open("ml/model_memory.pkl", "wb") as f:
    pickle.dump(model, f)

print("Model saved as ml/model_memory.pkl")