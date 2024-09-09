import string
import pandas as pd
import numpy as np

class IndicatorTable:
    def __init__(self):
        #pd.options.mode.chained_assignment = None  # default='warn'
        self.remove_rows = 200
        self.curtain = 14
        self.roll_back = 7
        self.signal_trigger = 0.05 # percentage of price change
        self.quick_trigger = 0.2
        self.compare_period_long = 20
        self.compare_period_short = 2
        self.regression_sensitivity = 0.0
        self.key_token = "none"
        self.input_to_model = ["RSI_EMA5","Stochastic","ADX",#"ADX",
                               "EMA15_30","Close_EMA200"]#,"EMA10_20"]
                               #"EMA10_15","EMA10_20","EMA15_20",
                               #"Slope_EMA20"]
    
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
        #self.table["EMA5"] = self.table[key_close].ewm(span=5).mean()
        #self.table["EMA10"] = self.table[key_close].ewm(span=10).mean()
        self.table["EMA15"] = self.table[key_close].ewm(span=15).mean()
        #self.table["EMA20"] = self.table[key_close].ewm(span=20).mean()
        self.table["EMA30"] = self.table[key_close].ewm(span=30).mean()
        self.table["EMA50"] = self.table[key_close].ewm(span=50).mean()
        self.table["EMA100"] = self.table[key_close].ewm(span=100).mean()
        self.table["EMA200"] = self.table[key_close].ewm(span=200).mean()
        self.table["Close_EMA200"] = self.table[key_close] - self.table["EMA200"]
        #self.table["Slope_EMA20"] = self.table["EMA20"].rolling(window=self.curtain).apply(self.calculate_slope, raw=True)

        # EMAs cuts
        #self.table["EMA5_10"] = self.table["EMA5"] - self.table["EMA10"]
        #self.table["EMA5_15"] = self.table["EMA5"] - self.table["EMA15"]
        #self.table["EMA5_20"] = self.table["EMA5"] - self.table["EMA20"]
        #self.table["EMA10_15"] = self.table["EMA10"] - self.table["EMA15"]
        #self.table["EMA10_20"] = self.table["EMA10"] - self.table["EMA30"]
        #self.table["EMA15_20"] = self.table["EMA15"] - self.table["EMA20"]
        self.table["EMA15_30"] = self.table["EMA15"] - self.table["EMA50"]
        #self.table["EMA20_30"] = self.table["EMA20"] - self.table["EMA30"]

            # calulateStochastic Oscillator
        self.table['LowestLow'] = self.table[key_low].rolling(window=self.curtain).min()
        self.table['HighestHigh'] = self.table[key_high].rolling(window=self.curtain).max()
        self.table['Stochastic'] = 100 * (self.table[key_close] - self.table['LowestLow']) / (self.table['HighestHigh'] - self.table['LowestLow'])

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
        self.table['RSI_EMA5'] = self.table["RSI"].ewm(span=10).mean()
        

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
        #scaler = MinMaxScaler()
        #self.table['Smooth_price'] = self.nadaraya_watson_estimator().reshape(-1, 1).flatten()
        #self.table['Smooth_price_upper'] = self.table['Smooth_price'] * 1.0015
        #self.table['Smooth_price_lower'] = self.table['Smooth_price'] * 0.9985
        #self.table["Slope_Smooth_price"] = self.table["Smooth_price"].rolling(window=5).apply(self.calculate_slope, raw=True)

        #self.table['Close_NW_upper'] = self.table['close'] - self.table['Smooth_price_upper']
        #self.table['Close_NW_lower'] = self.table['close'] - self.table['Smooth_price_lower']
        # adding backward data
        self.AddBackWard(True)
        
            #print(self.input_to_model)
        #return table
    #def nadaraya_watson_estimator(self, bandwidth=15):
    #    prices_array = np.array(self.table['close'])
    #    x = np.arange(len(prices_array)).reshape(-1, 1)
    #    kr = KernelReg(prices_array, x, 'c', 'lc', bw=[bandwidth])
    #    smoothed_prices, _ = kr.fit(x)
    #    return smoothed_prices

    def AddBackWard(self, enable):
        # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181]
        rolling = [2, 3, 5, 8, 13]
        for i in rolling:
            #ratio = int(np.round((i*i)/2,0))
            ratio = 3*i
            key = '_RB_'
            rsi_name = 'RSI_EMA5' + key + str(i)
            #atr_name = 'ATR' + key + str(i)
            stoch_name = "Stochastic" + key + str(i)
            #nw_up_name = 'Close_NW_upper' + key + str(i)
            #nw_low_name = 'Close_NW_lower' + key + str(i)
            #volume_name = 'tick_volume' + key + str(i)
            #EMA5_10_name = "EMA5_10" + key + str(i)
            #EMA5_15_name = "EMA5_15" + key + str(i)
            #EMA5_20_name = "EMA5_20" + key + str(i)
            #EMA10_15_name = "EMA10_15" + key + str(i)
            #EMA10_20_name = "EMA10_20" + key + str(i)
            #EMA15_20_name = "EMA15_20" + key + str(i)
            #Close_EMA50_name = "Close_EMA50" + key + str(i)
            rolling_EMA50 = "Rolling_EMA50" + key + str(i)
            EMA15_30_name = "EMA15_30" + key + str(i)
            #EMA20_30_name = "EMA20_30" + key + str(i)
            #slope_name = "Slope_EMA20" + key + str(i)
            adx_name = "ADX" + key + str(i)
            
            if (enable):
                self.table[rsi_name] = self.table['RSI_EMA5'].shift(ratio)
                self.table[adx_name] = self.table['ADX'].shift(ratio)
                self.table[stoch_name] = self.table['Stochastic'].shift(ratio)
                #self.table[nw_up_name] = self.table['Close_NW_upper'].shift(ratio)
                #self.table[nw_low_name] = self.table['Close_NW_lower'].shift(ratio)
                #self.table[volume_name] = self.table['tick_volume'].shift(ratio)
                #self.table[EMA5_10_name] = self.table['EMA5_10'].shift(ratio)
                #self.table[EMA5_15_name] = self.table['EMA5_15'].shift(i*ratio)
                #self.table[EMA5_20_name] = self.table['EMA5_20'].shift(i*ratio)
                #self.table[EMA10_15_name] = self.table['EMA10_15'].shift(ratio)
                #self.table[EMA10_20_name] = self.table['EMA10_20'].shift(ratio)
                #self.table[EMA15_20_name] = self.table['EMA15_20'].shift(ratio)
                #self.table[Close_EMA50_name] = self.table['Close_EMA50'].shift(ratio)
                self.table[rolling_EMA50] = (self.table['EMA50'] - self.table['EMA50'].shift(ratio))/self.table['EMA50'].shift(ratio)
                self.table[EMA15_30_name] = self.table['EMA15_30'].shift(ratio)
                #self.table[EMA20_30_name] = self.table['EMA20_30'].shift(ratio)
                #self.table[slope_name] = self.table['Slope_EMA20'].shift(ratio)
                #self.table[adx_name] = self.table['ADX'].shift(i*ratio)
            
            self.input_to_model.append(rsi_name)
            self.input_to_model.append(adx_name)
            self.input_to_model.append(stoch_name)
            #self.input_to_model.append(nw_up_name)
            #self.input_to_model.append(nw_low_name)
            #self.input_to_model.append(volume_name)
            #self.input_to_model.append(EMA5_10_name)
            #self.input_to_model.append(EMA5_15_name)
            #self.input_to_model.append(EMA5_20_name)
            #self.input_to_model.append(EMA10_15_name)
            #self.input_to_model.append(EMA10_20_name)
            #self.input_to_model.append(EMA15_20_name)
            #self.input_to_model.append(Close_EMA50_name)
            self.input_to_model.append(rolling_EMA50)
            self.input_to_model.append(EMA15_30_name)
            #self.input_to_model.append(EMA20_30_name)
            #self.input_to_model.append(slope_name)
            #self.input_to_model.append(adx_name)

        self.input_to_model = list(set(self.input_to_model))
    
    def ReuseTable(self, table):
        self.table = table
        self.AddBackWard(False)
    def ExportData(self):
        
        # remove first 200 rows, unused
        self.table = self.table.iloc[self.remove_rows:, :]
        return self.table[self.input_to_model]

    def UpdatePrediction(self, y_pred, y_pred_proba):
        # manual offset
        for i in range(len(y_pred)):
            up_prob = y_pred_proba[i][0] + self.regression_sensitivity
            down_prob = y_pred_proba[i][1] - self.regression_sensitivity

            if up_prob > down_prob:
                y_pred[i] = 1
                break
            elif up_prob < down_prob:
                y_pred[i] = 0
                break
            break

        self.table.loc[:, 'Predict'] = y_pred
        self.table.loc[:, 'Predict_down'] = y_pred_proba[:, 0]
        self.table.loc[:, 'Predict_up'] = y_pred_proba[:, 1]

    # AI generated
    def DataManipulate(self):
        key = "EMA30"
        signal = pd.Series(0, dtype="int64", index=self.table.index)
        for i in range(self.table.shape[0] - self.compare_period_long - self.compare_period_short):
            signal_value = -1
            for j in range(1, self.compare_period_long):
                shifter_min_1 = min(i + j, self.table.shape[0] - 1)
                if ((self.table[key].iloc[shifter_min_1] - self.table[key].iloc[i]) / self.table[key].iloc[i]) * 100 > self.signal_trigger:
                    if all(self.table[key].iloc[min(i + k, self.table.shape[0] - 1)] > self.table[key].iloc[i] for k in range(1, min(self.compare_period_short, self.table.shape[0] - i - 1))):
                        signal_value = 1
                        break
                elif ((self.table[key].iloc[shifter_min_1] - self.table[key].iloc[i]) / self.table[key].iloc[i]) * 100 < -self.signal_trigger:
                    if all(self.table[key].iloc[min(i + k, self.table.shape[0] - 1)] < self.table[key].iloc[i] for k in range(1, min(self.compare_period_short, self.table.shape[0] - i - 1))):
                        signal_value = 0
                        break
            if signal_value == -1 and i > 0:
                signal_value = signal[i - 1]
            signal[i] = int(signal_value)

        self.table['Bias'] = signal
        return signal[self.remove_rows:]
    
    def ReuseSignal(self):
        return self.table['Bias'][self.remove_rows:]