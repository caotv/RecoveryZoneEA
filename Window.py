import tkinter as tk
from tkinter import ttk
from tkinter import *
import tkinter.font as font
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
from threading import *

symbol = ""
tp_price = 0
entry_price = 0 
recovery_price = 0
direction = mt5.ORDER_TYPE_BUY 
tp_in_percent = 0
max_cycle = 0
recovery_tp_price = 0
current_cycle = 0
rr = 0

# work function
def work():
    while True:
        date_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(date_string + ":EA still runing" + symbol)
        #Start MT5 client
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            exit()

        #Check if price go to tp price, close all open and order
        price_ask = mt5.symbol_info_tick(symbol).ask
        price_bid = mt5.symbol_info_tick(symbol).bid


        if direction == mt5.ORDER_TYPE_BUY:
            if price_bid >= tp_price or price_bid <= recovery_tp_price:
                close_all_positions_and_orders()
                exit()
        elif direction == mt5.ORDER_TYPE_SELL:
            if price_ask <= tp_price or price_ask >= recovery_tp_price:
                close_all_positions_and_orders()
                exit()

        #check if no pending order, create one
        if  mt5.orders_total() == 0:
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



def buy_market():
    symbol = symbol_combobox.get()  # Symbol of the financial instrument
    tp_price = float(take_profit_price_entry.get())
    entry_price = 0 # set 0 if want to start with market order
    recovery_price = float(recovery_price_entry.get())
    direction = mt5.ORDER_TYPE_BUY #First order direction
    tp_in_percent = float(target_profit_entry.get()) #TP in percent
    max_cycle = int(max_open_entry.get()) #max open position

    #Start MT5 client
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        exit()

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


    # Loop forever thread
    t1=Thread(target=work)
    t1.start() 
    


def login():
    #Setup account
    login = 0 if account_entry.get() == "" else int (account_entry.get())
    server = server_entry.get()

    #Start MT5 client
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
    else:
        print("MT5 connect success!")
        
    if login != 0 and password != "" and server != "":
        if not mt5.login(login, password, server):
            print("Login failed, error code =", mt5.last_error())
        else:
            print("Login success!")

    buy_button['state'] = "normal"
    sell_button['state'] = "normal"

    symbols=mt5.symbols_get()
    list_symbols = []
    for s in symbols:
        list_symbols.append(s.name)
    symbol_combobox['values'] = list_symbols
    symbol_combobox.current(list_symbols.index("BTCUSD"))


def validate_numeric_input(text):
    # Check if the input can be converted to a float
    try:
        float(text)
        return True
    except ValueError:
        return False
    
def validate_percent(text):
    # Check if the input can be converted to a float and is between 1 and 100
    try:
        value = int(text)
        if value < 1 or value > 100:
            return False
        return True
    except ValueError:
        return False


def sell_market():
     print("Sell market:")

window = tk.Tk()
window.geometry("270x600")
window.title("Recovery Zone EA by CyrborkTrader")

# Make the window non-resizable
# window.resizable(False, False)

# Create a Notebook widget
notebook = ttk.Notebook(window)

# Create the Main tab
main_tab = ttk.Frame(notebook)
notebook.add(main_tab, text="Main")

# Create the Setting tab
setting_tab = ttk.Frame(notebook)
notebook.add(setting_tab, text="Setting")

# Configure the column widths
main_tab.grid_columnconfigure(0, weight=1)
main_tab.grid_columnconfigure(1, weight=1)

# Configure the column widths
setting_tab.grid_columnconfigure(0, weight=1)
setting_tab.grid_columnconfigure(1, weight=1)

# Create the Symbol label
symbol_label = ttk.Label(main_tab, text="Symbol:", anchor='w')
symbol_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

# Create the Symbol combobox
symbol_combobox = ttk.Combobox(main_tab, state="readonly", width=8)
symbol_combobox.grid(row=0, column=1, padx=5, pady=5, sticky='w')

