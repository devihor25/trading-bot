from datetime import datetime
from datetime import timedelta
from operator import index

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
        #actual = '|'.join(f"{x}" for x in list(self.table['time'][-5:]))
        #print(f"start: {start} end: {end} max: {self.time_max} actual max:{actual} from: {time_from.timestamp()} to: {time_to.timestamp()}")
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
        temp = int(min(timestamp, self.time_max))
        #print(f"stamp {timestamp} max: {self.time_max} temp: {temp}")
        #mask = (self.table['time'] >= temp) & (self.table['time'].shift(1) < temp)
        result = self.table[self.table['time'] >= temp].index 
        #result1 = self.table[mask].index
        return result[0] - 200 if not result.empty else None