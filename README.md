# Trading Bot with MetaTrader 5 Integration

This project is a trading bot designed to interact with the MetaTrader 5 (MT5) platform. It uses machine learning models for trade predictions, simulates trading scenarios, and manages trades in real-time or simulated environments.

## Features
- **MetaTrader 5 Integration**: Fetches historical and real-time trading data.
- **Indicator Calculation**: Computes technical indicators for trading decisions.
- **Machine Learning Models**: Predicts market trends using pre-trained models, I tried using plenty of models, the main and reliable for this project is Linear Regression model. This model will output 3 flags: Buy, Sell and do nothing.
- **Trade Management**: Places, verifies, and manages trades.
- **Simulation Mode**: Simulates trading scenarios for backtesting strategies. Please use this feature actively, as it will help you to understand your strategy and how to improve it.
- **Logging**: Logs trading activities and simulation results for analysis. Graph of everything is logged so you can check it again.
- **Automation**: This project has automated Github actions so you can run it on your connected devices/bot. It can open a position with stop-loss and take-profit levels, and it will close the position when the price reaches the stop-loss or take-profit level. It will also close the position if the price goes against you for a certain period of time.
- There are plent of different models sitting on different branches, which was not merged as they are still in development and testing phase. You can check them out and see if they are working for you.

## Project Structure
- `main.py`: The entry point of the application. Manages the overall workflow, including data fetching, model predictions, and trade execution.
- `Logger.py`: Handles logging of trading activities and simulation results.
- `IndicatorCalculator.py`: Calculates technical indicators for trading decisions.
- `OrderRequest.py`: Manages trade requests and account interactions with MT5.
- `ModelGenerator.py`: Generates and loads machine learning models for predictions.
- `Simulator.py`: Simulates trading scenarios for backtesting.

## Requirements
- Python 3.8+
- MetaTrader 5 Python API
- pandas
- numpy
- scikit-learn
- pytz

Install the required libraries using: pip install MetaTrader5 pandas numpy scikit-learn pytz

## Usage
1. **Setup MetaTrader 5**:
   - Ensure MetaTrader 5 is installed and configured.
   - Update the `trading_symbol` in `OrderRequest.py` to match your trading symbol.

2. **Run the Bot**:
   - To start the bot, execute `main.py`:

3. **Simulation Mode**:
   - Set `simulation = True` in `main.py` to enable simulation mode.
   - Adjust simulation parameters as needed.

4. **Training Data**:
   - Set `refresh_train_data = True` in `main.py` to refresh training data and save it to CSV files.

## Configuration
- **Polling Time**: Adjust `polling_time` in `main.py` to set the interval for fetching new data.
- **Suspend Time**: Modify `suspend_time` to set the sleep duration in case of errors.
- **Trade Waiting Time**: Set `trade_waiting_time` to control the delay between trades.

## Logging
Logs are saved in files named `log_session_<timestamp>.txt`. These logs include:
- Predictions
- Trade summaries
- Errors and warnings

## Simulation Results
When in simulation mode, results are saved to `Simulation.csv` for further analysis.

## License
This project is for leisure and educational purposes. You are free to use and modify it. The provided account is a demo account on MT5 platform, and you can create your own demo account for testing.

## Contact
Feel free to contact via email for any questions or suggestions: bincu008@gmail.com