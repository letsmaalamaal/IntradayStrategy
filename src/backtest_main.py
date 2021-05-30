# =============================================================================
# Intraday Options Buying Strategy - Backtest
# By Nanda Kishore M R
# =============================================================================

# =============================================================================
# SET PARAMETERS HERE
# =============================================================================

# Scenario 1: Target of 10%
# Scneario 2: Target of 30%
# Scenario 3: Target of 60%

GAP_TRADE_TIME = '09:30' # Time of first trade when there is a gap
GAP_THRESHOLD = 0.0039 # Percentage difference between previous day's close and current day's open that qualifies as gap
LOTS_SCALE_FACTOR = 1 # Number of traded lots will be this scale factor times 2
ENTRY_BUFFER = 0.1 # Entry order will be placed at 75 min High + this percentage
TARGET = 0.1 # Percentage from entry price at which profit is taken
STOP_LOSS = 0.6 # Percentage from entry price at which stop loss may be placed
SL_BUFFER = 0.1 # Stop loss may be placed at 75 min Low - this percentage

lotsize_mapping = {'NIFTY': 75,
                   'BANKNIFTY': 25}
min_strike_incr_mapping = {'NIFTY': 50,
                           'BANKNIFTY': 100}

# =============================================================================
# SCRIPT
# =============================================================================

from datetime import datetime
import os
import pandas as pd
import numpy as np
import math
import time

start = time.time()

YEARS = ['2018', '2019', '2020']
MONTHS = [x.strftime('%b').upper() for x in [datetime(2020,i,1) for i in range(1,13)]]

# filenames = [os.listdir('Data\\' + y + '\\' + m + '-' + y) for y in YEARS for m in MONTHS]
# filenames = [x for y in filenames for x in y]

months_select = MONTHS[1:]
filenames = [os.listdir('Data\\2020\\' + m + '-2020') for m in months_select]
filenames = [x for y in filenames for x in y]

# Define strategy evaluation times - every 75 min
strat_eval_times = ['09:16', '10:30', '11:45', '13:00', '14:15']
reference_bar_start_times = ['14:15', '09:15', '10:30', '11:45', '13:00']
reference_bar_end_times = ['15:29', '10:29', '11:44', '12:59', '14:14']

def get_option_price(data_select, ticker, time_now):
    if ticker != None and time_now in [x['Time'] for x in data_select]:
        try:
            return [[x['High'], x['Low'], x['Close']] for x in data_select if x['Ticker'] == ticker and x['Time'] == time_now][0]
        except:
            return [np.nan, np.nan, np.nan]
    else:
        return [np.nan, np.nan, np.nan]
    
