import pandas as pd
from datetime import date, time, timedelta
from ta.trend import SMAIndicator

weekday_idx = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday"
}

expiries_lookup = "./expiries_folder_lookup.csv"

def atm_strike(cmp):
    '''
    '''
    atm_strike = round(cmp / 50.0) * 50
    return atm_strike

def nearest_expiry(curr_date):
    '''
    '''
    expiries = [date(2021, 1, 7), date(2021, 1, 14), date(2021, 1, 21), date(2021, 1, 28)]
    days_to_expiry = [(i - curr_date) for i in expiries]
    return expiries[days_to_expiry.index(min([j for j in days_to_expiry if j.days > 0]))]

def aggregate_df(df, delta):
    '''
    '''
    df = df.copy()
    df.index = df.datetime
    df = df.sort_index()
    df = df[~df.index.duplicated(keep='first')]
    aggregation_dict = {
         'open': 'first',
         'high': 'max',
         'low': 'min',
         'close': 'last',
         'col1': 'sum',
         'col2': 'sum'
    }
    rename_dict = {
        'open': 'open',
        'high': 'high',
        'low': 'low',
        'close': 'close',
        'col1': 'col1',
        'col2': 'col2',
    }
    agg_df = df.resample(delta).agg(aggregation_dict).rename(columns=rename_dict)
    agg_df.fillna(method="ffill", inplace=True)
    return agg_df

def intraday_ohlc(file_path, ondate, dt_format, agg_time=timedelta(minutes=1)):
    '''
    '''
    spot_df = pd.read_csv(file_path, sep=",", header=None)
    spot_df[1] = spot_df[1].astype(str)
    spot_df[2] = spot_df[2].astype(str)
    spot_df[10] = spot_df[1] + ' ' + spot_df[2]
    spot_df = spot_df.drop(columns=[0, 1, 2])
    spot_df.columns = ['open', 'high', 'low', 'close', 'col1', 'col2', 'datetime']
    spot_df = spot_df[['datetime', 'open', 'high', 'low', 'close', 'col1', 'col2']]
    spot_df['datetime'] = pd.to_datetime(spot_df['datetime'], format=dt_format)
    intraday_df = spot_df[spot_df['datetime'].dt.date==ondate][spot_df['datetime'].dt.time>=time(9, 15, 0)][spot_df['datetime'].dt.time<=time(15, 15, 0)]
    intraday_agg_df = aggregate_df(intraday_df, agg_time)
    return intraday_agg_df

def sma_crossover(cmp_df, shortTerm=9, longTerm=21):
    '''
    '''
    smaShort = SMAIndicator(close=cmp_df['close'], window=shortTerm)
    smaLong = SMAIndicator(close=cmp_df['close'], window=longTerm)
    cmp_df['sma_short'] = smaLong.sma_indicator()
    cmp_df['sma_long'] = smaShort.sma_indicator()
    cmp_df['prev_short'] = cmp_df['sma_short'].shift(1)
    cmp_df['prev_long'] = cmp_df['sma_long'].shift(1)
    if ((cmp_df.loc[longTerm + 1, 'sma_short'] <= cmp_df.loc[longTerm + 1, 'sma_long']) & (cmp_df.loc[longTerm + 1, 'prev_short'] > cmp_df.loc[longTerm + 1, 'prev_long'])):
        signal = 'SHORT'
    elif ((cmp_df.loc[longTerm + 1, 'sma_short'] >= cmp_df.loc[longTerm + 1, 'sma_long']) & (cmp_df.loc[longTerm + 1, 'prev_short'] < cmp_df.loc[longTerm + 1, 'prev_long'])):
        signal = 'LONG'
    else:
        signal = None
    return signal

def squareoff_price_time(df, trade_price, target, r2r):
    '''
    '''
    target_price = trade_price + target
    sl_price = trade_price - (r2r * target)
    for idx in df.index:
        if df.loc[idx, 'low'] <= sl_price:
            sqoff_price = sl_price
            sqoff_time = idx
            break
        elif df.loc[idx, 'high'] >= target_price:
            sqoff_price = target_price
            sqoff_time = idx
            break
        else:
            sqoff_price = trade_price
            sqoff_time = idx
            continue
    # print(op_df.shape, trade_time, op_type, trade_price, target_price, sl_price, sqoff_price)
    return sqoff_price, sqoff_time

