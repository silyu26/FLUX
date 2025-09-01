# models.py
import pandas as pd
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from sklearn.preprocessing import StandardScaler

# ---------------------------
# Load and prepare data
# ---------------------------
df = pd.read_csv('../seattle-weather.csv', parse_dates=['date'])
df = df.sort_values('date').reset_index(drop=True)

# Moving average
df['ma_3day_pred'] = df['temp_max'].rolling(window=3).mean().shift(1)

# KNN training
df['target'] = df['temp_max'].shift(-1)
df_knn = df.dropna(subset=['target'])
features = ['temp_max', 'precipitation', 'wind']
X = df_knn[features]
y = df_knn['target']

split_idx = int(len(df_knn)*0.8)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

knn = KNeighborsRegressor(n_neighbors=3)
knn.fit(X_train_scaled, y_train)

# Markov Chain preparation
n_states = 3
df['state'] = pd.cut(df['temp_max'], bins=n_states, labels=[f'State_{i}' for i in range(n_states)])
transition_counts = pd.crosstab(df['state'].shift(1), df['state'], dropna=False)
transition_matrix = transition_counts.div(transition_counts.sum(axis=1), axis=0).fillna(0)

bin_edges = pd.cut(df['temp_max'], bins=n_states, retbins=True)[1]
state_midpoints = [(bin_edges[i] + bin_edges[i+1])/2 for i in range(n_states)]
state_to_temp = {f'State_{i}': state_midpoints[i] for i in range(n_states)}

# ---------------------------
# Prediction functions
# ---------------------------
def moving_average_predict(df_history):
    if len(df_history) < 3:
        return np.nan
    return df_history['temp_max'].iloc[-3:].mean()

def knn_predict(new_data):
    X_scaled = scaler.transform([new_data])
    return knn.predict(X_scaled)[0]

def predict_next_state(current_state):
    return transition_matrix.loc[current_state].idxmax()

def markov_predict(last_temp):
    last_state = pd.cut([last_temp], bins=n_states, labels=[f'State_{i}' for i in range(n_states)])[0]
    next_state = predict_next_state(last_state)
    return state_to_temp[next_state]
