
import argparse
import logging
import matplotlib.pyplot as plt
import numpy as np
import sys
import time

import src.model.asset as asset
import src.model.environment.environment as env
import src.model.environment.environment_time as env_time
import src.model.market.simulated_exchange as sim_exchange
import src.model.trader.experimentalagent as exp_agent
import src.model.trader.strategies.strategies as trade_strategies
import src.model.wallet as wallet


# logging
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


def main(argv):
  # Command-line args.
  parser = argparse.ArgumentParser()
  parser.add_argument('-log_level', action="store", type=str, default='')
  parser.add_argument('-num_agents', action="store", type=int, default=10)
  parser.add_argument('-timesteps', action="store", type=int, default=10)
  args = parser.parse_args(argv)

  print 'num agents: %d' % args.num_agents
  print 'num steps: %d' % args.timesteps

  # Logging
  if args.log_level:
    # Log level
    log_level = LOG_LEVELS[args.log_level]
    # Logging handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    formatter = logging.Formatter('%(name)s - %(levelname)s: %(message)s')
    ch.setFormatter(formatter)
    # Logger
    logger = logging.getLogger()
    logger.addHandler(ch)
    logger.setLevel(log_level)
  else:
    logger = None

  # Create time object for environment.
  time_obj = env_time.IntegerTime(start_time=0, time_unit=1)

  # Create exchange.
  symbols = [asset.Symbols.BTC]
  history = {asset.Symbols.BTC: [(-1, 20, -1)]}
  print 'initial price: %s' % history[asset.Symbols.BTC][0][1]
  ee = sim_exchange.SimulatedExchange(
      time=time_obj, symbols=symbols, history=history, logger=logger)

  # Create simulated trading environment.
  sim_env = env.TradingEnvironment(
      time=time_obj, exchanges=[ee], logger=logger)

  # Generate agents.
  strategy_dist = {
      trade_strategies.RandomStrategy(): 0.6,
      trade_strategies.BandedMomentumStrategy(): 0.1,
      trade_strategies.BandedMomentumStrategy(momentum=False): 0.3,
  }
  print 'Strategy distribution:'
  for strategy, ratio in strategy_dist.items():
    print '  %s = %s%%' % (strategy.__class__.__name__, ratio * 100)
  print
  initial_funds = {asset.Symbols.USD: 1000, asset.Symbols.BTC: 10}  # distr?
  sim_env.GenerateAgents(args.num_agents, strategy_dist, initial_funds)

  # Run the simulation.
  start_time = time.time()
  sim_env.Run(timesteps=args.timesteps)
  end_time = time.time()
  time_elapsed = end_time - start_time

  print 'final price: %s' % sim_env.exchanges[0].GetPrice(asset.Symbols.BTC)
  print 'simulation time: %.4f seconds' % time_elapsed

  # Plot price history.
  history = ee.GetHistory(asset.Symbols.BTC, limit=None)
  #print 'got history length %d' % len(history)
  t, p = zip(*history)
  #print t
  fig_hist = plt.figure()
  ax1 = fig_hist.add_subplot(111)
  ax1.plot(t, p, marker='x')
  ax1.set_xlabel('Timestep')
  ax1.set_ylabel('Price')
  ax1.set_title('Price History for %s' % asset.Symbols.BTC)

  # Get distribution of wealth.
  agents = sim_env.GetAgents()
  dollars = []
  shares = []
  for agent in agents:
    w = agent.GetWallet()
    d = w.GetAmount(asset.Symbols.USD)
    s = w.GetAmount(asset.Symbols.BTC)
    dollars.append(d)
    shares.append(s)
  cash_on_exchange = ee.wallet.GetAmount(asset.Symbols.USD)
  shares_on_exchange = ee.wallet.GetAmount(asset.Symbols.BTC)
  print '\ncash on exchange: %s' % cash_on_exchange
  print 'shares on exchange: %s' % shares_on_exchange
  # Plot distribution of dollars.
  fig_dollars = plt.figure()
  ax2 = fig_dollars.add_subplot(111)
  n, bins, patches = ax2.hist(dollars, 25, facecolor='green')
  ax2.set_xlabel('Amount of Cash')
  ax2.set_ylabel('Number of Agents')
  ax2.set_title('Distribution of Cash Among %d Traders' % len(agents))
  ax2.grid(True)
  # Plot distribution of shares.
  fig_shares = plt.figure()
  ax3 = fig_shares.add_subplot(111)
  ax3.hist(shares, 25, facecolor='green')
  #ax3.text(1, 1,'matplotlib', transform=ax3.transAxes, horizontalalignment='right', verticalalignment='top')
  ax3.set_xlabel('Number of Shares')
  ax3.set_ylabel('Number of Agents')
  ax3.set_title('Distribution of Shares Among %d Traders' % len(agents))
  ax3.grid(True)
  # Show plots.
  plt.show()
  print '\ndone.'


if __name__ == '__main__':
  main(sys.argv[1:])
