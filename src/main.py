# =============================================================================
# Intraday Options Buying Strategy Automation
# By Nanda Kishore M R
# =============================================================================

# =============================================================================
# INSTRUCTIONS
# Start the bot: To start the bot, press the 'Run File (F5)' button in the top pane
# Stop the bot: The bot will stop automatically at the end of the trading day. 
# To stop the bot manually, restart kernel by clicking on the 'Options' button 
# in the IPython console and selecting 'Restart kernel'
# 
# This code comes with 2 other codes and one config file. 
# The other two codes are used to get the fyers access token automatically (get_access_token.py)
# and to get 1 min candles for the required instruments (get_latest_data.py)
# Account and API information can be updated in the config.py file
# 
# Strategy parameters that can be modified are provided below this section. 
# 
# Dependencies- 
# Certain libraries may need to be installed before running this code. 
# To do so, follow the below steps - 
# 1. Open Anaconda Prompt from Start Menu
# 2. In the prompt, install libraries by typing the line -  
# pip install <library-name>
# E.g:- pip install fyers_api
# 
# To ensure accurate execution, uninterrupted internet connectivity is needed.
# Please run the code before market opens every day. 
# =============================================================================

# =============================================================================
# SET PARAMETERS HERE
# =============================================================================

TRACKING_START_TIME = '09:15' # Market open time in HH:MM format
TRACKING_END_TIME = '17:30' # Market close time in HH:MM format

GAP_TRADE_TIME = '09:30' # Time of first trade when there is a gap
GAP_THRESHOLD = 0.0039 # Percentage difference between previous day's close and current day's open that qualifies as gap
LOTS_SCALE_FACTOR = 1 # Number of traded lots will be this scale factor times 2
ENTRY_BUFFER = 0.02 # Entry order will be placed at 75 min High + this percentage
TARGET = 0.02 # Percentage from entry price at which profit is taken
STOP_LOSS = 0.05 # Percentage from entry price at which stop loss may be placed
SL_BUFFER = 0.025 # Stop loss may be placed at 75 min Low - this percentage

# =============================================================================
# SCRIPT
# =============================================================================

SYMBOLS = ['NIFTY 50', 'NIFTY BANK']
underlying_mapping = {'NIFTY 50': 'NIFTY', 
                      'NIFTY BANK': 'BANKNIFTY'}
lotsize_mapping = {'NIFTY 50': 75,
                   'NIFTY BANK': 25}
min_strike_incr_mapping = {'NIFTY 50': 50,
                           'NIFTY BANK': 100}

# Define strategy evaluation times - every 75 min
strat_eval_times = ['09:16', '10:30', '11:45', '13:15', '14:54']
reference_bar_start_times = ['14:15', '09:15', '10:30', '11:45', '13:00']
reference_bar_end_times = ['15:29', '10:29', '11:44', '12:59', '14:14']

from datetime import datetime, timedelta
import time
import math
import pandas as pd
import numpy as np
import requests
import io
import os
import sys
from fyers_api import fyersModel 

# Load custom functions and variables
# import get_access_token
from get_latest_data import connect_to_TD, get_data_underlyings, get_data_options
# Function to authenticate fyers
def authenticate_fyers():
    # get_access_token.main()
    token = open('fyers_token.txt', 'r').read()
    return token

# Function to get fyers instruments list for cash and FO markets
def get_instr_list():
    
    #nsecm_instr_url = 'http://public.fyers.in/sym_details/NSE_CM.csv'
    nsefo_instr_url = 'http://public.fyers.in/sym_details/NSE_FO.csv'
    #s=requests.get(nsecm_instr_url).content
    #cm_instr=pd.read_csv(io.StringIO(s.decode('utf-8')), header=None)
    s=requests.get(nsefo_instr_url).content
    fo_instr=pd.read_csv(io.StringIO(s.decode('utf-8')), header=None)
    fo_instr[1] = fo_instr[1].apply(lambda x: x.upper())
    
    return fo_instr

fo_instr_list = get_instr_list()
all_expiries = sorted(list(set([datetime.strptime(str(x)[4:10], '%y%m%d') for x in fo_instr_list[0].tolist()])))
nearest_expiry = all_expiries[0]
monthend_expiry = 'YES' if len([x for x in all_expiries if x.year == nearest_expiry.year and x.month == nearest_expiry.month]) == 1 else 'NO'

