
import unittest

import src.model.asset as asset
import src.model.environment.environment_time as env_time
import src.model.market.simulated_exchange as sim_exchange
import src.model.wallet as wallet


class TestSimulatedExchange_OrderProcessing(unittest.TestCase):
  """Test cases for buy/sell on simulated exchange."""

  # Default asset amount in test agents' wallets.
  DEFAULT_WALLET_AMOUNT = 100
  # Default price for assets on the exchange.
  DEFAULT_MARKET_PRICE = 1

  def setUp(self):
    """Test set up. Called before each test case."""
    # Create exchange.
    time_obj = env_time.IntegerTime(start_time=0, time_unit=1)
    symbols = [asset.Symbols.BTC]
    history = {asset.Symbols.BTC: [(-1, self.DEFAULT_MARKET_PRICE, 0)]}
    self.exchange = sim_exchange.SimulatedExchange(
        time=time_obj, symbols=symbols, history=history)
    # Create buyer / seller wallets.
    initial_balance = {
        asset.Symbols.USD: self.DEFAULT_WALLET_AMOUNT,
        asset.Symbols.BTC: self.DEFAULT_WALLET_AMOUNT,
    }
    self.buyer_wallet = wallet.Wallet(initial_balance)
    self.seller_wallet = wallet.Wallet(initial_balance)

  def tearDown(self):
    """Test tear down. Called after each test case."""
    pass

  # BEGIN tests for trade amount calculation.

  def test_LimitOrdersMatched_EqualSupplyAndDemand(self):
    """Both limit orders are filled and cleared from the orderbook."""
    # Buy order for some amount B.
    buy_price = 5
    buy_amount = 3
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, self.buyer_wallet, price=buy_price)
    # Sell order for amount S == B.
    sell_price = buy_price
    sell_amount = buy_amount
    self.exchange.Sell(asset.Symbols.BTC, sell_amount, self.seller_wallet, price=sell_price)

    # All shares transferred from seller to buyer.
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - buy_amount, self.seller_wallet.GetAmount(asset.Symbols.BTC))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + buy_amount, self.buyer_wallet.GetAmount(asset.Symbols.BTC))
    # Cash transferred from buyer to seller.
    cash_traded = buy_price * buy_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - cash_traded, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + cash_traded, self.seller_wallet.GetAmount(asset.Symbols.USD))

    # Orders cleared from orderbook.
    orderbook = self.exchange.GetOrderbook(asset.Symbols.BTC)
    self.assertTrue(len(orderbook['bids']) == 0)
    self.assertTrue(len(orderbook['asks']) == 0)

  def test_LimitOrdersMatched_ExcessDemand(self):
    """Buy order is partially filled and sell order is filled."""
    # Buy order for amount B.
    buy_price = 5
    buy_amount = 3
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, self.buyer_wallet, price=buy_price)
    # Sell order for S < B.
    sell_price = buy_price
    sell_amount = buy_amount - 1
    self.exchange.Sell(asset.Symbols.BTC, sell_amount, self.seller_wallet, price=sell_price)

    # The supplied amount S was traded.
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - sell_amount, self.seller_wallet.GetAmount(asset.Symbols.BTC))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + sell_amount, self.buyer_wallet.GetAmount(asset.Symbols.BTC))
    # Cash for the trade transferred.
    cash_in_pool = buy_price * buy_amount
    cash_traded = buy_price * sell_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - cash_in_pool, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + cash_traded, self.seller_wallet.GetAmount(asset.Symbols.USD))

    # Buy order partially filled.
    orderbook = self.exchange.GetOrderbook(asset.Symbols.BTC)
    self.assertTrue(len(orderbook['bids']) == 1)
    remaining_order = orderbook['bids'][0]
    excess_demand = buy_amount - sell_amount
    self.assertTrue(remaining_order.amount == excess_demand)
    # Sell order filled.
    self.assertTrue(len(orderbook['asks']) == 0)
      
  def test_LimitOrdersMatched_ExcessSupply(self):
    """Sell order is partially filled and buy order is filled."""
    # Buy order for amount B.
    buy_price = 5
    buy_amount = 3
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, self.buyer_wallet, price=buy_price)
    # Sell order for amount S > B.
    sell_price = buy_price
    sell_amount = buy_amount + 1
    self.exchange.Sell(asset.Symbols.BTC, sell_amount, self.seller_wallet, price=sell_price)

    # Specified amount of shares taken from seller.
    shares_in_pool = sell_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - shares_in_pool, self.seller_wallet.GetAmount(asset.Symbols.BTC))
    # The demanded amount B was transferred to buyer.
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + buy_amount, self.buyer_wallet.GetAmount(asset.Symbols.BTC))

    # Cash for the trade transferred.
    cash_traded = buy_price * buy_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - cash_traded, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + cash_traded, self.seller_wallet.GetAmount(asset.Symbols.USD))

    # Sell order partially filled.
    orderbook = self.exchange.GetOrderbook(asset.Symbols.BTC)
    self.assertTrue(len(orderbook['asks']) == 1)
    remaining_order = orderbook['asks'][0]
    excess_supply = sell_amount - buy_amount
    self.assertTrue(remaining_order.amount == excess_supply)
    # Buy order filled.
    self.assertTrue(len(orderbook['bids']) == 0)

  # END tests for trade amount calculation.
  # BEGIN tests for trade price calculation.

  def test_LimitOrders_NoPriceAgreement(self):
    """No trade is executed if S > B."""
    # Buyer places limit order at price B.
    buy_price = 1
    buy_amount = 1
    self.exchange.Buy(
        asset.Symbols.BTC, buy_amount, self.buyer_wallet, price=buy_price)
    # Seller places limit order at price S > B.
    sell_price = buy_price + 1
    sell_amount = 1
    self.exchange.Sell(
        asset.Symbols.BTC, sell_amount, self.seller_wallet, price=sell_price)
        
    # No trade was executed. However, posted amounts (i.e. cash from buyer,
    # stock from seller) should have been moved to the exchange's trade pool.
    buy_cash = buy_price * buy_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - buy_cash, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT, self.buyer_wallet.GetAmount(asset.Symbols.BTC))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT, self.seller_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - sell_amount, self.seller_wallet.GetAmount(asset.Symbols.BTC))

    # Trade pool contains posted assets.
    trade_pool = self.exchange.wallet
    self.assertEqual(buy_cash, trade_pool.GetAmount(asset.Symbols.USD))
    self.assertEqual(sell_amount, trade_pool.GetAmount(asset.Symbols.BTC))

  def test_LimitOrdersMatched_BuyerFirst(self):
    """Trade executes at price B if buyer places limit order first and S > B."""
    # Buyer places bid at price B.
    buy_price = 3
    buy_amount = 2
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, self.buyer_wallet, price=buy_price)
    # Seller places ask at price S < B.
    sell_price = buy_price - 1
    sell_amount = buy_amount
    self.exchange.Sell(asset.Symbols.BTC, sell_amount, self.seller_wallet, price=sell_price)

    # Shares transferred from seller to buyer.
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - buy_amount, self.seller_wallet.GetAmount(asset.Symbols.BTC))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + buy_amount, self.buyer_wallet.GetAmount(asset.Symbols.BTC))
    # Trade was executed at price B.
    cash_traded = buy_price * buy_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - cash_traded, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + cash_traded, self.seller_wallet.GetAmount(asset.Symbols.USD))

  def test_LimitOrdersMatched_SellerFirst(self):
    """Trade executes at price S if seller places limit order first."""
    # Seller places ask at price S.
    sell_price = 5
    sell_amount = 1
    self.exchange.Sell(asset.Symbols.BTC, sell_amount, self.seller_wallet, price=sell_price)
    # Buyer places bid at price B > S.
    buy_price = sell_price + 1
    buy_amount = sell_amount
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, self.buyer_wallet, price=buy_price)

    # Shares transferred from seller to buyer.
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + sell_amount, self.buyer_wallet.GetAmount(asset.Symbols.BTC))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - sell_amount, self.seller_wallet.GetAmount(asset.Symbols.BTC))
    # Trade was executed at price S.
    cash_traded = sell_price * sell_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - cash_traded, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + cash_traded, self.seller_wallet.GetAmount(asset.Symbols.USD))

  def test_MarketOrderBuy_LimitOrderSell(self):
    """Trade executes at price S if buyer places a market order."""
    # Buyer places market order.
    buy_amount = 1.0
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, self.buyer_wallet)
    # Seller places ask at price S.
    sell_price = 5.0
    sell_amount = buy_amount
    self.exchange.Sell(asset.Symbols.BTC, sell_amount, self.seller_wallet, price=sell_price)

    # Buy order was filled at S.
    cash_traded = sell_price * buy_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - cash_traded, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + cash_traded, self.seller_wallet.GetAmount(asset.Symbols.USD))
    # Shares transferred from seller to buyer.
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - sell_amount, self.seller_wallet.GetAmount(asset.Symbols.BTC))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + buy_amount, self.buyer_wallet.GetAmount(asset.Symbols.BTC))

  def test_LimitOrderBuy_MarketOrderSell(self):
    """Trade executes at price B if seller places a market order."""
    # Buyer places bid at price B.
    buy_price = 5
    buy_amount = 1
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, self.buyer_wallet, price=buy_price)
    # Seller places market order.
    sell_amount = buy_amount
    self.exchange.Sell(asset.Symbols.BTC, sell_amount, self.seller_wallet)

    # Shares transferred from seller to buyer.
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - buy_amount, self.seller_wallet.GetAmount(asset.Symbols.BTC))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + buy_amount, self.buyer_wallet.GetAmount(asset.Symbols.BTC))
    # Trade executed at price B.
    cash_traded = buy_price * buy_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - cash_traded, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + cash_traded, self.seller_wallet.GetAmount(asset.Symbols.USD))

  def test_MarketOrderBuy_MarketOrderSell(self):
    """Trade price is market price if both buyer and seller place market order."""
    # Buyer places market order.
    buy_amount = 5
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, self.buyer_wallet)
    # Seller places market order.
    sell_amount = buy_amount
    self.exchange.Sell(asset.Symbols.BTC, sell_amount, self.seller_wallet)

    # Trade was executed at market price.
    cash_traded = self.DEFAULT_MARKET_PRICE * buy_amount
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - cash_traded, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + cash_traded, self.seller_wallet.GetAmount(asset.Symbols.USD))
    # Shares transferred from seller to buyer.
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + buy_amount, self.buyer_wallet.GetAmount(asset.Symbols.BTC))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - buy_amount, self.seller_wallet.GetAmount(asset.Symbols.BTC))

  def test_MarketOrder_BestAvailablePrice(self):
    """Market order is filled at best available price."""
    # Buyers place limit orders.
    buy_amount = 1
    lower_buy_price = 8.0
    higher_buy_price = 10.0
    other_buyer_wallet = wallet.Wallet({asset.Symbols.USD: self.DEFAULT_WALLET_AMOUNT})
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, self.buyer_wallet, price=higher_buy_price)
    self.exchange.Buy(asset.Symbols.BTC, buy_amount, other_buyer_wallet, price=lower_buy_price)
    # Seller places market order.
    sell_amount = buy_amount
    self.exchange.Sell(asset.Symbols.BTC, sell_amount, self.seller_wallet)

    # Sell order filled at best available price.
    trade_price = higher_buy_price
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - trade_price, self.buyer_wallet.GetAmount(asset.Symbols.USD))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + trade_price, self.seller_wallet.GetAmount(asset.Symbols.USD))
    # Shares transferred from seller to buyer.
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT + buy_amount, self.buyer_wallet.GetAmount(asset.Symbols.BTC))
    self.assertEqual(self.DEFAULT_WALLET_AMOUNT - buy_amount, self.seller_wallet.GetAmount(asset.Symbols.BTC))

  # END tests for trade price calculation.


