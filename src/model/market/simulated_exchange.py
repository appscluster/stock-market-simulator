

import bisect
import collections
import Queue

import src.model.asset as asset
import src.model.market.exchange as exchange
import src.model.wallet as wallet


# Define order object.
Order = collections.namedtuple(
    'Order', 'id, symbol, price, amount, wallet')


class SimulatedExchange(exchange.Exchange):
  """Simulated exchange where agents can trade assets."""

  # Define unlimited price for market orders.
  inf = float('inf')

  def __init__(self, *args, **kwargs):
    """Initialize the exchange.

    Args:
      time: Time reference used on this exchange.
      symbols: Symbols traded on this exchange.
      history: History for assets on this exchange.
    """
    # Time reference for this exchange.
    self.time = kwargs['time']
    # List of stocks on this exchange.
    self.symbols = kwargs['symbols']
    self.history = kwargs['history']
    self.cached_history = {}
    # Make sure there is history for every symbol.
    for symbol in self.symbols:
      if (symbol not in self.history) or (len(self.history[symbol]) == 0):
        raise ValueError('No history given for symbol \'%s\'' % symbol)
      # Candles are cached in (timestamp, candle_size, candles) format.
      self.cached_history[symbol] = (None, None, None)
    # Order queues.
    self.bids = {}
    self.asks = {}
    # Keep track of order arrival.
    self.trade_id = 0
    # Initialize orderbook for each stock.
    for symbol in self.symbols:
      # orderbook for this symbol
      self.bids[symbol] = Queue.PriorityQueue()  #populate?
      self.asks[symbol] = Queue.PriorityQueue()  #populate?
    # Trade pool where assets are held for trade.
    self.wallet = wallet.Wallet()
    # Logging
    if 'logger' in kwargs:
      self.logger = kwargs['logger']
    else:
      self.logger = None

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
    if symbol not in self.symbols:
      raise Exception('%s not on this exchange.' % symbol)
    # Return last trading price.
    last_trade = self.history[symbol][-1]
    return last_trade[1]

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

  def GetHistory(self, symbol, limit=25, candle_size=1):
    """Get trade history for specified for asset.

    Args:
      symbol: Name of the asset.
      limit: Number of candles to retrieve.
      candle_size: Number of time units per candle.

    Returns:
      List of (timestamp, closing price) candles.
    """
    # Current time on the exchange.
    now = self.time.GetCurrentTime()

    # Check the cache for candles.
    cached_history = self.cached_history[symbol]  # (timestamp, candle_size, candles)
    if cached_history[0] == now and cached_history[1] == candle_size:
      if len(cached_history[2]) >= limit:
        # Return cached candles.
        return cached_history[2][-limit:]

    # Make sure history exists for this asset.
    history = self.history[symbol]
    if len(history) == 0:
      return []

    # Determine time range for the candles.
    # Candles end on current time.
    candles_end = now
    # Candles start limit number of candles before end point.
    candles_start = self.time.TimeDelta(candles_end, -(candle_size * limit))

    # History records are (timestamp, price, amount) tuples.
    first_trade_timestamp = history[0][0]
    # Make sure candle range is within history.
    if candles_start < first_trade_timestamp:
      # Not enough history for requested number of candles.
      # Start candles in first interval containing history.
      history_length = now - first_trade_timestamp
      if candle_size <= history_length:
        dist_to_candle_end = history_length % candle_size
        dist_to_candle_start = candle_size - dist_to_candle_end
      else:
        # Candle size is greater than available history.
        dist_to_candle_start = candle_size - history_length
      # Adjust start of candles range.
      candles_start = first_trade_timestamp - dist_to_candle_start

    # Binary search to find the first record within the candles' time range.
    # The candles contain price info from time (start, end].
    # Exclude records with timestamp == start_candles (i.e. bisect right).
    history_idx = bisect.bisect_right(history, (candles_start, self.inf, self.inf))

    # Create dummy candle with initial price.
    # Needed if first real candle has no trades (use previous candle price).
    if history_idx > 0:
      # Use last price point before candles start.
      initial_price = history[history_idx - 1][1]
    else:
      # Use first historical price point.
      initial_price = history[0][1]
    dummy_candle = [-1, initial_price]

    # Create candles with timestamps from (candles_start, candles_end].
    time_idx = self.time.TimeDelta(candles_start, candle_size)
    candles = [dummy_candle]
    while time_idx <= candles_end:
        # Create candle for this interval.
        candle = [time_idx, None]
        for record in history[history_idx:]:
          # Each record is a (timestamp, price, amount) tuple.
          if record[0] <= time_idx:
            # Record is in this candle's interval.
            candle[1] = record[1]
            history_idx += 1
          else:
            break
        # Make sure the candle has data.
        if candle[1] is None:
          # Use price of last candle. Dummy candle needed here.
          candle[1] = candles[-1][1]
        # Save candle and go to next time interval.
        candles.append(candle)
        time_idx = self.time.TimeDelta(time_idx, candle_size)

    # Remove dummy candle.
    candles = candles[1:]
    # Cache the computed results.
    to_cache = (now, candle_size, candles)
    self.cached_history[symbol] = to_cache
    # Return results.
    return candles

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
    if self.logger:
      self.logger.debug(
          'Placed bid: (price: %s, amount: %s)' % (price, amount))
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
    if self.logger:
      self.logger.debug(
          'Placed ask: (price: %s, amount: %s)' % (order.price, order.amount))
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
          trade_price = self.GetPrice(bid.symbol)
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
      # Stop processing orders if there is no "breakeven".
      if trade_price is None:
        # Put orders back in the queue.
        bid_q.put((-highest_bid.price, highest_bid.id, highest_bid))
        ask_q.put((lowest_ask.price, lowest_ask.id, lowest_ask))
        # Stop processing orders.
        break

      # Determine trade amount.
      trade_amount = self._DetermineTradeAmount(highest_bid, lowest_ask)

      # Execute the trade.
      self._ExecuteTrade(trade_amount, trade_price, highest_bid, lowest_ask)

      if self.logger:
        self.logger.debug(
            'Trade executed (price: %s, amount: %s).' % (
            trade_price, trade_amount))

      # Record trade history.
      timestamp = self.time.GetCurrentTime()
      self.history[symbol].append((timestamp, trade_price, trade_amount))

    # All matching trades resolved.
    if self.logger:
      self.logger.debug('Orders processed.')