def update_long_position(data_select, spot_data_select, opt_dict, reference_period_data_opt, symbol, time_now, i):
    
    if spot_data_select[i-1]['Long Position'] in ['', 'Exit Buy']:
        if (time_now >= spot_data_select[i]['Trade Scheduled Time']):
            spot_data_select[i]['Long Option Ticker'] = [x['Ticker'] for x in opt_dict if x['Symbol'] == s and x['Strike'] == spot_data_select[i]['Call Strike'] and x['Option Type'] == 'CE'][0]
            
            try:
                spot_data_select[i]['Long Reference Period High'] = max([x['High'] for x in reference_period_data_opt if x['Ticker'] == spot_data_select[i]['Long Option Ticker']])
            except:
                spot_data_select[i]['Long Reference Period High'] = np.nan
                
            try:
                spot_data_select[i]['Long Reference Period Low'] = min([x['Low'] for x in reference_period_data_opt if x['Ticker'] == spot_data_select[i]['Long Option Ticker']])
            except:
                spot_data_select[i]['Long Reference Period Low'] = np.nan
            
            opt_hlc = get_option_price(data_select, spot_data_select[i]['Long Option Ticker'], time_now)
            spot_data_select[i]['Long Option High'] = opt_hlc[0]
            spot_data_select[i]['Long Option Low'] = opt_hlc[1]
            spot_data_select[i]['Long Option Close'] = opt_hlc[2]
            
            if (spot_data_select[i]['Cycle Long Count'] == 0) and (time_now <= datetime(2020,1,1,15,20,0).time()) and spot_data_select[i]['Long Option High'] >= spot_data_select[i]['Long Reference Period High']*(1+ENTRY_BUFFER):
                
                spot_data_select[i]['Long Position'] = 'Buy'
                
                spot_data_select[i]['Long Buy Price'] = spot_data_select[i]['Long Option Close']
                spot_data_select[i]['Long TP'] = spot_data_select[i]['Long Buy Price']*(1+TARGET)
                spot_data_select[i]['Long Trail TP'] = spot_data_select[i]['Long TP']
                spot_data_select[i]['Long SL'] = max(spot_data_select[i]['Long Buy Price']*(1-STOP_LOSS), spot_data_select[i]['Long Reference Period Low']*(1-SL_BUFFER))
                spot_data_select[i]['Long Exit Price'] = np.nan
                spot_data_select[i]['Long P&L'] = np.nan
                spot_data_select[i]['Cycle Long Count'] = 1
                
            else:
                
                spot_data_select[i]['Long Position'] = ''
                spot_data_select[i]['Long Buy Price'] = np.nan
                spot_data_select[i]['Long TP'] = np.nan
                spot_data_select[i]['Long Trail TP'] = np.nan
                spot_data_select[i]['Long SL'] = np.nan
                spot_data_select[i]['Long Exit Price'] = np.nan
                spot_data_select[i]['Long P&L'] = np.nan
            
        else:
            spot_data_select[i]['Long Position'] = ''
            spot_data_select[i]['Long Option Ticker'] = None
            spot_data_select[i]['Long Reference Period High'] = np.nan
            spot_data_select[i]['Long Reference Period Low'] = np.nan
            
            opt_hlc = get_option_price(data_select, spot_data_select[i]['Long Option Ticker'], time_now)
            spot_data_select[i]['Long Option High'] = opt_hlc[0]
            spot_data_select[i]['Long Option Low'] = opt_hlc[1]
            spot_data_select[i]['Long Option Close'] = opt_hlc[2]
            spot_data_select[i]['Long Buy Price'] = np.nan
            spot_data_select[i]['Long TP'] = np.nan
            spot_data_select[i]['Long Trail TP'] = np.nan
            spot_data_select[i]['Long SL'] = np.nan
            spot_data_select[i]['Long Exit Price'] = np.nan
            spot_data_select[i]['Long P&L'] = np.nan
                
    elif spot_data_select[i-1]['Long Position'] == 'Buy':
    
        spot_data_select[i]['Long Option Ticker'] = spot_data_select[i-1]['Long Option Ticker']
        
        spot_data_select[i]['Long Reference Period High'] = spot_data_select[i-1]['Long Reference Period High']
        spot_data_select[i]['Long Reference Period Low'] = spot_data_select[i-1]['Long Reference Period Low']
        
        opt_hlc = get_option_price(data_select, spot_data_select[i]['Long Option Ticker'], time_now)
        spot_data_select[i]['Long Option High'] = opt_hlc[0]
        spot_data_select[i]['Long Option Low'] = opt_hlc[1]
        spot_data_select[i]['Long Option Close'] = opt_hlc[2]
        spot_data_select[i]['Long Buy Price'] = spot_data_select[i-1]['Long Buy Price']
        spot_data_select[i]['Long TP'] = spot_data_select[i-1]['Long TP']
        spot_data_select[i]['Long Trail TP'] = spot_data_select[i-1]['Long TP']
        spot_data_select[i]['Long SL'] = spot_data_select[i-1]['Long SL']
        
        if spot_data_select[i]['Long Option High'] >= spot_data_select[i]['Long TP']:    
            spot_data_select[i]['Long Position'] = 'Partial Exit Buy'
            spot_data_select[i]['Long Exit Price'] = spot_data_select[i]['Long TP']
            spot_data_select[i]['Long P&L'] = (spot_data_select[i]['Long Exit Price'] - spot_data_select[i]['Long Buy Price']) * 1 * lotsize_mapping[symbol]
        elif spot_data_select[i]['Long Option Low'] <= spot_data_select[i]['Long SL']:
            spot_data_select[i]['Long Position'] = 'Exit Buy'
            spot_data_select[i]['Long Exit Price'] = spot_data_select[i]['Long SL']
            spot_data_select[i]['Long P&L'] = (spot_data_select[i]['Long Exit Price'] - spot_data_select[i]['Long Buy Price']) * 2 * lotsize_mapping[symbol]
        elif time_now == datetime(2020,1,1,15,19,0).time():
            spot_data_select[i]['Long Position'] = 'Exit Buy'
            spot_data_select[i]['Long Exit Price'] = spot_data_select[i]['Long Option Close']
            spot_data_select[i]['Long P&L'] = (spot_data_select[i]['Long Exit Price'] - spot_data_select[i]['Long Buy Price']) * 2 * lotsize_mapping[symbol]
        else:
            spot_data_select[i]['Long Position'] = 'Buy'
            spot_data_select[i]['Long Exit Price'] = np.nan
            spot_data_select[i]['Long P&L'] = np.nan
        spot_data_select[i]['Cycle Long Count'] = 1
            
    elif spot_data_select[i-1]['Long Position'] == 'Partial Exit Buy':
        
        spot_data_select[i]['Long Option Ticker'] = spot_data_select[i-1]['Long Option Ticker']
        
        spot_data_select[i]['Long Reference Period High'] = spot_data_select[i-1]['Long Reference Period High']
        spot_data_select[i]['Long Reference Period Low'] = spot_data_select[i-1]['Long Reference Period Low']
        
        opt_hlc = get_option_price(data_select, spot_data_select[i]['Long Option Ticker'], time_now)
        spot_data_select[i]['Long Option High'] = opt_hlc[0]
        spot_data_select[i]['Long Option Low'] = opt_hlc[1]
        spot_data_select[i]['Long Option Close'] = opt_hlc[2]
        spot_data_select[i]['Long Buy Price'] = spot_data_select[i-1]['Long Buy Price']
        spot_data_select[i]['Long TP'] = spot_data_select[i-1]['Long TP']
        spot_data_select[i]['Long Trail TP'] = round(((spot_data_select[i-1]['Long Option Close'] + spot_data_select[i-1]['Long TP']) / 2) / 0.05) * 0.05 if spot_data_select[i-1]['Long Option Close'] > spot_data_select[i-1]['Long TP'] else spot_data_select[i-1]['Long Trail TP']
        spot_data_select[i]['Long SL'] = spot_data_select[i-1]['Long SL']
        
        if spot_data_select[i]['Long Option Low'] <= spot_data_select[i]['Long SL']:
            spot_data_select[i]['Long Position'] = 'Exit Buy'
            spot_data_select[i]['Long Exit Price'] = spot_data_select[i]['Long SL']
            spot_data_select[i]['Long P&L'] = (spot_data_select[i]['Long Exit Price'] - spot_data_select[i]['Long Buy Price']) * 1 * lotsize_mapping[symbol]
        elif spot_data_select[i]['Long Option Low'] <= spot_data_select[i]['Long Trail TP']:    
            spot_data_select[i]['Long Position'] = 'Exit Buy'
            spot_data_select[i]['Long Exit Price'] = spot_data_select[i]['Long Trail TP']
            spot_data_select[i]['Long P&L'] = (spot_data_select[i]['Long Exit Price'] - spot_data_select[i]['Long Buy Price']) * 1 * lotsize_mapping[symbol]
        elif time_now == datetime(2020,1,1,15,19,0).time():
            spot_data_select[i]['Long Position'] = 'Exit Buy'
            spot_data_select[i]['Long Exit Price'] = spot_data_select[i]['Long Option Close']
            spot_data_select[i]['Long P&L'] = (spot_data_select[i]['Long Exit Price'] - spot_data_select[i]['Long Buy Price']) * 1 * lotsize_mapping[symbol]
        else:
            spot_data_select[i]['Long Position'] = 'Partial Exit Buy'
            spot_data_select[i]['Long Exit Price'] = np.nan
            spot_data_select[i]['Long P&L'] = np.nan
        spot_data_select[i]['Cycle Long Count'] = 1
            
    return spot_data_select

