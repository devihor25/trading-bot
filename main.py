# Required libraries
from asyncio import to_thread
import MetaTrader5 as MT5
import pandas as pd
import numpy as np
import IndicatorCalculator as IC
from datetime import datetime
from datetime import timedelta
import pytz
import time
import ModelGenerator as MG
from sklearn.preprocessing import MinMaxScaler
import OrderRequest as OR
import Logger
import Simulator
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.widgets import Slider
import tkinter as tk
from tkinter import ttk

refresh_train_data = False
simulation = False

polling_time = 120 #seconds
suspend_time = 300 #seconds
trade_waiting_time = 120
train_data_output_file = "train_data.csv"
test_data_output_file = "test_data.csv"

if __name__ == "__main__":
    trade_manager = OR.MT_trade_manager(simulation)
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
    
    train_data = pd.DataFrame(MT5.copy_rates_range(trade_manager.trading_symbol, MT5.TIMEFRAME_M3, date_from_train, date_to_train))
    test_data = pd.DataFrame(MT5.copy_rates_range(trade_manager.trading_symbol, MT5.TIMEFRAME_M3, date_to_train, date_to))
    
    if (refresh_train_data):
        train_data.to_csv(train_data_output_file, sep=",")
        test_data.to_csv(test_data_output_file, sep=",")
    mod = MG.GenerateModel(refresh_train_data)
    my_model = mod["long"]
    my_model_short = mod["short"]
    simulator = None

    if simulation:
        sim_time_from = (datetime.now(utc_time) - timedelta(days =100)).replace(hour=0, minute=0, second=0, microsecond=0)
        #sim_time_to = (datetime.now(utc_time) - timedelta(days =0)).replace(hour=0, minute=0, second=0, microsecond=0)
        sim_time_to = now = datetime.now(utc_time) + timedelta(hours=7)
        table = pd.DataFrame(MT5.copy_rates_range(trade_manager.trading_symbol, MT5.TIMEFRAME_M3, sim_time_from, sim_time_to))
        simulator = Simulator.Simulator(table, sim_time_from, sim_time_to, 180, IC.IndicatorTable())
        now = sim_time_from + timedelta(days =31)
        start_point = now
        duration = sim_time_to.timestamp() - start_point.timestamp()
        counter = 0
        date_from = now - timedelta(days =30)
        polling_time = 0 #seconds
        suspend_time = 0 #seconds
        trade_waiting_time = 0

    while True:
        log_list = []
        try:
            if not simulation:
                if not MT5.initialize():
                    print("initialize() failed")
                    MT5.shutdown()

            data_manager = IC.IndicatorTable()

            if simulation:
                now = now + timedelta(seconds= 180)
                date_from = now - timedelta(days =30)
                gold_ticks = simulator.OutputData(date_from, now)
            else:
                now = datetime.now(utc_time) + timedelta(hours=7)
                date_from = (noww - timedelta(days =30)).replace(hour=0, minute=0, second=0, microsecond=0)
                gold_ticks = pd.DataFrame(MT5.copy_rates_range(trade_manager.trading_symbol, MT5.TIMEFRAME_M3, date_from, now))
            
            data_manager.Calculate(gold_ticks)

            scaler = MinMaxScaler()
            a = data_manager.ExportData()
            normalized_data = scaler.fit_transform(data_manager.ExportData())
            normalized_data_short = scaler.fit_transform(data_manager.ExportData_short())
        
            pred = my_model.predict(normalized_data)
            pred_short = my_model_short.predict(normalized_data_short)
            pred_proba = my_model.predict_proba(normalized_data)
            pred_short_proba = my_model_short.predict_proba(normalized_data_short)
            #data_manager.UpdatePrediction(pred, pred_proba, pred_short)
            my_pos = MT5.positions_get()
            history_order = MT5.history_orders_get(now - timedelta(hours=10),now)
            #data_manager.table.iloc[-1000:].to_csv("debug.csv", sep=",")

            trade_sum = trade_manager.trade_summary(now)
            pred_string = '|'.join([f"{x}" for x in list(pred[-21:-1])])
            pred_string_short = '|'.join([f"{x}" for x in list(pred_short[-21:-1])])

            up_rate = '|'.join([f"{x:.3f}" for x in list(pred_proba[-21:-1][:, 1])])
            down_rate = '|'.join([f"{x:.3f}" for x in list(pred_proba[-21:-1][:, 0])])
            up_rate_short = '|'.join([f"{x:.3f}" for x in list(pred_short_proba[-21:-1][:, 1])])
            down_rate_short = '|'.join([f"{x:.3f}" for x in list(pred_short_proba[-21:-1][:, 0])])

            #rate_string = f"long_up:{up_rate} long_down {down_rate}"
            #log_list.append(rate_string)
            #rate_string = f"short_up:{up_rate_short} short_down {down_rate_short}"
            #log_list.append(rate_string)

            if simulation:
                txt = f"{now.timestamp()} {(now).strftime('%H_%M_%S-%d_%m_%Y')}: price: {gold_ticks.iloc[-1]['close']} pred: {pred_string} pred_short: {pred_string_short} ATR: {data_manager.table.iloc[-1]['ATR']:.3f} RSI: {data_manager.table.iloc[-1]['RSI']:.3f} STOCH: {data_manager.table.iloc[-1]['Stochastic_EMA5']:.3f} BandUp: {data_manager.table.iloc[-1]['Upper Band']:.3f} BandDown: {data_manager.table.iloc[-1]['Lower Band']:.3f} Middle: {data_manager.table.iloc[-1]['Middle Band']:.3f}"
            else:
                txt = f"{now.timestamp()} {(now).strftime('%H_%M_%S-%d_%m_%Y')}: ask: {MT5.symbol_info_tick(trade_manager.trading_symbol).ask} bid:{MT5.symbol_info_tick(trade_manager.trading_symbol).bid} pred: {pred_string} pred_short: {pred_string_short} ATR: {data_manager.table.iloc[-1]['ATR']:.3f} RSI: {data_manager.table.iloc[-1]['RSI']:.3f} STOCH: {data_manager.table.iloc[-1]['Stochastic_EMA5']:.3f} BandUp: {data_manager.table.iloc[-1]['Upper Band']:.3f} BandDown: {data_manager.table.iloc[-1]['Lower Band']:.3f} Middle: {data_manager.table.iloc[-1]['Middle Band']:.3f} win: {trade_sum['win']} lose: {trade_sum['lose']}"
            log_list.append(txt)
            #print(txt)
            
            verify = trade_manager.verify_order_status(my_pos, history_order, pred[-21:-1], pred_short[-21:-1], simulator, data_manager.table.iloc[-200:-1])
            log_list.append(verify["message"])
            if (verify["result"]):#((len(my_pos) == 0) and (flag == False)):
                result = trade_manager.check_for_trade(pred_short[-21:-1], pred_proba[-21:-1], pred[-21:-1], data_manager.table.iloc[-200:-1])
                log_list.append(result["message"])
                #if (result["result"]):
                    #time.sleep(trade_waiting_time)
            else:
                txt = "2 positions available, skip"
                log_list.append(txt)
                print(txt)
        except Exception as e:
            if not simulation:
                txt = f"{now} error while executing code [{e}], sleep for {suspend_time}s"
                logger.write_log(txt)
                time.sleep(suspend_time)
        
        logger.write_log_list(log_list)
        
        time.sleep(polling_time)
        if simulation:
            counter = counter + 1
            if counter > 100:
                completion = now.timestamp() - start_point.timestamp()
                print(f"\rCompletion: {(completion/duration) * 100:.2f}%", end="")
                counter = 0
            if simulator.end_flag:
                print()
                table = simulator.Export(IC.IndicatorTable())
                summ = trade_manager.Simulation_result()
                logger.write_log(summ)
                table.to_csv("Simulation.csv")
                print("--------DONE--------")
                break
    if simulation:
        # Load the CSV file
        df = pd.read_csv('Simulation.csv').iloc[5000:, :]

        simulate_collumns = ['time', 'close', 'Lower Band', 'Upper Band', 'EMA30', 'EMA50' ]
        # Initial plot
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, gridspec_kw={'height_ratios': [3, 1, 1, 1]}, figsize=(10, 12))
        plt.subplots_adjust(left=0.1, bottom=0.25)

        # Main plot
        l1, = ax1.plot(df['time'], df['close'], label='close')
        l2, = ax1.plot(df['time'], df['Lower Band'], label='Lower Band')
        l3, = ax1.plot(df['time'], df['Upper Band'], label='Upper Band')
        l4, = ax1.plot(df['time'], df['EMA30'], label='EMA30')
        l5, = ax1.plot(df['time'], df['EMA50'], label='EMA50')
        ln, = ax1.plot(df['time'], df['EMA20'], label='EMA20')

        ax1.set_xlabel('time')
        ax1.set_ylabel('Values')
        ax1.set_title('Line Chart with Multiple Lines')
        ax1.legend()
        ax1.grid(True)

        # RSI plot
        l6, = ax2.plot(df['time'], df['RSI'], label='RSI', color='purple')
        l9, = ax2.plot(df['time'], df['Stochastic_EMA5'], label='Stochastic', color='orange')  # Added line for stoch
        ax2.axhline(y=70, color='r')
        ax2.axhline(y=30, color='r')
        ax2.set_xlabel('time')
        ax2.set_ylabel('RSI')
        ax2.legend()

        # Trade flag plot
        l7, = ax3.plot(df['time'], df['trade_flag'], label='trade_flag', color='green')
        ax3.set_xlabel('time')
        ax3.set_ylabel('Trade Flag')
        ax3.legend()

        # Trade result plot
        l8, = ax4.plot(df['time'], df['trade_result'], label='trade_result', color='blue')
        ax4.set_xlabel('time')
        ax4.set_ylabel('Trade Result')
        ax4.legend()

        # Slider axes
        axcolor = 'lightgoldenrodyellow'
        ax_start = plt.axes([0.1, 0.1, 0.65, 0.03], facecolor=axcolor)
        ax_end = plt.axes([0.1, 0.15, 0.65, 0.03], facecolor=axcolor)

        # Sliders
        start_slider = Slider(ax_start, 'Start', 0, len(df)-1, valinit=0, valstep=1)
        end_slider = Slider(ax_end, 'End', 0, len(df)-1, valinit=len(df)-1, valstep=1)

        # Update function
        def update(val):
            start = int(start_slider.val)
            end = int(end_slider.val)
            l1.set_xdata(df['time'][start:end])
            l1.set_ydata(df['close'][start:end])
            l2.set_xdata(df['time'][start:end])
            l2.set_ydata(df['Lower Band'][start:end])
            l3.set_xdata(df['time'][start:end])
            l3.set_ydata(df['Upper Band'][start:end])
            l4.set_xdata(df['time'][start:end])
            l4.set_ydata(df['EMA30'][start:end])
            l5.set_xdata(df['time'][start:end])
            l5.set_ydata(df['EMA50'][start:end])
            ln.set_xdata(df['time'][start:end])
            ln.set_ydata(df['EMA20'][start:end])
            l6.set_xdata(df['time'][start:end])
            l6.set_ydata(df['RSI'][start:end])
            l9.set_xdata(df['time'][start:end])  # Update for stoch
            l9.set_ydata(df['Stochastic_EMA5'][start:end])  # Update for stoch
            l7.set_xdata(df['time'][start:end])
            l7.set_ydata(df['trade_flag'][start:end])
            l8.set_xdata(df['time'][start:end])
            l8.set_ydata(df['trade_result'][start:end])
            ax1.relim()
            ax1.autoscale_view()
            ax2.relim()
            ax2.autoscale_view()
            ax3.relim()
            ax3.autoscale_view()
            ax4.relim()
            ax4.autoscale_view()
            fig.canvas.draw_idle()

        # Connect sliders to update function
        start_slider.on_changed(update)
        end_slider.on_changed(update)

        plt.show()

        

        # List of columns to plot
        columns_to_plot = [
            'ADX', 'ADX_RB_13', 'ADX_RB_21', 'ADX_RB_34', 'ADX_RB_8', 'EMA15_30', 'EMA15_30_RB_13', 
            'EMA15_30_RB_21', 'EMA15_30_RB_34', 'EMA15_30_RB_8', 'EMA20_100_RB_short_13', 
            'EMA20_100_RB_short_3', 'EMA20_100_RB_short_5', 'EMA20_100_RB_short_8', 'Rolling_EMA30_RB_short_13', 
            'Rolling_EMA30_RB_short_3', 'Rolling_EMA30_RB_short_5', 'Rolling_EMA30_RB_short_8', 'RSI', 
            'RSI_EMA5', 'RSI_RB_short_3', 'RSI_RB_short_5', 'RSI_RB_8', 'RSI_RB_13',
           'RSI_RB_21', 'RSI_RB_34', 'RSI_RB_short_8', 'RSI_RB_short_13', 'Stochastic_EMA5', 'Stochastic_EMA5_RB_short_3','Stochastic_EMA5_RB_short_5', 'Stochastic_EMA5_RB_8', 'Stochastic_EMA5_RB_13', 'Stochastic_EMA5_RB_21', 
            'Stochastic_EMA5_RB_34', 'Stochastic_EMA5_RB_short_13', 
             'Stochastic_EMA5_RB_short_8'
        ]

        df[columns_to_plot] = df[columns_to_plot].shift(1)
        df.to_csv("Simulation_shift.csv")
        # Filter the rows where trade_result is 1 or -1
        filtered_df = df[df['trade_result'].isin([1, -1])]

        # Create a new column that combines trade_flag and trade_result
        filtered_df['trade_combination'] = filtered_df['trade_flag'].astype(str) + '_' + filtered_df['trade_result'].astype(str)

        


        # Calculate the number of rows needed
        num_columns = 5
        num_rows = (len(columns_to_plot) + num_columns - 1) // num_columns

        filtered_df[columns_to_plot] = filtered_df[columns_to_plot].shift(1)
        # Create a figure and axis for each column
        fig, axes = plt.subplots(nrows=num_rows, ncols=num_columns, figsize=(18, num_rows * 5))

        # Flatten the axes array for easy iteration
        axes = axes.flatten()

        # Plot each column
        for ax, column in zip(axes, columns_to_plot):
            filtered_df.boxplot(column=column, by='trade_combination', ax=ax)
            ax.set_title(f'Box plot of {column}')
            ax.set_ylabel(column)
            ax.set_xlabel('trade_combination')

        # Remove the automatic titles to avoid overlap
        plt.suptitle('')

        # Adjust layout to prevent overlap
        plt.tight_layout()

        # Create a Tkinter window
        root = tk.Tk()
        root.title("Scrollable Box Plots")

        # Create a canvas and a vertical scrollbar
        canvas = tk.Canvas(root)
        scroll_y = tk.Scrollbar(root, orient="vertical", command=canvas.yview)

        # Create a frame to hold the plots
        frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor='nw')

        # Add the canvas and scrollbar to the window
        canvas.configure(yscrollcommand=scroll_y.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        # Add the figure to the Tkinter window
        canvas_fig = FigureCanvasTkAgg(fig, master=frame)
        canvas_fig.draw()
        canvas_fig.get_tk_widget().pack(side="top", fill="both", expand=True)

        # Update the scroll region
        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        # Start the Tkinter main loop
        root.mainloop()

