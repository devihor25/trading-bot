# Required libraries
import MetaTrader5 as MT5
import pandas as pd
import numpy as np
import IndicatorCalculator as IC
from datetime import datetime
from datetime import timedelta
import pytz
import os
import pickle
import time
import ModelGenerator as MG
from sklearn.preprocessing import MinMaxScaler
import OrderRequest as OR
import Logger

generate_model = False
one_minute_model = "my_trained_model_1m_normalized.pkl"
polling_time = 180 #seconds
suspend_time = 300 #seconds
trade_waiting_time = 300

if __name__ == "__main__":
    trade_manager = OR.MT_trade_manager()
    if MT5.initialize():
        trade_manager.login_account()
    else:
        print("initialize() failed")
        MT5.shutdown()
        
    utc_time = pytz.timezone('UTC')
    # stupid server is UTC + 3!
    noww = datetime.now(utc_time) + timedelta(hours=3)
    date_ = noww - timedelta(days =5)
    date_from = date_.replace() #(hour=0, minute=0, second=0, microsecond=0)
    date_to = noww
    
    date_from_train = noww - timedelta(days = 100)
    date_to_train = noww - timedelta(days = 32)
    
    log_file_name = "log_session_" + (noww + timedelta(hours=4)).strftime("%H_%M_%S-%d_%m_%Y") + ".txt"
    logger = Logger.Logger(log_file_name)

    if (generate_model):
        train_data = pd.DataFrame(MT5.copy_rates_range(trade_manager.trading_symbol, MT5.TIMEFRAME_M3, date_from_train, date_to_train))
        test_data = pd.DataFrame(MT5.copy_rates_range(trade_manager.trading_symbol, MT5.TIMEFRAME_M3, date_to_train, date_to))
        MG.GenerateModel(train_data, test_data)
    
    with open(one_minute_model, 'rb') as file:
        my_model = pickle.load(file)
        
    while True:
        log_list = []
        try:
            if not MT5.initialize():
                print("initialize() failed")
                MT5.shutdown()

            now = datetime.now(utc_time) + timedelta(hours=3)
            date_from = (noww - timedelta(days =60)).replace(hour=0, minute=0, second=0, microsecond=0)

            data_manager = IC.IndicatorTable()
            gold_ticks = pd.DataFrame(MT5.copy_rates_range(trade_manager.trading_symbol, MT5.TIMEFRAME_M3, date_from, now))
            data_manager.Calculate(gold_ticks)

            scaler = MinMaxScaler()
            normalized_data = scaler.fit_transform(data_manager.ExportData())
            
        
            pred = my_model.predict(normalized_data)[-50:]
            pred_proba = my_model.predict_proba(normalized_data)[-50:]

            my_pos = MT5.positions_get()
            history_order = MT5.history_orders_get(now - timedelta(hours=3),now)
            
            trade_sum = trade_manager.trade_summary()
            pred_string = '|'.join([f"{x}" for x in list(pred[-10:])])
            txt = f"{(now + timedelta(hours=4)).strftime('%H_%M_%S-%d_%m_%Y')}: ask: {MT5.symbol_info_tick(trade_manager.trading_symbol).ask} bid:{MT5.symbol_info_tick(trade_manager.trading_symbol).bid} prediction: {pred_string} ATR: {data_manager.table.iloc[-1]['ATR']:.3f} win: {trade_sum['win']} lose: {trade_sum['lose']}"
            log_list.append(txt)
            #print(txt)
        
            if (trade_manager.verify_order_status(my_pos, history_order)):#((len(my_pos) == 0) and (flag == False)):
                result = trade_manager.check_for_trade(pred, pred_proba, data_manager.table.tail(50))
                log_list.append(result["message"])
                if (result["result"]):
                    time.sleep(trade_waiting_time)
            else:
                txt = "Position available, skip"
                log_list.append(txt)
                print(txt)
        except:
            txt = f"time: {now} error while executing code, sleep for {suspend_time}s"
            logger.write_log(txt)
            time.sleep(suspend_time)
        
        logger.write_log_list(log_list)
        
        time.sleep(polling_time)
