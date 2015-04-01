
import copy


class Wallet(object):
  """Wallet containing multiple types of assets."""

  def __init__(self, amounts={}):
    # Make sure this wallet has its own copy of "amounts".
    # Note: This is a shallow copy.
    self.amounts = copy.copy(amounts)

  def GetAmount(self, symbol):
    """Get amount of asset in this wallet.

    Args:
      symbol: Name of the asset.

    Returns:
      Decimal amount of the asset this wallet contains.
    """
    if symbol in self.amounts:
      return self.amounts[symbol]
    return 0

  def AddAmount(self, symbol, amount):
    """Add specified amount of asset to this wallet.
    
    Args:
      symbol: Name of the asset.
      amount: Amount to add the wallet.
    """
    if symbol in self.amounts:
      self.amounts[symbol] += amount
    else:
      self.amounts[symbol] = amount

  def RemoveAmount(self, symbol, amount):
    """Remove specified amount of asset from this wallet.
    
    Args:
      symbol: Name of the asset.
      amount: Amount to add the wallet.
    """
    if symbol in self.amounts:
      self.amounts[symbol] -= amount
    else:
      raise Exception('%s not in this wallet.' % symbol)

  def __str__(self):
    """toString method"""
    result = '('
    for symbol, amount in self.amounts.items():
      result += '%s: %s, ' % (symbol, amount)
    result += ')'
    return result
    
