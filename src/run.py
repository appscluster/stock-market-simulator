
# Set up PYTHONPATH
# Run from root directory: 'python -m src.run'
#import os
#import sys
#sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

import src.model.market.simulated_exchange as sim_exchange
import src.model.wallet as wallet
import src.model.securities as securities


# testing
symbols = [securities.BTC]
prices = {securities.BTC: 10}
ee = sim_exchange.SimulatedExchange(symbols=symbols)
print 'stocks:', ee.GetSymbols()

my_wallet1 = wallet.Wallet({securities.USD: 10, securities.BTC: 10})
my_wallet2 = wallet.Wallet({securities.USD: 10, securities.BTC: 10})

print 'Before trade:'
print '  buyer wallet: %s' % my_wallet1
print '  seller wallet: %s' % my_wallet2

# Place buy and sell orders.
ee.Buy(securities.BTC, 1, my_wallet1, price=5)
ee.Sell(securities.BTC, 1, my_wallet2, price=4)

print 'After trade:'
print '  buyer wallet: %s' % my_wallet1
print '  seller wallet: %s' % my_wallet2

print '\norderbook: %s' % ee.GetOrderbook()[securities.BTC]
print 'done.'