# Create labels and text input fields in a grid layout
target_profit_label = ttk.Label(main_tab, text="Target Profit Percent:", anchor='w')
target_profit_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
target_profit_entry = ttk.Entry(main_tab)
target_profit_entry.insert(END, '1')
target_profit_entry['validatecommand'] = (target_profit_entry.register(validate_percent), '%P')
target_profit_entry.grid(row=1, column=1, padx=5, pady=5, sticky='we')

max_open_label = ttk.Label(main_tab, text="Max Open Position:", anchor='w')
max_open_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')
max_open_entry = ttk.Entry(main_tab)
max_open_entry.insert(END, '5')
max_open_entry['validatecommand'] = (max_open_entry.register(validate_percent), '%P')
max_open_entry.grid(row=2, column=1, padx=5, pady=5, sticky='we')

# Create the take profit price input
take_profit_label = ttk.Label(main_tab, text="Take Profit Price:", anchor='w')
take_profit_label.grid(row=3, column=0, padx=5, pady=5, sticky='w')
take_profit_price_entry = ttk.Entry(main_tab, validate="key")
take_profit_price_entry['validatecommand'] = (take_profit_price_entry.register(validate_numeric_input), '%P')
take_profit_price_entry.grid(row=3, column=1, padx=5, pady=5, sticky='we')

# Create recovery price input
recovery_price_label = ttk.Label(main_tab, text="Recovery Price:", anchor='w')
recovery_price_label.grid(row=4, column=0, padx=5, pady=5, sticky='w')
recovery_price_entry = ttk.Entry(main_tab, validate="key")
recovery_price_entry['validatecommand'] = (recovery_price_entry.register(validate_numeric_input), '%P')
recovery_price_entry.grid(row=4, column=1, padx=5, pady=5, sticky='we')

# define font
myFont = font.Font(size=12)

# Create the Buy Market button
buy_button = Button(main_tab, text='Buy Market', bg='green', fg='#ffffff', command=buy_market)
buy_button.grid(row=5, column=0, padx=5, pady=5,  sticky='w')
buy_button['font'] = myFont
buy_button["state"] = "disabled"

# Create the Sell Market button
sell_button = Button(main_tab, text='Sell Market', bg='red', fg='#ffffff', command=sell_market)
sell_button.grid(row=5, column=1, padx=5, pady=5,  sticky='w')
sell_button['font'] = myFont
sell_button["state"] = "disabled"



# Create the Logs label
logs_label = ttk.Label(main_tab, text="Logs",  anchor='w')
logs_label['font'] = myFont
logs_label.grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky='w')

# Create the Logs text area
logs_text = tk.Text(main_tab, height=20, width=30, state='disabled')
logs_text.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky='we')


#####################################################
#Setting tab
# Create labels and text input fields in a grid layout
server_label = ttk.Label(setting_tab, text="Server:", anchor='w')
server_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')
server_entry = ttk.Entry(setting_tab)
server_entry.grid(row=0, column=1, padx=5, pady=5, sticky='we')

account_label = ttk.Label(setting_tab, text="Account:", anchor='w')
account_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')
account_entry = ttk.Entry(setting_tab)
account_entry['validatecommand'] = (account_entry.register(validate_numeric_input), '%P')
account_entry.grid(row=1, column=1, padx=5, pady=5, sticky='we')

password_label = ttk.Label(setting_tab, text="Password:", anchor='w')
password_label.grid(row=2, column=0, padx=5, pady=5, sticky='w')
password_entry = ttk.Entry(setting_tab)
password_entry.grid(row=2, column=1, padx=5, pady=5, sticky='we')

# Create the Buy Market button
login_button = Button(setting_tab, text='Login/Connect MT5', bg='green', fg='#ffffff', command=login)
login_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5,  sticky='we')
login_button['font'] = myFont


# Pack the Notebook widget
notebook.pack(fill=tk.BOTH, expand=True)

window.mainloop()