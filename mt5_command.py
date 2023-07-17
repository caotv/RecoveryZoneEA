import MetaTrader5 as mt5
import pandas as pd 
from sklearn.linear_model import LinearRegression #
import pickle
from feature_transform import generate_feature
from datetime import datetime
import time

def caculate_pips_value(symbol):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} does not exist in the Market Watch")
        return 0
    contract_size = symbol_info.trade_contract_size
    point  = symbol_info.point
    profit_currency = symbol_info.currency_profit
    pipsvalue = pipsvalue = point * 10 * contract_size

    #if profit currency is not USD, get exchange rate then exchange to USD
    if profit_currency != "USD":
        exchange_symbol = profit_currency + "USD"
        exchange_symbol_info = mt5.symbol_info(exchange_symbol)
        if exchange_symbol_info is None:
            exchange_symbol = "USD" + profit_currency 
            exchange_symbol_info = mt5.symbol_info(exchange_symbol)
            exchange_price = mt5.symbol_info_tick(exchange_symbol).bid
            pipsvalue = pipsvalue / exchange_price
        else:
            exchange_price = mt5.symbol_info_tick(exchange_symbol).bid
            print(exchange_price)
            pipsvalue = exchange_price * pipsvalue

    return pipsvalue


def create_market_order(symbol, direction, volume, take_profit, stop_loss,  cycle_number):
    # Connect to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return False

    # Check if the symbol is available for trading
    if not mt5.symbol_select(symbol, True):
        print("Symbol", symbol, "is not found, error code =", mt5.last_error())
        mt5.shutdown()
        return False

    price = 0
    if direction == mt5.ORDER_TYPE_SELL:
        price = mt5.symbol_info_tick(symbol).bid
    elif direction == mt5.ORDER_TYPE_BUY:
        price = mt5.symbol_info_tick(symbol).ask
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type":  direction,
        "price": price,
        "tp": float(take_profit),
        "sl": float(stop_loss),
        "comment": f"RecoveryZone EA: cycle {cycle_number}",
    }
    # print(request)

    result = mt5.order_send(request)
    if result is None:
        print("Send order return None")
        return False
    # Check the result
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Failed to create a market order, error code: ", result)
        return False
    else:
        print("Market order created successfully!")
        return True
    

def create_recovery_pending_order(symbol, recover_direction, volume, price, take_profit, stop_loss, cycle_number):
    # Connect to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return False

    # Check if the symbol is available for trading
    if not mt5.symbol_select(symbol, True):
        print("Symbol", symbol, "is not found, error code =", mt5.last_error())
        mt5.shutdown()
        return False
    
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Symbol {symbol} does not exist in the Market Watch")
        return 0

    take_profit = round(take_profit, symbol_info.digits)
    price = round(price, symbol_info.digits)

    request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": symbol,  
        "volume": volume, 
        "type": recover_direction,
        "price": float(price),  
        "sl": 0.0,  
        "tp": float(take_profit),
        "sl": float(stop_loss),
        "comment": f"RecoveryZone EA: cycle {cycle_number}",
        "type_time": mt5.ORDER_TIME_GTC, 
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    # print(request)


    result = mt5.order_send(request)
    if result is None:
        print("Send order return None")
        return False
    # Check the result
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Failed to create a pending order, error code =", result.retcode)
        return False
    else:
        print("Pending order created successfully!")
        return True



def linear_predict(model_name, symbol, day_not_closed = 0):
    # Connect to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return
    
    #load model with model name
    loaded_model = pickle.load(open(model_name, 'rb'))
    #OHLC data get
    ohlc_data = pd.DataFrame(mt5.copy_rates_from_pos(symbol, 
                                                mt5.TIMEFRAME_D1, 
                                                day_not_closed,
                                                50))
    ohlc_data['time'] = pd.to_datetime(ohlc_data['time'], unit='s')

    ohlc_data.drop('real_volume', axis=1, inplace=True)
    ohlc_data.rename(columns={'tick_volume': 'volume'}, inplace=True)
    ohlc_data.set_index('time', inplace=True)
    ohlc_data = generate_feature(ohlc_data)
    ohlc_data = ohlc_data.drop(ohlc_data.index[:25])
    ohlc_data = ohlc_data.drop(['high_t1', 'low_t1'], axis=1)

    ohlc_data['predict_value'] = loaded_model.predict(ohlc_data)
    
    return float(ohlc_data.tail(1)['predict_value'].values)


def check_new_candle(symbol, time_frame):
    # Connect to the MetaTrader 5 terminal
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return False

    # Check if the symbol is available for trading
    if not mt5.symbol_select(symbol, True):
        print("Symbol", symbol, "is not found, error code =", mt5.last_error())
        mt5.shutdown()
        return False


    # Get the latest two bars
    rates = pd.DataFrame(mt5.copy_rates_from_pos(symbol, time_frame, 0, 1))
    open_time = int(rates.tail(1)['time'])
    current_time = int(time.time())
    # print('open_time', open_time)
    # print('current_time', current_time)
    if open_time + 1 == current_time:
        return True

    return False


def close_all_positions_and_orders():
    # Connect to MetaTrader 5 terminal
    print("Close all open positions and orders!")
    if not mt5.initialize():
        print("Failed to initialize MetaTrader 5")
        return

    # Close positions
    positions = mt5.positions_get()
    for position in positions:
        result = mt5.PositionClose(position.ticket)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close position {position.ticket}: {result.comment}")

    # Close orders
    orders = mt5.orders_get()
    for order in orders:
        result = mt5.OrderClose(order.ticket)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close order {order.ticket}: {result.comment}")



def get_total_open_volume(direction):
    # Connect to MetaTrader 5 terminal
    if not mt5.initialize():
        print("Failed to initialize MetaTrader 5")
        return

    # Request all open positions
    positions = mt5.positions_get()

    # Calculate total buy volume
    total_buy_volume = sum(position.volume for position in positions if position.type == direction)

    # Disconnect from MetaTrader 5 terminal
    mt5.shutdown()

    # Return the total buy volume
    return total_buy_volume
    

def close_all_positions_and_orders():
    # Connect to MetaTrader 5 terminal
    if not mt5.initialize():
        print("Failed to initialize MetaTrader 5")
        return

    # Close all open positions
    positions = mt5.positions_get()
    for position in positions:
        result = close_position(position)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close position {position.ticket}. Error code: {result.retcode}, Error description: {result.comment}")
        else:
            print(f"Position {position.ticket} closed successfully")


    # Close all pending orders
    orders = mt5.orders_get()
    for order in orders:
        # Close the order
        result = close_order(order)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close order {order.ticket}. Error code: {result.retcode}, Error description: {result.comment}")
        else:
            print(f"Order {order.ticket} closed successfully")


def close_position(position):

    tick = mt5.symbol_info_tick(position.symbol)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": position.ticket,
        "symbol": position.symbol,
        "type": mt5.ORDER_TYPE_BUY if position.type == 1 else mt5.ORDER_TYPE_SELL,
        "price": tick.ask if position.type == 1 else tick.bid,  
        "deviation": 20,
        "magic": 100,
        "comment": "python script close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    return result


def close_order(order):
    request = {
        "action": mt5.TRADE_ACTION_REMOVE,
        "order": order.ticket,
    }
    result = mt5.order_send(request)
    return result




