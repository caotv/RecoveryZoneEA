from ta.volume import on_balance_volume
from ta.momentum import rsi
from ta.volatility import bollinger_mavg, bollinger_lband, bollinger_hband
from ta.trend import ema_indicator

def generate_feature(df):
    df = df.astype('float')
    df['close_open_diff'] = df['close'] - df['open']
    df['high_close_diff'] = df['high'] - df['close']
    df['low_close_diff'] = df['low'] - df['close']
    df['high_open_diff'] = df['high'] - df['open']
    df['low_open_diff'] = df['low'] - df['open']
    df['high_low_diff'] = df['high'] - df['low']

    df['open_diff_pct_p1'] = df['open'].pct_change(1)
    df['open_diff_pct_p2'] = df['open'].pct_change(2)
    df['open_diff_pct_p3'] = df['open'].pct_change(3)
    df['open_diff_pct_p7'] = df['open'].pct_change(7)

    df['close_p1'] = df['close'].shift(1)
    df['close_p2'] = df['close'].shift(2)
    df['close_p3'] = df['close'].shift(3)
    df['close_p4'] = df['close'].shift(4)
    df['close_p5'] = df['close'].shift(5)

    df['low_p1'] = df['low'].shift(1)
    df['low_p2'] = df['low'].shift(2)
    df['low_p3'] = df['low'].shift(3)
    df['low_p4'] = df['low'].shift(4)
    df['low_p5'] = df['low'].shift(5)

    df['high_p1'] = df['high'].shift(1)
    df['high_p2'] = df['high'].shift(2)
    df['high_p3'] = df['high'].shift(3)
    df['high_p4'] = df['high'].shift(4)
    df['high_p5'] = df['high'].shift(5)

    df['high_t1'] = df['high'].shift(-1)
    df['low_t1'] = df['low'].shift(-1)

    df['close_diff_p1'] = df['close'].diff(1)
    df['close_diff_p2'] = df['close'].diff(2)
    df['close_diff_p3'] = df['close'].diff(3)
    df['close_diff_p7'] = df['close'].diff(7)

    df['close_diff_pct_p1'] = df['close'].pct_change(1)
    df['close_diff_pct_p2'] = df['close'].pct_change(2)
    df['close_diff_pct_p3'] = df['close'].pct_change(3)
    df['close_diff_pct_p7'] = df['close'].pct_change(7)

    df['volume_p1'] = df['volume'].shift(1)
    df['volume_p2'] = df['volume'].shift(2)
    df['volume_p3'] = df['volume'].shift(3)
    df['volume_p7'] = df['volume'].shift(7)

    df['volume_diff_p1'] = df['volume'].diff(1)
    df['volume_diff_p2'] = df['volume'].diff(2)
    df['volume_diff_p3'] = df['volume'].diff(3)
    df['volume_diff_p7'] = df['volume'].diff(7)

    df['volume_diff_pct_p1'] = df['volume'].pct_change(1)
    df['volume_diff_pct_p2'] = df['volume'].pct_change(2)
    df['volume_diff_pct_p3'] = df['volume'].pct_change(3)
    df['volume_diff_pct_p7'] = df['volume'].pct_change(7)

    df['on_balance_volume'] = on_balance_volume(df['close'], df['volume'])

    df['rsi_window_14'] = rsi(df['close'])
    df['rsi_window_7'] = rsi(df['close'], 7)

    df['bollinger_mavg_20'] = bollinger_mavg(df['close'])
    df['bollinger_lband_20'] = bollinger_lband(df['close'])
    df['bollinger_hband_20'] = bollinger_hband(df['close'])

    df['ema_12'] = ema_indicator(df['close'])
    df['ema_26'] = ema_indicator(df['close'], 26)

    df['close_open_diff_pct'] = (df['close'] / df['open'] - 1) * 100
    df['high_close_diff_pct'] = (df['high'] / df['close'] - 1) * 100
    df['low_close_diff_pct'] = (df['low'] / df['close'] - 1) * 100
    df['high_open_diff_pct'] = (df['high'] / df['open'] - 1) * 100
    df['low_open_diff_pct'] = (df['low'] / df['open'] - 1) * 100
    df['high_low_diff_pct'] = (df['high'] / df['low'] - 1) * 100

    df['on_balance_volume_diff_pct'] = (df['on_balance_volume'] / df['volume']) * 100
    df['close_bollinger_mavg_20_diff_pct'] = (df['close'] / df['bollinger_mavg_20']) * 100
    df['close_bollinger_lband_20_diff_pct'] = (df['close'] / df['bollinger_lband_20']) * 100
    df['close_bollinger_hband_20_diff_pct'] = (df['close'] / df['bollinger_hband_20']) * 100

    df['close_ema_12_diff_pct'] = (df['close'] / df['ema_12']) * 100
    df['close_ema_26_diff_pct'] = (df['close'] / df['ema_26']) * 100
    return df