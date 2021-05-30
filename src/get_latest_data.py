from truedata_ws.websocket.TD import TD
from func_timeout import func_timeout, FunctionTimedOut
import time
from Intraday_1.config import TD_USERNAME, TD_PASSWORD

realtime_port = 8082
history_port = 8092

def connect_to_TD(SYMBOLS):

    while True:
        try:
            print('Connecting to TrueData...')
            td_app = func_timeout(10, TD, kwargs=({'login_id':TD_USERNAME, 'password':TD_PASSWORD, 'live_port':realtime_port, 'historical_port':history_port}))
            req_ids = td_app.start_live_data(SYMBOLS)
            break
        except FunctionTimedOut:
            pass
        except:
            pass
        
    return td_app, req_ids

def get_data_underlyings(td_app, SYMBOLS):
    
    data_1min = {}
    for symbol in SYMBOLS:
        
        i = 0
        while i < 10:
            print(symbol + ' data extraction: Attempt ' + str(i+1))
        
            try:
                data_1min[symbol] = td_app.get_historic_data(symbol, duration='3 D', bar_size='1 min')
                #data_1min[symbol] = data_1min[symbol][0]
                break
            except:
                i += 1
        
    return data_1min

def get_data_options(td_app, contract_symbols):
    
    data_1min = {}
    for contract in contract_symbols:
        
        i = 0
        while i < 10:
            print(contract + ' data extraction: Attempt ' + str(i+1))
            
            try:
                data_1min[contract] = td_app.get_historic_data(contract, duration='3 D', bar_size='1 min')
                #data_1min[contract] = data_1min[contract][0]
                break
            except:
                i += 1
                
    return data_1min

def main():
    
    td_app, req_ids = connect_to_TD()
    time.sleep(1)
    data_1min = get_data_underlyings(td_app)
    
    return data_1min

if __name__ == '__main__':
    data_1min = main()