class TestSimulatedExchange_History(unittest.TestCase):
  """Test cases for simulated exchange."""

  # Default price for assets on the exchange.
  DEFAULT_MARKET_PRICE = 100

  def setUp(self):
    """Test set up. Called before each test case."""
    # Create exchange.
    self.time_obj = env_time.IntegerTime(start_time=0, time_unit=1)
    self.symbols = [asset.Symbols.BTC]
    self.history = {asset.Symbols.BTC: [(-1, self.DEFAULT_MARKET_PRICE, -1)]}
    self.exchange = sim_exchange.SimulatedExchange(
        time=self.time_obj, symbols=self.symbols, history=self.history)

  def test_GetHistory_NoHistory(self):
    """No candles returned if there is no history for the asset."""
    self.exchange.history[asset.Symbols.BTC] = []
    candles = self.exchange.GetHistory(asset.Symbols.BTC)
    # Returns empty list.
    self.assertIsNotNone(candles)
    self.assertTrue(len(candles) == 0)

  def test_GetHistory_EnoughHistory(self):
    """Requested number of candles are generated."""
    # Generate history for t=1,2,3
    history = []
    num_data_points = 3
    for i in range(num_data_points):
      # Step time forward.
      self.exchange.time.Step()
      # Create record for each time step.
      timestamp = self.exchange.time.GetCurrentTime()
      record = (timestamp, self.DEFAULT_MARKET_PRICE + i, 1)
      history.append(record)
    # The exchange has the history.
    self.exchange.history[asset.Symbols.BTC] = history

    # Ask for candles within the range of available history.
    limit = num_data_points - 1
    candles = self.exchange.GetHistory(asset.Symbols.BTC, limit=limit)
    # Last two data points are returned.
    self.assertIsNotNone(candles)
    self.assertTrue(len(candles) == limit)
    expected_candles = history[-limit:]
    for i, candle in enumerate(candles):
      expected_timestamp = expected_candles[i][0]
      self.assertEqual(expected_timestamp, candle[0])
      expected_price = expected_candles[i][1]
      self.assertEqual(expected_price, candle[1])

  def test_GetHistory_NotEnoughHistory(self):
    """Data points before beginning of available history not returned."""
    # Generate history for t=1,2,3
    history = []
    num_data_points = 3
    for i in range(num_data_points):
      # Step time forward.
      self.exchange.time.Step()
      # Create record for each time step.
      timestamp = self.exchange.time.GetCurrentTime()
      record = (timestamp, self.DEFAULT_MARKET_PRICE + i, 1)
      history.append(record)
    # The exchange has the history.
    self.exchange.history[asset.Symbols.BTC] = history

    #  Ask for more data points than available.
    limit = num_data_points + 1
    candles = self.exchange.GetHistory(asset.Symbols.BTC, limit=limit)
    # Only available data points were returned.
    self.assertIsNotNone(candles)
    self.assertTrue(len(candles) == num_data_points)
    expected_candles = history
    for i, candle in enumerate(candles):
      expected_timestamp = expected_candles[i][0]
      expected_price = expected_candles[i][1]
      self.assertEqual(expected_timestamp, candle[0])
      self.assertEqual(expected_price, candle[1])

  def test_GetHistory_CandleSizeGreaterThanHistory(self):
    """Only one candle is returned."""
    initial_time = self.exchange.time.GetCurrentTime()
    # Generate history for t=1,2,3
    history = []
    num_data_points = 3
    for i in range(num_data_points):
      # Step time forward.
      self.exchange.time.Step()
      # Create record for each time step.
      timestamp = self.exchange.time.GetCurrentTime()
      record = (timestamp, self.DEFAULT_MARKET_PRICE + i, 1)
      history.append(record)
    # The exchange has the history.
    self.exchange.history[asset.Symbols.BTC] = history

    # Candle has greater length than history.
    limit = 1
    candle_size = 5
    candles = self.exchange.GetHistory(
        asset.Symbols.BTC, limit=limit, candle_size=candle_size)

    # Only one candle is returned.
    self.assertIsNotNone(candles)
    self.assertTrue(len(candles) == 1)
    expected_price = history[-1][1]
    self.assertEqual(expected_price, candles[0][1])
