# Required libraries
import pandas as pd
import numpy as np
import yfinance as yf
import pickle
from datetime import datetime
import IndicatorCalculator as IC
#import tensorflow as tf
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
import Logger


sample_path = "manipulate.csv"
train_data_output_file = "train_data.csv"
test_data_output_file = "test_data.csv"
cluster_file = "cluster.csv"

train_data_processed_output_file = "train_data_processed.csv"
test_data_processed_output_file = "test_data_processed.csv"

def GenerateModel(refresh_train_data):
    
    test_data_manager = IC.IndicatorTable()
    train_data_manager = IC.IndicatorTable()
    if (refresh_train_data):
        train_data = pd.read_csv(train_data_output_file)
        test_data = pd.read_csv(test_data_output_file)

        test_data_manager.Calculate(test_data)
        train_data_manager.Calculate(train_data)
    
        test_data_output = test_data_manager.DataManipulate()
        train_data_output = train_data_manager.DataManipulate()

        test_data_output_short = test_data_manager.DataManipulate_short()
        train_data_output_short = train_data_manager.DataManipulate_short()

        logger = Logger.Logger(train_data_processed_output_file)
        logger.dump_dataframe(train_data_manager.table)

        logger = Logger.Logger(test_data_processed_output_file)
        logger.dump_dataframe(test_data_manager.table)

    else:
        test_data_table = pd.read_csv(test_data_processed_output_file)
        train_data_table = pd.read_csv(train_data_processed_output_file)
        
        test_data_manager.ReuseTable(test_data_table)
        train_data_manager.ReuseTable(train_data_table)
        
        test_data_output = test_data_manager.ReuseSignal()
        train_data_output = train_data_manager.ReuseSignal()

        test_data_output_short = test_data_manager.ReuseSignal_short()
        train_data_output_short = train_data_manager.ReuseSignal_short()

    # ======================== generating Logistic Regression Model ========================
    
    scaler = MinMaxScaler()
    train_data_trasform = scaler.fit_transform(train_data_manager.ExportData())
    train_data_trasform_short = scaler.fit_transform(train_data_manager.ExportData_short())
    test_data_transform = scaler.fit_transform(test_data_manager.ExportData())
    test_data_transform_short = scaler.fit_transform(test_data_manager.ExportData_short())

    # Train logistic regression model
    model = LogisticRegression(multi_class='ovr', solver='lbfgs', max_iter=1000)
    model_short = LogisticRegression(multi_class='ovr', solver='lbfgs', max_iter=1000)
    model.fit(train_data_trasform, train_data_output)
    model_short.fit(train_data_trasform_short, train_data_output_short)

    # Evaluate model
    
    y_pred = model.predict(test_data_transform)
    y_pred_short = model_short.predict(test_data_transform_short)
    accuracy = (y_pred == test_data_output).mean()
    accuracy_short = (y_pred_short == test_data_output_short).mean()
    print(f"ACCURACY: {accuracy}")
    print(f"ACCURACY_short: {accuracy_short}")
    if (refresh_train_data):
        y_pred_proba = model.predict_proba(test_data_transform)

        test_data_manager.UpdatePrediction(y_pred, y_pred_proba, y_pred_short)
    
        output = test_data_manager.table.iloc[-1000:, :]
        output['formatted_time'] = output['time'].apply(convert_unix_time)
        logger = Logger.Logger(sample_path)
        logger.dump_dataframe(output)
    #output.to_csv(sample_path, sep=",")

    return {"long" : model, "short" : model_short}
def GenerateCluster(count):
    test_data_manager = IC.IndicatorTable()
    train_data = pd.read_csv(cluster_file)
    test_data_manager.ReuseTable(train_data)
    output = test_data_manager.table['trade_result']
    scaler = StandardScaler()
    test_data_manager.Init_cluster_MG(count)
    scaled_features = scaler.fit_transform(test_data_manager.ExportData_cluster_MG())
    # K-Means clustering
    model = LogisticRegression(multi_class='ovr', solver='lbfgs', max_iter=1000)
    model.fit(scaled_features, output)
    return model

def convert_unix_time(unix_time):
    dt = datetime.utcfromtimestamp(unix_time)
    return dt.strftime('%H:%M:%S')
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


