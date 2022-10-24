##backtesting only, not live trade optimized 


from blueshift_library.technicals.indicators import bollinger_band, ema

from blueshift.finance import commission, slippage
from blueshift.api import(    symbol,
                            order_target_percent,
                            set_commission,
                            set_slippage,
                       )

def initialize(context):
      context.securities = [symbol('NIFTY-I'),symbol('BANKNIFTY-I')]

    context.params = {'indicator_lookback':375,
                      'indicator_freq':'1m',
                      'buy_signal_threshold':0.5,
                      'sell_signal_threshold':-0.5,
                      'SMA_period_short':15,
                      'SMA_period_long':60,
                      'BBands_period':300,
                      'trade_freq':5,
                      'leverage':2}

    context.bar_count = 0

    context.signals = dict((security,0) for security in context.securities)
    context.target_position = dict((security,0) for security in context.securities)

    set_commission(commission.PerShare(cost=0.0, min_trade_cost=0.0))
    set_slippage(slippage.FixedSlippage(0.00))


def handle_data(context, data):
 
    context.bar_count = context.bar_count + 1
    if context.bar_count < context.params['trade_freq']:
        return

    context.bar_count = 0
    run_strategy(context, data)


def run_strategy(context, data):
  
    generate_signals(context, data)
    generate_target_position(context, data)
    rebalance(context, data)

def rebalance(context,data):
  
    for security in context.securities:
        order_target_percent(security, context.target_position[security])

def generate_target_position(context, data):
  
    num_secs = len(context.securities)
    weight = round(1.0/num_secs,2)*context.params['leverage']

    for security in context.securities:
        if context.signals[security] > context.params['buy_signal_threshold']:
            context.target_position[security] = weight
        elif context.signals[security] < context.params['sell_signal_threshold']:
            context.target_position[security] = -weight
        else:
            context.target_position[security] = 0


def generate_signals(context, data):
 
    try:
        price_data = data.history(context.securities, 'close',
            context.params['indicator_lookback'],
            context.params['indicator_freq'])
    except:
        return

    for security in context.securities:
        px = price_data.loc[:,security].values
        context.signals[security] = signal_function(px, context.params)

def signal_function(px, params):
  
    upper, mid, lower = bollinger_band(px,params['BBands_period'])
    if upper - lower == 0:
        return 0
    
    ind2 = ema(px, params['SMA_period_short'])
    ind3 = ema(px, params['SMA_period_long'])
    last_px = px[-1]
    dist_to_upper = 100*(upper - last_px)/(upper - lower)

    if dist_to_upper > 95:
        return -1
    elif dist_to_upper < 5:
        return 1
    elif dist_to_upper > 40 and dist_to_upper < 60 and ind2-ind3 < 0:
        return -1
    elif dist_to_upper > 40 and dist_to_upper < 60 and ind2-ind3 > 0:
        return 1
    else:
        return 0
