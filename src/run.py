
import time

import src.model.market.simulated_exchange as sim_exchange
import src.model.wallet as wallet
import src.model.asset as asset
import src.model.trader.experimentalagent as agent


# exchange
symbols = [asset.Symbols.BTC]
prices = {asset.Symbols.BTC: 250}
ee = sim_exchange.SimulatedExchange(symbols=symbols, prices=prices)

# initial funds
my_wallet1 = wallet.Wallet({asset.Symbols.USD: 1000, asset.Symbols.BTC: 10})
my_wallet2 = wallet.Wallet({asset.Symbols.USD: 1000, asset.Symbols.BTC: 10})

# agents
agent1 = agent.ExperimentalAgent(my_wallet1, ee)
agent2 = agent.ExperimentalAgent(my_wallet2, ee)

# trade
timestep = 0
while True:
  print 'TIMESTEP %d' % timestep
  print '  stock prices:'
  for symbol in ee.GetSymbols():
    print '    %s %f' % (symbol, ee.GetPrice(symbol))
  print '  buyer wallet: %s' % my_wallet1
  print '  seller wallet: %s' % my_wallet2
  print '  trade pool: %s' % ee.wallet

  #print 'Before trade:'
  #print '  buyer wallet: %s' % my_wallet1
  #print '  seller wallet: %s' % my_wallet2
  agent1.RandomStrategy()
  agent2.RandomStrategy()

  # Print orderbook
  orderbook = ee.GetOrderbook(asset.Symbols.BTC)
  bids = orderbook['bids']
  asks = sorted(orderbook['asks'], key=lambda x: x.price, reverse=True)
  # asks
  print '\nAsks for %s:' % asset.Symbols.BTC
  for ask in asks:
    if abs(ask.price) is float('inf'):
      ask_amnt = 'variable'
    else:
      ask_amnt = ask.amount
    print '  (price: %s, amount: %s)' % (ask.price, ask_amnt)
  # bids
  print 'Bids for %s:' % asset.Symbols.BTC
  for bid in bids:
    if bid.price is float('inf'):
      bid_amnt = 'variable'
    else:
      bid_amnt = bid.amount
    print '  (price: %s, amount: %s)' % (bid.price, bid_amnt)

  print '-----\n'

  # Update timestep.
  time.sleep(1)
  timestep += 1

print 'done.'
    
