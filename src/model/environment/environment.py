"""Environment for trading agents."""

import src.model.environment.environment_time as env_time
import src.model.trader.experimentalagent as exp_agent
import src.model.wallet as wallet


class TradingEnvironment(object):
  """Environment where agents can trade on the market."""

  inf = float('inf')

  def __init__(self, *args, **kwargs):
    """Initialize the trading environment."""
    # Time definition for the environment.
    self.time = kwargs['time']
    # Markets in the environment.
    self.exchanges = kwargs['exchanges']
    #self.trade_order = kwargs['trade_order'] or None
    for exchange in self.exchanges:
      # exchange.time = self.time  # cyclic dep?
      pass
    # Agents in the environment.
    self.agents = []
    # Logging.
    if 'logger' in kwargs:
      self.logger = kwargs['logger']
    else:
      self.logger = None

  def GetTime(self):
    """Return time object used in this environment."""
    return self.time

  def GetAgents(self):
    """Gets agents in the environment."""
    return self.agents

  def GenerateAgents(self, num_agents, strategy_distribution, initial_funds):
    """Use given distribution to create agents with various trading strategies.

    Args:
      num_agents: Number of agents to create.
      strategy_distribution: Distribution of trading strategies.
      initial_funds: Starting funds for each agent.
    """
    # Create agents using the strategy distribution.
    for strategy, ratio in strategy_distribution.items():
      for _ in range(int(ratio * num_agents)):
        trading_account = wallet.Wallet(initial_funds)
        agent = exp_agent.ExperimentalAgent(
            strategy, initialWallet=trading_account, initialExchanges=self.exchanges)
        self.agents.append(agent)
      # logging
      if self.logger:
        self.logger.info('Generated %d agents with %s.' % (
            ratio * num_agents, strategy.__class__.__name__))

  def Run(self, timesteps=inf):
    """Run the simulation for specified number of timesteps.

    Args:
      timesteps: (optional) Number of time steps to run the simulation.
    """
    steps_taken = 0
    while steps_taken < timesteps:
      # logging
      if self.logger:
        self.logger.debug('TIMESTEP %d' % steps_taken)
        for exchange in self.exchanges:
          self.logger.debug('  Stock prices on %s:' % exchange.__class__.__name__)
          for symbol in exchange.GetSymbols():
            self.logger.debug('    %s %d' % (symbol, exchange.GetPrice(symbol)))
      # Agents trade.
      for agent in self.agents:
        agent.Trade()
      # Update timestep.
      self.time.Step()
      steps_taken += 1
