#!/usr/bin/env python
import os
import datetime as dt
from datetime import datetime
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import vim_util as vim


BLP_LOADED = False
if os.name == 'nt':
    try:
        import blp_test
        BLP_LOADED = True
        PRICES_LOADED = False
    except ModuleNotFoundError:
        print('Wrong o/s or version of python. Needs py35 on Windows')


#%%   
def open_price_file(filename, sheetname):
    '''Read an Excel workbook located in the data directory where
    the first column is a date index, all other columns are historical prices.
        filename: name of the file
        sheetname: name of the tab'''
    if os.name == 'nt':
        fname = os.path.join(vim.get_vim_dir(), 'data', filename)
    elif os.uname().nodename == 'debian':  # implies work computer
         fname = os.path.join(vim.get_vim_dir(), 'data', filename)
    else:  # for home computer?
        fname = os.path.join('data', filename)
    with pd.ExcelFile(fname) as xls:
        df = pd.read_excel(xls, sheetname, header=0, index_col=0)
    return df

#%%
def get_prices(ticker, startdate=None, enddate=None, 
               dframe = None, source='bbg'):
    '''
    Get historical prices. The default source is Bloomberg,
    otherwise prices are from an Excel workbook
    ticker: Bloomberg ticker
    optional,
    startdate: YYYYMMDD
    enddate: YYYYMMDD and enddate later than startdate
    '''
    if source == 'bbg':
        df = get_bbg_prices(ticker, startdate, enddate)
    elif source == 'xls':
        if not PRICES_LOADED:
            price_file = open_price_file('VIR Research Prices.xlsx', 'Prices')
            PRICES_LOADED == True
        df = get_xls_prices(price_file, ticker, startdate, enddate)
    elif source == 'mem':
        df = dframe[ticker]
    calc_returns(df)
    calc_indicators(df, ticker)
    return df
    
#%%
def get_bbg_prices(ticker, startdate = None, enddate = None):
    '''
    Use the Bloomberg API to get the price history. Normally accessed from 
    the get_prices function
    
    Parameters
    ----------
    ticker: Bloomberg ticker in the form of <sym> <exchg> Equity
    startdate: YYYYMMDD, default is today - 104 weeks
    enddate: YYYYMMDD, default is today
    enddate must be later than startdate
    '''
    blp = blp_test.BLPInterface()
    if startdate == None:
        startdate=(datetime.today()-dt.timedelta(weeks=104)).strftime('%Y%m%d')
    if enddate == None:
        enddate=datetime.today().strftime('%Y%m%d')
    field_list = ['PX_LAST']
    price_hist_bbg = blp.historicalRequest(ticker, field_list,
                                           startdate, enddate)
    price_hist_bbg.rename(columns={'PX_LAST': ticker}, inplace=True)
    return price_hist_bbg

#%%
def get_bdh(ticker, field_list, startdate = None, enddate = None):
    '''
    Like the bdh function
    
    Parameters
    ----------
    ticker: Bloomberg ticker in the form of <sym> <exchg> Equity
    startdate: YYYYMMDD, default is today - 104 weeks
    enddate: YYYYMMDD, default is today
    enddate must be later than startdate
    '''
    blp = blp_test.BLPInterface()
    if startdate == None:
        startdate=(datetime.today()-dt.timedelta(weeks=52)).strftime('%Y%m%d')
    if enddate == None:
        enddate=datetime.today().strftime('%Y%m%d')
    price_hist_bbg = blp.historicalRequest(ticker, field_list,
                                           startdate, enddate)
    price_hist_bbg.rename(columns={'PX_LAST': ticker}, inplace=True)
    return price_hist_bbg

#%%
def get_bdp_single(ticker, field):
    '''
    Like the bdp excel function
    
    Parameters
    ----------
    ticker: Bloomberg ticker in the form of <sym> <exchg> Equity
    field: The field to get
    
    Returns
    -------
    Just a single number based on ticker and field.
    '''
    blp = blp_test.BLPInterface()
    bdp_item = blp.referenceRequest(ticker, field)
    return bdp_item

#%%
def get_bdp_list(sym_list, field):
    '''
    Like the bdp excel function but gets field for a list of securities
    
    Parameters
    ----------
    sym_list:  List of Bloomberg tickers in the form of <sym> <exchg> Equity
    field: The field to get
    
    Returns
    -------
    
    '''
    blp = blp_test.BLPInterface()
    bdp_item = blp.referenceRequest(sym_list, field)
    return bdp_item

#%%
def get_bbg_prices_list(sym_list, startdate = None, enddate = None):
    '''
    Use the Bloomberg API to get the price history. Normally accessed from 
    the get_prices function
    
    Parameters
    ----------
    sym_list: Bloomberg ticker in the form of <sym> <exchg> Equity
    startdate: YYYYMMDD, default is today - 104 weeks
    enddate: YYYYMMDD, default is today
    enddate must be later than startdate
    '''
    blp = blp_test.BLPInterface()
    if startdate == None:
        startdate=(datetime.today()-dt.timedelta(weeks=104)).strftime('%Y%m%d')
    if enddate == None:
        enddate=datetime.today().strftime('%Y%m%d')
    field_list = ['PX_LAST']
    price_hist_bbg = blp.historicalRequest(sym_list, field_list,
                                           startdate, enddate)
    # price_hist_bbg.rename(columns={'PX_LAST': }, inplace=True)
    return price_hist_bbg