def update_short_position(data_select, spot_data_select, opt_dict, reference_period_data_opt, symbol, time_now, i):
    
    if spot_data_select[i-1]['Short Position'] in ['', 'Exit Buy']:
        if (time_now >= spot_data_select[i]['Trade Scheduled Time']):
            spot_data_select[i]['Short Option Ticker'] = [x['Ticker'] for x in opt_dict if x['Symbol'] == s and x['Strike'] == spot_data_select[i]['Put Strike'] and x['Option Type'] == 'PE'][0]
            
            try:
                spot_data_select[i]['Short Reference Period High'] = max([x['High'] for x in reference_period_data_opt if x['Ticker'] == spot_data_select[i]['Short Option Ticker']])
            except:
                spot_data_select[i]['Short Reference Period High'] = np.nan
                
            try:
                spot_data_select[i]['Short Reference Period Low'] = min([x['Low'] for x in reference_period_data_opt if x['Ticker'] == spot_data_select[i]['Short Option Ticker']])
            except:
                spot_data_select[i]['Short Reference Period Low'] = np.nan
            
            opt_hlc = get_option_price(data_select, spot_data_select[i]['Short Option Ticker'], time_now)
            spot_data_select[i]['Short Option High'] = opt_hlc[0]
            spot_data_select[i]['Short Option Low'] = opt_hlc[1]
            spot_data_select[i]['Short Option Close'] = opt_hlc[2]
            
            if (spot_data_select[i]['Cycle Short Count'] == 0) and (time_now <= datetime(2020,1,1,15,20,0).time()) and spot_data_select[i]['Short Option High'] >= spot_data_select[i]['Short Reference Period High']*(1+ENTRY_BUFFER):
                
                spot_data_select[i]['Short Position'] = 'Buy'
            
                spot_data_select[i]['Short Buy Price'] = spot_data_select[i]['Short Option Close']
                spot_data_select[i]['Short TP'] = spot_data_select[i]['Short Buy Price']*(1+TARGET)
                spot_data_select[i]['Short Trail TP'] = spot_data_select[i]['Long TP']
                spot_data_select[i]['Short SL'] = max(spot_data_select[i]['Short Buy Price']*(1-STOP_LOSS), spot_data_select[i]['Short Reference Period Low']*(1-SL_BUFFER))
                spot_data_select[i]['Short Exit Price'] = np.nan
                spot_data_select[i]['Short P&L'] = np.nan
                spot_data_select[i]['Cycle Short Count'] = 1
                
            else:
                
                spot_data_select[i]['Short Position'] = ''
                spot_data_select[i]['Short Buy Price'] = np.nan
                spot_data_select[i]['Short TP'] = np.nan
                spot_data_select[i]['Short Trail TP'] = np.nan
                spot_data_select[i]['Short SL'] = np.nan
                spot_data_select[i]['Short Exit Price'] = np.nan
                spot_data_select[i]['Short P&L'] = np.nan
            
        else:
            spot_data_select[i]['Short Position'] = ''
            spot_data_select[i]['Short Option Ticker'] = None
            spot_data_select[i]['Short Reference Period High'] = np.nan
            spot_data_select[i]['Short Reference Period Low'] = np.nan
            
            opt_hlc = get_option_price(data_select, spot_data_select[i]['Short Option Ticker'], time_now)
            spot_data_select[i]['Short Option High'] = opt_hlc[0]
            spot_data_select[i]['Short Option Low'] = opt_hlc[1]
            spot_data_select[i]['Short Option Close'] = opt_hlc[2]
            spot_data_select[i]['Short Buy Price'] = np.nan
            spot_data_select[i]['Short TP'] = np.nan
            spot_data_select[i]['Short Trail TP'] = np.nan
            spot_data_select[i]['Short SL'] = np.nan
            spot_data_select[i]['Short Exit Price'] = np.nan
            spot_data_select[i]['Short P&L'] = np.nan
            
    elif spot_data_select[i-1]['Short Position'] == 'Buy':
    
        spot_data_select[i]['Short Option Ticker'] = spot_data_select[i-1]['Short Option Ticker']
        
        spot_data_select[i]['Short Reference Period High'] = spot_data_select[i-1]['Short Reference Period High']
        spot_data_select[i]['Short Reference Period Low'] = spot_data_select[i-1]['Short Reference Period Low']
        
        opt_hlc = get_option_price(data_select, spot_data_select[i]['Short Option Ticker'], time_now)
        spot_data_select[i]['Short Option High'] = opt_hlc[0]
        spot_data_select[i]['Short Option Low'] = opt_hlc[1]
        spot_data_select[i]['Short Option Close'] = opt_hlc[2]
        spot_data_select[i]['Short Buy Price'] = spot_data_select[i-1]['Short Buy Price']
        spot_data_select[i]['Short TP'] = spot_data_select[i-1]['Short TP']
        spot_data_select[i]['Short Trail TP'] = spot_data_select[i-1]['Short TP']
        spot_data_select[i]['Short SL'] = spot_data_select[i-1]['Short SL']
        
        if spot_data_select[i]['Short Option High'] >= spot_data_select[i]['Short TP']:    
            spot_data_select[i]['Short Position'] = 'Partial Exit Buy'
            spot_data_select[i]['Short Exit Price'] = spot_data_select[i]['Short TP']
            spot_data_select[i]['Short P&L'] = (spot_data_select[i]['Short Exit Price'] - spot_data_select[i]['Short Buy Price']) * 1 * lotsize_mapping[symbol]
        elif spot_data_select[i]['Short Option Low'] <= spot_data_select[i]['Short SL']:
            spot_data_select[i]['Short Position'] = 'Exit Buy'
            spot_data_select[i]['Short Exit Price'] = spot_data_select[i]['Short SL']
            spot_data_select[i]['Short P&L'] = (spot_data_select[i]['Short Exit Price'] - spot_data_select[i]['Short Buy Price']) * 2 * lotsize_mapping[symbol]
        elif time_now == datetime(2020,1,1,15,19,0).time():
            spot_data_select[i]['Short Position'] = 'Exit Buy'
            spot_data_select[i]['Short Exit Price'] = spot_data_select[i]['Short Option Close']
            spot_data_select[i]['Short P&L'] = (spot_data_select[i]['Short Exit Price'] - spot_data_select[i]['Short Buy Price']) * 2 * lotsize_mapping[symbol]
        else:
            spot_data_select[i]['Short Position'] = 'Buy'
            spot_data_select[i]['Short Exit Price'] = np.nan
            spot_data_select[i]['Short P&L'] = np.nan
        spot_data_select[i]['Cycle Short Count'] = 1
            
    elif spot_data_select[i-1]['Short Position'] == 'Partial Exit Buy':
        
        spot_data_select[i]['Short Option Ticker'] = spot_data_select[i-1]['Short Option Ticker']
        
        spot_data_select[i]['Short Reference Period High'] = spot_data_select[i-1]['Short Reference Period High']
        spot_data_select[i]['Short Reference Period Low'] = spot_data_select[i-1]['Short Reference Period Low']
        
        opt_hlc = get_option_price(data_select, spot_data_select[i]['Short Option Ticker'], time_now)
        spot_data_select[i]['Short Option High'] = opt_hlc[0]
        spot_data_select[i]['Short Option Low'] = opt_hlc[1]
        spot_data_select[i]['Short Option Close'] = opt_hlc[2]
        spot_data_select[i]['Short Buy Price'] = spot_data_select[i-1]['Short Buy Price']
        spot_data_select[i]['Short TP'] = spot_data_select[i-1]['Short TP']
        spot_data_select[i]['Short Trail TP'] = round(((spot_data_select[i-1]['Short Option Close'] + spot_data_select[i-1]['Short TP']) / 2) / 0.05) * 0.05 if spot_data_select[i-1]['Short Option Close'] > spot_data_select[i-1]['Short TP'] else spot_data_select[i-1]['Short Trail TP']
        spot_data_select[i]['Short SL'] = spot_data_select[i-1]['Short SL']
        
        if spot_data_select[i]['Short Option Low'] <= spot_data_select[i]['Short SL']:
            spot_data_select[i]['Short Position'] = 'Exit Buy'
            spot_data_select[i]['Short Exit Price'] = spot_data_select[i]['Short SL']
            spot_data_select[i]['Short P&L'] = (spot_data_select[i]['Short Exit Price'] - spot_data_select[i]['Short Buy Price']) * 1 * lotsize_mapping[symbol]
        elif spot_data_select[i]['Short Option Low'] <= spot_data_select[i]['Short Trail TP']:    
            spot_data_select[i]['Short Position'] = 'Exit Buy'
            spot_data_select[i]['Short Exit Price'] = spot_data_select[i]['Short Trail TP']
            spot_data_select[i]['Short P&L'] = (spot_data_select[i]['Short Exit Price'] - spot_data_select[i]['Short Buy Price']) * 1 * lotsize_mapping[symbol]  
        elif time_now == datetime(2020,1,1,15,19,0).time():
            spot_data_select[i]['Short Position'] = 'Exit Buy'
            spot_data_select[i]['Short Exit Price'] = spot_data_select[i]['Short Option Close']
            spot_data_select[i]['Short P&L'] = (spot_data_select[i]['Short Exit Price'] - spot_data_select[i]['Short Buy Price']) * 1 * lotsize_mapping[symbol]
        else:
            spot_data_select[i]['Short Position'] = 'Partial Exit Buy'
            spot_data_select[i]['Short Exit Price'] = np.nan
            spot_data_select[i]['Short P&L'] = np.nan
        spot_data_select[i]['Cycle Short Count'] = 1
                        
    return spot_data_select

