import MetaTrader5 as MT5
from datetime import datetime
from datetime import timedelta
import time
import pytz
import Logger

class MT_trade_manager:
    def __init__(self):
        self.ID = 312299110
        self.PW = 'Mituongden123!'
        self.SV = 'XMGlobal-MT5 7'
        self.trading_symbol = "GOLD#"
        self.lot = 0.01
        self.price = 0.0
        self.spread = 0.0
        self.order_taken = []
        self.penalty = False
        
        self.now = (datetime.now(pytz.timezone('UTC')) + timedelta(hours=7)).strftime("%H_%M_%S-%d_%m_%Y")
        self.log_file = "position_taken_session_" + self.now + ".csv"
        self.logger = Logger.Logger(self.log_file)
        self.logger.write_log("Time,Position ID,Type,Price,TP,SL,Buy Rate,Neutral Rate,Sell Rate,Result,Profit")
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
    
    def login_account(self):
        MT5.login(self.ID, self.PW, self.SV)
        account_info = MT5.account_info()
        print(account_info)
        print(MT5.terminal_info())
        print(f"\n\n===== TRADING SYMBOL [{self.trading_symbol}] =====")

    def verify_order_status(self, my_pos, history_order):
        for i in range(len(self.order_taken)):
            if (self.order_taken[i]["Status"] == "Open"):
                for order in history_order:
                    if (order.position_id == self.order_taken[i]["ID"] and "sl" in order.comment and self.order_taken[i]["Status"] == "Open"):
                        self.order_taken[i]["Status"] = "Lose"
                        self.penalty = True
                        #Time,Position ID,Type,Price,TP,SL,Buy Rate,Neutral Rate,Sell Rate,Result,Profit
                        profit = -(self.lot/0.01) * abs((self.order_taken[i]['Detail']['price'] - self.order_taken[i]['Detail']['sl']))
                        self.logger.write_log(f"{self.now},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Buy_rate']},{self.order_taken[i]['Neutral_rate']},{self.order_taken[i]['Sell_rate']},Lose,{profit}")

                    elif (order.position_id == self.order_taken[i]["ID"] and "tp" in order.comment and self.order_taken[i]["Status"] == "Open"):
                        self.order_taken[i]["Status"] = "Win"
                        profit = (self.lot/0.01) * abs((self.order_taken[i]['Detail']['price'] - self.order_taken[i]['Detail']['tp']))
                        self.logger.write_log(f"{self.now},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Buy_rate']},{self.order_taken[i]['Neutral_rate']},{self.order_taken[i]['Sell_rate']},Win,{profit}")

        if (len(my_pos) > 1):
            return False
        if (len(self.order_taken) > 2):
            if (self.order_taken[-1]["Status"] == "Lose" and self.order_taken[-2]["Status"] == "Lose" and self.penalty == True):
                print("2 losing streak, penalty 10m")
                self.penalty = False
                #time.sleep(600)
                #return True
        return True

    def validate_buy(self, pred, close, EMA50):
        rate = '|'.join(f"{x}" for x in list(pred[-6:]))
        filterList = ["1|0|1", "1|0|0|1"]
        for filt in filterList:
            if filt in rate:
                return False
        if ("0|1|1" in rate[:-2]):
            if ((pred[-2] == 1) and (pred[-3] == 1) and (close > EMA50)):
                return True
        return False

    def validate_sell(self, pred, close, EMA50):
        rate = '|'.join(f"{x}" for x in list(pred[-6:]))
        filterList = ["0|1|0", "0|1|1|0"]
        for filt in filterList:
            if filt in rate:
                return False
        if ("1|0|0" in rate[:-2]):
            if ((pred[-2] == 0) and (pred[-3] == 0) and (close < EMA50)):
                return True
        return False

    def check_for_trade(self, pred, pred_proba, dataframe):
        infor = MT5.symbol_info_tick(self.trading_symbol)
        # previous candle
        offset = dataframe.iloc[-2]['ATR']
        close = dataframe.iloc[-2]['close']
        EMA50 = dataframe.iloc[-2]['EMA50']
        #adx = dataframe.iloc[-2]['ADX']

        buy_price = infor.ask
        sell_price = infor.bid
        self.spread = buy_price - sell_price
        #if offset < 1:  #take trade only when ATR >= 2 dollar
        #    return {"result" : False, "message" : f"Small ATR {offset:.3f} skip trade"}

        #if adx < 20:  #adx should be > 20 to indicate strong trend
        #    return {"result" : False, "message" : f"Small ADX {adx:.3f} skip trade"}

        if (self.spread > offset):
            guard_band = 2*self.spread
        else:
            guard_band = offset
        
        up_rate = '|'.join([f"{x:.3f}" for x in list(pred_proba[-10:][:, 1])])
        down_rate = '|'.join([f"{x:.3f}" for x in list(pred_proba[-10:][:, 0])])

        if (self.validate_buy(pred, close, EMA50)):
            #if (close < ema10):
            #    return {"result" : False, "message" : f"Enter buy but close price [{close}] < ema10 [{ema10}]"}
            self.request_buy["price"] = buy_price
            self.request_buy["sl"] = buy_price - (1*guard_band) # 2 dollar please
            self.request_buy["tp"] = buy_price + (1.5*guard_band)
            result = MT5.order_send(self.request_buy)
            txt = f"Order status: {result}"
            if result.comment == 'Request executed':
                self.order_taken.append({"ID" : result.order, "Status" : "Open","Type": "Buy", "Detail" : self.request_buy, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
            print(txt)
            return {"result" : True, "message" : {"ID" : result.order, "Status" : "Open","Type": "Buy", "Detail" : self.request_buy, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}}}

        elif (self.validate_sell(pred, close, EMA50)):
            #if (close > ema10):
            #    return {"result" : False, "message" : f"Enter sell but close price [{close}] > ema10 [{ema10}]"}
            self.request_sell["price"] = sell_price
            self.request_sell["sl"] = sell_price + (1*guard_band) # 2 dollar please
            self.request_sell["tp"] = sell_price - (1.5*guard_band)
            result = MT5.order_send(self.request_sell)
            txt = f"Order status: {result}"
            if result.comment == 'Request executed':
                self.order_taken.append({"ID" : result.order, "Status" : "Open","Type": "Sell", "Detail" : self.request_sell, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
            print(txt)
            return {"result" : True, "message" : {"ID" : result.order, "Status" : "Open","Type": "Sell", "Detail" : self.request_buy, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}}}
        return {"result" : False, "message" : "No trade"}
    
    def trade_summary(self):
        self.now = (datetime.now(pytz.timezone('UTC')) + timedelta(hours=7)).strftime("%H_%M_%S-%d_%m_%Y")
        win = 0
        lose = 0
        for order in self.order_taken:
            if order["Status"] == "Win":
                win += 1
            if order["Status"] == "Lose":
                lose += 1
        return {"win" : win, "lose" : lose}
