import math
# from decimal import Decimal
import time
from typing import Dict, Union

import json
import datetime

import numpy as np
# import pandas as pd

import jesse.helpers as jh
import jesse.utils as utils

import csv
from jesse.config import config
#
from jesse.services.candle import generate_candle_from_one_minutes, print_candle, candle_includes_price, split_candle
from jesse.libs import DynamicNumpyArray
#_store
# from jesse.enums import timeframes

def normal_trailing_tp1(str):
    if str.is_long:
        str.stop_loss   = abs(str.position.qty), str.price - str.atr * str.lvars["atr_sl_multiplier"]
        if str.vars["trailing_stoploss"]:
            str.take_profit = [
                (abs(str.position.qty) / 2, str.price + str.atr* str.lvars["atr_tp_multiplier"] / 2),
                (abs(str.position.qty) / 2, str.price + str.atr* str.lvars["atr_tp_multiplier"])
            ]
        else:
            str.take_profit = abs(str.position.qty), str.price + str.atr * str.lvars["atr_tp_multiplier"]    
    if str.is_short:
        str.stop_loss   = abs(str.position.qty), str.price + str.atr * str.svars["atr_sl_multiplier"]
        if str.vars["trailing_stoploss"]:
            str.take_profit = [
                (abs(str.position.qty) / 2, str.price - str.atr* str.svars["atr_tp_multiplier"] / 2),
                (abs(str.position.qty) / 2, str.price - str.atr* str.svars["atr_tp_multiplier"])
            ]
        else:
            str.take_profit = abs(str.position.qty), str.price - str.atr * str.svars["atr_tp_multiplier"]   

def timestamp_to_gmt7(timestamp):
    return datetime.datetime.utcfromtimestamp(timestamp + 7 *3600).strftime('%Y-%m-%d %H:%M')

def write_csv(filename, header, data):
    filename = f'strategies/VWAP/debug/' + filename +"-"+ str(datetime.datetime.now().timestamp()) + ".csv" 
    with open(filename, 'w', encoding='UTF8') as f:
        writer = csv.writer(f)

        # write the header
        writer.writerow(header)

        # write the data
        writer.writerows(data)
        f.close()

def write_pine(filename, initial_capital, data):
    filename = f'strategies/VWAP/debug/' + filename +"-"+ str(datetime.datetime.now().timestamp()) + ".pine"
    f = open(filename, 'w')
    f.write(f'//@version=4 \n')
    f.write(f'strategy("backtest", overlay=true, initial_capital={initial_capital}, commission_type=strategy.commission.percent, commission_value=0.00)\n')
    f.write(data)
    f.close()


def load_params(filename):
    f = open(filename, 'r')
    json_object = json.loads(f.read())
    f.close()
    return json_object

def save_params(filename, vars):
    json_object = json.dumps(vars, indent = 4)
    f = open(filename, 'w')
    f.write(json_object)
    f.close()


def ctf_forming_estimation(self, exchange: str, symbol: str, timeframe: str) -> tuple:
    long_key = jh.key(exchange, symbol, timeframe)
    short_key = jh.key(exchange, symbol, '1m')
    required_1m_to_complete_count = jh.timeframe_to_one_minutes(timeframe)
    current_1m_count = len(self.get_storage(exchange, symbol, '1m'))

    dif = current_1m_count % required_1m_to_complete_count
    # CTF, dif reset at 00:00
    if current_1m_count % 1440  == 0:
        dif = 0
    return dif, long_key, short_key
    
# # Generate candles from one minute data
# def generate_realtime_ctf_candle(self, exchange: str, symbol: str) -> np.ndarray:
#     # generate and add candles for bigger timeframes
#     for timeframe in config['app']['ctf_timeframes']:
#         dif, long_key, short_key = ctf_forming_estimation(exchange, symbol, timeframe)
#         long_count = len(store.candles.get_storage(exchange, symbol, timeframe))
#         short_count = len(store.candles.get_storage(exchange, symbol, '1m'))

