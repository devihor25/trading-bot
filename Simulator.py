from datetime import datetime
from datetime import timedelta

class Simulator:
    def __init__(self, table, time_from, time_to, unit, pred_count):
        self.table = table
        self.table["trade_flag"] = 0
        self.table["trade_result"] = 0
        self.calculated_table = 0
        self.time_min = time_from.timestamp()
        self.time_max = time_to.timestamp()
        self.time_unit = unit #seconds
        self.end_flag = False
        self.pred_count = pred_count
        self.feature = ["trade_flag", "trade_result"]

        #for i in range(self.pred_count):
        #    name = "pred_" + str(i)
        #    name_short = "pred_short_" + str(i)
        #    self.table[name] = 0
        #    self.table[name_short] = 0
        #self.table.to_csv("debgugu.csv")
    
    def OutputData (self, time_from, time_to):
        start = self.find_index_greater_than(time_from.timestamp())
        end = self.find_index_greater_than(time_to.timestamp())
        if time_to.timestamp() >= self.time_max:
            self.end_flag = True
        return self.table.iloc[start:end]

    def AddTradeFlag (self, time_from, time_to, key, result, preds_up, preds_up_short, preds_down, preds_down_short):
        start = self.find_index_greater_than(time_from.timestamp())
        end = self.find_index_greater_than(time_to.timestamp())
        self.table.loc[start:end, 'trade_flag'] = key
        self.table.at[start, 'trade_result'] = result

        for i in range(len(preds_up)):
            name_up = "pred_up_" + str(i)
            name_up_short = "pred_up_short_" + str(i)
            name_down = "pred_down_" + str(i)
            name_down_short = "pred_down_short_" + str(i)
            self.table.at[start, name_up] = preds_up[i]
            self.table.at[start, name_up_short] = preds_up_short[i]
            self.table.at[start, name_down] = preds_down[i]
            self.table.at[start, name_down_short] = preds_down_short[i]
            self.feature.append(name_up)
            self.feature.append(name_up_short)
            self.feature.append(name_down)
            self.feature.append(name_down_short)
        self.feature = list(set(self.feature))
        self.feature.sort()

    def Export(self, calculator):
        self.feature = list(set(self.feature))
        self.feature.sort()
        calculator.Calculate(self.table)
        calculated_data = calculator.ExportData_simulate(self.feature)
        #calculated_data['formatted_time'] = self.table['time'].apply(self.convert_unix_time)
        return calculated_data

    def convert_unix_time(self, unix_time):
        dt = datetime.utcfromtimestamp(unix_time)
        return dt.strftime('%H-%M-%S_%d-%m-%Y')

    def find_index_greater_than(self, timestamp):
        temp = min(timestamp, self.time_max)
        result = self.table[self.table['time'] >= temp].index
        return result[0] if not result.empty else None