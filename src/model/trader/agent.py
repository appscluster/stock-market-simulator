

class Agent(object):
  """Base class for trading agents."""

  def Trade(self):
    """Invokes the agent's trade strategy."""
    raise NotImplementedError('Override this method in a subclass.')

  def GetExchange(self, *args):
    """Gets the exchange the trader wants to trade on"""
    raise NotImplementedError('Override this method in a subclass.')

  def GetWallet(self):
    """Gets the wallet of assets specific to this trader"""
    raise NotImplementedError('Override this method in a subclass.')
