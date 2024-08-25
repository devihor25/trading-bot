import string
import pandas as pd
import numpy as np

class IndicatorTable:
    def __init__(self):
        pd.options.mode.chained_assignment = None  # default='warn'
        self.curtain = 14
        self.roll_back = 7
        self.signal_trigger = 0.1 # percentage of price change
        self.quick_trigger = 0.2
        self.compare_period_long = -12
        self.compare_period_short = -30
        self.regression_sensitivity = 0.0
        self.key_token = "none"
        self.input_to_model = ["RSI","ATR","tick_volume","EMA5_10","EMA5_15","EMA5_20",
                               "EMA10_15","EMA10_20","EMA15_20","ADX",
                               "Slope_EMA50"]
    
    def calculate_slope(self, values):
        return np.gradient(values)[-1]

    def Calculate(self, table):
        self.table = table
        if self.key_token == "HA":
            self.table['HA_Close'] = (table['open'] + table[key_high] + table[key_low] + table['close']) / 4
            self.table['HA_Open'] = table['HA_Close']
            self.table['HA_Open'] = (table['HA_Close'].shift(1) + table['HA_Open'].shift(1)) / 2
            self.table['HA_High'] = table[[key_high, 'HA_Open', 'HA_Close']].max(axis=1)
            self.table['HA_Low'] = table[[key_low, 'HA_Open', 'HA_Close']].min(axis=1)
            key_close = 'HA_Close'
            key_high = 'HA_High'
            key_low = 'HA_Low'
            #key_open = 'HA_Open'
        else:
            key_close = 'close'
            key_high = 'high'
            key_low = 'low'
            #key_open = 'open'

        # Calculate 15-minute EMA
        self.table["EMA5"] = self.table[key_close].ewm(span=5).mean()
        self.table["EMA10"] = self.table[key_close].ewm(span=10).mean()
        self.table["EMA15"] = self.table[key_close].ewm(span=15).mean()
        self.table["EMA20"] = self.table[key_close].ewm(span=20).mean()
        self.table["EMA50"] = self.table[key_close].ewm(span=50).mean()
        self.table["Close_EMA50"] = self.table[key_close] - self.table["EMA50"]
        self.table["Slope_EMA50"] = self.table["EMA50"].rolling(window=self.curtain).apply(self.calculate_slope, raw=True)

        # EMAs cuts
        self.table["EMA5_10"] = self.table["EMA5"] - self.table["EMA10"]
        self.table["EMA5_15"] = self.table["EMA5"] - self.table["EMA15"]
        self.table["EMA5_20"] = self.table["EMA5"] - self.table["EMA20"]
        self.table["EMA10_15"] = self.table["EMA10"] - self.table["EMA15"]
        self.table["EMA10_20"] = self.table["EMA10"] - self.table["EMA20"]
        self.table["EMA15_20"] = self.table["EMA15"] - self.table["EMA20"]
        

        # Calculate RSI
        delta = self.table[key_close].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        avg_gain = pd.Series(gain).rolling(window=self.curtain).mean()
        avg_loss = pd.Series(loss).rolling(window=self.curtain).mean()
        rs = avg_gain / avg_loss
        holder = 100 - (100 / (1 + rs))

        self.table["RSI"] = pd.Series(dtype="double")
        if len(holder) == len(self.table["RSI"]):
            for i in range(len(self.table["RSI"])):
                self.table["RSI"].values[i] = holder.values[i]

        # calculate Average True Range
        self.table['TR'] = np.maximum(self.table[key_high] - self.table[key_low], 
                            np.maximum(abs(self.table[key_high] - self.table[key_close].shift(1)), 
                                       abs(self.table[key_low] - self.table[key_close].shift(1))))
        self.table['ATR'] = self.table['TR'].rolling(window=14).mean()
        self.table['RSI_EMA14'] = self.table["RSI"].ewm(span=14).mean()

        # calculate ADX
        self.table['DM_minus'] = np.where((self.table[key_low].shift(1) - self.table[key_low]) > (self.table[key_high] - self.table[key_high].shift(1)), 
                                np.maximum(self.table[key_low].shift(1) - self.table[key_low], 0), 0)
    
        # Calculate the Smoothed True Range (ATR), DM+ and DM-
        self.table['DM_plus'] = np.where((self.table[key_high] - self.table[key_high].shift(1)) > (self.table[key_low].shift(1) - self.table[key_low]), 
                               np.maximum(self.table[key_high] - self.table[key_high].shift(1), 0), 0)
        self.table['DM_minus'] = np.where((self.table[key_low].shift(1) - self.table[key_low]) > (self.table[key_high] - self.table[key_high].shift(1)), 
                                np.maximum(self.table[key_low].shift(1) - self.table[key_low], 0), 0)
        self.table['TR_smooth'] = self.table['TR'].rolling(window=self.curtain).mean()
        self.table['DM_plus_smooth'] = self.table['DM_plus'].rolling(window=self.curtain).mean()
        self.table['DM_minus_smooth'] = self.table['DM_minus'].rolling(window=self.curtain).mean()
    
        # Calculate the Directional Index (DI)
        self.table['DI_plus'] = 100 * (self.table['DM_plus_smooth'] / self.table['TR_smooth'])
        self.table['DI_minus'] = 100 * (self.table['DM_minus_smooth'] / self.table['TR_smooth'])
    
        # Calculate the Directional Movement Index (DX)
        self.table['DX'] = 100 * (abs(self.table['DI_plus'] - self.table['DI_minus']) / (self.table['DI_plus'] + self.table['DI_minus']))
    
        # Calculate the Average Directional Index (ADX)
        self.table['ADX'] = self.table['DX'].rolling(window=self.curtain).mean()

        # adding backward data

        for i in range(1, self.roll_back + 1):
            ratio = int(np.round((i*i)/2,0))
            key = '_RB_'
            #rsi_name = 'RSI' + key + str(i)
            volume_name = 'tick_volume' + key + str(i)
            EMA5_10_name = "EMA5_10" + key + str(i)
            #EMA5_15_name = "EMA5_15" + key + str(i)
            #EMA5_20_name = "EMA5_20" + key + str(i)
            EMA10_15_name = "EMA10_15" + key + str(i)
            EMA10_20_name = "EMA10_20" + key + str(i)
            #EMA15_20_name = "EMA15_20" + key + str(i)
            slope_name = "Slope_EMA50" + key + str(i)
            #adx_name = "ADX" + key + str(i)

            #self.table[rsi_name] = self.table['RSI'].shift(i*ratio)
            self.table[volume_name] = self.table['tick_volume'].shift(ratio)
            self.table[EMA5_10_name] = self.table['EMA5_10'].shift(ratio)
            #self.table[EMA5_15_name] = self.table['EMA5_15'].shift(i*ratio)
            #self.table[EMA5_20_name] = self.table['EMA5_20'].shift(i*ratio)
            self.table[EMA10_15_name] = self.table['EMA10_15'].shift(ratio)
            self.table[EMA10_20_name] = self.table['EMA10_20'].shift(ratio)
            #self.table[EMA15_20_name] = self.table['EMA15_20'].shift(i*ratio)
            self.table[slope_name] = self.table['Slope_EMA50'].shift(ratio)
            #self.table[adx_name] = self.table['ADX'].shift(i*ratio)
            
            #self.input_to_model.append(rsi_name)
            self.input_to_model.append(volume_name)
            self.input_to_model.append(EMA5_10_name)
            #self.input_to_model.append(EMA5_15_name)
            #self.input_to_model.append(EMA5_20_name)
            self.input_to_model.append(EMA10_15_name)
            self.input_to_model.append(EMA10_20_name)
            #self.input_to_model.append(EMA15_20_name)
            self.input_to_model.append(slope_name)
            #self.input_to_model.append(adx_name)

            self.input_to_model = list(set(self.input_to_model))
            #print(self.input_to_model)
        # remove first 200 rows, unused
        self.table = table.iloc[200:, :]
        #return table
    
    def ExportData(self):
        return self.table[self.input_to_model]

    def UpdatePrediction(self, y_pred, y_pred_proba):
        # manual offset
        for i in range(len(y_pred)):
            buy_prob = y_pred_proba[i][0] + self.regression_sensitivity
            neutral_prob = y_pred_proba[i][1] - 2 * self.regression_sensitivity
            sell_prob = y_pred_proba[i][2] + self.regression_sensitivity

            if ((neutral_prob > buy_prob) and (neutral_prob > sell_prob)):
                y_pred[i] = 0
                break
            elif buy_prob > sell_prob:
                y_pred[i] = 1
                break
            elif buy_prob < sell_prob:
                y_pred[i] = -1
                break
            y_pred[i] = 0
            break

        self.table.loc[:, 'Predict'] = y_pred
        self.table.loc[:, 'Predict_buy'] = y_pred_proba[:, 2]
        self.table.loc[:, 'Predict_neut'] = y_pred_proba[:, 1]
        self.table.loc[:, 'Predict_sell'] = y_pred_proba[:, 0]

    def DataManipulate(self):
        signal = pd.Series(dtype="int")
        signal = np.where((((self.table["EMA5"].shift(self.compare_period_long) - self.table["EMA5"])/self.table["EMA5"]) * 100 > self.signal_trigger),
            1,
            0,
        )

        signal = np.where((((self.table["EMA5"].shift(self.compare_period_long) - self.table["EMA5"])/self.table["EMA5"]) * 100 < -(self.signal_trigger)),
            -1,
            signal,
        )

        self.table.loc[:, 'Signal'] = signal
        return signal