import collections
import Queue

import src.model.market.exchange as exchange


# Define order object.
Order = collections.namedtuple('Order', 'price, id, amount, wallet')


class ExperimentalExchange(exchange.Exchange):
  
  # Define unlimited price for market orders.
  inf = float('inf')

  def __init__(self, symbols=None, history=None):
    self.symbols = symbols or []
    self.history = history or {}
    #self.orders
    self.bids = {}
    self.asks = {}
    self.trade_id = 0  # keep track of arrival order
    # Initialize history and orderbook for each stock.
    for symbol in self.symbols:
      if symbol not in self.history:
        self.history[symbol] = []
      self.bids[symbol] = Queue.PriorityQueue()  #populate?
      self.asks[symbol] = Queue.PriorityQueue()  #populate?

  def GetSymbols(self):
    """Get list of all stocks traded on this exchange."""
    return self.symbols
    
  def GetHistory(self, symbol):
    """Return available history for the specified stock."""
    if symbol in self.symbols:
      return self.history[symbol]
    else:
      raise Exception('%s not on exchange.' % symbol)

  def Buy(self, symbol, amount, wallet, price=inf):
    """Buy specified amount of given stock. Price is for limit orders only.

    Args:
      symbol: Name of the stock to buy.
      amount: Number of shares to buy.
      wallet: The buyer's wallet which contains cash to buy.
      price: The buyer's bidding price.
    """
    self.trade_id += 1
    order = Order(price=price, id=self.trade_id, amount=amount, wallet=wallet)
    print 'placed bid: %s' % str(order)
    self.bids[symbol].put((order.price, order.id, order))

  def Sell(self, symbol, amount, wallet, price=inf):
    """Sell specified amount of given stock. Price is for limit orders only.

    Args:
      symbol: Name of the stock to sell.
      amount: Number of shares to sell.
      wallet: The seller's wallet which contains shares to sell.
      price: The seller's asking price.
    """
    self.trade_id += 1
    order = Order(price=price, id=self.trade_id, amount=amount, wallet=wallet)
    print 'placed ask: %s' % str(order)
    self.asks[symbol].put((-order.price, order.id, order))
