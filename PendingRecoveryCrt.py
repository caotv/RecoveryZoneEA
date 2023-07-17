import MetaTrader5 as mt5
import warnings
warnings.filterwarnings('ignore')
from mt5_command import create_recovery_pending_order
from mt5_command import get_total_open_volume
from mt5_command import caculate_pips_value
import time

#Input parameter, need change every single run
symbol = "XAUUSD"  # Symbol of the financial instrument
tp_price = 1911
entry_price = 1908.721 # set 0 if want to start with market order
recovery_price = 1908
recovery_tp_price = 1905.721
direction = mt5.ORDER_TYPE_BUY #First order direction
tp_in_percent = 1 #TP in percent
max_cycle = 5 #max cycle 
current_cycle = 1

#Setup account
login = 114490112
password = '123456Aa@'
server = 'Exness-MT5Trial6'

#Start MT5 client
if not mt5.initialize():
    print("initialize() failed, error code =", mt5.last_error())
    exit()


if not mt5.login(login, password, server):
    print("initialize() failed, error code =", mt5.last_error())
    exit()
else:
    print("Login success!")


#Get acccount infomation
account_info = mt5.account_info()
balance = account_info.balance
symbol_info = mt5.symbol_info(symbol)
if symbol_info is None:
    print(f"Symbol {symbol} does not exist in the Market Watch")
    exit()
# print(symbol_info)

#Caculate entry volume
rr = abs(tp_price - entry_price) / abs(entry_price - recovery_price) 
target_profit = balance * tp_in_percent / 100
tp_in_pips = abs(tp_price - entry_price) / (symbol_info.point * 10) 
volume = target_profit / (tp_in_pips * caculate_pips_value(symbol))
volume = round(volume, 2)
recovery_volume = volume * (entry_price - recovery_price) / (tp_price - entry_price) 


orders = mt5.orders_get()
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
