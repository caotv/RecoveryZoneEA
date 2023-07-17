import MetaTrader5 as mt5
import warnings
warnings.filterwarnings('ignore')
from mt5_command import create_market_order
from mt5_command import caculate_pips_value
from mt5_command import create_market_order
from mt5_command import create_recovery_pending_order
from mt5_command import get_total_open_volume
from mt5_command import close_all_positions_and_orders
import time
import datetime


#Input parameter, need change every single run
symbol = "XAUUSD"  # Symbol of the financial instrument
tp_price = 1952
entry_price = 0 # set 0 if want to start with market order
recovery_price = 1965
direction = mt5.ORDER_TYPE_SELL #First order direction
tp_in_percent = 5 #TP in percent
max_cycle = 4 #max cycle 


# #Setup account
# login = 114490112
# password = '123456Aa@'
# server = 'Exness-MT5Trial6'

#Start MT5 client
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    exit()


# if not mt5.login(login, password, server):
#     print("initialize() failed, error code =", mt5.last_error())
#     exit()
# else:
#     print("Login success!")

#Get acccount infomation
account_info = mt5.account_info()
balance = account_info.balance
symbol_info = mt5.symbol_info(symbol)
if symbol_info is None:
    print(f"Symbol {symbol} does not exist in the Market Watch")
    exit()
# print(symbol_info)


#cycle start
current_cycle = 0
entry_price = 0
recover_direction = None
recovery_tp_price = 0

# If entry is market order
if entry_price == 0:
    symbol_ticks = mt5.symbol_info_tick(symbol)
    if symbol_ticks is None:
        print(f"Failed to get ticks for {symbol}")
        exit()

    if direction == mt5.ORDER_TYPE_BUY:
        entry_price = symbol_ticks.ask
        recovery_tp_price = recovery_price - (tp_price - entry_price)
        recover_direction = mt5.ORDER_TYPE_SELL_STOP
    elif direction == mt5.ORDER_TYPE_SELL:
        entry_price = symbol_ticks.bid
        recovery_tp_price = recovery_price + (entry_price - tp_price)
        recover_direction = mt5.ORDER_TYPE_BUY_STOP


#Caculate entry volume
rr = abs(tp_price - entry_price) / abs(entry_price - recovery_price) 
target_profit = balance * tp_in_percent / 100
tp_in_pips = abs(tp_price - entry_price) / (symbol_info.point * 10) 
volume = target_profit / (tp_in_pips * caculate_pips_value(symbol))
volume = round(volume, 2)
recovery_volume = volume*(1 + rr)/rr
print(f"YOUR RR IS: {rr}")


# Create first trade and recovery pending order
create_market_order(symbol, direction, volume, tp_price, recovery_tp_price, current_cycle)
create_recovery_pending_order(symbol, recover_direction, round(recovery_volume, 2), recovery_price, recovery_tp_price, tp_price, current_cycle)


# Loop forever 
while True:
    date_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(date_string + ":EA still runing")

    #Check if price go to tp price, close all open and order
    price_ask = mt5.symbol_info_tick(symbol).ask
    price_bid = mt5.symbol_info_tick(symbol).bid

    if direction == mt5.ORDER_TYPE_BUY:
        if price_bid >= tp_price or price_bid <= recovery_tp_price:
            close_all_positions_and_orders(symbol)
            exit()
    elif direction == mt5.ORDER_TYPE_SELL:
        if price_ask <= tp_price or price_ask >= recovery_tp_price:
            close_all_positions_and_orders(symbol)
            exit()

    #check if no pending order, create one
    if  mt5.orders_total(symbol) == 0 and mt5.positions_get(symbol) < max_cycle:
        print(date_string + ": Create recovery pending order")
        buy_volume = get_total_open_volume(mt5.POSITION_TYPE_BUY)
        sell_volume = get_total_open_volume(mt5.POSITION_TYPE_SELL)
        if buy_volume < sell_volume:
            next_order_direction = mt5.ORDER_TYPE_BUY_STOP
            next_order_volume = sell_volume*(1 + rr)/rr - buy_volume
            if direction == mt5.ORDER_TYPE_BUY:
                create_recovery_pending_order(symbol, next_order_direction, round(next_order_volume, 2), entry_price, tp_price, recovery_price, current_cycle)
            elif direction == mt5.ORDER_TYPE_SELL:
                create_recovery_pending_order(symbol, next_order_direction, round(next_order_volume, 2), recovery_price, recovery_tp_price, tp_price, current_cycle)
        elif buy_volume > sell_volume:
            next_order_direction = mt5.ORDER_TYPE_SELL_STOP
            next_order_volume = buy_volume*(1 + rr)/rr - sell_volume
            if direction == mt5.ORDER_TYPE_BUY:
                create_recovery_pending_order(symbol, next_order_direction, round(next_order_volume, 2), recovery_price, recovery_tp_price, tp_price, current_cycle)
            elif direction == mt5.ORDER_TYPE_SELL:
                create_recovery_pending_order(symbol, next_order_direction, round(next_order_volume, 2), entry_price, tp_price, recovery_tp_price, current_cycle)


    time.sleep(10)