def get_options_contract(underlying, opt_type, strike, nearest_expiry, monthend_expiry):
    
    if monthend_expiry == 'YES':
        fyers_symbol = 'NSE:' + underlying_mapping[underlying] + str(nearest_expiry.year - 2000) + nearest_expiry.strftime('%b').upper() + str(strike)
    else:
        fyers_symbol = 'NSE:' + underlying_mapping[underlying] + str(nearest_expiry.year - 2000) + str(int(nearest_expiry.strftime('%m'))) + nearest_expiry.strftime('%d') + str(strike)
    td_symbol = underlying_mapping[underlying] + str(nearest_expiry.year - 2000) + nearest_expiry.strftime('%m') + nearest_expiry.strftime('%d') + str(strike)
    
    if opt_type == 'CE':
        fyers_symbol = fyers_symbol + 'CE'
        td_symbol = td_symbol + 'CE'
    else:
        fyers_symbol = fyers_symbol + 'PE'
        td_symbol = td_symbol + 'PE'
        
    return fyers_symbol, td_symbol

def limit_order(fyers, token, symbol, qty, direction, price):
    
    side = 1 if direction == 'BUY' else -1

    order = fyers.place_orders(token, data={'symbol': symbol, "qty": qty, "type": 1, "side": side, 
                                            "productType": "INTRADAY", "limitPrice": price, "stopPrice": 0, "disclosedQty": 0, "validity": "DAY",
                                            "offlineOrder": "False", "stopLoss": 0, "takeProfit": 0})
    
    time_now = datetime.today().strftime('%H:%M')
    print(time_now + ' - Order placed: ' + symbol + ' ' + direction + ' ' + str(qty) + ' ' + str(price))
    
    try:
        return order['data']['id']
    except:
        print('Order placement error: ' + order['message'])
        return np.nan

def sl_order(fyers, token, symbol, qty, direction, price):
    
    side = 1 if direction == 'BUY' else -1

    order = fplace_ordersyers.place_orders(token, data={'symbol': symbol, "qty": qty, "type": 3, "side": side,
                                            "productType": "INTRADAY", "limitPrice": 0, "stopPrice": price, "disclosedQty": 0, "validity": "DAY",
                                            "offlineOrder": "False", "stopLoss": 0, "takeProfit": 0})
    
    time_now = datetime.today().strftime('%H:%M')
    print(time_now + ' - Order placed: ' + symbol + ' ' + direction + ' ' + str(qty) + ' ' + str(price))
    
    try:
        return order['data']['id']
    except:
        print('Order placement error: ' + order['message'])
        return np.nan

if os.path.exists('fyers_token.txt') == False or datetime.fromtimestamp(os.path.getmtime('fyers_token.txt')) < datetime.combine(datetime.today().date(), datetime.strptime('06:00:00', '%H:%M:%S').time()):
    token = authenticate_fyers()
else:
    token = open('fyers_token.txt', 'r').read()
td_app, req_ids = connect_to_TD(SYMBOLS)

is_async = False
fyers = fyersModel.FyersModel(is_async)

eval_completion_times = []

CE_entry_orderid = {s: None for s in SYMBOLS}
CE_tp_orderid = {s: None for s in SYMBOLS}
CE_sl_orderid = {s: None for s in SYMBOLS}
CE_trailtp_orderid = {s: None for s in SYMBOLS}
PE_entry_orderid = {s: None for s in SYMBOLS}
PE_tp_orderid = {s: None for s in SYMBOLS}
PE_sl_orderid = {s: None for s in SYMBOLS}
PE_trailtp_orderid = {s: None for s in SYMBOLS}

CE_entry_price = {s: np.nan for s in SYMBOLS}
CE_tp_price = {s: np.nan for s in SYMBOLS}
CE_sl_price = {s: np.nan for s in SYMBOLS}
PE_entry_price = {s: np.nan for s in SYMBOLS}
PE_tp_price = {s: np.nan for s in SYMBOLS}
PE_sl_price = {s: np.nan for s in SYMBOLS}

