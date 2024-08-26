# Required libraries
import pandas as pd
import numpy as np
import yfinance as yf
import pickle
import IndicatorCalculator as IC
#import tensorflow as tf
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler
import Logger


sample_path = "manipulate.csv"
train_data_output_file = "train_data.csv"
test_data_output_file = "test_data.csv"

def GenerateModel(refresh_train_data):
    train_data = pd.read_csv(train_data_output_file)
    test_data = pd.read_csv(test_data_output_file)
    test_data_manager = IC.IndicatorTable()
    train_data_manager = IC.IndicatorTable()

    test_data_manager.Calculate(test_data)
    train_data_manager.Calculate(train_data)
    
    test_data_output = test_data_manager.DataManipulate()
    train_data_output = train_data_manager.DataManipulate()
    

    # ======================== generating Logistic Regression Model ========================
    
    scaler = MinMaxScaler()
    train_data_trasform = scaler.fit_transform(train_data_manager.ExportData())
    test_data_transform = scaler.fit_transform(test_data_manager.ExportData())

    # Train logistic regression model
    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000)
    model.fit(train_data_trasform, train_data_output)

    # Evaluate model
    if (refresh_train_data):
        y_pred = model.predict(test_data_transform)
        accuracy = (y_pred == test_data_output).mean()
        print(f"ACCURACY: {accuracy}")
        y_pred_proba = model.predict_proba(test_data_transform)

        test_data_manager.UpdatePrediction(y_pred, y_pred_proba)
    
        output = test_data_manager.table.iloc[-3000:, :]
        logger = Logger.Logger(sample_path)
        logger.dump_dataframe(output)
    #output.to_csv(sample_path, sep=",")

    return model
    # ======================== generating LSTM Model ========================
    features = train_data[IC.input_to_model].values
    # Normalize features to [0, 1] range
    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(features)
    
    sequence_length = 30
    X, y = [], []
    for i in range(len(scaled_features) - sequence_length):
        X.append(scaled_features[i : i + sequence_length])
        y.append(scaled_features[i + sequence_length])

    X, y = np.array(X), np.array(y)

    # repeat for test data
    features = test_data[IC.input_to_model].values
    # Normalize features to [0, 1] range
    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(features)
    
    sequence_length = 30
    X_test, y_test = [], []
    for i in range(len(scaled_features) - sequence_length):
        X_test.append(scaled_features[i : i + sequence_length])
        y_test.append(scaled_features[i + sequence_length])

    X, y = np.array(X), np.array(y)

    model_LSTM = tf.keras.Sequential([
    tf.keras.layers.LSTM(64, activation='relu', input_shape=(X.shape[1], X.shape[2])),
    tf.keras.layers.Dense(1)  # Output dimension matches the number of features (buy, sell, do nothing)
    ])

    model_LSTM.compile(optimizer='adam', loss='mean_squared_error')
    
    model_LSTM.fit(X, y, shuffle = False, epochs=50, batch_size=32)
    loss = model.evaluate(X_test, y_test)
    print(f"LSTM test Loss: {loss:.4f}")


    test_data['Singal_predict_regress'] = y_pred
    test_data.to_csv(sample_path, sep=",")


