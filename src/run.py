
# Set up PYTHONPATH
import os
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

#import src.market as market
import src.model.market.experimental_exchange as exp
import src.model.wallet as wallet

BTC_USD = 'btcusd'


# testing
ee = exp.ExperimentalExchange(symbols=[BTC_USD])
stock_names = ee.GetSymbols()
print 'stocks:', stock_names

my_wallet = wallet.Wallet(5.00)
ee.Buy(BTC_USD, 2, my_wallet)

print 'done.'