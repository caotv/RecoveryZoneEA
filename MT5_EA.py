import MetaTrader5 as mt5
from datetime import datetime
import numpy as np
from sklearn.linear_model import LinearRegression #
import matplotlib.pyplot as plt
import mplfinance as mplf
import warnings
warnings.filterwarnings('ignore')
import pandas as pd 
from mt5_command import create_market_order
from mt5_command import linear_predict
from mt5_command import check_new_candle
import time



symbol = "XAUUSDm"  # Symbol of the financial instrument
volume = 0.1  # Volume of the trade
stop_loss = 1000  # Stop loss in pips
take_profit = 1000  # Take profit in pips


while True:
    if check_new_candle(symbol, mt5.TIMEFRAME_D1):
        # Current price
        price_ask = mt5.symbol_info_tick(symbol).ask
        price_bid = mt5.symbol_info_tick(symbol).bid

        # Predict today high&low
        predict_high_d1 = linear_predict('linear_predict_high_model.pkl')
        predict_low_d1 = linear_predict('linear_predict_low_model.pkl')

        #Gia hien tai nho hon predict low thi buy
        if price_ask < predict_low_d1 and predict_high_d1 > predict_low_d1:
            sl_price = price_ask - (predict_high_d1 - price_ask)
            create_market_order(symbol, mt5.ORDER_TYPE_BUY, predict_high_d1, sl_price)
        

        #Gia hien tai lon hon predict low thi sell
        if price_bid > predict_high_d1 and predict_high_d1 > predict_low_d1:
            sl_price = price_bid + (price_bid - predict_low_d1)
            create_market_order(symbol, mt5.ORDER_TYPE_SELL, predict_low_d1, sl_price)

        #Gia hien tai nam giua thi ben nao profit lon hon thi buy/sell
        if price_ask < predict_high_d1 and price_ask > predict_low_d1:
            if (predict_high_d1 - price_ask) > (price_ask - predict_low_d1):
                create_market_order(symbol, mt5.ORDER_TYPE_BUY, volume, predict_high_d1, predict_low_d1)
            else:
                create_market_order(symbol, mt5.ORDER_TYPE_SELL, volume, predict_low_d1, predict_high_d1)
    # update every 1 second
    print('====================')

    
    time.sleep(1)