

class Exchange(object):

  def __init__(self, *args, **kwargs):
    pass

  def GetSymbols(self):
    """Gets the names of securities traded on this exchange."""
    raise NotImplementedError()

  def GetHistory(self, symbol):
    """Get market history for security with given name.

    Args:
      symbol: Name of the security.

    Returns:
      All available market history for the specified asset.
    """
    raise NotImplementedError()

  def Buy(self, *args, **kwargs):
    """Submit a buy order for some security on this exchange."""
    raise NotImplementedError()

  def Sell(self, *args, **kwargs):
    """Submit a sell order for some security on this exchange."""
    raise NotImplementedError()