CE_ticker = {s: None for s in SYMBOLS}
PE_ticker = {s: None for s in SYMBOLS}

trade_scheduled = {s: None for s in SYMBOLS}

reference_period_start_time = {s: None for s in SYMBOLS}
reference_period_end_time = {s: None for s in SYMBOLS}

def run_strategy(time_now):
    
    global CE_entry_orderid, CE_tp_orderid, CE_sl_orderid, CE_trailtp_orderid, PE_entry_orderid, PE_tp_orderid, PE_sl_orderid, PE_trailtp_orderid
    global CE_entry_price, CE_tp_price, CE_sl_price, PE_entry_price, PE_tp_price, PE_sl_price
    global CE_ticker, PE_ticker
    global eval_completion_times
    global trade_scheduled
    global reference_period_start_time, reference_period_end_time
    
    # Check if CE or PE position exists
    existing_CE_position = {s: 'NO' for s in SYMBOLS}
    existing_PE_position = {s: 'NO' for s in SYMBOLS}
    curr_positions = fyers.positions(token) ##### strategy specific
    
    if curr_positions['code'] == 200:
        curr_positions = curr_positions['data']['netPositions']    
        curr_positions = [x for x in curr_positions if x['qty'] != 0]
        for s in SYMBOLS:
            if len(curr_positions) > 0:
                existing_CE_position[s] = [x for x in curr_positions if x['symbol'].startswith('NSE:' + underlying_mapping[s]) and x['symbol'].endswith('CE')]
                existing_CE_position[s] = 'YES' if len(existing_CE_position[s]) > 0 else 'NO'
                existing_PE_position[s] = [x for x in curr_positions if x['symbol'].startswith('NSE:' + underlying_mapping[s]) and x['symbol'].endswith('PE')]
                existing_PE_position[s] = 'YES' if len(existing_PE_position[s]) > 0 else 'NO'
            
    else:
        print(curr_positions['message'])
        print(time_now + '- Unable to retrieve current position')    
        for s in SYMBOLS:
            existing_CE_position[s] = ''
            existing_PE_position[s] = ''
        time.sleep(3)
    
    if time_now not in eval_completion_times:
        
        eval_completion_times.append(time_now)
        
        # Get latest 1 min data df
        # time.sleep(1)
        data_1min = get_data_underlyings(td_app, SYMBOLS)
        date_curr = datetime.today().date()
        #date_curr = datetime(2021, 2, 17).date()
        
        for s in SYMBOLS:
            
            data_1min_select = data_1min[s]
            
            # If it is 9:16 evaluation, check for gap 
            if time_now == strat_eval_times[0]:
                # If there is a gap, consider bar from 9:15 to 9:25, else, consider the 75 min bar
                date_prev = sorted(list(set([x['time'].date() for x in data_1min_select])))
                date_prev = date_prev[date_prev.index(date_curr) - 1]
                
                prev_close = [x['c'] for x in data_1min_select if x['time'] == datetime(date_prev.year, date_prev.month, date_prev.day, 15, 29, 0)][0]
                curr_open = [x['o'] for x in data_1min_select if x['time'] == datetime(date_prev.year, date_prev.month, date_prev.day, 9, 15, 0)][0]
                gap_abs = (curr_open - prev_close) / prev_close
                gap = 'YES' if abs(gap_abs) >= GAP_THRESHOLD else 'NO'
                
                if gap == 'YES':
                    print(time_now + ' - ' + s + ': There is a sizeable gap from the previous trading day. Trade will be taken at 9:30')
                    trade_scheduled[s] = GAP_TRADE_TIME                
                    reference_period_start_time[s] = datetime(date_curr.year, date_curr.month, date_curr.day, 9, 15, 0)
                    reference_period_end_time[s] = datetime(date_curr.year, date_curr.month, date_curr.day, 9, 24, 0)
                else:
                    trade_scheduled[s] = None
                    reference_period_start_time[s] = datetime.combine(date_prev, datetime.strptime(reference_bar_start_times[0], '%H:%M').time())
                    reference_period_end_time[s] = datetime.combine(date_prev, datetime.strptime(reference_bar_end_times[0], '%H:%M').time())
            
            elif time_now in strat_eval_times:
                # If it is not the 9:16 evaluation, consider the 75 min bar
                reference_period_start_time[s] = datetime.combine(date_curr, datetime.strptime(reference_bar_start_times[strat_eval_times.index(time_now)], '%H:%M').time())
                reference_period_end_time[s] = datetime.combine(date_curr, datetime.strptime(reference_bar_end_times[strat_eval_times.index(time_now)], '%H:%M').time())
            
            # Check if CE or PE position exists
            # existing_CE_position = 'NO'
            # existing_PE_position = 'NO'
            # curr_positions = fyers.positions(token)
            # if curr_positions['code'] == 200:
            #     curr_positions = curr_positions['data']['netPositions']
                
            #     if len(curr_positions) > 0:
            #         existing_CE_position = [x for x in curr_positions if x['symbol'].startswith('NSE:' + underlying_mapping[s]) and x['symbol'].endswith('CE')]
            #         existing_CE_position = 'YES' if len(existing_CE_position) > 0 else 'NO'
            #         existing_PE_position = [x for x in curr_positions if x['symbol'].startswith('NSE:' + underlying_mapping[s]) and x['symbol'].endswith('PE')]
            #         existing_PE_position = 'YES' if len(existing_PE_position) > 0 else 'NO'
                    
            # else:
            #     print(time_now + ' - ' + s + ': Unable to retrieve current position')
            #     existing_CE_position = 'YES'
            #     existing_PE_position = 'YES'
            
            if (pd.isnull(trade_scheduled[s]) == True and time_now in strat_eval_times) or (pd.isnull(trade_scheduled[s]) == False and time_now == trade_scheduled[s]):
                
                trade_scheduled[s] = None
                
                # Identify bar high/low and call/put strikes - Call strike: Round down high to nearest 50, Put strike: Round up low to nearest 50                                        
                reference_period_data = [x for x in data_1min_select if x['time'] >= reference_period_start_time[s] and x['time'] <= reference_period_end_time[s]]
                reference_period_ohlc = {'o': reference_period_data[0]['o'], 
                                         'h': max([x['h'] for x in reference_period_data]),
                                         'l': min([x['l'] for x in reference_period_data]),
                                         'c': reference_period_data[-1]['c']}
                
                call_strike = int(math.floor(reference_period_ohlc['h'] / float(min_strike_incr_mapping[s])))*min_strike_incr_mapping[s]
                put_strike = int(math.ceil(reference_period_ohlc['l'] / float(min_strike_incr_mapping[s])))*min_strike_incr_mapping[s]
                
                call_fyers_symbol, call_td_symbol = get_options_contract(s, 'CE', call_strike, nearest_expiry, monthend_expiry)
                put_fyers_symbol, put_td_symbol = get_options_contract(s, 'PE', put_strike, nearest_expiry, monthend_expiry)
                
                # if s == 'NIFTY 50':
                #     call_fyers_symbol, call_td_symbol = 'NSE:SBIN-EQ', 'SBIN'
                #     put_fyers_symbol, put_td_symbol = 'NSE:ITC-EQ', 'ITC'
                # else:
                #     call_fyers_symbol, call_td_symbol = 'NSE:HINDALCO-EQ', 'HINDALCO'
                #     put_fyers_symbol, put_td_symbol = 'NSE:VEDL-EQ', 'VEDL'
                
                # Get latest 1 min data for the call and put strike options and convert to 75 min bars
                data_1min_opt = get_data_options(td_app, [call_td_symbol, put_td_symbol])
                
                reference_period_data_optCE = [x for x in data_1min_opt[call_td_symbol] if x['time'] >= reference_period_start_time[s] and x['time'] <= reference_period_end_time[s]]
                reference_period_ohlc_optCE = {'o': reference_period_data_optCE[0]['o'], 
                                               'h': max([x['h'] for x in reference_period_data_optCE]),
                                               'l': min([x['l'] for x in reference_period_data_optCE]),
                                               'c': reference_period_data_optCE[-1]['c']}
                reference_period_data_optPE = [x for x in data_1min_opt[put_td_symbol] if x['time'] >= reference_period_start_time[s] and x['time'] <= reference_period_end_time[s]]
                reference_period_ohlc_optPE = {'o': reference_period_data_optPE[0]['o'], 
                                               'h': max([x['h'] for x in reference_period_data_optPE]),
                                               'l': min([x['l'] for x in reference_period_data_optPE]),
                                               'c': reference_period_data_optPE[-1]['c']}
                
                # If there is no call position, place entry order for CE option at 75 Min High + 10%
                if existing_CE_position[s] == 'NO':  
                    if pd.isnull(CE_entry_orderid[s]) == False:
                        print(time_now + ' - ' + s + ': Cancelling previous entry order.')
                        fyers.delete_orders(token, data={'id': CE_entry_orderid[s]}) ### user specific
                    
                    if pd.isnull(CE_sl_orderid[s]) == False:
                        print(time_now + ' - ' + s + ': CE position has exited. Cancelling existing SL order.')
                        fyers.delete_orders(token, data={'id': CE_sl_orderid[s]})   ### user specific
                    
                    if pd.isnull(CE_tp_orderid[s]) == False:
                        print(time_now + ' - ' + s + ': CE position has exited. Cancelling existing TP order.')
                        fyers.delete_orders(token, data={'id': CE_tp_orderid[s]})   ### user specific
                        
                    if pd.isnull(CE_trailtp_orderid[s]) == False:
                        print(time_now + ' - ' + s + ': CE position has exited. Cancelling existing Trailing TP order.')
                        fyers.delete_orders(token, data={'id': CE_trailtp_orderid[s]})  ### user specific
                        
                    CE_entry_orderid[s] = None
                    CE_tp_orderid[s] = None
                    CE_sl_orderid[s] = None
                    CE_trailtp_orderid[s] = None

                    CE_entry_price[s] = round(reference_period_ohlc_optCE['h']*(1+ENTRY_BUFFER) / 0.05) * 0.05
                    CE_tp_price[s] = round(CE_entry_price[s]*(1+TARGET) / 0.05) * 0.05
                    CE_sl_price[s] = round(max(CE_entry_price[s]*(1-STOP_LOSS), reference_period_ohlc_optCE['l']*(1+SL_BUFFER)) / 0.05) * 0.05
                    
                    print(time_now + ' - ' + s + ': No CE position. Placing fresh entry order')
                    
                    # Place exit order for 1 lot at Entry + 60% and stop loss for 2 lots at max(Entry - 60%, 75 Min Low - 10%)
                    CE_entry_orderid[s] = sl_order(fyers, token, call_fyers_symbol, lotsize_mapping[s]*LOTS_SCALE_FACTOR*2, 'BUY', CE_entry_price[s])
                    #CE_sl_orderid[s] = sl_order(fyers, token, call_fyers_symbol, lotsize_mapping[s]*LOTS_SCALE_FACTOR*2, 'SELL', CE_sl_price[s])
                    CE_ticker[s] = call_fyers_symbol
                    
                    
                    time.sleep(1)
                    
                else:
                    print(time_now + ' - ' + s + ': CE position already exists. No new entry is taken.')
                    
                # If there is no put position, place entry order for PE option at 75 Min High + 10%
                if existing_PE_position[s] == 'NO':
                    if pd.isnull(PE_entry_orderid[s]) == False:
                        print(time_now + ' - ' + s + ': Cancelling previous entry order.')
                        fyers.delete_orders(token, data={'id': PE_entry_orderid[s]})
                    
                    if pd.isnull(PE_sl_orderid[s]) == False:
                        print(time_now + ' - ' + s + ': PE position has exited. Cancelling existing SL order.')
                        fyers.delete_orders(token, data={'id': PE_sl_orderid[s]})
                    
                    if pd.isnull(PE_tp_orderid[s]) == False:
                        print(time_now + ' - ' + s + ': PE position has exited. Cancelling existing TP order.')
                        fyers.delete_orders(token, data={'id': PE_tp_orderid[s]})
                        
                    if pd.isnull(PE_trailtp_orderid[s]) == False:
                        print(time_now + ' - ' + s + ': PE position has exited. Cancelling existing Trailing TP order.')
                        fyers.delete_orders(token, data={'id': PE_trailtp_orderid[s]})
                        
                    PE_entry_orderid[s] = None
                    PE_tp_orderid[s] = None
                    PE_sl_orderid[s] = None
                    PE_trailtp_orderid[s] = None
                    
                    PE_entry_price[s] = round(reference_period_ohlc_optPE['h']*(1+ENTRY_BUFFER) / 0.05) * 0.05
                    PE_tp_price[s] = round(PE_entry_price[s]*(1+TARGET) / 0.05) * 0.05
                    PE_sl_price[s] = round(max(PE_entry_price[s]*(1-STOP_LOSS), reference_period_ohlc_optPE['l']*(1+SL_BUFFER)) / 0.05) * 0.05
                    
                    print(time_now + ' - ' + s + ': No PE position. Placing fresh entry order')
                    
                    # Place exit order for 1 lot at Entry + 60% and stop loss for 2 lots at max(Entry - 60%, 75 Min Low - 10%)
                    PE_entry_orderid[s] = sl_order(fyers, token, put_fyers_symbol, lotsize_mapping[s]*LOTS_SCALE_FACTOR*2, 'BUY', PE_entry_price[s])
                    #PE_sl_orderid[s] = sl_order(fyers, token, put_fyers_symbol, lotsize_mapping[s]*LOTS_SCALE_FACTOR*2, 'SELL', PE_sl_price[s])
                    PE_ticker[s] = put_fyers_symbol
                    
                    time.sleep(1)
                    
                else:
                    print(time_now + ' - ' + s + ': PE position already exists. No new entry is taken.')
    
    for s in SYMBOLS:            
    
        # Track open positions
        if existing_CE_position[s] == 'YES':
            
            if pd.isnull(CE_sl_orderid[s]):
                print(time_now + ' - ' + s + ' ' + CE_ticker[s] + ': Placing SL order')
                CE_sl_orderid[s] = sl_order(fyers, token, CE_ticker[s], lotsize_mapping[s]*LOTS_SCALE_FACTOR*2, 'SELL', CE_sl_price[s])
            
            if pd.isnull(CE_tp_orderid[s]):
                # Place take profit order for 1 lot if entry order is executed
                print(time_now + ' - ' + s + ' ' + CE_ticker[s] + ': CE Entry order has been executed. Placing first profit order')
                CE_tp_orderid[s] = limit_order(fyers, token, CE_ticker[s], lotsize_mapping[s]*LOTS_SCALE_FACTOR*1, 'SELL', CE_tp_price[s])
                
            else:
                # Track if exit profit order for the 1 lot is executed.
                tp_order_status = fyers.order_status(token, data={'id': CE_tp_orderid[s]})
                if tp_order_status == 2:
                    print(time_now + ' - ' + s + ' ' + CE_ticker[s] + ': Placing / modifying second CE profit order')
                    # If yes, place or modify stop tp order
                    if data_1min_opt[call_td_symbol][-1]['c'] > CE_tp_price[s]:
                        trail_price = round(CE_tp_price[s] + (data_1min_opt[call_td_symbol][-1]['c'] - CE_tp_price[s])*0.5 / 0.05) * 0.05
                        CE_trailtp_orderid[s] = sl_order(fyers, token, CE_ticker[s], lotsize_mapping[s]*LOTS_SCALE_FACTOR*1, 'SELL', trail_price)
                    else:
                        trail_price = CE_tp_price[s]
                        CE_trailtp_orderid[s] = sl_order(fyers, token, CE_ticker[s], lotsize_mapping[s]*LOTS_SCALE_FACTOR*1, 'SELL', trail_price)
                        
        else:
            
            if pd.isnull(CE_sl_orderid[s]) == False:
                print(time_now + ' - ' + s + ' ' + CE_ticker[s] + ': CE position has exited. Cancelling existing SL order.')
                fyers.delete_orders(token, data={'id': CE_sl_orderid[s]})
            
            if pd.isnull(CE_tp_orderid[s]) == False:
                print(time_now + ' - ' + s + ' ' + CE_ticker[s] + ': CE position has exited. Cancelling existing TP order.')
                fyers.delete_orders(token, data={'id': CE_tp_orderid[s]})
                
            if pd.isnull(CE_trailtp_orderid[s]) == False:
                print(time_now + ' - ' + s + ' ' + CE_ticker[s] + ': CE position has exited. Cancelling existing Trailing TP order.')
                fyers.delete_orders(token, data={'id': CE_trailtp_orderid[s]})
                
            CE_tp_orderid[s] = None
            CE_sl_orderid[s] = None
            CE_trailtp_orderid[s] = None
        
        if existing_PE_position[s] == 'YES':
            
            if pd.isnull(PE_sl_orderid[s]):
                print(time_now + ' - ' + s + ' ' + PE_ticker[s] + ': Placing SL order')
                PE_sl_orderid[s] = sl_order(fyers, token, PE_ticker[s], lotsize_mapping[s]*LOTS_SCALE_FACTOR*2, 'SELL', PE_sl_price[s])
            
            if pd.isnull(PE_tp_orderid[s]):
                # Place take profit order for 1 lot if entry order is executed
                print(time_now + ' - ' + s + ' ' + PE_ticker[s] + ': PE Entry order has been executed. Placing first profit order')
                PE_tp_orderid[s] = limit_order(fyers, token, PE_ticker[s], lotsize_mapping[s]*LOTS_SCALE_FACTOR*1, 'SELL', PE_tp_price[s])
                
            else:
                # Track if exit profit order for the 1 lot is executed.
                tp_order_status = fyers.order_status(token, data={'id': PE_tp_orderid[s]})
                if tp_order_status == 2:
                    print(time_now + ' - ' + s + ' ' + PE_ticker[s] + ': Placing / modifying second PE profit order')
                    # If yes, place or modify stop tp order
                    if data_1min_opt[put_td_symbol][-1]['c'] > PE_tp_price[s]:
                        trail_price = PE_tp_price[s] + (data_1min_opt[put_td_symbol][-1]['c'] - PE_tp_price[s])*0.5
                        PE_trailtp_orderid[s] = sl_order(fyers, token, PE_ticker[s], lotsize_mapping[s]*LOTS_SCALE_FACTOR*1, 'SELL', trail_price)
                    else:
                        trail_price = PE_tp_price[s]
                        PE_trailtp_orderid[s] = sl_order(fyers, token, PE_ticker[s], lotsize_mapping[s]*LOTS_SCALE_FACTOR*1, 'SELL', trail_price)
                        
        else:
            
            if pd.isnull(PE_sl_orderid[s]) == False:
                print(time_now + ' - ' + s + ' ' + PE_ticker[s] + ': PE position has exited. Cancelling existing SL order.')
                fyers.delete_orders(token, data={'id': PE_sl_orderid[s]})
            
            if pd.isnull(PE_tp_orderid[s]) == False:
                print(time_now + ' - ' + s + ' ' + PE_ticker[s] + ': PE position has exited. Cancelling existing TP order.')
                fyers.delete_orders(token, data={'id': PE_tp_orderid[s]})
                
            if pd.isnull(PE_trailtp_orderid[s]) == False:
                print(time_now + ' - ' + s + ' ' + PE_ticker[s] + ': PE position has exited. Cancelling existing Trailing TP order.')
                fyers.delete_orders(token, data={'id': PE_trailtp_orderid[s]})
                
            PE_tp_orderid[s] = None
            PE_sl_orderid[s] = None
            PE_trailtp_orderid[s] = None
            
# Main function to control all operations
def main():
            
    time_now = datetime.today().strftime('%H:%M')
    
    print_cnt = 0
    while True:
    
        while (time_now >= TRACKING_START_TIME) and (time_now <= TRACKING_END_TIME):
            try:
                run_strategy(time_now)
                time.sleep(3)
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print(str(exc_tb.tb_lineno), e)
                time.sleep(1)
            time_now = datetime.today().strftime('%H:%M')
        
        time_now = datetime.today().strftime('%H:%M')
        if time_now >= TRACKING_END_TIME:
            break
        elif time_now < TRACKING_START_TIME:
            if print_cnt == 0:
                print('Waiting for market to open...')
                print_cnt += 1
        else:
            print('Market is open')
    
    td_app.disconnect()
    print('\nTracking successfully completed for the day!')
    
if __name__ == '__main__':
    main()
    #pass
