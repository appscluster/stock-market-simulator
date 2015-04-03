
# Set up PYTHONPATH
# Run from root directory: 'python -m src.run'
#import os
#import sys
#sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

import src.model.market.simulated_exchange as sim_exchange
import src.model.wallet as wallet
import src.model.securities as securities
import src.model.trader.experimentalagent as agent
import time


# testing
symbols = [securities.BTC]
prices = {securities.BTC: 10}
ee = sim_exchange.SimulatedExchange(symbols=symbols, prices=prices)
print 'stocks:', ee.GetSymbols()

my_wallet1 = wallet.Wallet({securities.USD: 1000, securities.BTC: 10})
my_wallet2 = wallet.Wallet({securities.USD: 1000, securities.BTC: 10})


while True:
  print 'Before trade:'
  print '  buyer wallet: %s' % my_wallet1
  print '  seller wallet: %s' % my_wallet2

  # Place buy and sell orders.
  agent1 = agent.ExperimentalAgent(my_wallet1, ee)
  agent2 = agent.ExperimentalAgent(my_wallet2, ee)

  print 'After trade:'
  print '  buyer wallet: %s' % my_wallet1
  print '  seller wallet: %s' % my_wallet2
  agent1.RandomStrategy()
  agent2.RandomStrategy()

  time.sleep(2)


  print '\norderbook: %s' % ee.GetOrderbook()[securities.BTC]
  print 'symbols: %s'% ee.GetSymbols()
    
print 'done.'
    