s = 'NIFTY'

for s in ['BANKNIFTY']:

    spot_data_instr = pd.read_csv('spot_data_' + s + '.csv')
    spot_data_instr.columns = ['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI']
    spot_data_instr['Timestamp'] = spot_data_instr['Timestamp'].apply(lambda x: datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
    spot_data_instr['Date'] = spot_data_instr['Timestamp'].apply(lambda x: x.date())
    spot_data_instr['Time'] = spot_data_instr['Timestamp'].apply(lambda x: datetime(x.year, x.month, x.day, x.hour, x.minute, 0).time())
    spot_data_instr = spot_data_instr.loc[:,['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    spot_data_instr = spot_data_instr.loc[spot_data_instr['Time'] < datetime(2020,1,1,15,30,0).time(),:]
    spot_data_instr = spot_data_instr.loc[spot_data_instr['Time'] >= datetime(2020,1,1,9,15,0).time(),:]
    
    spot_data_dates = sorted(spot_data_instr['Date'].unique().tolist())
    
    all_trades_data = pd.DataFrame()
    
    for f in filenames:
    
        date = f.split('_')[2][:8]
        
        print(datetime.strftime(datetime.strptime(date, '%d%m%Y'), '%Y-%m-%d'))
        
        try:
        
            month_year = datetime.strftime(datetime.strptime(date, '%d%m%Y'), '%b-%Y').upper()
            data = pd.read_csv('Data\\' + date[4:] + '\\' + month_year + '\\' + f)
            data['Date'] = data['Date'].apply(lambda x: datetime.strptime(x, '%d/%m/%Y').date())
            data['Time'] = data['Time'].apply(lambda x: datetime(2000,1,1,int(x.split(':')[0]),int(x.split(':')[1]),0).time())
            data = data.loc[data['Time'] < datetime(2020,1,1,15,30,0).time(),:]
            data = data.loc[data['Time'] >= datetime(2020,1,1,9,15,0).time(),:]
            
            spot_data_select = spot_data_instr.loc[spot_data_instr['Date'] == datetime.strptime(date, '%d%m%Y').date(), :]
            prev_date = spot_data_dates[spot_data_dates.index(datetime.strptime(date, '%d%m%Y').date()) - 1]
            spot_data_prev = spot_data_instr.loc[spot_data_instr['Date'] == prev_date, :]
            
            spot_data_select = spot_data_select.to_dict('records')
            spot_data_prev = spot_data_prev.to_dict('records')
            
            opt_symbols = set(list(data['Ticker'].tolist()))
            opt_symbols = [x for x in opt_symbols if 'I.NFO' not in x]
            
            opt_dict = []
            for o in opt_symbols:
                symbol = 'BANKNIFTY' if 'BANKNIFTY' in o else 'NIFTY'
                exp_date = datetime.strptime(o.replace(symbol,'')[:7], '%d%b%y').date()
                opt_type = o.replace(symbol,'').replace(exp_date.strftime('%d%b%y').upper(),'').replace('.NFO','')
                strike = int(opt_type.replace('CE','').replace('PE',''))
                opt_type = 'CE' if 'CE' in opt_type else 'PE'    
                opt_dict.append({'Ticker': o, 'Symbol': symbol, 'Expiry Date': exp_date, 'Strike': strike, 'Option Type': opt_type})
            
            all_expiry = sorted([x['Expiry Date'] for x in opt_dict])
            near_expiry = all_expiry[0]
            
            opt_dict = [x for x in opt_dict if x['Expiry Date'] == near_expiry]
            
            data_select = data.loc[data['Ticker'].isin(opt_symbols),:]
            data_select = data_select.to_dict('records')
            
            prev_date = prev_date.strftime('%d%m%Y')
            month_year_prev = datetime.strftime(datetime.strptime(prev_date, '%d%m%Y'), '%b-%Y').upper()
            
            data_prev = pd.read_csv('Data\\' + prev_date[4:] + '\\' + month_year_prev + '\\GFDLNFO_OPTIONS_' + prev_date + '.csv')
            data_prev['Date'] = data_prev['Date'].apply(lambda x: datetime.strptime(x, '%d/%m/%Y').date())
            data_prev['Time'] = data_prev['Time'].apply(lambda x: datetime(2000,1,1,int(x.split(':')[0]),int(x.split(':')[1]),0).time())
            data_prev = data_prev.loc[data_prev['Time'] < datetime(2020,1,1,15,30,0).time(),:]
            data_prev = data_prev.loc[data_prev['Time'] >= datetime(2020,1,1,9,15,0).time(),:]
            
            data_prev_select = data_prev.loc[data_prev['Ticker'].isin(opt_symbols),:]
            data_prev_select = data_prev_select.to_dict('records')
            
            reference_period_data = []
            reference_period_data_opt = []
            for i in range(len(spot_data_select)):
                
                # print(i)
                
                time_now = spot_data_select[i]['Time']
                
                #try:
                
                # If it is 9:16 evaluation, check for gap 
                if time_now.strftime('%H:%M') in strat_eval_times:
                    
                    if time_now.strftime('%H:%M') == strat_eval_times[0]:
                    
                        # If there is a gap, consider bar from 9:15 to 9:25, else, consider the 75 min bar
                        prev_close = [x['Close'] for x in spot_data_prev if x['Time'] == datetime(2020,1,1,15,29,0).time()][0]
                        curr_open = [x['Open'] for x in spot_data_select if x['Time'] == datetime(2020,1,1,9,15,0).time()][0]
                        gap_abs = (curr_open - prev_close) / prev_close
                        gap = 'YES' if abs(gap_abs) >= GAP_THRESHOLD else 'NO'
                        
                        if gap == 'YES':
                            reference_period_data = [x for x in spot_data_select if x['Time'] >= datetime(2020,1,1,9,15,0).time() and x['Time'] <= datetime(2020,1,1,9,24,0).time()]
                            spot_data_select[i]['Trade Scheduled Time'] = datetime.strptime(GAP_TRADE_TIME, '%H:%M').time()
                            reference_period_data_opt = [x for x in data_select if x['Time'] >= datetime(2020,1,1,9,15,0).time() and x['Time'] <= datetime(2020,1,1,9,24,0).time()]
                            
                        else:
                            reference_period_data = [x for x in spot_data_prev if x['Time'] >= datetime.strptime(reference_bar_start_times[0], '%H:%M').time() and x['Time'] <= datetime.strptime(reference_bar_end_times[0], '%H:%M').time()]
                            spot_data_select[i]['Trade Scheduled Time'] = time_now            
                            reference_period_data_opt = [x for x in data_prev_select if x['Time'] >= datetime.strptime(reference_bar_start_times[0], '%H:%M').time() and x['Time'] <= datetime.strptime(reference_bar_end_times[0], '%H:%M').time()]
                            
                    else:
                        # If it is not the 9:16 evaluation, consider the 75 min bar
                        reference_period_data = [x for x in spot_data_select if x['Time'] >= datetime.strptime(reference_bar_start_times[strat_eval_times.index(time_now.strftime('%H:%M'))], '%H:%M').time() and x['Time'] <= datetime.strptime(reference_bar_end_times[strat_eval_times.index(time_now.strftime('%H:%M'))], '%H:%M').time()]
                        spot_data_select[i]['Trade Scheduled Time'] = time_now
                        reference_period_data_opt = [x for x in data_select if x['Time'] >= datetime.strptime(reference_bar_start_times[strat_eval_times.index(time_now.strftime('%H:%M'))], '%H:%M').time() and x['Time'] <= datetime.strptime(reference_bar_end_times[strat_eval_times.index(time_now.strftime('%H:%M'))], '%H:%M').time()]    
                    
                    spot_data_select[i]['Reference Period High'] = max([x['High'] for x in reference_period_data])
                    spot_data_select[i]['Reference Period Low'] = min([x['Low'] for x in reference_period_data])
                    
                    spot_data_select[i]['Call Strike'] = int(math.floor(spot_data_select[i]['Reference Period High'] / float(min_strike_incr_mapping[s])))*min_strike_incr_mapping[s]
                    spot_data_select[i]['Put Strike'] = int(math.ceil(spot_data_select[i]['Reference Period Low'] / float(min_strike_incr_mapping[s])))*min_strike_incr_mapping[s]
                    
                    spot_data_select[i]['Cycle Long Count'] = 0
                    spot_data_select[i]['Cycle Short Count'] = 0
                    
                    # Long Position, Long Option Ticker, Long Option Price, Long Buy Price, Long SL, Long TP, Long Trail TP
                    # Short Position, Short Option Ticker, Short Option Price, Short Buy Price, Short SL, Short TP, Short Trail TP
                    
                    spot_data_select = update_long_position(data_select, spot_data_select, opt_dict, reference_period_data_opt, s, time_now, i)
                    spot_data_select = update_short_position(data_select, spot_data_select, opt_dict, reference_period_data_opt, s, time_now, i)
                    
                    # if spot_data_select[i-1]['Short Position'] in ['', 'Exit Short']:
                    #     pass
                    # else:
                    #     pass
                                 
                else:
                    if time_now.strftime('%H:%M') != '09:15':
                        if time_now == spot_data_select[i-1]['Trade Scheduled Time']:
                            spot_data_select[i]['Trade Scheduled Time'] = time_now
                        else:    
                            spot_data_select[i]['Trade Scheduled Time'] = spot_data_select[i-1]['Trade Scheduled Time']
                        spot_data_select[i]['Reference Period High'] = spot_data_select[i-1]['Reference Period High']
                        spot_data_select[i]['Reference Period Low'] = spot_data_select[i-1]['Reference Period Low']
                        spot_data_select[i]['Call Strike'] = spot_data_select[i-1]['Call Strike']
                        spot_data_select[i]['Put Strike'] = spot_data_select[i-1]['Put Strike']
                        
                        spot_data_select[i]['Cycle Long Count'] = spot_data_select[i-1]['Cycle Long Count']
                        spot_data_select[i]['Cycle Short Count'] = spot_data_select[i-1]['Cycle Short Count']
                        
                        spot_data_select = update_long_position(data_select, spot_data_select, opt_dict, reference_period_data_opt, s, time_now, i)
                        spot_data_select = update_short_position(data_select, spot_data_select, opt_dict, reference_period_data_opt, s, time_now, i)
                        
                    else:
                        spot_data_select[i]['Trade Scheduled Time'] = None
                        spot_data_select[i]['Reference Period High'] = np.nan
                        spot_data_select[i]['Reference Period Low'] = np.nan
                        spot_data_select[i]['Call Strike'] = np.nan
                        spot_data_select[i]['Put Strike'] = np.nan
                        
                        spot_data_select[i]['Cycle Long Count'] = 0
                        spot_data_select[i]['Cycle Short Count'] = 0
                        
                        spot_data_select[i]['Long Position'] = ''
                        spot_data_select[i]['Long Option Ticker'] = None
                        spot_data_select[i]['Long Reference Period High'] = np.nan
                        spot_data_select[i]['Long Reference Period Low'] = np.nan
                        spot_data_select[i]['Long Option High'] = np.nan
                        spot_data_select[i]['Long Option Low'] = np.nan
                        spot_data_select[i]['Long Option Close'] = np.nan
                        spot_data_select[i]['Long Buy Price'] = np.nan
                        spot_data_select[i]['Long TP'] = np.nan
                        spot_data_select[i]['Long Trail TP'] = np.nan
                        spot_data_select[i]['Long SL'] = np.nan
                        spot_data_select[i]['Long Exit Price'] = np.nan
                        spot_data_select[i]['Long P&L'] = np.nan
                        
                        spot_data_select[i]['Short Position'] = ''
                        spot_data_select[i]['Short Option Ticker'] = None
                        spot_data_select[i]['Short Reference Period High'] = np.nan
                        spot_data_select[i]['Short Reference Period Low'] = np.nan
                        spot_data_select[i]['Short Option High'] = np.nan
                        spot_data_select[i]['Short Option Low'] = np.nan
                        spot_data_select[i]['Short Option Close'] = np.nan
                        spot_data_select[i]['Short Buy Price'] = np.nan
                        spot_data_select[i]['Short TP'] = np.nan
                        spot_data_select[i]['Short Trail TP'] = np.nan
                        spot_data_select[i]['Short SL'] = np.nan
                        spot_data_select[i]['Short Exit Price'] = np.nan
                        spot_data_select[i]['Short P&L'] = np.nan
                            
                #except Exception as e:
                #    print(e)
                
            spot_data_select = pd.DataFrame(spot_data_select)
            
            all_trades_data = pd.concat([all_trades_data, spot_data_select], axis=0)
            ''
        except Exception as e:
            print(e)
            print('Skipping date: ' + datetime.strftime(datetime.strptime(date, '%d%m%Y'), '%Y-%m-%d'))
    
    all_trades_data['P&L'] = all_trades_data['Long P&L'].fillna(0) + all_trades_data['Short P&L'].fillna(0)
    
    def calc_perf_metrics(data):
        
        data['Year'] = data['Date'].apply(lambda x: x.year)
        data['Cumulative P&L'] = data.groupby('Year')['P&L'].fillna(0).cumsum()
        data['Rolling Max P&L'] = data.groupby('Year')['Cumulative P&L'].cummax()
        data['Drawdown'] = data['Cumulative P&L'] - data['Rolling Max P&L']
        
        years = data['Year'].unique().tolist()
        
        output_df = pd.DataFrame()
        for y in years:
            data_select = data.loc[data['Year'] == y, :]
            
            days_cnt = data_select['Date'].nunique()
            trades_cnt = len(data_select.loc[data_select['Short Position'] == 'Exit Buy',:]) + len(data_select.loc[data_select['Long Position'] == 'Exit Buy',:])
            pnl = data_select['P&L'].sum()
            winning_trades_cnt = len(data_select.loc[np.logical_and(data_select['Short Position'] == 'Exit Buy', data_select['Short P&L'] > 0),:]) + len(data_select.loc[np.logical_and(data_select['Long Position'] == 'Exit Buy', data_select['Long P&L'] > 0),:])
            losing_trades_cnt = len(data_select.loc[np.logical_and(data_select['Short Position'] == 'Exit Buy', data_select['Short P&L'] <= 0),:]) + len(data_select.loc[np.logical_and(data_select['Long Position'] == 'Exit Buy', data_select['Long P&L'] <= 0),:])
            win_perc = winning_trades_cnt / (winning_trades_cnt + losing_trades_cnt)
            avg_profit_per_winning_trade = (data_select.loc[data_select['Short P&L'] > 0,'Short P&L'].sum() + data_select.loc[data_select['Long P&L'] > 0,'Long P&L'].sum()) / winning_trades_cnt
            avg_loss_per_losing_trade = (data_select.loc[data_select['Short P&L'] <= 0,'Short P&L'].sum() + data_select.loc[data_select['Long P&L'] <= 0,'Long P&L'].sum()) / losing_trades_cnt
            risk_reward = avg_profit_per_winning_trade / abs(avg_loss_per_losing_trade)
            max_drawdown = data_select['Drawdown'].min()
            max_drawdown = abs(max_drawdown) if max_drawdown < 0 else 0
            calmar_ratio = pnl / max_drawdown
            expectancy = avg_profit_per_winning_trade*win_perc + avg_loss_per_losing_trade*(1-win_perc)
            
            select_output_li = [y, days_cnt, trades_cnt, pnl, winning_trades_cnt, losing_trades_cnt, win_perc, 
                         avg_profit_per_winning_trade, avg_loss_per_losing_trade, risk_reward, 
                         max_drawdown, calmar_ratio, expectancy]
            select_output_df = pd.DataFrame(select_output_li).transpose()
            select_output_df.columns = ['Year', 'Days', 'No. Trades', 'P&L Points', 'Winning Trades', 'Losing Trades', 'Win %', 
                                        'Avg. Win', 'Avg. Loss', 'R/R', 'Max DD', 'Calmar Ratio', 'Expectancy']
            output_df = pd.concat([output_df, select_output_df], axis=0)
            
        return output_df
    
    output = calc_perf_metrics(all_trades_data)
    
    all_trades_data.to_csv('backtest_trades_' + s + '_2020_TP' + str(TARGET*100) + '.csv', index=False)
    output.to_csv('backtest_results_' + s + '_2020_TP' + str(TARGET*100) + '.csv', index=False)
    
print('Time taken: ' + (str(round(time.time() - start, 2))))