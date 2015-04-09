

class Exchange(object):
  """Interface for an exchange where agents trade."""

  def __init__(self, *args, **kwargs):
    pass

  def GetSymbols(self):
    """Gets the names of assets traded on this exchange."""
    raise NotImplementedError()

  def GetHistory(self, symbol):
    """Get market history for asset with given name.

    Args:
      symbol: Name of the asset.

    Returns:
      All available market history for the specified asset.
    """
    raise NotImplementedError()

  def Buy(self, *args, **kwargs):
    """Submit a buy order for some asset on this exchange."""
    raise NotImplementedError()

  def Sell(self, *args, **kwargs):
    """Submit a sell order for some asset on this exchange."""
    raise NotImplementedError()