#%%
def get_xls_prices(price_file, ticker, startdate, enddate):
    '''
    Get prices from the Excel worksheet. Normally accessed from the get_prices
    function where source = 'xls'
    '''
    try:
        price_hist_xls = pd.DataFrame(price_file[ticker])
    except KeyError:
        print('If source is "xls" then "Equity" is not needed',
              'after the Bloomberg ticker.')
    else:
        return price_hist_xls

#%%
def update_last_price(ticker):
    '''
    Get the latest price from Bloomberg using get_bbg_prices but
    startdate = enddate. Note how the value is referenced from the
    get_bbg_prices returned dataframe
    
    Parameters
    ----------
    ticker: Bloomberg ticker
    
    Returns
    -------
    a single value that is extracted from a dataframe
    '''
    if datetime.today().weekday() >= 5:
        days = datetime.today().weekday() - 4
    else:
        days = 0
    startdate = (datetime.today() - dt.timedelta(days=days)).strftime('%Y%m%d')  
    x = get_bbg_prices(ticker, startdate, startdate)
    return x.iloc[0][0]

#%%
def update_last_prices(ticker_list):
    '''
    Get the latest price from Bloomberg using get_bbg_prices but
    startdate = enddate. Note how the value is referenced from the
    get_bbg_prices returned dataframe
    
    Parameters
    ----------
    ticker: Bloomberg ticker
    
    Returns
    -------
    a single value that is extracted from a dataframe
    '''
    if datetime.today().weekday() >= 5:
        days = datetime.today().weekday() - 4
    else:
        days = 0
    startdate = (datetime.today() - dt.timedelta(days=days)).strftime('%Y%m%d') 
    x = get_bbg_prices_list(ticker_list, startdate, startdate)
    return x
        
#%%
def calc_returns(hist_prices):
    '''
    Calcuate the returns for a historial price series given.
    
    Parameters
    ----------
    hist_prices: A dataframe of prices indexed by date
    
    Returns
    -------
    hist_returns: Daily log returns in a Series indexed by date.
    '''
    hist_returns = np.log(hist_prices) - np.log(hist_prices.shift(1))
    return hist_returns

#%%
def get_prev_price(hist_prices):
    '''
    Assumes that the historical price data is current and already exists.
    
    Parameters
    ----------
    hist_prices: A dataframe of prices indexed by date
    
    Returns
    -------
    prev_price: The previous day's closing price as a float
    '''
    prev_price = hist_prices[-2][0]
    return prev_price

#%%
def calc_indicators(price_ts, sym):
    DAYS=200 # rolling average days
    price_ts['mavg_200d'] = (price_ts[sym].rolling(window=DAYS,
                             min_periods=1).mean())
    price_ts['up'] = 0.0
    price_ts['prev_pr'] = price_ts[sym].shift(1)
    price_ts.loc[price_ts[sym] > price_ts['prev_pr'],
                 'up'] = price_ts[sym] - price_ts['prev_pr']
    price_ts['down'] = 0.0
    price_ts.loc[price_ts[sym] < price_ts[sym].shift(1),
                 'down'] = price_ts[sym].shift(1) - price_ts[sym]
    price_ts['up_ema'] = price_ts['up'].ewm(com=14, min_periods=1,
                                            adjust=True,
                                            ignore_na=False).mean()
    price_ts['down_ema'] = price_ts['down'].ewm(com=14, min_periods=1,
                                                adjust=True,
                                                ignore_na=False).mean()
    price_ts['rsi'] = 100 - (100 / (1 + price_ts['up_ema'] 
                             / price_ts['down_ema']))
    # comment out the line below for debugging
    price_ts.drop(['up', 'down', 'up_ema', 'down_ema'], axis=1, inplace=True)

#%%
def get_announcement_dates(ticker):
    """
    Gets the earnings announcment dates over the last 104 weeks for a given
    security
    :param ticker: Bloomberg ticker including security type, e.g. AAPL US Equity
    :return: a dataframe of earnings announcment dates
    """
    startdate = (datetime.today() - dt.timedelta(weeks=104)).strftime('%Y%m%d')
    enddate = datetime.today().strftime('%Y%m%d')
    df = get_bdh(ticker, 'ANNOUNCEMENT DT', startdate, enddate)
    return pd.to_datetime(df['ANNOUNCEMENT DT'], format='%Y%m%d').unique()


#%%
def calc_beta(price_ts, sym):
    # price_ts = price_ts[-60:]
    print(sym.split(' '))
    if sym.split(' ')[1] == 'CN':
        mkt_sym = 'XIC CN Equity'
    elif sym.split(' ')[1] == 'CT':
        mkt_sym = 'XIC CT Equity'
    elif sym.split(' ')[1] == 'US':
        mkt_sym = 'SPY US Equity'
    mkt = price_ts[mkt_sym]
    print(mkt.tail())
    stk = price_ts[sym]
    print(stk.tail())
#    model = smf.OLS(mkt, stk)
#    results = model.fit()
#    df = pd.DataFrame(stk.columns[0], results.params, results.tvalues,
#                      results.rsquared())
#    return df
#%%


#%%
if __name__ == '__main__':
    # x = open_price_file('VIR Research Prices.xlsx', 'Equity')
    pass


