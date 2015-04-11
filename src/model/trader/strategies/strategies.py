
import random as rand


class Strategy(object):
  """Different types of trading strategies"""

  def __init__(self, *args, **kwargs):
    """Base class initialization here."""
    pass

  def Invoke(self, *args, **kwargs):
    """Invokes this strategy."""
    raise NotImplementedError('Override this method in a subclass.')


class RandomStrategy(Strategy):
  """Zero-intelligence, random trading strategy."""
  
  def __init__(self, buy_price_std=1, sell_price_std=1):
    """Initialize the trade strategy."""
    # Price is determined by Gauss(mean=market_price, std) distribution.
    self.buy_price_std = buy_price_std
    self.sell_price_std = sell_price_std

  def Invoke(self, exchanges, wallet):
    """Invoke the random strategy.

    Args:
      exchanges: Exchanges where trades can be made.
      wallet: The assets available for trading.
    """
    # Pick one exchange and one asset to trade on.
    exchange = rand.choice(exchanges)
    symbol = rand.choice(exchange.GetSymbols())
    price = exchange.GetPrice(symbol)

    #variable that decides whether agent will buy or sell
    buy = rand.getrandbits(1)
    if buy:
      # Pick bid price from Gaussian distribution centered at market price.
      buyPrice = int(rand.gauss(price, self.buy_price_std))
      walletCash = wallet.GetAmount('usd')
      if walletCash > buyPrice:
        # Buy amount from [1, max_amount_affordable]
        amount = rand.randint(1, int(walletCash/buyPrice))
        exchange.Buy(symbol, amount, wallet, buyPrice)
    if not buy:
      # Pick bid price from Gaussian distribution centered at market price.
      sellPrice = int(rand.gauss(price, self.sell_price_std))
      walletAmount = wallet.GetAmount(symbol)
      if walletAmount >= 1:
        # Sell amount from [1, total_shares_int_wallet]
        amount = rand.randint(1, int(walletAmount))
        #print("Wallet Amount is %s" % walletAmount)
        exchange.Sell(symbol, amount, wallet, sellPrice)
