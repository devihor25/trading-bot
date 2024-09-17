from dataclasses import asdict
import MetaTrader5 as MT5
from datetime import datetime
from datetime import timedelta
import time
import pytz
import Logger
import random
import Simulator

class MT_trade_manager:
    def __init__(self, simulation):
        self.ID = 312299110
        self.PW = 'Mituongden123!'
        self.SV = 'XMGlobal-MT5 7'
        self.trading_symbol = "GOLD#"
        self.lot = 0.01
        self.price = 0.0
        self.spread = 0.0
        self.order_taken = []
        self.penalty = False
        self.simulation = simulation
        self.ID_pool = []
        self.now = (datetime.now(pytz.timezone('UTC')) + timedelta(hours=7)).strftime("%H_%M_%S-%d_%m_%Y")
        self.log_file = "position_taken_session_" + self.now + ".csv"
        self.logger = Logger.Logger(self.log_file)
        self.logger.write_log("Time,Time stamp,Position ID,Type,Price,TP,SL,Up Rate,Down Rate,Result,Profit")
        
        self.request_buy = {
        "action": MT5.TRADE_ACTION_DEAL,
        "symbol": self.trading_symbol,
        "volume": self.lot,
        "type": MT5.ORDER_TYPE_BUY,
        "price": self.price,
        "sl": self.price - 100,
        "tp": self.price + 100,
        "comment": "python script",
        "type_time": MT5.ORDER_TIME_GTC,
        "type_filling": MT5.ORDER_FILLING_IOC,
        }

        self.request_sell = {
        "action": MT5.TRADE_ACTION_DEAL,
        "symbol": self.trading_symbol,
        "volume": self.lot,
        "type": MT5.ORDER_TYPE_SELL,
        "price": self.price,
        "sl": self.price - 100,
        "tp": self.price + 100,
        "comment": "python script",
        "type_time": MT5.ORDER_TIME_GTC,
        "type_filling": MT5.ORDER_FILLING_IOC,
        }

        self.request_modify = {
        "action": MT5.TRADE_ACTION_SLTP,
        "symbol": self.trading_symbol,
        "position": 123456, #change to actual ticket
        "sl": -100,
        "tp": 100,
        "type_time": MT5.ORDER_TIME_GTC,
        "type_filling": MT5.ORDER_FILLING_RETURN,
        }

        self.request_close = {
        "action": MT5.TRADE_ACTION_DEAL,
        "symbol": self.trading_symbol,
        "volume": self.lot,
        "price": self.price,
        "type": MT5.ORDER_TYPE_SELL, #if position[0].type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
        "position": 123456,
        "type_time": MT5.ORDER_TIME_GTC,
        "comment": "python script close",
        "type_filling": MT5.ORDER_FILLING_IOC,
}

    
    def login_account(self):
        MT5.login(self.ID, self.PW, self.SV)
        account_info = MT5.account_info()
        print(account_info)
        print(MT5.terminal_info())
        print(f"\n\n===== TRADING SYMBOL [{self.trading_symbol}] =====")

    def verify_order_status(self, my_pos, history_order, pred, pred_short, simulator):
        message = ["verify_order_status"]
        #simulation part only
        if self.simulation:
            for i in range(len(self.order_taken)):
                if (self.order_taken[i]["Status"] == "Open"):
                    time_to = self.now
                    time_from = self.order_taken[i]["Time"]
                    ticks = simulator.OutputData(time_from, time_to)

                    for ind in ticks.index:
                        if (self.order_taken[i]["Type"] == "Buy"):
                            if ticks['close'][ind] + 0.4 >= self.order_taken[i]['Detail']['tp'] or ticks['high'][ind] >= self.order_taken[i]['Detail']['tp']:
                                self.order_taken[i]["Status"] = "Win-sim"
                                profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['tp'] - self.order_taken[i]['Detail']['price'])
                                self.order_taken[i]["profit"] = profit
                                self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Win-simulate,{profit}")
                                message.append(f"Simulation: Win result")
                                simulator.AddTradeFlag(time_from, time_to, 1, 1)
                                break

                            if ticks['close'][ind] + 0.4 <= self.order_taken[i]['Detail']['sl'] or ticks['low'][ind] <= self.order_taken[i]['Detail']['sl']:
                                self.order_taken[i]["Status"] = "Lose-sim"
                                profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['sl'] - self.order_taken[i]['Detail']['price'])
                                self.order_taken[i]["profit"] = profit
                                self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Lose-simulate,{profit}")
                                message.append(f"Simulation: Lose result")
                                simulator.AddTradeFlag(time_from, time_to, 1, -1)
                                break

                        if (self.order_taken[i]["Type"] == "Sell"):
                            if ticks['close'][ind] - 0.4 <= self.order_taken[i]['Detail']['tp'] or ticks['low'][ind] <= self.order_taken[i]['Detail']['tp']:
                                self.order_taken[i]["Status"] = "Win-sim"
                                profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['price'] - self.order_taken[i]['Detail']['tp'])
                                self.order_taken[i]["profit"] = profit
                                self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Win-simulate,{profit}")
                                message.append(f"Simulation: Win result")
                                simulator.AddTradeFlag(time_from, time_to, -1, 1)
                                break

                            if ticks['close'][ind] - 0.4 >= self.order_taken[i]['Detail']['sl'] or ticks['high'][ind] >= self.order_taken[i]['Detail']['sl']:
                                self.order_taken[i]["Status"] = "Lose-sim"
                                profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['price'] - self.order_taken[i]['Detail']['sl'])
                                self.order_taken[i]["profit"] = profit
                                self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Lose-simulate,{profit}")
                                message.append(f"Simulation: Lose result")
                                simulator.AddTradeFlag(time_from, time_to, -1, -1)
                                break

        tick = MT5.symbol_info_tick(self.trading_symbol)
        for i in range(len(self.order_taken)):
            if (self.order_taken[i]["Status"] == "Open"):
                if (self.order_taken[i]["Type"] == "Buy"):
                    if (pred[-1] == 0) or (pred_short[-1] == 0):
                        self.request_close["type"] = MT5.ORDER_TYPE_SELL
                        self.request_close["position"] = self.order_taken[i]["ID"]
                        self.request_close["price"] = tick.ask
                        if self.simulation:
                            time_to = self.now
                            time_from = self.order_taken[i]["Time"]
                            self.order_taken[i]["Status"] = "ClosedOnDM"
                            ticks = simulator.OutputData(time_from, time_to)
                            profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['price'] - ticks['close'].tail(1).values[0])
                            ID = self.order_taken[i]["ID"]
                            self.order_taken[i]["profit"] = profit
                            self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},CloseOnDM,{profit}")
                            message.append(f"Successfully close order {ID} due to reversing trend")
                        else:
                            result = MT5.order_send(self.request_close)
                            if result.comment == 'Request executed':
                                ID = self.order_taken[i]["ID"]
                                self.order_taken[i]["Status"] = "ClosedOnDM"
                                profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['price'] - tick.ask)
                                self.order_taken[i]["profit"] = profit
                                self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},CloseOnDM,{profit}")
                                message.append(f"Successfully close order {ID} due to reversing trend")
                
                if (self.order_taken[i]["Type"] == "Sell"):
                    if (pred[-1] == 1) or (pred_short[-1] == 1):
                        self.request_close["type"] = MT5.ORDER_TYPE_BUY
                        self.request_close["position"] = self.order_taken[i]["ID"]
                        self.request_close["price"] = tick.bid
                        if self.simulation:
                            time_to = self.now
                            time_from = self.order_taken[i]["Time"]
                            self.order_taken[i]["Status"] = "ClosedOnDM"
                            ticks = simulator.OutputData(time_from, time_to)
                            profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['price'] - ticks['close'].tail(1).values[0])
                            ID = self.order_taken[i]["ID"]
                            self.order_taken[i]["profit"] = profit
                            self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},CloseOnDM,{profit}")
                            message.append(f"Successfully close order {ID} due to reversing trend")
                        else:
                            result = MT5.order_send(self.request_close)
                            if result.comment == 'Request executed':
                                ID = self.order_taken[i]["ID"]
                                self.order_taken[i]["Status"] = "ClosedOnDM"
                                profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['price'] - tick.bid)
                                self.order_taken[i]["profit"] = profit
                                self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},CloseOnDM,{profit}")
                                message.append(f"Successfully close order {ID} due to reversing trend")

                for order in history_order:
                    if (order.position_id == self.order_taken[i]["ID"] and "sl" in order.comment and self.order_taken[i]["Status"] == "Open"):
                        self.order_taken[i]["Status"] = "Lose"
                        self.penalty = True
                        #Time,Position ID,Type,Price,TP,SL,Up Rate,Down Rate,Result,Profit
                        profit = -(self.lot/0.01) * abs((self.order_taken[i]['Detail']['price'] - self.order_taken[i]['Detail']['sl']))
                        self.order_taken[i]["profit"] = profit
                        self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Lose,{profit}")

                    elif (order.position_id == self.order_taken[i]["ID"] and "tp" in order.comment and self.order_taken[i]["Status"] == "Open"):
                        self.order_taken[i]["Status"] = "Win"
                        profit = (self.lot/0.01) * abs((self.order_taken[i]['Detail']['price'] - self.order_taken[i]['Detail']['tp']))
                        self.order_taken[i]["profit"] = profit
                        self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Win,{profit}")

        if (len(my_pos) > 1):
            message.append("2 Positions are available")
            return {"result" : False, "message" : "|".join(message)}

        if (len(self.order_taken) > 2):
            if (self.order_taken[-1]["Status"] == "Lose" and self.order_taken[-2]["Status"] == "Lose" and self.penalty == True):
                print("2 losing streak, penalty 10m")
                self.penalty = False
                #time.sleep(600)
                #return True
        return {"result" : True, "message" : "|".join(message)}

    def validate_buy(self, pred_short, pred, dataframe):
        rate = '|'.join(f"{x}" for x in list(pred[-8:]))
        short_rate = '|'.join(f"{x}" for x in list(pred_short[-8:]))
        rsi = dataframe.iloc[-1]['RSI_EMA5']
        filterList = ["0|1|0|1", "1|0|1|0"]
        for filt in filterList:
            if filt in rate:
                return {"result" : False, "message" : "validate_buy [skip - filter long]"}
            if filt in short_rate:
                return {"result" : False, "message" : "validate_buy [skip - filter short]"}

        #for i in range (1, 3):
        close_mean = dataframe.tail(3)['close'].mean()
        ema15_mean = dataframe.tail(3)['EMA15'].mean()
        #if close_mean < ema15_mean:
        #    return {"result" : False, "message" : f"validate_buy [skip - price mean [{close_mean}] below EMA15 mean {ema15_mean}]"}

        for order in self.order_taken:
            if order["Status"] == "Open" and order["Type"] == "Buy":
                return {"result" : False, "message" : "validate_buy [skip - buy position available]"}
 
        #if rsi < 40:
        #    return {"result" : False, "message" : f"validate_buy [skip - rsi {rsi} weak, waiting to get stronger]"}

        if "1|1" not in short_rate or not short_rate.endswith("1|1"):
            return {"result" : False, "message" : f"validate_buy [skip - short rate {short_rate} does not contain buy signal]"}

        if ("0|1|1" in rate and pred[-1] == 1):# and (pred_short[-2] == 1)):
            return {"result" : True, "message" : ""}
        return {"result" : False, "message" : "validate_buy [no matching condition]"}

    def validate_sell(self, pred_short, pred, dataframe):
        rate = '|'.join(f"{x}" for x in list(pred[-8:]))
        short_rate = '|'.join(f"{x}" for x in list(pred_short[-8:]))
        rsi = dataframe.iloc[-1]['RSI_EMA5']
        filterList = ["0|1|0|1", "1|0|1|0"]
        for filt in filterList:
            if filt in rate:
                return {"result" : False, "message" : "validate_buy [skip - filter long]"}
            if filt in short_rate:
                return {"result" : False, "message" : "validate_buy [skip - filter short]"}
        
        #for i in range (1, 3):
        close_mean = dataframe.tail(3)['close'].mean()
        ema15_mean = dataframe.tail(3)['EMA15'].mean()
        #if close_mean > ema15_mean:
        #    return {"result" : False, "message" : f"validate_sell [skip - price mean [{close_mean}] above EMA15 mean {ema15_mean}]]"}

        for order in self.order_taken:
            if order["Status"] == "Open" and order["Type"] == "Sell":
                return {"result" : False, "message" : "validate_sell [skip - sell position available]"}

        #if rsi > 60:
        #    return {"result" : False, "message" : f"validate_buy [skip - rsi {rsi} strong, waiting to get weaker]"}

        if "0|0" not in short_rate or not short_rate.endswith("0|0"):
            return {"result" : False, "message" : f"validate_buy [skip - short rate {short_rate} does not contain sell signal]"}

        if ("1|0|0" in rate and pred[-1] == 0):# and (pred_short[-2] == 0) and (rsi < 40)):
            return {"result" : True, "message" : ""}
        return {"result" : False, "message" : "validate_sell [no matching condition]"}

    def check_for_trade(self, pred_short, pred_proba, pred, dataframe):
        infor = MT5.symbol_info_tick(self.trading_symbol)
        # previous candle
        atr = dataframe.iloc[-1]['ATR']
        adx = dataframe.iloc[-1]['ADX']

        if self.simulation:
            buy_price = dataframe.iloc[-1]['close']
            sell_price = dataframe.iloc[-1]['close']
        else:
            buy_price = infor.ask
            sell_price = infor.bid
        self.spread = buy_price - sell_price
        if atr < 0.5:  #take trade only when ATR >= 2 dollar
            return {"result" : False, "message" : f"Small ATR {atr:.3f} skip trade"}

        if adx < 20:  #take trade only when ATR >= 2 dollar
            return {"result" : False, "message" : f"Weak ADX {adx:.3f} skip trade"}

        #if adx < 20:  #adx should be > 20 to indicate strong trend
        #    return {"result" : False, "message" : f"Small ADX {adx:.3f} skip trade"}

        if (atr < 1.5):
            guard_band = 2 #risking 2 dollars for weak trend
        else:
            guard_band = atr
        
        up_rate = '|'.join([f"{x:.3f}" for x in list(pred_proba[-10:][:, 1])])
        down_rate = '|'.join([f"{x:.3f}" for x in list(pred_proba[-10:][:, 0])])

        validate_result = self.validate_buy(pred_short, pred, dataframe)
        message = validate_result["message"]
        if (validate_result["result"]):
            #if (close < ema10):
            #    return {"result" : False, "message" : f"Enter buy but close price [{close}] < ema10 [{ema10}]"}
            self.request_buy["price"] = buy_price
            self.request_buy["sl"] = buy_price - (1.5*guard_band) # 2 dollar please
            self.request_buy["tp"] = buy_price + (2.5*guard_band)
            if self.simulation:
                ID = self.GenerateID()
                logger = Logger.Logger(f"trade_taken_simulate_{ID}.csv")
                logger.dump_dataframe(dataframe)
                self.order_taken.append({"ID" : ID, "Time" : self.now, "Status" : "Open","Type": "Buy", "Detail" : self.request_buy, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
            #print(txt)
                return {"result" : True, "message" : {"ID" : ID, "Status" : "Open","Type": "Buy", "TP": buy_price + (1.5*guard_band), "SL": buy_price - (1*guard_band)}}
            else:
                result = MT5.order_send(self.request_buy)
                #txt = f"Order status: {result}"
                if result.comment == 'Request executed':
                    logger = Logger.Logger(f"trade_taken_{result.order}.csv")
                    logger.dump_dataframe(dataframe)
                    self.order_taken.append({"ID" : result.order, "Time" : self.now, "Status" : "Open","Type": "Buy", "Detail" : self.request_buy, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
                #print(txt)
                    return {"result" : True, "message" : {"ID" : result.order, "Status" : "Open","Type": "Buy", "TP": buy_price + (1.5*guard_band), "SL": buy_price - (1*guard_band)}}
        
        validate_result = self.validate_sell(pred_short, pred, dataframe)
        message = message + "|" + validate_result["message"]
        if (validate_result["result"]):
            #if (close > ema10):
            #    return {"result" : False, "message" : f"Enter sell but close price [{close}] > ema10 [{ema10}]"}
            self.request_sell["price"] = sell_price
            self.request_sell["sl"] = sell_price + (1.5*guard_band) # 2 dollar please
            self.request_sell["tp"] = sell_price - (2.5*guard_band)
            if self.simulation:
                ID = self.GenerateID()
                logger = Logger.Logger(f"trade_taken_simulate_{ID}.csv")
                logger.dump_dataframe(dataframe)
                self.order_taken.append({"ID" : ID, "Time" : self.now, "Status" : "Open","Type": "Sell", "Detail" : self.request_sell, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
                return {"result" : True, "message" : {"ID" : ID, "Status" : "Open","Type": "Sell", "TP": sell_price - (1.5*guard_band), "SL": sell_price + (1*guard_band)}}

            else:
                result = MT5.order_send(self.request_sell)
                #txt = f"Order status: {result}"
                if result.comment == 'Request executed':
                    logger = Logger.Logger(f"trade_taken_{result.order}.csv")
                    logger.dump_dataframe(dataframe)
                    self.order_taken.append({"ID" : result.order, "Time" : self.now, "Status" : "Open","Type": "Sell", "Detail" : self.request_sell, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
                #print(txt)
                    return {"result" : True, "message" : {"ID" : result.order, "Status" : "Open","Type": "Sell", "TP": sell_price - (1.5*guard_band), "SL": sell_price + (1*guard_band)}}
        return {"result" : False, "message" : f"{message}"}
    
    def trade_summary(self, now):
        if self.simulation:
            self.now = now
        else:
            self.now = now
        win = 0
        lose = 0
        for order in self.order_taken:
            if order["Status"] == "Win":
                win += 1
            if order["Status"] == "Lose":
                lose += 1
        return {"win" : win, "lose" : lose}
    
    def GenerateID(self):
        while True:
            ID = random.randint(10000, 99999)
            if ID not in self.ID_pool:
                return ID

    def Simulation_result(self):
        print(f"Trade taken: {len(self.order_taken)}")
        win = 0
        lose = 0
        forcelose = 0
        random = 0
        profit = 0
        lost = 0
        for order in self.order_taken:
            if "Win" in order["Status"]:
                profit += order["profit"]
                win += 1
                continue
            if "Lose" in order["Status"]:
                lost += order["profit"]
                lose += 1
                continue
            if "ClosedOnDM" in order["Status"]:
                forcelose += 1
                continue
            random += 1

        total = win+lose
        if total == 0:
            total = 1
        print(f"Win {win} Lose {lose} force close {forcelose} other {random} successrate {100*win/(total)}")
        print(f"Profit {profit} lost {lost} total {profit + lost}")
        return f"Win {win} Lose {lose} force close {forcelose} other {random} successrate {100*win/(total)}\nProfit {profit} lost {lost} total {profit + lost}"
