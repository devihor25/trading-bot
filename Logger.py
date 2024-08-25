import os
import pandas as pd

class Logger:
    def __init__(self, filename):
        self.directory = os.getcwd()
        self.log_path = os.path.join(os.path.dirname(self.directory), "logs")
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)

        self.file_name = os.path.join(self.log_path, filename)
    
    def write_log_list(self, message):
        file = open(self.file_name, "a")  # append mode
        for line in message:
            file.write(f"{line}\n")
        file.close()

    def write_log(self, message):
        file = open(self.file_name, "a")  # append mode
        file.write(f"{message}\n")
        file.close()
    
    def dump_dataframe(self, dataframe):
        dataframe.to_csv(self.file_name, sep=",")