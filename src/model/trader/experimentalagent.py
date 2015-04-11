
import random as rand

import src.model.trader.agent as agent
import src.model.wallet as wallet


class ExperimentalAgent(agent.Agent):

  def __init__(self, strategy, initialWallet=None, initialExchanges=[]):
    """Initialize the agent.
    
    Args:
      strategy: The trader's trading strategy.
      initialWallet: (optional) The trader's initial funds.
      initialExchanges: (optional) The exchanges the trader should trade on.
    """
    self.strategy = strategy
    self.wallet = initialWallet or wallet.Wallet()
    self.exchanges = initialExchanges

  def Trade(self):
    """Invokes this agent's trade strategy."""
    self.strategy.Invoke(self.exchanges, self.wallet)

  def GetExchanges(self):
    """Gets the exchange the trader wants to trade on"""
    return self.exchanges

  def GetWallet(self):
    """Gets the portfolio of agent"""
    return self.wallet
