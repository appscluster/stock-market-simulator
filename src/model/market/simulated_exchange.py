import collections
import Queue

import src.model.market.exchange as exchange
import src.model.asset as asset
import src.model.wallet as wallet


# Define order object.
Order = collections.namedtuple(
    'Order', 'id, symbol, price, amount, wallet')


class SimulatedExchange(exchange.Exchange):
  """Simulated exchange where agents can trade assets."""

  # Define unlimited price for market orders.
  inf = float('inf')

  def __init__(self, symbols=None, prices=None):
    """Initialize the exchange.
    
    Args:
      symbols: (optional) Symbols traded on this exchange.
      prices: (optional) Initial prices of assets on this exchange.
    """
    # List of stocks on this exchange.
    self.symbols = symbols or []
    # Current stock prices.
    self.prices = prices or {}
    # Order queues.
    self.bids = {}
    self.asks = {}
    # Keep track of order arrival.
    self.trade_id = 0
    # Initialize price and orderbook for each stock.
    for symbol in self.symbols:
      if symbol not in self.prices:
        self.prices[symbol] = None
      self.bids[symbol] = Queue.PriorityQueue()  #populate?
      self.asks[symbol] = Queue.PriorityQueue()  #populate?
    # Assets stored on the exchange pending trade
    self.wallet = wallet.Wallet()

  def GetSymbols(self):
    """Get list of all stocks traded on this exchange."""
    return self.symbols

  def GetPrice(self, symbol):
    """Return price for the given stock.

    Args:
      symbol: Name of the share to buy.

    Returns:
      Current price of the stock.
    """
    if symbol in self.symbols:
      return self.prices[symbol]
    else:
      raise Exception('%s not on this exchange.' % symbol)

  def GetOrderbook(self, symbol):
    """Gets pending bids and asks for specified asset.
    
    Args:
      symbol: Name of the stock.
    
    Returns:
      All pending trades for this stock.
    """
    all_bids = [item[-1] for item in self.bids[symbol].queue]
    all_asks = [item[-1] for item in self.asks[symbol].queue]
    orderbook = {
        'bids': all_bids,
        'asks': all_asks,
    }
    return orderbook

  def Buy(self, symbol, amount, wallet, price=inf):
    """Place buy order for desired amount of stock.
    
    Note: Price is for limit orders only.

    Limit order:
      - Buy given amount of the stock for the specified price.
      - The cash amount of (price)x(amount) is removed from the buyer's wallet
        and put in the exchange's trading pool.

    Market order:
      - Buy given amount of stock at the best available price (i.e the price is
        not specified). The buyer can expect the purchase price to be the
        current market price unless unless some sudden volatility causes the
        price to slip.
      - No cash is removed from the buyer's wallet until the trade is executed.

    Args:
      symbol: Name of the stock to buy.
      amount: Number of shares to buy.
      wallet: The buyer's wallet which contains cash to buy.
      price: (optional) The buyer's bidding price.
    """
    # Determine amount of cash needed for the order.
    if price is self.inf:
      # This is a market order. Take cash when trade executes.
      cash_for_trade = 0
    else:
      # This is a limit order. Reserve cash required for trade.
      cash_for_trade = price * amount

    # The exchange withholds required amount of cash from the buyer.
    # Make sure the buyer has enough cash.
    if wallet.GetAmount(asset.Symbols.USD) < cash_for_trade:
      raise Exception('Buy error: Wallet contains insufficient USD.')
    # Reserve the buyer's cash for the order.
    wallet.RemoveAmount(asset.Symbols.USD, cash_for_trade)
    self.wallet.AddAmount(asset.Symbols.USD, cash_for_trade)

    # Place new bid.
    self.trade_id += 1
    order = Order(
        id=self.trade_id,
        symbol=symbol,
        price=price,
        amount=amount,
        wallet=wallet,
    )
    # Sort buy orders by (-price, timestamp).
    self.bids[symbol].put((-order.price, order.id, order))
    print 'Placed bid: (price: %s, amount: %s)' % (price, amount)
    # Process orders.
    self._ProcessOrders(symbol)

  def Sell(self, symbol, amount, wallet, price=-inf):
    """Place order for desired amount of given stock.

    Note: Price is for limit orders only.

    Limit order:
      - Sell given amount of stock for the specified price.
      - The stock amount is transferred to pool for trade.

    Market order:
      - Sell given amount of stock at the best available price (i.e the price
        is not specified).
      - The stock amount is transferred to pool for trade.

    Args:
      symbol: Name of the stock to sell.
      amount: Number of shares to sell.
      wallet: The seller's wallet which contains shares to sell.
      price: (optional) The seller's asking price.
    """
    # Take stocks to sell from the seller's wallet.
    if wallet.GetAmount(symbol) < amount:
      raise Exception('Sell error: Wallet contains insufficient %s.' % symbol)
    wallet.RemoveAmount(symbol, amount)
    # put stocks on exchange
    self.wallet.AddAmount(symbol,amount)

    # Place new ask.
    self.trade_id += 1
    order = Order(
        id=self.trade_id,
        symbol=symbol,
        price=price,
        amount=amount,
        wallet=wallet
    )
    # prioritize sell orders by (price, timestamp)
    self.asks[symbol].put((order.price, order.id, order))
    print 'placed ask: %s' % str(order)
    # Process orders.
    self._ProcessOrders(symbol)

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
        # B is a market order at price inf.
        #print 'buyer placed market order'
        if abs(ask.price) == self.inf:
          # Seller also placed market order (at price -inf). Use market price.
          #print 'seller also placed market order'
          trade_price = self.prices[bid.symbol]
        else:
          # The buyer is willing to pay S.
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
    """Determine amount of stock to be traded at given price.

    Args:
      bid: The buy order.
      ask: The sell order.

    Returns:
      Amount of stock that should be traded given the buy and sell orders.
    """
    # Determine how many shares will be traded.
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

  def _ExecuteTrade(self, amount, price, bid, ask):
    """Exchange assets between buyer and seller.
    
    Args:
      amount: Amount of asset being traded.
      price: Price per unit of asset.
      bid: The buy order.
      ask: The sell order.
    """
    assert ask.symbol == bid.symbol
    symbol = ask.symbol

    # Transfer cash from buyer to seller.
    cash = price * amount
    if bid.price is self.inf:
      # Buy is market order -- take cash now.
      bid.wallet.RemoveAmount(asset.Symbols.USD, cash)
    else:
      # Buy is limit order -- cash was reserved on exchange.
      # Remove cash from exchange.
      expected_cash = bid.price * amount
      self.wallet.RemoveAmount(asset.Symbols.USD, expected_cash)
      # Calculate change for buyer.
      leftover_cash = expected_cash - cash
      bid.wallet.AddAmount(asset.Symbols.USD, leftover_cash)
    ask.wallet.AddAmount(asset.Symbols.USD, cash)

    # Transfer shares to buyer.
    self.wallet.RemoveAmount(symbol, amount)
    bid.wallet.AddAmount(symbol, amount)

    # Put excess supply or demand back in orderbook.
    excess_supply = ask.amount - amount
    excess_demand = bid.amount - amount
    if excess_supply > 0:
      # Excess supply goes back in orderbook with original timestamp.
      remaining_order = Order(
          id=ask.id, symbol=ask.symbol, price=ask.price,
          amount=excess_supply, wallet=ask.wallet)
      ask_q = self.asks[symbol]
      ask_q.put((remaining_order.price, remaining_order.id, remaining_order))
    if excess_demand > 0:
      # Excess demand goes back in orderbook with original timestamp.
      remaining_order = Order(
          id=bid.id, symbol=bid.symbol, price=bid.price,
          amount=excess_demand, wallet=bid.wallet)
      bid_q = self.bids[symbol]
      bid_q.put((-remaining_order.price, remaining_order.id, remaining_order))

  def _ProcessOrders(self, symbol):
    """Match pending bids and asks for given symbol."""
    # Process all bids and asks.
    bid_q = self.bids[symbol]
    ask_q = self.asks[symbol]
    while bid_q.qsize() and ask_q.qsize():
      # Compare highest bid B to lowest ask S.
      highest_bid = bid_q.get()[-1]  # order is last item in tuple
      lowest_ask = ask_q.get()[-1]

      # Determine trade price based on B and S.
      trade_price = self._DetermineTradePrice(highest_bid, lowest_ask)
      print 'trade price: %s' % trade_price
      # Stop processing orders if there is no "breakeven".
      if trade_price is None:
        # Put orders back in the queue.
        bid_q.put((-highest_bid.price, highest_bid.id, highest_bid))
        ask_q.put((lowest_ask.price, lowest_ask.id, lowest_ask))
        # Stop processing orders.
        break

      # Determine trade amount.
      trade_amount = self._DetermineTradeAmount(highest_bid, lowest_ask)
      print 'trade amount: %f' % trade_amount

      # Execute the trade.
      self._ExecuteTrade(trade_amount, trade_price, highest_bid, lowest_ask)
      print 'trade executed'

      # Update market price.
      self.prices[symbol] = trade_price

    print 'orders processed.'