def backtest(from_date, to_date, target, r2r, starting_capital=100000, trade_only_on=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]):
    '''
    '''
    spot_file_path = "./NIFTY_January/IntradayData_JAN2021/NIFTY.txt"
    option_dir = "./NIFTY_January/Expiry 28th January/"
    trading_days = 0
    symbol, order_type, buy_time, qtys, buy_price, sell_price, sell_time, pnls, pc_returns, trading_capital = [], [], [], [], [], [], [], [], [], []
    curr_capital = starting_capital
    for i in range((to_date - from_date).days + 1):
        curr_date = from_date + timedelta(days=i)
        day_of_week = curr_date.weekday
        if weekday_idx[day_of_week] in trade_only_on:
            agg_spot_df = intraday_ohlc(spot_file_path, curr_date, "%Y%m%d %H:%M", timedelta(minutes=1))
            if len(agg_spot_df) > 0:
                trading_days += 1
            for curr_datetime in agg_spot_df.index:
                curr_agg_spot_df = agg_spot_df.loc[curr_datetime - timedelta(minutes=23): curr_datetime, :].reset_index()
                if len(curr_agg_spot_df) < 23:
                    continue
                else:
                    cmp = agg_spot_df.loc[curr_datetime, 'open']
                    atm_strike_price = atm_strike(cmp)
                    atm_strike_ce, atm_strike_pe = atm_strike_price - 0, atm_strike_price + 0
                    signal = sma_crossover(curr_agg_spot_df)
                    if signal != None:
                        if signal == 'LONG':
                            symbol_name = 'NIFTY' + str(atm_strike_ce) + 'CE'
                        else:
                            symbol_name = 'NIFTY' + str(atm_strike_pe) + 'PE'
                        agg_opt_df = intraday_ohlc(option_dir + symbol_name + '.csv', curr_date, "%Y/%m/%d %H:%M", timedelta(minutes=1))
                        buyprice = agg_opt_df.loc[curr_datetime, 'open']
                        buyqty = int(curr_capital / (50*buyprice))
                        qtys.append(buyqty)
                        symbol.append(symbol_name)
                        order_type.append(signal)
                        buy_time.append(curr_datetime)
                        buy_price.append(buyprice)
                        sellprice, selltime = squareoff_price_time(agg_opt_df.loc[curr_datetime:, :], buyprice, target, r2r)
                        sell_price.append(sellprice)
                        sell_time.append(selltime)
                        pnl = buyqty * 50 * (sellprice - buyprice)
                        # print(symbol_name, buyprice, sellprice, curr_capital, pnl)
                        pnls.append(pnl)
                        curr_capital = curr_capital + pnl
                        trading_capital.append(curr_capital)
                        pc_returns.append(((sellprice - buyprice) / buyprice) * 100)
                    else:
                        continue
    overall_roi = ((curr_capital - starting_capital) / starting_capital) * 100
    overall_pc_profitability = ((len(list(filter(lambda x: (x >= 0), pnls)))) / len(pnls)) * 100
    if overall_roi > 0:
        print("Total trades: {}, Trading days: {}, Trades/day: {:.2f}, Profit target: {} pts, R2R: {}, ROI: {:.2f}%, Profitability: {:.2f}%".format(len(pnls), trading_days, (len(pnls)/trading_days), target, r2r, overall_roi, overall_pc_profitability))
    return None

if __name__ == '__main__':
    '''
    TODO:   Analyse results (max drawdown, roi, average trade holding time.)
            Day wise. Daily. Monthly. Plot equity curve, drawdown.
            Adjust PnL for brokerage.
    '''
    from_date = date(2021, 1, 28)
    to_date = date(2021, 1, 28)
    tgt_pts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    r2rs = [0.5, 0.667, 0.75, 1, 1.25, 1.33, 1.5, 1.75, 2, 2.25, 2.5, 3]
    for pt in tgt_pts:
        for r2r in r2rs:
            backtest(from_date, to_date, pt, r2r)
    # backtest(from_date, to_date, 2, 0.5)