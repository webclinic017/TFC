from jesse.strategies import Strategy, cached
import jesse.indicators as ta
from jesse import utils
import numpy as np
import jesse.helpers as jh
from wt import wt
from rsimfi import rsimfi
import utils as tu
from strategies.TFC.utils import utils as tu
import strategies.TFC.lib as lib
from jesse.helpers import get_candle_source, slice_candles


class TFC(Strategy):
    def __init__(self):
        super().__init__()
        self.debug_log                              = 1          ## Turn on for debug logging to CSV, 
        self.price_precision                        = 2 		#self._price_precision()
        self.hps                                    = []
        self.svars                                  = {}
        self.lvars                                  = {}
        self.data_header                            = ['Index', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Action', 'Cmt', 'Starting Balance', 'Finishing Balance', 'Profit', 'Qty','SL','TP']
        self.data_log                               = []
        self.indicator_header                       = ['Index', 'Time', ]
        self.indicator_log                          = []

        self.pine_log                               = ''
        self.pine_orderid                           = 0

        self.sliced_candles                         = {}
        self.is_optimising                          = False
        self.params_overdrive                       = True          ## Overwrite params to file, turn off for production, turn on for testing / optimizing

        self.pre_index                              = 0
        self.qty                                    = 0

        self.long_sl                                = 0
        self.long_tp                                = 0
        self.short_sl                               = 0
        self.short_tp                               = 0

        self.initial_entry                          = 0
        self.starting_capital                       = 0
        self.starting_balance                       = 0

        self.onlyLong                               = False         # True: Only Long Position
        self.onlyShort                              = False         # True: Only Short Position
        self.LS                                     = True          # True: Long and Short Position

        self.vars["enableLong"]                     = True          # Enable Long Entry
        self.vars["enableShort"]                    = True          # Enable Short Entry
        self.vars["botRisk"]                        = 2             # Bot Risk % each entry
        # self.botLeverage                            = 10          # Bot Leverage
        self.vars["botPricePrecision"]              = 2             # Bot Order Price Precision
        self.vars["botBasePrecision"]               = 3             # Bot Order Coin Precision
        self.vars["atrLength"]                      = 14            # ATR Length
        self.vars["atrSmoothing"]                   = 'RMA'         # ATR Smoothing
        self.vars["getConfirmation"]                = True          # Get Trend Confirmation from longer timeframe?
        self.vars["confirmationResolution"]         = 'D'           # Confirmation Timeframe
        self.vars["lrsiApplyFractalsEnergy"]        = True          # LRSI: Apply Fractals Energy?
        self.vars["lrsiApplyNormalization"]         = False         # LRSI:Apply Normalization to [0, 100]?
        
        # Long
        self.lvars["AtrSLMultipier"]                = 1.6           # Short ATR SL Multipier
        self.lvars["AtrTPMultipier"]                = 3             # Short ATR TP Multipier
        self.lvars["enableTrailingSL"]              = False         # Enable Trailing SL Type 1
        self.lvars["trailingSLPercent"]             = 0.5           # Trailing SL 1 Percent
        self.lvars["enableTrailingSL2"]             = True          # Enable Trailing SL Type 2: 3 steps
        self.lvars["trailingSLPercent1"]            = 0.8           # Step 1: Red Zone
        self.lvars["trailingSLPercent2"]            = 1             # Step 2: Red Zone
        self.lvars["trailingSLPercent3"]            = 1.1           # Step 3: Green Zone
        self.lvars["trailingTrigger1"]              = 0.33          # Step 1 Trigger: Low > X%
        self.lvars["trailingTrigger2"]              = 0.66          # Step 2 Trigger: High > X%

        self.lvars["st1Factor"]                     = 1.5           # SuperTrend 1: Factor
        self.lvars["st1Period"]                     = 7             # SuperTrend 1: Period
        self.lvars["st2Factor"]                     = 1.65          # SuperTrend 2: Factor
        self.lvars["st2Period"]                     = 100           # SuperTrend 2: Period    
        self.lvars["emaFast"]                       = 8             # EMA Cross: Fast
        self.lvars["emaSlow"]                       = 15            # EMA Cross: Slow
        self.lvars["aroonLength"]                   = 8             # Aroon: Length
        self.lvars["dmiLength"]                     = 8             # DMI: Length
        self.lvars["lrsiAlpha"]                     = 0.7           # LRSI: Alpha
        self.lvars["lrsiFeLength"]                  = 13            # LRSI: Fractals Energy Length
        self.lvars["threshold"]                     = 3             # Indicator Threshold
        
        # Short
        self.svars["AtrSLMultipier"]                = 1.6           # Short ATR SL Multipier
        self.svars["AtrTPMultipier"]                = 3             # Short ATR TP Multipier
        self.svars["enableTrailingSL"]              = False         # Enable Trailing SL Type 1
        self.svars["trailingSLPercent"]             = 0.5           # Trailing SL 1 Percent
        self.svars["enableTrailingSL2"]             = True          # Enable Trailing SL Type 2: 3 steps
        self.svars["trailingSLPercent1"]            = 0.8           # Step 1: Red Zone
        self.svars["trailingSLPercent2"]            = 1             # Step 2: Red Zone
        self.svars["trailingSLPercent3"]            = 1.1           # Step 3: Green Zone
        self.svars["trailingTrigger1"]              = 0.33          # Step 1 Trigger: Low > X%
        self.svars["trailingTrigger2"]              = 0.66          # Step 2 Trigger: High > X%

        self.svars["st1Factor"]                     = 1.5           # SuperTrend 1: Factor
        self.svars["st1Period"]                     = 7             # SuperTrend 1: Period
        self.svars["st2Factor"]                     = 1.65          # SuperTrend 2: Factor
        self.svars["st2Period"]                     = 100           # SuperTrend 2: Period    
        self.svars["emaFast"]                       = 8             # EMA Cross: Fast
        self.svars["emaSlow"]                       = 15            # EMA Cross: Slow
        self.svars["aroonLength"]                   = 8             # Aroon: Length
        self.svars["dmiLength"]                     = 8             # DMI: Length
        self.svars["lrsiAlpha"]                     = 0.7           # LRSI: Alpha
        self.svars["lrsiFeLength"]                  = 13            # LRSI: Fractals Energy Length
        self.svars["threshold"]                     = 3             # Indicator Threshold

        self.longStop                               = 0
        self.longProfit1                            = 0
        self.longProfit2                            = 0
        self.shortStop                              = 0
        self.shortProfit1                           = 0
        self.shortProfit2                           = 0
        self.entryPrice                             = 0
        self.entryAtr                               = 0
        self.trailSLStep                            = 0
        self.trailTPStep                            = 0
        self.pyramiding                             = 0

        self.st1TrendUp_Tf1                         = 0.0
        self.st1TrendDown_Tf1                       = 0.0
        self.st1Trend_Tf1                           = 0.0
        self.pre_st1TrendUp_Tf1                     = 0.0
        self.pre_st1TrendDown_Tf1                   = 0.0
        self.pre_st1Trend_Tf1                       = 0.0
        # self.pre_close                              = 0
        self.st1TrendUp_Tf2                         = 0.0
        self.st1TrendDown_Tf2                       = 0.0
        self.st1Trend_Tf2                           = 0.0
        self.pre_st1TrendUp_Tf2                     = 0.0
        self.pre_st1TrendDown_Tf2                   = 0.0
        self.pre_st1Trend_Tf2                       = 0.0
        
        self.st2TrendUp_Tf1                         = 0.0
        self.st2TrendDown_Tf1                       = 0.0
        self.st2Trend_Tf1                           = 0.0
        self.pre_st2TrendUp_Tf1                     = 0.0
        self.pre_st2TrendDown_Tf1                   = 0.0
        self.pre_st2Trend_Tf1                       = 0.0
        # self.pre_close                              = 0
        self.st2TrendUp_Tf2                         = 0.0
        self.st2TrendDown_Tf2                       = 0.0
        self.st2Trend_Tf2                           = 0.0
        self.pre_st2TrendUp_Tf2                     = 0.0
        self.pre_st2TrendDown_Tf2                   = 0.0
        self.pre_st2Trend_Tf2                       = 0.0



    def hyperparameters(self):
        return [ 

            {'name': 'longAtrSLMultipier', 'title': 'Long ATR SL Multipier', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.6},
            {'name': 'longAtrTPMultipier', 'title': 'Long ATR TP Multipier', 'type': float, 'min': 2.0, 'max': 6.0, 'default': 3.0},
            {'name': 'longTrailingSLPercent', 'title': 'Long Trailing SL Percent', 'type': float, 'min': 0.05, 'max': 0.95, 'default': 0.5},
            {'name': 'longTrailingSLPercent1', 'title': 'Long Trailing SL Percent Step 1: Red Zone',  'type': float,'min': 0.6, 'max': 1.0, 'default': 0.8},
            {'name': 'longTrailingSLPercent2', 'title': 'Long Trailing SL Percent Step 1: Red Zone', 'type': float, 'min': 0.8, 'max': 1.2, 'default': 1.0},
            {'name': 'longTrailingSLPercent3', 'title': 'Long Trailing SL Percent Step 3: Green Zone', 'type': float, 'min': 0.9, 'max': 1.3, 'default': 1.1},
            {'name': 'longTrailingTrigger1', 'title': 'Long Trailing Trigger 1 Step 1 Trigger: Low > X%', 'type': float, 'min': 0.1, 'max': 0.45, 'default': 0.33},
            {'name': 'LongTrailingTrigger2', 'title': 'Long Trailing Trigger 2 Step 2 Trigger: High > X%', 'type': float, 'min': 0.54, 'max': 0.89, 'default': 0.66},
            {'name': 'longSt1Factor', 'title': 'Long SuperTrend 1: Factor', 'type': float, 'min': 0.5, 'max': 3.0, 'default': 1.5},
            {'name': 'longSt1Period', 'title': 'Long SuperTrend 1: Period', 'type': int, 'min': 3, 'max': 10, 'default': 7},
            {'name': 'longSt2Factor', 'title': 'Long SuperTrend 2: Factor', 'type': float, 'min': 0.5, 'max': 3.0, 'default': 1.65},
            {'name': 'longSt2Period', 'title': 'Long SuperTrend 2: Period', 'type': int, 'min': 90, 'max': 110, 'default': 100},
            {'name': 'longEmaFast', 'title': 'Long EMA Fast', 'type': int, 'min': 5, 'max': 20, 'default': 8},
            {'name': 'longEmaSlow', 'title': 'Long EMA Slow', 'type': int, 'min': 10, 'max': 30, 'default': 15},
            {'name': 'longAroonLength', 'title': 'Long Aroon Length', 'type': int, 'min': 5, 'max': 20, 'default': 20},
            {'name': 'longDmiLength', 'title': 'Long DMI Length', 'type': int, 'min': 5, 'max': 20, 'default': 20},
            {'name': 'longLrsiAlpha', 'title': 'Long LRSI Alpha', 'type': float, 'min': 0.4, 'max': 0.9, 'default': 0.7},
            {'name': 'longLrsiFeLength', 'title': 'Long LRSI Fractals Energy Length', 'type': int, 'min': 5, 'max': 20, 'default': 13},
            {'name': 'longThreshold', 'title': 'Long Indicator Threshold', 'type': int, 'min': 1, 'max': 6, 'default': 3 }, 

            {'name': 'shortAtrSLMultipier', 'title': 'Short ATR SL Multipier', 'type': float, 'min': 1.0, 'max': 3.0, 'default': 1.6},
            {'name': 'shortAtrTPMultipier', 'title': 'Short ATR TP Multipier', 'type': float, 'min': 2.0, 'max': 6.0, 'default': 3.0},
            {'name': 'shortTrailingSLPercent', 'title': 'Short Trailing SL Percent', 'type': float, 'min': 0.05, 'max': 0.95, 'default': 0.5},
            {'name': 'shortTrailingSLPercent1', 'title': 'Short Trailing SL Percent Step 1: Red Zone',  'type': float,'min': 0.6, 'max': 1.0, 'default': 0.8},
            {'name': 'shortTrailingSLPercent2', 'title': 'Short Trailing SL Percent Step 1: Red Zone', 'type': float, 'min': 0.8, 'max': 1.2, 'default': 1.0},
            {'name': 'shortTrailingSLPercent3', 'title': 'Short Trailing SL Percent Step 3: Green Zone', 'type': float, 'min': 0.9, 'max': 1.3, 'default': 1.1},
            {'name': 'shortTrailingTrigger1', 'title': 'Short Trailing Trigger 1 Step 1 Trigger: Low > X%', 'type': float, 'min': 0.1, 'max': 0.45, 'default': 0.33},
            {'name': 'shortTrailingTrigger2', 'title': 'Short Trailing Trigger 2 Step 2 Trigger: High > X%', 'type': float, 'min': 0.54, 'max': 0.89, 'default': 0.66},
            {'name': 'shortSt1Factor', 'title': 'Short SuperTrend 1: Factor', 'type': float, 'min': 0.5, 'max': 3.0, 'default': 1.5},
            {'name': 'shortSt1Period', 'title': 'Short SuperTrend 1: Period', 'type': int, 'min': 3, 'max': 10, 'default': 7},
            {'name': 'shortSt2Factor', 'title': 'Short SuperTrend 2: Factor', 'type': float, 'min': 0.5, 'max': 3.0, 'default': 1.65},
            {'name': 'shortSt2Period', 'title': 'Short SuperTrend 2: Period', 'type': int, 'min': 90, 'max': 110, 'default': 100},
            {'name': 'shortEmaFast', 'title': 'Short EMA Fast', 'type': int, 'min': 5, 'max': 20, 'default': 8},
            {'name': 'shortEmaSlow', 'title': 'Short EMA Slow', 'type': int, 'min': 10, 'max': 30, 'default': 15},
            {'name': 'shortAroonLength', 'title': 'Short Aroon Length', 'type': int, 'min': 5, 'max': 20, 'default': 20},
            {'name': 'shortDmiLength', 'title': 'Short DMI Length', 'type': int, 'min': 5, 'max': 20, 'default': 20},
            {'name': 'shortLrsiAlpha', 'title': 'Short LRSI Alpha', 'type': float, 'min': 0.4, 'max': 0.9, 'default': 0.7},
            {'name': 'shortLrsiFeLength', 'title': 'Short LRSI Fractals Energy Length', 'type': int, 'min': 5, 'max': 20, 'default': 13},
            {'name': 'shortThreshold', 'title': 'Short Indicator Threshold', 'type': int, 'min': 1, 'max': 6, 'default': 3 }, 

        ]


    def on_first_candle(self):
        self.starting_balance = self.capital

        # print("On First Candle")
        if jh.is_livetrading():
            self.price_precision = self._price_precision()
            self.qty_precision = self._qty_precision()
        else:
            self.price_precision = 2
            self.qty_precision = 2

        # Load params from file if not loaded
        file_name = "params/" + type(self).__name__ + '_' + self.symbol + '_' + self.timeframe +'.json'
        vars = {}
        file_exists = jh.file_exists(file_name)
        if file_exists:
            fvars = tu.load_params(file_name)
            param_update = False
            if len(self.vars) + len(self.lvars) + len(self.svars) != len(fvars['common_vars']) + len(fvars['long_vars']) + len(fvars['short_vars']):
                # print("Params file is updated")
                param_update = True
            if not self.params_overdrive:
                self.vars  = fvars['common_vars']
                self.lvars = fvars['long_vars']
                self.svars = fvars['short_vars']
            if param_update:
                vars['common_vars'] = self.vars
                vars['long_vars']   = self.lvars
                vars['short_vars']  = self.svars
                tu.save_params(file_name, vars)
               
        else:
            # Write default params
            vars['common_vars'] = self.vars
            vars['long_vars']   = self.lvars
            vars['short_vars']  = self.svars
            tu.save_params(file_name, vars)

        if jh.is_optimizing():
            # Long
            self.lvars["AtrSLMultipier"]                = self.hp["longAtrSLMultipier"]
            self.lvars["AtrTPMultipier"]                = self.hp["longAtrTPMultipier"]
            self.lvars["trailingSLPercent"]             = self.hp["longTrailingSLPercent"]
            self.lvars["trailingSLPercent1"]            = self.hp["longTrailingSLPercent1"]
            self.lvars["trailingSLPercent2"]            = self.hp["longTrailingSLPercent2"]
            self.lvars["trailingSLPercent3"]            = self.hp["longTrailingSLPercent3"]
            self.lvars["trailingTrigger1"]              = self.hp["longTrailingTrigger1"]
            self.lvars["trailingTrigger2"]              = self.hp["longTrailingTrigger2"]
            self.lvars["st1Factor"]                     = self.hp["longSt1Factor"]
            self.lvars["st1Period"]                     = self.hp["longSt1Period"]
            self.lvars["st2Factor"]                     = self.hp["longSt2Factor"]
            self.lvars["st2Period"]                     = self.hp["longSt2Period"] 
            self.lvars["emaFast"]                       = self.hp["longEmaFast"]
            self.lvars["emaSlow"]                       = self.hp["longEmaSlow"]
            self.lvars["aroonLength"]                   = self.hp["longAroonLength"]
            self.lvars["dmiLength"]                     = self.hp["longDmiLength"]
            self.lvars["lrsiAlpha"]                     = self.hp["longLrsiAlpha"]
            self.lvars["lrsiFeLength"]                  = self.hp["longLrsiFeLength"]
            self.lvars["threshold"]                     = self.hp["longThreshold"]

            # Short
            self.svars["AtrSLMultipier"]                = self.hp["shortAtrSLMultipier"]
            self.svars["AtrTPMultipier"]                = self.hp["shortAtrTPMultipier"]
            self.svars["trailingSLPercent"]             = self.hp["shortTrailingSLPercent"]
            self.svars["trailingSLPercent1"]            = self.hp["shortTrailingSLPercent1"]
            self.svars["trailingSLPercent2"]            = self.hp["shortTrailingSLPercent2"]
            self.svars["trailingSLPercent3"]            = self.hp["shortTrailingSLPercent3"]
            self.svars["trailingTrigger1"]              = self.hp["shortTrailingTrigger1"]
            self.svars["trailingTrigger2"]              = self.hp["shortTrailingTrigger2"]
            self.svars["st1Factor"]                     = self.hp["shortSt1Factor"]
            self.svars["st1Period"]                     = self.hp["shortSt1Period"]
            self.svars["st2Factor"]                     = self.hp["shortSt2Factor"]
            self.svars["st2Period"]                     = self.hp["shortSt2Period"] 
            self.svars["emaFast"]                       = self.hp["shortEmaFast"]
            self.svars["emaSlow"]                       = self.hp["shortEmaSlow"]
            self.svars["aroonLength"]                   = self.hp["shortAroonLength"]
            self.svars["dmiLength"]                     = self.hp["shortDmiLength"]
            self.svars["lrsiAlpha"]                     = self.hp["shortLrsiAlpha"]
            self.svars["lrsiFeLength"]                  = self.hp["shortLrsiFeLength"]
            self.svars["threshold"]                     = self.hp["shortThreshold"]

           
        
    def on_new_candle(self):
        if self.debug_log > 0:  
            self.ts = tu.timestamp_to_gmt7(self.current_candle[0] / 1000)
        return 

    def before(self):

        # # Long
        # self.lvars["AtrSLMultipier"]                = self.hp["longAtrSLMultipier"]
        # self.lvars["AtrTPMultipier"]                = self.hp["longAtrTPMultipier"]
        # self.lvars["trailingSLPercent"]             = self.hp["longTrailingSLPercent"]
        # self.lvars["trailingSLPercent1"]            = self.hp["longTrailingSLPercent1"]
        # self.lvars["trailingSLPercent2"]            = self.hp["longTrailingSLPercent2"]
        # self.lvars["trailingSLPercent3"]            = self.hp["longTrailingSLPercent3"]
        # self.lvars["trailingTrigger1"]              = self.hp["longTrailingTrigger1"]
        # self.lvars["trailingTrigger2"]              = self.hp["longTrailingTrigger2"]
        # self.lvars["st1Factor"]                     = self.hp["longSt1Factor"]
        # self.lvars["st1Period"]                     = self.hp["longSt1Period"]
        # self.lvars["st2Factor"]                     = self.hp["longSt2Factor"]
        # self.lvars["st2Period"]                     = self.hp["longSt2Period"] 
        # self.lvars["emaFast"]                       = self.hp["longEmaFast"]
        # self.lvars["emaSlow"]                       = self.hp["longEmaSlow"]
        # self.lvars["aroonLength"]                   = self.hp["longAroonLength"]
        # self.lvars["dmiLength"]                     = self.hp["longDmiLength"]
        # self.lvars["lrsiAlpha"]                     = self.hp["longLrsiAlpha"]
        # self.lvars["lrsiFeLength"]                  = self.hp["longLrsiFeLength"]
        # self.lvars["threshold"]                     = self.hp["longThreshold"]

        # # Short
        # self.svars["AtrSLMultipier"]                = self.hp["shortAtrSLMultipier"]
        # self.svars["AtrTPMultipier"]                = self.hp["shortAtrTPMultipier"]
        # self.svars["trailingSLPercent"]             = self.hp["shortTrailingSLPercent"]
        # self.svars["trailingSLPercent1"]            = self.hp["shortTrailingSLPercent1"]
        # self.svars["trailingSLPercent2"]            = self.hp["shortTrailingSLPercent2"]
        # self.svars["trailingSLPercent3"]            = self.hp["shortTrailingSLPercent3"]
        # self.svars["trailingTrigger1"]              = self.hp["shortTrailingTrigger1"]
        # self.svars["trailingTrigger2"]              = self.hp["shortTrailingTrigger2"]
        # self.svars["st1Factor"]                     = self.hp["shortSt1Factor"]
        # self.svars["st1Period"]                     = self.hp["shortSt1Period"]
        # self.svars["st2Factor"]                     = self.hp["shortSt2Factor"]
        # self.svars["st2Period"]                     = self.hp["shortSt2Period"] 
        # self.svars["emaFast"]                       = self.hp["shortEmaFast"]
        # self.svars["emaSlow"]                       = self.hp["shortEmaSlow"]
        # self.svars["aroonLength"]                   = self.hp["shortAroonLength"]
        # self.svars["dmiLength"]                     = self.hp["shortDmiLength"]
        # self.svars["lrsiAlpha"]                     = self.hp["shortLrsiAlpha"]
        # self.svars["lrsiFeLength"]                  = self.hp["shortLrsiFeLength"]
        # self.svars["threshold"]                     = self.hp["shortThreshold"]


        # Call on first candle
        if self.index == 0:
            self.on_first_candle()
        self.sliced_candles = np.nan_to_num(jh.slice_candles(self.candles, sequential=True))

        # Call on new candle
        self.on_new_candle()

    def risk_qty_long(self):
        risk_loss = self.capital * self.vars["botRisk"]  / (self.atr * self.lvars["slMult"] * 100) 
        return risk_loss

    def risk_qty_short(self):
        risk_loss = self.capital * self.vars["botRisk"]  / (self.atr * self.svars["slMult"] * 100) 
        return risk_loss

    def f_atr(self, source, length):
        if self.atrSmoothing == 'RMA':
            temp = ta.rma(self.candles, length=length, source_type=source)
        elif self.atrSmoothing == 'SMA':
            temp = ta.sma(self.candles, period=length, source_type=source)
        elif self.atrSmoothing == ' EMA':
            temp = ta.ema(self.candles, period=length, source_type=source)
        else:
            temp = ta.wma(self.candles, period=length, source_type=source)
        return temp

    @property
    @cached
    def c_atr(self):
        tr = ta.trange(self.candles)
        temp = self.f_atr(tr,self.atrLength)
        return temp
    
    # Define SuperTrend Functions
    @property
    @cached
    def stUp(self, stFactor, stPeriod):
        hl2 = (self.high + self.low)/2
        temp = hl2 - (stFactor * ta.atr(self.candles, period=stPeriod))
        return temp
    
    @property
    @cached
    def stDn(self, stFactor, stPeriod):
        hl2 = (self.high + self.low)/2
        temp = hl2 + (stFactor * ta.atr(self.candles, period=stPeriod))
        return temp
    
    # Define EMA Cross and Determine Status
    @property
    def ma1(self, emaFast):
        return ta.ema(self.candles, period=emaFast, source_type="close")

    @property
    def ma2(self, emaSlow):
        return ta.ema(self.candles, period=emaSlow, source_type="close")

    def maTrend(self):
        if self.ma1 < self.ma2:
            return -1
        else:
            return 1

    #Determine SuperTrend 1 Values on First Timeframe 
    def st1_first(self, st1Factor, st1Period):
        candles = slice_candles(self.candles, sequential=True)
        pre_close = candles[-2:,2][0]
        # self.st1TrendUp_Tf1 = 0.0
        # St1TrendUp_Tf1 := close[1] > St1TrendUp_Tf1[1] ? max(StUp(St1Factor, St1Period), St1TrendUp_Tf1[1]) : StUp(St1Factor, St1Period)
        if pre_close > self.pre_st1TrendUp_Tf1:
            self.st1TrendUp_Tf1 = max(self.stUp(st1Factor, st1Period), self.pre_st1TrendUp_Tf1)
        else:
            self.st1TrendUp_Tf1 = self.stUp(st1Factor, st1Period)

        # self.st1TrendDown_Tf1 = 0.0
        # St1TrendDown_Tf1 := close[1] < St1TrendDown_Tf1[1] ? min(StDn(St1Factor, St1Period), St1TrendDown_Tf1[1]) : StDn(St1Factor, St1Period)
        if pre_close < self.pre_st1TrendDown_Tf1:
            self.st1TrendDown_Tf1 = min(self.stUp(st1Factor, st1Period), self.pre_st1TrendDown_Tf1)
        else:
            self.st1TrendDown_Tf1 = self.stDn(st1Factor, st1Period)
        
        # self.st1Trend_Tf1 = 0.0
        # St1Trend_Tf1 := close > St1TrendDown_Tf1[1] ? 1 : close < St1TrendUp_Tf1[1] ? -1 : nz(St1Trend_Tf1[1],1)
        if self.close > self.pre_st1TrendDown_Tf1:
            self.st1Trend_Tf1 = 1
        elif self.close < self.pre_st1TrendUp_Tf1:
            self.st1Trend_Tf1 = -1
        else:
            self.st1Trend_Tf1 = lib.nz(self.pre_st1Trend_Tf1, 1)
        
        self.pre_st1TrendUp_Tf1 = self.st1TrendUp_Tf1
        self.pre_st1TrendDown_Tf1 = self.st1TrendDown_Tf1
        self.pre_st1Trend_Tf1 = self.st1Trend_Tf1
        # self.pre_close = self.close
    
    # Determine SuperTrend 1 Values on Second Timeframe
    def st1_second(self, st1Factor, st1Period):
        candles = slice_candles(self.candles, sequential=True)
        pre_close = candles[-2:,2][0]
        # St1TrendUp_Tf2 = 0.0
        # St1TrendUp_Tf2 := close[1] > St1TrendUp_Tf2[1] ? max(security(syminfo.tickerid, ConfirmationResolution, StUp(St1Factor, St1Period)), St1TrendUp_Tf2[1]) : security(syminfo.tickerid, ConfirmationResolution, StUp(St1Factor, St1Period))
        if pre_close > self.pre_st1TrendUp_Tf2:
            if self.vars["getConfirmation"]:
                self.st1TrendUp_Tf2 = max(self.stUp(st1Factor, st1Period), self.pre_st1TrendUp_Tf2)
        else:
            if self.vars["getConfirmation"]:
                self.st1TrendUp_Tf2 = self.stUp(st1Factor, st1Period)   
        
        # St1TrendDown_Tf2 = 0.0
        # St1TrendDown_Tf2 := close[1] < St1TrendDown_Tf2[1] ? min(security(syminfo.tickerid, ConfirmationResolution, StDn(St1Factor, St1Period)), St1TrendDown_Tf2[1]) : security(syminfo.tickerid, ConfirmationResolution, StDn(St1Factor, St1Period))
        if pre_close < self.pre_st1TrendDown_Tf2:
            if self.vars["getConfirmation"]:
                self.st1TrendUp_Tf2 = max(self.stDn(st1Factor, st1Period), self.pre_st1TrendDown_Tf2)
        else:
            if self.vars["getConfirmation"]:
                self.st1TrendDown_Tf2 = self.stDn(st1Factor, st1Period)  
        # St1Trend_Tf2 = 0.0
        # St1Trend_Tf2 := close > St1TrendDown_Tf2[1] ? 1 : close < St1TrendUp_Tf2[1] ? -1 : nz(St1Trend_Tf2[1],1)
        if self.close > self.pre_st1TrendDown_Tf2:
            self.st1Trend_Tf2 = 1
        elif self.close < self.pre_st1TrendUp_Tf2:
            self.st1Trend_Tf2 = -1
        else:
            self.st1Trend_Tf2 = lib.nz(self.pre_st1Trend_Tf2, 1)

        self.pre_st1TrendUp_Tf2 = self.st1TrendUp_Tf2
        self.pre_st1TrendDown_Tf2 = self.st1TrendDown_Tf2
        self.pre_st1Trend_Tf2 = self.st1Trend_Tf2
        # self.pre_close = self.close
    

    # Determine SuperTrend 2 Values on First Timeframe
    def st2_first(self, st2Factor, st2Period):
        candles = slice_candles(self.candles, sequential=True)
        pre_close = candles[-2:,2][0]
        # St2TrendUp_Tf1 = 0.0
        # St2TrendUp_Tf1 := close[1] > St2TrendUp_Tf1[1] ? max(StUp(St2Factor, St2Period), St2TrendUp_Tf1[1]) : StUp(St2Factor, St2Period)
        if pre_close > self.pre_st2TrendUp_Tf1:
            self.st2TrendUp_Tf1 = max(self.stUp(st2Factor, st2Period), self.pre_st2TrendUp_Tf1)
        else:
            self.st2TrendUp_Tf1 = self.stUp(st2Factor, st2Period)

        # St2TrendDown_Tf1 = 0.0
        # St2TrendDown_Tf1 := close[1] < St2TrendDown_Tf1[1] ? min(StDn(St2Factor, St2Period), St2TrendDown_Tf1[1]) : StDn(St2Factor, St2Period)
        if pre_close < self.pre_st2TrendDown_Tf1:
            self.st2TrendDown_Tf1 = min(self.stUp(st2Factor, st2Period), self.pre_st2TrendDown_Tf1)
        else:
            self.st2TrendDown_Tf1 = self.stDn(st2Factor, st2Period)
        
        # St2Trend_Tf1 = 0.0
        # St2Trend_Tf1 := close > St2TrendDown_Tf1[1] ? 1 : close < St2TrendUp_Tf1[1] ? -1 : nz(St2Trend_Tf1[1],1)
        if self.close > self.pre_st2TrendDown_Tf1:
            self.st2Trend_Tf1 = 1
        elif self.close < self.pre_st2TrendUp_Tf1:
            self.st2Trend_Tf1 = -1
        else:
            self.st2Trend_Tf1 = lib.nz(self.pre_st2Trend_Tf1, 1)
        
        self.pre_st2TrendUp_Tf1 = self.st2TrendUp_Tf1
        self.pre_st2TrendDown_Tf1 = self.st2TrendDown_Tf1
        self.pre_st2Trend_Tf1 = self.st2Trend_Tf1
        # self.pre_close = self.close

    # Determine SuperTrend 2 Values on Second Timeframe
    def st2_second(self, st2Factor, st2Period):
        candles = slice_candles(self.candles, sequential=True)
        pre_close = candles[-2:,2][0]
        # St2TrendUp_Tf2 = 0.0
        # St2TrendUp_Tf2 := close[1] > St2TrendUp_Tf2[1] ? max(security(syminfo.tickerid, ConfirmationResolution, StUp(St2Factor, St2Period)), St2TrendUp_Tf2[1]) : security(syminfo.tickerid, ConfirmationResolution, StUp(St2Factor, St2Period))
        if pre_close > self.pre_st2TrendUp_Tf2:
            if self.vars["getConfirmation"]:
                self.st2TrendUp_Tf2 = max(self.stUp(st2Factor, st2Period), self.pre_st2TrendUp_Tf2)
        else:
            if self.vars["getConfirmation"]:
                self.st2TrendUp_Tf2 = self.stUp(st2Factor, st2Period)   
        
        # St2TrendDown_Tf2 = 0.0
        # St2TrendDown_Tf2 := close[1] < St2TrendDown_Tf2[1] ? min(security(syminfo.tickerid, ConfirmationResolution, StDn(St2Factor, St2Period)), St2TrendDown_Tf2[1]) : security(syminfo.tickerid, ConfirmationResolution, StDn(St2Factor, St2Period))
        if pre_close < self.pre_st2TrendDown_Tf2:
            if self.vars["getConfirmation"]:
                self.st2TrendUp_Tf2 = max(self.stDn(st2Factor, st2Period), self.pre_st2TrendDown_Tf2)
        else:
            if self.vars["getConfirmation"]:
                self.st2TrendDown_Tf2 = self.stDn(st2Factor, st2Period)  
        
        # St2Trend_Tf2 = 0.0
        # St2Trend_Tf2 := close > St2TrendDown_Tf2[1] ? 1 : close < St2TrendUp_Tf2[1] ? -1 : nz(St2Trend_Tf2[1],1)
        if self.close > self.pre_st2TrendDown_Tf2:
            self.st2Trend_Tf2 = 1
        elif self.close < self.pre_st2TrendUp_Tf2:
            self.st2Trend_Tf2 = -1
        else:
            self.st2Trend_Tf2 = lib.nz(self.pre_st2Trend_Tf2, 1)

        self.pre_st2TrendUp_Tf2 = self.st2TrendUp_Tf2
        self.pre_st2TrendDown_Tf2 = self.st2TrendDown_Tf2
        self.pre_st2Trend_Tf2 = self.st2Trend_Tf2
        # self.pre_close = self.close
    
    
    # Combine the SuperTrends on the first timeframe into one, determine values, and plot
    # StComboTrend_Tf1 = 0.0
    # StComboTrend_Tf1 := St1Trend_Tf1 == St2Trend_Tf1 ? St1Trend_Tf1 : na
    # StComboTrendUp_Tf1 = St1TrendUp_Tf1 < St2TrendUp_Tf1 ? St1TrendUp_Tf1 : St2TrendUp_Tf1
    # StComboTrendDown_Tf1 = St1TrendDown_Tf1 > St2TrendDown_Tf1 ? St1TrendDown_Tf1 : St2TrendDown_Tf1
    # StComboTsl_Tf1 = StComboTrend_Tf1 == 1 ? StComboTrendUp_Tf1 : StComboTrend_Tf1 == -1 ? StComboTrendDown_Tf1 : na
    # StComboLinecolor_Tf1 = StComboTrend_Tf1 == 1 ? #00ff00 : #ff0000
    # plot(StComboTsl_Tf1, color = StComboLinecolor_Tf1, style = plot.style_linebr, linewidth = 2, title = "SuperTrend Combo (Chart Timeframe)")

    # Combine the SuperTrends on the second timeframe into one and determine values
    # StComboTrend_Tf2 = 0.0
    # StComboTrend_Tf2 := St1Trend_Tf2 == St2Trend_Tf2 ? St1Trend_Tf2 : na
    # StComboTrendUp_Tf2 = St1TrendUp_Tf2 < St2TrendUp_Tf2 ? St1TrendUp_Tf2 : St2TrendUp_Tf2
    # StComboTrendDown_Tf2 = St1TrendDown_Tf2 > St2TrendDown_Tf2 ? St1TrendDown_Tf2 : St2TrendDown_Tf2
    # StComboTsl_Tf2 = StComboTrend_Tf2 == 1 ? StComboTrendUp_Tf2 : StComboTrend_Tf2 == -1 ? StComboTrendDown_Tf2 : na

    # Determine Overall SuperTrend Direction
    # StComboTrend = 0.0
    # StComboTrend := GetConfirmation == true ? StComboTrend_Tf1 == StComboTrend_Tf2 ? StComboTrend_Tf1 : na : StComboTrend_Tf1

    # Define Aroon Indicator and Determine Status
    # AroonIndicatorUpper = 100 * (highestbars(high, AroonLength + 1) + AroonLength) / AroonLength
    # AroonIndicatorLower = 100 * (lowestbars(low, AroonLength + 1) + AroonLength) / AroonLength
    # AroonIndictorTrend = 0
    # AroonIndictorTrend := crossover(AroonIndicatorUpper, AroonIndicatorLower) ? 1 : crossover(AroonIndicatorLower, AroonIndicatorUpper) ? -1 : AroonIndictorTrend[1]

    # Define Aroon Oscillator and Determine Status
    # AroonOscillatorMidpoint = 0
    # AroonOscillator = AroonIndicatorUpper - AroonIndicatorLower
    # AroonOscillatorSignal = 0
    # AroonOscillatorSignal := crossover(AroonOscillator, -80) ? 1 : crossunder(AroonOscillator, 80) ? -1 : AroonOscillatorSignal[1]

    # Define Directional Movement Index and Determine Values
    # DmiUp = change(high)
    # DmiDown = -change(low)
    # DmiPlusDm = na(DmiUp) ? na : (DmiUp > DmiDown and DmiUp > 0 ? DmiUp : 0)
    # DmiMinusDm = na(DmiDown) ? na : (DmiDown > DmiUp and DmiDown > 0 ? DmiDown : 0)
    # DmiTrur = rma(tr, DmiLength)
    # DmiPlus = fixnan(100 * rma(DmiPlusDm, DmiLength) / DmiTrur)
    # DmiMinus = fixnan(100 * rma(DmiMinusDm, DmiLength) / DmiTrur)
    # DmiTrend = 0
    # DmiTrend := crossover(DmiPlus, DmiMinus) ? 1 : crossover(DmiMinus, DmiPlus) ? -1 : DmiTrend[1]

    # Define Laguerre RSI and Determine Values
    # LrsiOC = (open + nz(close[1])) / 2
    # LrsiHC = max(high, nz(close[1]))
    # LrsiLC = min(low, nz(close[1]))
    # LrsiFeSrc = (LrsiOC + LrsiHC + LrsiLC + close) / 4
    # LrsiFeAlpha = log(sum((LrsiHC - LrsiLC) / (highest(LrsiFeLength) - lowest(LrsiFeLength)), LrsiFeLength)) / log(LrsiFeLength)
    # LrsiAlphaCalc = LrsiApplyFractalsEnergy ? LrsiFeAlpha : LrsiAlpha
    # LrsiL0 = 0.0
    # LrsiL0 := LrsiAlphaCalc * (LrsiApplyFractalsEnergy ? LrsiFeSrc : close) + (1 - LrsiAlphaCalc) * nz(LrsiL0[1])
    # LrsiL1 = 0.0
    # LrsiL1 := -(1 - LrsiAlphaCalc) * LrsiL0 + nz(LrsiL0[1]) + (1 - LrsiAlphaCalc) * nz(LrsiL1[1])
    # LrsiL2 = 0.0
    # LrsiL2 := -(1 - LrsiAlphaCalc) * LrsiL1 + nz(LrsiL1[1]) + (1 - LrsiAlphaCalc) * nz(LrsiL2[1])
    # LrsiL3 = 0.0
    # LrsiL3 := -(1 - LrsiAlphaCalc) * LrsiL2 + nz(LrsiL2[1]) + (1 - LrsiAlphaCalc) * nz(LrsiL3[1])
    # LrsiCU = 0.0
    # LrsiCU := (LrsiL0 >= LrsiL1 ? LrsiL0 - LrsiL1 : 0) + (LrsiL1 >= LrsiL2 ? LrsiL1 - LrsiL2 : 0) + (LrsiL2 >= LrsiL3 ? LrsiL2 - LrsiL3 : 0)
    # LrsiCD = 0.0
    # LrsiCD := (LrsiL0 >= LrsiL1 ? 0 : LrsiL1 - LrsiL0) + (LrsiL1 >= LrsiL2 ? 0 : LrsiL2 - LrsiL1) + (LrsiL2 >= LrsiL3 ? 0 : LrsiL3 - LrsiL2)
    # Lrsi = LrsiCU + LrsiCD != 0
    #         ? LrsiApplyNormalization ? 100 * LrsiCU / (LrsiCU + LrsiCD) : LrsiCU / (LrsiCU + LrsiCD)
    #         : 0
    # LrsiMult = (LrsiApplyNormalization ? 100 : 1)
    # LrsiOverBought = 0.8 * LrsiMult
    # LrsiOverSold = 0.2 * LrsiMult
    # LrsiSignal = 0
    # LrsiSignal := crossover(Lrsi, LrsiOverSold) ? 1 : crossunder(Lrsi, LrsiOverBought) ? -1 : LrsiSignal[1]

    # Determine Strength of Trend Based on Status of All Indicators
    # MaTrendCalc = StComboTrend == MaTrend ? StComboTrend : 0
    # AroonIndictorTrendCalc = StComboTrend == AroonIndictorTrend ? StComboTrend : 0
    # AroonOscillatorSignalCalc = StComboTrend == AroonOscillatorSignal ? StComboTrend : 0
    # DmiTrendCalc = StComboTrend == DmiTrend ? StComboTrend : 0
    # LrsiSignalCalc = StComboTrend == LrsiSignal ? StComboTrend : 0
    # TrendStrength = MaTrendCalc + AroonIndictorTrendCalc + AroonOscillatorSignalCalc + DmiTrendCalc + LrsiSignalCalc



    def should_long(self) -> bool:
        return False

    def should_short(self) -> bool:
        return False

    def should_cancel(self) -> bool:
        return True

    def go_long(self):
        pass

    def go_short(self):
        pass

        
    def watch_list(self):
        return [
            
        ]
    def terminate(self):
        print(f'Backtest is done, Total Capital : {self.capital}')
        if self.debug_log >= 1:
            print(self.indicator_log)
            tu.write_csv(type(self).__name__ +'-' + self.symbol +'-' + self.timeframe, self.data_header, self.data_log)
            tu.write_csv(type(self).__name__ +'-' + self.symbol +'-' + self.timeframe + '-indicator', self.indicator_header, self.indicator_log)
            tu.write_pine(type(self).__name__ +'-' + self.symbol +'-' + self.timeframe, self.starting_balance, self.pine_log)

    def pine_long(self, comment, ts, qty, ts_out, sl, tp):
        self.pine_orderid += 1
        ts = int(ts) + jh.timeframe_to_one_minutes(self.timeframe) * 60 * 1000
        
        self.pine_log += f'strategy.entry("{self.pine_orderid}", strategy.long, {qty}, {tp:.2f}, when = time_close == {ts:.0f}, comment="{comment}")\n'
        self.pine_log += f'strategy.exit("{self.pine_orderid}","{self.pine_orderid}", stop = {sl:.2f}, limit = {tp:.2f}, when = time_close >= {ts_out:.0f})\n'

    def pine_short(self, comment, ts, qty, ts_out, sl, tp):
        self.pine_orderid += 1
        ts = int(ts) + jh.timeframe_to_one_minutes(self.timeframe) * 60 * 1000
        
        self.pine_log += f'strategy.entry("{self.pine_orderid}", strategy.short, {qty}, {tp:.2f}, when = time_close == {ts:.0f}, comment="{comment}")\n'
        self.pine_log += f'strategy.exit("{self.pine_orderid}","{self.pine_orderid}", stop = {sl:.2f}, limit = {tp:.2f}, when = time_close >= {ts_out:.0f})\n'

   