#         # complete candle
#         # CTF Hack: Reset Candle at of
#         # i_timeframe = jh.timeframe_to_one_minutes(timeframe)
#         if (short_count % 1440 == 0 and short_count > 0) and dif != 0:
#         # if dif != 0:
#             return generate_candle_from_one_minutes(
#                 timeframe, store.candles.storage[short_key][short_count - dif:short_count],
#                 True
#             )
#         if long_count == 0:
#             return np.zeros((0, 6))
#         else:
#             return store.candles.storage[long_key][-1]  



def minutes_from_reset_time():
    now = (jh.now()//60000) % 1440
    return now


def generate_ctf_candles(candles: np.ndarray, exchange: str,symbol: str):
    # generate and add candles for bigger timeframes
    # logger.info(f"generate_ctf_candles ")
    import jesse.services.logger as logger
    from jesse.store import store   
    
    for timeframe in config['app']['ctf_timeframes']:

        # logger.info(f"generate_ctf_candles {timeframe}")
        # for 1m, no work is needed
        if timeframe == '1m':
            continue

        count = jh.timeframe_to_one_minutes(timeframe)

        i = minutes_from_reset_time()
        
        # Only reset when timeframe < 1D
        #if count < 1440:
        
        #k = (i + 1439) % 1440  
        k = i % 1440
        # Last candle of the day, it's not a full candle 
        # logger.info (f"K {k} count {count} i={i}")
        # logger.info(f"---len {len(candles)}")
        c = round(k % count)
        if i == 0:
            """
            Last candle of the day.
            """
            c = round(1440 - (1440 // count) * count)
            # logger.info(f"Last candle: Generating full candle c = {c} - i = {i}")
            generated_candle = generate_candle_from_one_minutes(
                timeframe,
                candles[-c:],
                True)
            store.candles.add_candle(generated_candle, exchange, symbol, timeframe, with_execution=False,
                                        with_generation=False)
            # logger.info(f"Generating short candle k = {k} - i = {i} ts ={generated_candle[0]}")
            logger.info(f"Last candle of day: c = {c} - i = {i} ts={generated_candle}")
            print_candle(generated_candle, True, symbol)
        else:
            # logger.info(f"Generating with c = {c}")
            # Full candle exclude first candle of day
            if c == 0:

                """
                Full candle
                """

                # logger.info(f"Generating full candle c = {c} - i = {len(candles[-count-1:-1])}")
                generated_candle = generate_candle_from_one_minutes(
                    timeframe,
                    candles[-count:])
                store.candles.add_candle(generated_candle, exchange, symbol, timeframe, with_execution=False,
                                        with_generation=False)        
                # logger.info(f"Generating full candle c = {c} - i = {i} ts ={generated_candle[0]}")
                logger.info(f"Full candle:  c = {c} - i = {i} ts={generated_candle}")
                print_candle(generated_candle, False, symbol)
            else:           
                """
                Short candle
                """ 
                # logger.info(f"Generating short candle c = {c} - i = {c+1}") #  {len(candles[-c-1:-1])}")
                generated_candle = generate_candle_from_one_minutes(
                    timeframe,
                    candles[-c:],
                    True)
                store.candles.add_candle(generated_candle, exchange, symbol, timeframe, with_execution=False,
                                            with_generation=False)
                # logger.info(f"Generating short candle c = {c} - i = {i} ts ={generated_candle[0]}")
                logger.info(f"Short candle: c = {c} - i = {i} ts={generated_candle}")
                print_candle(generated_candle, True, symbol)

def hook(hookfunc, oldfunc):
    def foo(*args, **kwargs):
        hookfunc(*args, **kwargs)
        return oldfunc(*args, **kwargs)
    return foo

def new_on_new_candle(*args, **kwargs):
    utils.log("**********New Candle Hook")
    for arg in args:
        utils.log.info(arg)    
    for key, value in kwargs.items():
        utils.log.info("%s == %s" %(key, value))

