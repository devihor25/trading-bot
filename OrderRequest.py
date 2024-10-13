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
        self.moving_stop_loss = 3
        self.simulation = simulation
        self.ID_pool = []
        self.now = (datetime.now(pytz.timezone('UTC')) + timedelta(hours=7)).strftime("%H_%M_%S-%d_%m_%Y")
        self.log_file = "position_taken_session_" + self.now + ".csv"
        self.logger = Logger.Logger(self.log_file)
        self.logger.write_log("Time,Time stamp,Position ID,Type,Price,TP,SL,Up Rate,Down Rate,Result,Profit")
        
        # buying toggler
        self.buy_toggle_1 = False
        self.buy_toggle_2 = False
        self.toggle_counter_buy = 0

        #selling toggler
        self.sell_toggle_1 = False
        self.sell_toggle_2 = False
        self.toggle_counter_sell = 0

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

    def verify_order_status(self, my_pos, history_order, pred, pred_short, simulator, table):
        message = ["verify_order_status"]

        #simulation part only for marking order as winning or losing
        if self.simulation:
            for i in range(len(self.order_taken)):
                if (self.order_taken[i]["Status"] == "Open"):
                    time_to = self.now
                    time_from = self.order_taken[i]["Time"]
                    ticks = simulator.OutputData(time_from, time_to)

                    for ind in ticks.index:
                        if (self.order_taken[i]["Type"] == "Buy"):
                            if ticks.shape[0] > 0:
                                if ticks['close'][ind] + 0.4 >= self.order_taken[i]['Detail']['tp'] or ticks['high'][ind] + 0.4 >= self.order_taken[i]['Detail']['tp']:

                                    self.order_taken[i]["Status"] = "Win-sim"
                                    profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['tp'] - self.order_taken[i]['Detail']['price'])
                                    self.order_taken[i]["profit"] = profit
                                    self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Win-simulate,{profit}")
                                    message.append(f"Simulation: Win result")
                                    simulator.AddTradeFlag(time_from, time_to, 1, 1)
                                    logger = Logger.Logger(f"trade_taken_simulate_{self.order_taken[i]['ID']}.csv")
                                    time_from_trade = self.order_taken[i]["Time"] - timedelta(seconds=3600)
                                    time_to_trade = time_to + timedelta(seconds=3600)
                                    frame = simulator.OutputData(time_from_trade, time_to_trade)
                                    logger.dump_dataframe(frame)
                                    break

                                if ticks['close'][ind] + 0.4 <= self.order_taken[i]['Detail']['sl'] or ticks['low'][ind] + 0.4 <= self.order_taken[i]['Detail']['sl']:

                                    self.order_taken[i]["Status"] = "Lose-sim"
                                    profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['sl'] - self.order_taken[i]['Detail']['price'])
                                    self.order_taken[i]["profit"] = profit
                                    if self.order_taken[i]["option"] == "movesl":
                                        self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Lose-simulate_movesl,{profit}")
                                    else:
                                        self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Lose-simulate,{profit}")
                                    message.append(f"Simulation: Lose result")
                                    simulator.AddTradeFlag(time_from, time_to, 1, -1)
                                    logger = Logger.Logger(f"trade_taken_simulate_{self.order_taken[i]['ID']}.csv")
                                    time_from_trade = self.order_taken[i]["Time"] - timedelta(seconds=3600)
                                    time_to_trade = time_to + timedelta(seconds=3600)
                                    frame = simulator.OutputData(time_from_trade, time_to_trade)
                                    logger.dump_dataframe(frame)
                                    break

                        if (self.order_taken[i]["Type"] == "Sell"):
                            if ticks.shape[0] > 0:
                                if ticks['close'][ind] - 0.4 <= self.order_taken[i]['Detail']['tp'] or ticks['low'][ind] - 0.4 <= self.order_taken[i]['Detail']['tp']:

                                    self.order_taken[i]["Status"] = "Win-sim"
                                    profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['price'] - self.order_taken[i]['Detail']['tp'])
                                    self.order_taken[i]["profit"] = profit
                                    self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Win-simulate,{profit}")
                                    message.append(f"Simulation: Win result")
                                    simulator.AddTradeFlag(time_from, time_to, -1, 1)
                                    logger = Logger.Logger(f"trade_taken_simulate_{self.order_taken[i]['ID']}.csv")
                                    time_from_trade = self.order_taken[i]["Time"] - timedelta(seconds=3600)
                                    time_to_trade = time_to + timedelta(seconds=3600)
                                    frame = simulator.OutputData(time_from_trade, time_to_trade)
                                    logger.dump_dataframe(frame)
                                    break

                                if ticks['close'][ind] - 0.4 >= self.order_taken[i]['Detail']['sl'] or ticks['high'][ind] - 0.4 >= self.order_taken[i]['Detail']['sl']:

                                    self.order_taken[i]["Status"] = "Lose-sim"
                                    profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['price'] - self.order_taken[i]['Detail']['sl'])
                                    self.order_taken[i]["profit"] = profit
                                    if self.order_taken[i]["option"] == "movesl":
                                        self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Lose-simulate_movesl,{profit}")
                                    else:
                                        self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Lose-simulate,{profit}")
                                    message.append(f"Simulation: Lose result")
                                    simulator.AddTradeFlag(time_from, time_to, -1, -1)
                                    logger = Logger.Logger(f"trade_taken_simulate_{self.order_taken[i]['ID']}.csv")
                                    time_from_trade = self.order_taken[i]["Time"] - timedelta(seconds=3600)
                                    time_to_trade = time_to + timedelta(seconds=3600)
                                    frame = simulator.OutputData(time_from_trade, time_to_trade)
                                    logger.dump_dataframe(frame)
                                    break

        tick = MT5.symbol_info_tick(self.trading_symbol)
        for i in range(len(self.order_taken)):
            if (self.order_taken[i]["Status"] == "Open"):
                #drive_time = round((self.now.timestamp() - self.order_taken[i]["Time"].timestamp())/180)
                duration = round((self.now.timestamp() - self.order_taken[i]["Time"].timestamp())/180)
                if True:# (drive_time >= self.order_taken[i]["free_drive"]):

                    if (duration >= self.order_taken[i]["duration"]):
                        self.order_taken[i]["option"] = "close"

                    if (self.order_taken[i]["Type"] == "Buy"):
                        # adaptive stop loss
                        if self.simulation:
                            time_to = self.now
                            time_from = self.order_taken[i]["Time"]
                            ticks = simulator.OutputData(time_from, time_to)
                            if ticks.shape[0] > 2:
                                if (ticks['close'].tail(1).values[0] - self.order_taken[i]['Detail']["price"])/(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["tp"])) >= 0.8 and not self.order_taken[i]["option"] == "movesl":
                                    ID = self.order_taken[i]["ID"]
                                    message.append(f"successfully modifying sl of order {ID} from {self.order_taken[i]['Detail']['sl']} to {self.order_taken[i]['Detail']['price']}")
                                    self.order_taken[i]["option"] = "movesl"
                                    self.order_taken[i]['Detail']["sl"] = self.order_taken[i]['Detail']["price"] - 0.33*(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["sl"]))

                                if (ticks['close'].tail(1).values[0] - self.order_taken[i]['Detail']["price"]) > 2 and self.order_taken[i]["option"] !=  "check" and self.order_taken[i]["option"] !=  "movesl":
                                    self.order_taken[i]["option"] = "check"

                                if self.order_taken[i]["option"] == "check":
                                    if ticks['low'].tail(1).values[0] < ticks['EMA5'].tail(1).values[0]:
                                        self.order_taken[i]["option"] = "close"

                                if self.order_taken[i]["option"] == "movesl":
                                   if ticks['low'].tail(2).values[0] < ticks['close'].tail(2).values[1]:
                                        self.order_taken[i]["option"] = "close"

                                #if (drive_time >= self.order_taken[i]["free_drive"]):
                                #    if ticks['close'].tail(1).values[0] - self.order_taken[i]['Detail']["price"] < 0:
                                #        self.order_taken[i]["option"] = "close"

                            #if self.order_taken[i]["option"] == "movesl" and ticks['close'].tail(2).values[1] < ticks['low'].tail(2).values[0]:
                            #    self.order_taken[i]["option"] = "close"
                            #    
                        
                                #flag1 = False
                                #flag2 = False
                                #print(f"{ticks.shape[0]}")
                                #for a in range(0, min(10, ticks.shape[0]) - 1):
                                #    print(f"i={a}")
                                #    if ticks['RSI_EMA5'].tail(min(10, ticks.shape[0]) - 1).values[a] >= 65:
                                #        flag1 = True
                                #    if  ticks['Stochastic_EMA5'].tail(min(10, ticks.shape[0]) - 1).values[a] >= 70:
                                #        flag2 = True
                                #    if flag1 and flag2:
                                #        self.order_taken[i]["option"] = "close"
                        else:
                            if (tick.ask - self.order_taken[i]['Detail']["price"])/(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["tp"])) >= 0.8 and not self.order_taken[i]["option"] == "movesl":
                                self.request_modify["position"] = self.order_taken[i]["ID"]
                                self.request_modify["sl"] = self.order_taken[i]['Detail']["price"] - 0.33*(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["sl"]))
                                self.request_modify["tp"] = self.order_taken[i]['Detail']["tp"]
                                result = MT5.order_send(self.request_modify)
                                if result.comment == 'Request executed':
                                    ID = self.order_taken[i]["ID"]
                                    message.append(f"Successfully modifying sl of order {ID} from {self.order_taken[i]['Detail']['sl']} to {self.request_modify['sl']}")
                                    self.order_taken[i]["option"] = "movesl"
                                    self.order_taken[i]['Detail']["sl"] = self.order_taken[i]['Detail']["price"] - 0.33*(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["sl"]))

                            #closing winning order
                            if self.order_taken[i]["option"] == "movesl":
                                if table.iloc[-1]['close'] < table.iloc[-2]['close']:
                                    self.order_taken[i]["option"] = "close"
                            #flag1 = False
                            #flag2 = False
                            #for a in range(1, 10):
                            #    if table.iloc[-a]['RSI_EMA5'] >= 65:
                            #        flag1 = True
                            #    if  table.iloc[-a]['Stochastic_EMA5'] >= 70:
                            #        flag2 = True
                            #    if flag1 and flag2:
                            #        self.order_taken[i]["option"] = "close"

                        # closing reverse trend
                        if self.order_taken[i]["option"] == "close":# or table.iloc[-1]['close'] < table.iloc[-1]['EMA30']):(pred_short[-1] == 0): #
                            if self.simulation:
                                time_to = self.now
                                time_from = self.order_taken[i]["Time"]
                                ticks = simulator.OutputData(time_from, time_to)
                                if ticks.shape[0] > 0:
                                    self.order_taken[i]["Status"] = "ClosedOnDM"
                                    profit = (self.lot/0.01) * (ticks['close'].tail(1).values[0] - self.order_taken[i]['Detail']['price'])
                                    ID = self.order_taken[i]["ID"]
                                    self.order_taken[i]["profit"] = profit
                                    self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},CloseOnDM,{profit}")
                                    message.append(f"Successfully close order {ID} due to reversing trend")

                                    logger = Logger.Logger(f"trade_taken_simulate_{self.order_taken[i]['ID']}.csv")
                                    time_from_trade = self.order_taken[i]["Time"] - timedelta(seconds=3600)
                                    time_to_trade = time_to - timedelta(seconds=1000)
                                    frame = simulator.OutputData(time_from_trade, time_to_trade)

                            else:
                                self.request_close["type"] = MT5.ORDER_TYPE_SELL
                                self.request_close["position"] = self.order_taken[i]["ID"]
                                self.request_close["price"] = tick.ask
                                result = MT5.order_send(self.request_close)
                                if result.comment == 'Request executed':
                                    ID = self.order_taken[i]["ID"]
                                    self.order_taken[i]["Status"] = "ClosedOnDM"
                                    profit = (self.lot/0.01) * (tick.ask - self.order_taken[i]['Detail']['price'])
                                    self.order_taken[i]["profit"] = profit
                                    self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},CloseOnDM,{profit}")
                                    message.append(f"Successfully close order {ID} due to reversing trend")
                
                    if (self.order_taken[i]["Type"] == "Sell"):
                        # adaptive stop loss
                        if self.simulation:
                            time_to = self.now
                            time_from = self.order_taken[i]["Time"]
                            ticks = simulator.OutputData(time_from, time_to)
                            if ticks.shape[0] > 2:
                                if (self.order_taken[i]['Detail']["price"] - ticks['close'].tail(1).values[0])/(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["tp"])) >= 0.8 and not self.order_taken[i]["option"] == "movesl":
                                    ID = self.order_taken[i]["ID"]
                                    message.append(f"Successfully modifying sl of order {ID} from {self.order_taken[i]['Detail']['sl']} to {self.order_taken[i]['Detail']['price']}")
                                    self.order_taken[i]["option"] = "movesl"
                                    self.order_taken[i]['Detail']["sl"] = self.order_taken[i]['Detail']["price"] + 0.33*(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["sl"]))

                                if (self.order_taken[i]['Detail']["price"] - ticks['close'].tail(1).values[0]) > 2 and self.order_taken[i]["option"] != "check" and self.order_taken[i]["option"] !=  "movesl":
                                    self.order_taken[i]["option"] = "check"

                                if self.order_taken[i]["option"] == "check":
                                    if ticks['close'].tail(1).values[0] > ticks['EMA5'].tail(1).values[0]:
                                        self.order_taken[i]["option"] = "close"

                                if self.order_taken[i]["option"] == "movesl":
                                    if ticks['high'].tail(2).values[0] > ticks['close'].tail(2).values[1]:
                                        self.order_taken[i]["option"] = "close"
                                
                                #if (drive_time >= self.order_taken[i]["free_drive"]):
                                #    if self.order_taken[i]['Detail']["price"] - ticks['close'].tail(1).values[0]  < 0:
                                #        self.order_taken[i]["option"] = "close"

                            #if self.order_taken[i]["option"] == "movesl"  and ticks['close'].tail(2).values[1] > ticks['high'].tail(2).values[0]:
                            #    self.order_taken[i]["option"] = "close"

                                #flag1 = False
                                #flag2 = False
                                #for a in range(0, min(10, ticks.shape[0]) - 1):
                                #    if ticks['RSI_EMA5'].tail(min(10, ticks.shape[0]) - 1).values[a] <= 35:
                                #        flag1 = True
                                #    if  ticks['Stochastic_EMA5'].tail(min(10, ticks.shape[0]) - 1).values[a] <= 30:
                                #        flag2 = True
                                #    if flag1 and flag2:
                                #        self.order_taken[i]["option"] = "close"
                        else:
                            if (self.order_taken[i]['Detail']["price"] - tick.bid)/(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["tp"])) >= 0.8 and not self.order_taken[i]["option"] == "movesl":
                                self.request_modify["position"] = self.order_taken[i]["ID"]
                                self.request_modify["sl"] = self.order_taken[i]['Detail']["price"] + 0.33*(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["sl"]))
                                self.request_modify["tp"] = self.order_taken[i]['Detail']["tp"]
                                result = MT5.order_send(self.request_modify)
                                if result.comment == 'Request executed':
                                    ID = self.order_taken[i]["ID"]
                                    message.append(f"Successfully modifying sl of order {ID} from {self.order_taken[i]['Detail']['sl']} to {self.request_modify['sl']}")
                                    self.order_taken[i]["option"] = "movesl"
                                    self.order_taken[i]['Detail']["sl"] = self.order_taken[i]['Detail']["price"] + 0.33*(abs(self.order_taken[i]['Detail']["price"] - self.order_taken[i]['Detail']["sl"]))

                            if self.order_taken[i]["option"] == "movesl":
                                if table.iloc[-1]['close'] > table.iloc[-2]['close']:
                                    self.order_taken[i]["option"] = "close"

                            #closing winning order
                            #flag1 = False
                            #flag2 = False
                            #for a in range(1, 10):
                            #    if table.iloc[-a]['RSI_EMA5'] <= 35:
                            #        flag1 = True
                            #    if  table.iloc[-a]['Stochastic_EMA5'] <= 30:
                            #        flag2 = True
                            #    if flag1 and flag2:
                            #        self.order_taken[i]["option"] = "close"

                        # closing reverse trend
                        if self.order_taken[i]["option"] == "close":# or table.iloc[-1]['close'] > table.iloc[-1]['EMA30']:(pred_short[-1] == 1): #
                            if self.simulation:
                                time_to = self.now
                                time_from = self.order_taken[i]["Time"]
                                ticks = simulator.OutputData(time_from, time_to)
                                if ticks.shape[0] > 0:
                                    self.order_taken[i]["Status"] = "ClosedOnDM"
                                    profit = (self.lot/0.01) * (self.order_taken[i]['Detail']['price'] - ticks['close'].tail(1).values[0])
                                    ID = self.order_taken[i]["ID"]
                                    self.order_taken[i]["profit"] = profit
                                    self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},CloseOnDM,{profit}")
                                    message.append(f"Successfully close order {ID} due to reversing trend")
                                    logger = Logger.Logger(f"trade_taken_simulate_{self.order_taken[i]['ID']}.csv")
                                    time_from_trade = self.order_taken[i]["Time"] - timedelta(seconds=3600)
                                    time_to_trade = time_to - timedelta(seconds=1000)
                                    frame = simulator.OutputData(time_from_trade, time_to_trade)
                            else:
                                self.request_close["type"] = MT5.ORDER_TYPE_BUY
                                self.request_close["position"] = self.order_taken[i]["ID"]
                                self.request_close["price"] = tick.bid
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
                        if self.order_taken[i]["option"] == "movesl":
                            self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Lose_movesl,{profit}")
                        else:
                            self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Lose,{profit}")

                    elif (order.position_id == self.order_taken[i]["ID"] and "tp" in order.comment and self.order_taken[i]["Status"] == "Open"):
                        self.order_taken[i]["Status"] = "Win"
                        profit = (self.lot/0.01) * abs((self.order_taken[i]['Detail']['price'] - self.order_taken[i]['Detail']['tp']))
                        self.order_taken[i]["profit"] = profit
                        self.logger.write_log(f"{self.order_taken[i]['Time']},{self.order_taken[i]['Time'].timestamp()},{self.order_taken[i]['ID']},{self.order_taken[i]['Type']},{self.order_taken[i]['Detail']['price']},{self.order_taken[i]['Detail']['tp']},{self.order_taken[i]['Detail']['sl']},{self.order_taken[i]['Up_rate']},{self.order_taken[i]['Down_rate']},Win,{profit}")

        #if (len(my_pos) > 1):
        #    message.append("2 Positions are available")
        #    return {"result" : False, "message" : "|".join(message)}

        if (len(self.order_taken) > 2):
            if (self.order_taken[-1]["Status"] == "Lose" and self.order_taken[-2]["Status"] == "Lose" and self.penalty == True):
                print("2 losing streak, penalty 10m")
                self.penalty = False
                #time.sleep(600)
                #return True
        return {"result" : True, "message" : "|".join(message)}

    def validate_buy(self, pred_short, pred, dataframe):
        rate = '|'.join(f"{x}" for x in list(pred[-10:]))
        short_rate = '|'.join(f"{x}" for x in list(pred_short[-10:]))
        rsi = dataframe.iloc[-1]['RSI']
        stoch = dataframe.iloc[-1]['Stochastic_EMA5']
        rsi_B2 = dataframe.iloc[-3]['RSI']
        stoch_B2 = dataframe.iloc[-3]['Stochastic_EMA5']

        up_band = round(dataframe.iloc[-1]['Upper Band'], 1)
        low_band = round(dataframe.iloc[-1]['Lower Band'], 1)
        mid_band = round(dataframe.iloc[-1]['Middle Band'], 1)
        close = round(dataframe.iloc[-1]['close'], 1)

        #if rsi < 35:
        #    self.buy_toggle_1 = True
        #    self.toggle_counter_buy = 0

        #if stoch < 30:
        #    self.buy_toggle_2 = True
        #    self.toggle_counter_buy = 0

        if close <= low_band:
            self.buy_toggle_1 = True
            self.toggle_counter_buy = 0

        if self.buy_toggle_1 and close > low_band:# and (mid_band - close)/(mid_band - low_band) > 0.4:
            self.buy_toggle_2 = True
            #self.toggle_counter_buy = 0
        else:
            self.buy_toggle_2 = False
        
        if self.buy_toggle_1 or self.buy_toggle_2:
            self.toggle_counter_buy += 1
            if self.toggle_counter_buy >= 7:
                self.buy_toggle_1 = False
                self.buy_toggle_2 = False
                self.toggle_counter_buy = 0

        if self.buy_toggle_1 and self.buy_toggle_2:

            #filterList = ["0|1|0|1", "1|0|1|0", "0|0"]
            #for filt in filterList:
            #    if filt in rate:
            #        return {"result" : False, "message" : "validate_buy [skip - filter long]"}
                #if filt in short_rate:
                #    return {"result" : False, "message" : "validate_buy [skip - filter short]"}

            #for i in range (1, 3):
            #close_mean = dataframe.tail(3)['close'].mean()
            #ema15_mean = dataframe.tail(3)['EMA5'].mean()
            #if close_mean < ema15_mean:
            #    return {"result" : False, "message" : f"validate_buy [skip - price mean [{close_mean}] below EMA15 mean {ema15_mean}]"}

            for order in self.order_taken:
                if order["Status"] == "Open" and order["Type"] == "Buy":
                    return {"result" : False, "message" : "validate_buy [skip - buy position available]"}
 
            #if rsi < 40:
            #    return {"result" : False, "message" : f"validate_buy [skip - rsi {rsi} weak, waiting to get stronger]"}

            if "1|1" not in rate or not rate.endswith("1|1"):
                return {"result" : False, "message" : f"validate_buy [skip - short rate {rate} does not contain buy signal]"}

            #if ("0|1|1" in short_rate and pred_short[-1] == 1):# and (pred_short[-2] == 1)):
            #    return {"result" : True, "message" : ""}

            # reverse 
            if "1|1" not in short_rate or not short_rate.endswith("1|1"):
                return {"result" : False, "message" : f"validate_buy [skip - short rate {short_rate} does not contain buy signal]"}

            #if ("0|1|1" in short_rate and pred_short[-1] == 1):# and (pred_short[-2] == 1)):
            #    return {"result" : True, "message" : ""}   
            if 40 <= rsi <= 60 and 40 <= stoch <= 60: #> stoch_B2 and rsi < 60:
                self.buy_toggle_1 = False
                self.buy_toggle_2 = False
                self.toggle_counter_buy = 0
                return {"result" : True, "message" : ""}

        return {"result" : False, "message" : f"validate_buy [no matching condition {rsi} {rsi_B2} {stoch} {stoch_B2} {self.buy_toggle_1} {self.buy_toggle_2}]"}

    def validate_sell(self, pred_short, pred, dataframe):
        rate = '|'.join(f"{x}" for x in list(pred[-10:]))
        short_rate = '|'.join(f"{x}" for x in list(pred_short[-10:]))
        rsi = dataframe.iloc[-1]['RSI']
        stoch = dataframe.iloc[-1]['Stochastic_EMA5']
        rsi_B2 = dataframe.iloc[-3]['RSI']
        stoch_B2 = dataframe.iloc[-3]['Stochastic_EMA5']

        up_band = round(dataframe.iloc[-1]['Upper Band'], 1)
        low_band = round(dataframe.iloc[-1]['Lower Band'], 1)
        mid_band = round(dataframe.iloc[-1]['Middle Band'], 1)
        close = round(dataframe.iloc[-1]['close'], 1)

        #if rsi > 65:
        #    self.sell_toggle_1 = True
        #    self.toggle_counter_sell = 0

        #if stoch > 70:
        #    self.sell_toggle_2 = True
        #    self.toggle_counter_sell = 0

        if close >= up_band:
            self.sell_toggle_1 = True
            self.toggle_counter_sell = 0

        if self.sell_toggle_1 and close < up_band:# and (close - mid_band)/(up_band - mid_band) > 0.4:
            self.sell_toggle_2 = True
            #self.toggle_counter_sell = 0
        else:
            self.sell_toggle_2 = False
        
        if self.sell_toggle_1 or self.sell_toggle_2:
            self.toggle_counter_sell += 1
            if self.toggle_counter_sell >= 7:
                self.sell_toggle_1 = False
                self.sell_toggle_2 = False
                self.toggle_counter_sell = 0

        if self.sell_toggle_1 and self.sell_toggle_2:
            #filterList = ["0|1|0|1", "1|0|1|0", "1|1"]
            #for filt in filterList:
            #    if filt in rate:
            #        return {"result" : False, "message" : "validate_buy [skip - filter long]"}
                #if filt in short_rate:
                #    return {"result" : False, "message" : "validate_buy [skip - filter short]"}
        
            #for i in range (1, 3):
            #close_mean = dataframe.tail(3)['close'].mean()
            #ema15_mean = dataframe.tail(3)['EMA5'].mean()
            #if close_mean > ema15_mean:
            #    return {"result" : False, "message" : f"validate_sell [skip - price mean [{close_mean}] above EMA15 mean {ema15_mean}]]"}

            for order in self.order_taken:
                if order["Status"] == "Open" and order["Type"] == "Sell":
                    return {"result" : False, "message" : "validate_sell [skip - sell position available]"}

            #if rsi > 60:
            #    return {"result" : False, "message" : f"validate_buy [skip - rsi {rsi} strong, waiting to get weaker]"}

            if "0|0" not in rate or not rate.endswith("0|0"):
                return {"result" : False, "message" : f"validate_sell [skip - short rate {rate} does not contain sell signal]"}

            #if ("1|0|0" in short_rate and pred_short[-1] == 0):# and (pred_short[-2] == 0) and (rsi < 40)):
            #    return {"result" : True, "message" : ""}

            if "0|0" not in short_rate or not short_rate.endswith("0|0"):
                return {"result" : False, "message" : f"validate_buy [skip - short rate {short_rate} does not contain sell signal]"}

            #if ("1|0|0" in short_rate and pred_short[-1] == 0):# and (pred_short[-2] == 0) and (rsi < 40)):
            #    return {"result" : True, "message" : ""}

            if 40 <= rsi <= 60 and 40 <= stoch <= 60:# and rsi > 40:
                self.sell_toggle_1 = False
                self.sell_toggle_2 = False
                self.toggle_counter_sell = 0
                return {"result" : True, "message" : ""}

        return {"result" : False, "message" : f"validate_sell [no matching condition {rsi} {rsi_B2} {stoch} {stoch_B2} {self.sell_toggle_1} {self.sell_toggle_2}]"}

    def check_for_trade(self, pred_short, pred_proba, pred, dataframe):
        infor = MT5.symbol_info_tick(self.trading_symbol)
        # previous candle
        atr = dataframe.iloc[-1]['ATR']
        adx = dataframe.iloc[-1]['ADX']
        up_band = dataframe.iloc[-1]['Upper Band']
        low_band = dataframe.iloc[-1]['Lower Band']
        gap_band = abs(up_band - low_band)

        if self.simulation:
            buy_price = dataframe.iloc[-1]['close']
            sell_price = dataframe.iloc[-1]['close']
        else:
            buy_price = infor.ask
            sell_price = infor.bid
        self.spread = buy_price - sell_price
        #if atr < 0.5:  #take trade only when ATR >= 2 dollar
        #    return {"result" : False, "message" : f"Small ATR {atr:.3f} skip trade"}

        #if adx < 15:  #take trade only when ATR >= 2 dollar
        #    return {"result" : False, "message" : f"Weak ADX {adx:.3f} skip trade"}

        #if adx < 20:  #adx should be > 20 to indicate strong trend
        #    return {"result" : False, "message" : f"Small ADX {adx:.3f} skip trade"}

        #if (atr < 1):
        #    guard_band = min(5, gap_band) #risking 2 dollars for weak trend
        #    guard_band_sl = min(3, gap_band)
        #else:
        guard_band = min(5*atr, 10, gap_band)
        guard_band_sl = min(3*atr, 7, 0.6*gap_band)
        
        up_rate = '|'.join([f"{x:.3f}" for x in list(pred_proba[-10:][:, 1])])
        down_rate = '|'.join([f"{x:.3f}" for x in list(pred_proba[-10:][:, 0])])

        validate_result = self.validate_buy(pred_short, pred, dataframe)
        message = validate_result["message"]
        if (validate_result["result"]):
            #if (close < ema10):
            #    return {"result" : False, "message" : f"Enter buy but close price [{close}] < ema10 [{ema10}]"}
            self.request_buy["price"] = buy_price
            self.request_buy["sl"] = buy_price - (guard_band_sl) # 2 dollar please
            self.request_buy["tp"] = buy_price + (guard_band)
            if self.simulation:
                ID = self.GenerateID()
                #logger = Logger.Logger(f"trade_taken_simulate_{ID}.csv")
                #logger.dump_dataframe(dataframe)
                self.order_taken.append({"ID" : ID, "duration" : 100, "free_drive" : 20, "option" : None, "profit" : 0, "Time" : self.now, "Status" : "Open","Type": "Buy", "Detail" : self.request_buy, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
            #print(txt)
                return {"result" : True, "message" : {"ID" : ID, "Status" : "Open","Type": "Buy", "TP": buy_price + guard_band, "SL": buy_price - guard_band_sl, "Price": buy_price}}
            else:
                result = MT5.order_send(self.request_buy)
                #txt = f"Order status: {result}"
                if result.comment == 'Request executed':
                    logger = Logger.Logger(f"trade_taken_{result.order}.csv")
                    logger.dump_dataframe(dataframe)
                    self.order_taken.append({"ID" : result.order, "duration" : 100, "free_drive" : 20, "option" : None, "Time" : self.now, "Status" : "Open","Type": "Buy", "Detail" : self.request_buy, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
                #print(txt)
                    return {"result" : True, "message" : {"ID" : result.order, "Time" : self.now, "Status" : "Open","Type": "Buy", "TP": buy_price + guard_band, "SL": buy_price - guard_band_sl, "Price": buy_price}}
        
        validate_result = self.validate_sell(pred_short, pred, dataframe)
        message = message + "|" + validate_result["message"]
        if (validate_result["result"]):
            #if (close > ema10):
            #    return {"result" : False, "message" : f"Enter sell but close price [{close}] > ema10 [{ema10}]"}
            self.request_sell["price"] = sell_price
            self.request_sell["sl"] = sell_price + (guard_band_sl) # 2 dollar please
            self.request_sell["tp"] = sell_price - guard_band
            if self.simulation:
                ID = self.GenerateID()
                #logger = Logger.Logger(f"trade_taken_simulate_{ID}.csv")
                #logger.dump_dataframe(dataframe)
                self.order_taken.append({"ID" : ID, "duration" : 100, "free_drive" : 20, "option" : None, "profit" : 0, "Time" : self.now, "Status" : "Open", "Type": "Sell", "Detail" : self.request_sell, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
                return {"result" : True, "message" : {"ID" : ID, "Time" : self.now, "Status" : "Open","Type": "Sell", "TP": sell_price - guard_band, "SL": sell_price + guard_band_sl, "Price": sell_price}}

            else:
                result = MT5.order_send(self.request_sell)
                #txt = f"Order status: {result}"
                if result.comment == 'Request executed':
                    logger = Logger.Logger(f"trade_taken_{result.order}.csv")
                    logger.dump_dataframe(dataframe)
                    self.order_taken.append({"ID" : result.order, "duration" : 100, "free_drive" : 20, "option" : None, "Time" : self.now, "Status" : "Open", "Type": "Sell", "Detail" : self.request_sell, "Up_rate" : {up_rate}, "Down_rate" : {down_rate}})
                #print(txt)
                    return {"result" : True, "message" : {"ID" : result.order, "Status" : "Open","Type": "Sell", "TP": sell_price - guard_band, "SL": sell_price + guard_band_sl, "Price": sell_price}}
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
        Fwin = 0
        Floss = 0
        forcelose = 0
        random = 0
        profit = 0
        forceclose_profit = 0
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
                forceclose_profit += order["profit"]
                if order["profit"] > 0:
                    Fwin += 1
                else:
                    Floss += 1
                continue
            random += 1

        total = win+lose
        Ftotal = Fwin + Floss

        if total == 0:
            total = 1

        if Ftotal == 0:
            Ftotal = 1
        print(f"Win {win} Lose {lose} force close {forcelose} [Fwin {Fwin} Floss {Floss} rate {100*Fwin/Ftotal}] other {random} successrate {100*win/(total)}")
        print(f"Profit {profit} lost {lost} force close {forceclose_profit} total {profit + lost + forceclose_profit}")
        return f"Win {win} Lose {lose} force close {forcelose} other {random} successrate {100*win/(total)}\nProfit {profit} lost {lost} total {profit + lost}"
