from datetime import datetime
from datetime import timedelta

class Simulator:
    def __init__(self, table, time_from, time_to, unit, calculator):
        self.table = table
        self.table["trade_flag"] = 0
        self.table["trade_result"] = 0
        
        calculator.Calculate(self.table)
        self.table = calculator.ExportData_simulate()
        self.calculated_table = 0
        self.time_min = time_from.timestamp()
        self.time_max = time_to.timestamp()
        self.time_unit = unit #seconds
        self.end_flag = False
        #self.table.to_csv("debgugu.csv")
    
    def OutputData (self, time_from, time_to):
        start = self.find_index_greater_than(time_from.timestamp())
        end = self.find_index_greater_than(time_to.timestamp())
        if time_to.timestamp() >= self.time_max:
            self.end_flag = True
        return self.table.iloc[start:end]

    def AddTradeFlag (self, time_from, time_to, key, result):
        start = self.find_index_greater_than(time_from.timestamp())
        end = self.find_index_greater_than(time_to.timestamp())
        self.table.loc[start:end, 'trade_flag'] = key
        self.table.at[start, 'trade_result'] = result

    def Export(self, calculator):
        #calculator.Calculate(self.table)
        #calculated_data = calculator.ExportData_simulate()
        self.table['formatted_time'] = self.table['time'].apply(self.convert_unix_time)
        return self.table

    def convert_unix_time(self, unix_time):
        dt = datetime.utcfromtimestamp(unix_time)
        return dt.strftime('%H-%M-%S_%d-%m-%Y')

    def find_index_greater_than(self, timestamp):
        temp = min(timestamp, self.time_max)
        result = self.table[self.table['time'] >= temp].index
        return result[0] if not result.empty else None