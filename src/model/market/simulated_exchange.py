import collections
import Queue

import src.model.market.exchange as exchange
import src.model.securities as securities


# Define order object.
Order = collections.namedtuple('Order', 'id, symbol, price, amount, wallet')


class SimulatedExchange(exchange.Exchange):

  # Define unlimited price for market orders.
  inf = float('inf')

  def __init__(self, symbols=None, prices=None):
    self.symbols = symbols or []
    self.prices = prices or {}
    self.bids = {}
    self.asks = {}
    self.trade_id = 0  # keep track of arrival order
    # Initialize history and orderbook for each stock.
    for symbol in self.symbols:
      if symbol not in self.prices:
        self.prices[symbol] = None
      self.bids[symbol] = Queue.PriorityQueue()  #populate?
      self.asks[symbol] = Queue.PriorityQueue()  #populate?

  def GetSymbols(self):
    """Get list of all stocks traded on this exchange."""
    return self.symbols

  def GetPrice(self, symbol):
    """Return price for the specified stock."""
    if symbol in self.symbols:
      return self.prices[symbol]
    else:
      raise Exception('%s not on exchange.' % symbol)

  def GetOrderbook(self):
    """Gets pending bids and asks for all securities on this exchange."""
    orderbook = {}
    for symbol in self.symbols:
      orderbook[symbol] = {
          'bids': self.bids[symbol].queue,
          'asks': self.asks[symbol].queue,
      }
    return orderbook

  def Buy(self, symbol, amount, wallet, price=inf):
    """Buy specified amount of given stock. Price is for limit orders only.

    Args:
      symbol: Name of the stock to buy.
      amount: Number of shares to buy.
      wallet: The buyer's wallet which contains cash to buy.
      price: The buyer's bidding price.
    """
    # Place new bid.
    self.trade_id += 1
    order = Order(id=self.trade_id, symbol=symbol, price=price, amount=amount, wallet=wallet)
    self.bids[symbol].put((order.price, order.id, order))
    # Process orders.
    self._ProcessOrders(symbol)
    #print 'placed bid: %s' % str(order)

  def Sell(self, symbol, amount, wallet, price=-inf):
    """Sell specified amount of given stock. Price is for limit orders only.

    Args:
      symbol: Name of the stock to sell.
      amount: Number of shares to sell.
      wallet: The seller's wallet which contains shares to sell.
      price: The seller's asking price.
    """
    self.trade_id += 1
    order = Order(id=self.trade_id, symbol=symbol, price=price, amount=amount, wallet=wallet)
    self.asks[symbol].put((order.price, order.id, order))
    # Process orders.
    self._ProcessOrders(symbol)
    #print 'placed ask: %s' % str(order)

  def _DetermineTradePrice(self, bid, ask):
    """Determines trading price for given bid and ask.
    
    Args:
      bid: The buy order.
      ask: The sell order.
      
    Returns:
      Trade price determined by the given orders.
    """
    assert bid.symbol == ask.symbol
    # Determine trade price.
    trade_price = None
    if ask.price > bid.price:
      # Seller asks for more than buyer offers.
      #print 'S > B: no trade possible'
      pass
    elif bid.price > ask.price:
      # Buyer offers more than seller asks.
      #print 'B > S: buyer offers more than seller asks'
      if bid.price == self.inf:
        # B is a market order -- buyer willing to pay S.
        #print 'buyer placed market order'
        if abs(ask.price) == self.inf:
          # Buyer and seller placed market order. Use market price.
          #print 'seller also placed market order'
          trade_price = self.prices[bid.symbol]
        else:
          trade_price = ask.price
      else:
        # B is not a market order -- use timestamps to determine price.
        if ask.id < bid.id:
          # Seller placed order first. Check if S is a market order.
          if abs(ask.price) == self.inf:
            #print 'seller placed market order'
            # Seller willing to sell for B.
            trade_price = bid.price
          else:
            trade_price = ask.price
        else:
          # Buyer placed order first.
          trade_price = bid.price
    else:
      # B == S. Use agreed price.
      #print 'buyer and seller agree on price'
      trade_price = ask.price
    return trade_price

  def _DetermineTradeAmount(self, bid, ask):
    """Determine amount to be traded given bid and ask."""
    supply_demand_diff = ask.amount - bid.amount
    trade_amount = None
    if supply_demand_diff > 0:
      # Seller has excess supply.
      trade_amount = bid.amount
    elif supply_demand_diff < 0:
      # Buyer has excess demand.
      trade_amount = ask.amount
    else:
      # Equal supply and demand.
      trade_amount = ask.amount
    return trade_amount
    
  def _ExecuteTrade(self, symbol, amount, price, buyer_wallet, seller_wallet):
    """Exchange assets between buyer and seller."""
    # Transfer shares from seller to buyer.
    seller_wallet.RemoveAmount(symbol, amount)
    buyer_wallet.AddAmount(symbol, amount)
    # Transfer cash from buyer to seller.
    cash = price * amount
    buyer_wallet.RemoveAmount(securities.USD, cash)
    seller_wallet.AddAmount(securities.USD, cash)

  def _ProcessOrders(self, symbol):
    """Match pending bids and asks for given symbol."""
    # Process all bids and asks.
    bid_q = self.bids[symbol]
    ask_q = self.asks[symbol]
    while bid_q.qsize() and ask_q.qsize():
      # Compare highest bid B to lowest ask S.
      highest_bid = bid_q.get()[-1]  # order is last item in tuple
      lowest_ask = ask_q.get()[-1]

      # Determine trade price.
      trade_price = self._DetermineTradePrice(highest_bid, lowest_ask)
      #print 'trade price: %s' % trade_price
      # Stop processing orders if there is no "breakeven".
      if trade_price is None:
        break

      # Determine trade amount.
      trade_amount = self._DetermineTradeAmount(highest_bid, lowest_ask)
      #print 'trade amount: %d' % trade_amount

      # Put excess order back in orderbook.
      supply_demand_diff = lowest_ask.amount - highest_bid.amount
      remaining_order = None
      if supply_demand_diff > 0:
        # Put remaining sell order back in orderbook.
        remaining_order = Order(id=lowest_ask.id, symbol=lowest_ask.symbol,
            price=lowest_ask.price, amount=supply_demand_diff, wallet=lowest_ask.wallet)
        ask_q.put((remaining_order.price, remaining_order.id, remaining_order))
      elif supply_demand_diff < 0:
        # Put remaining buy order back in orderbook.
        remaining_order = Order(id=highest_bid.id, symbol=highest_bid.symbol,
            price=highest_bid.price, amount=abs(supply_demand_diff), wallet=highest_bid.wallet)
        bid_q.put((remaining_order.price, remaining_order.id, remaining_order))
      
      # Execute the trade.
      self._ExecuteTrade(symbol, trade_amount, trade_price, highest_bid.wallet, lowest_ask.wallet)
      #print 'trade executed'
      # Update market price.
      self.prices[symbol] = trade_price
