
import argparse
import logging
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
  history = {asset.Symbols.BTC: [(-1, 100, -1)]}
  print 'initial price: %s' % history[asset.Symbols.BTC][0][1]
  ee = sim_exchange.SimulatedExchange(
      time=time_obj, symbols=symbols, history=history, logger=logger)

  # Create simulated trading environment.
  sim_env = env.TradingEnvironment(
      time=time_obj, exchanges=[ee], logger=logger)

  # Generate agents.
  strategy_dist = {
      trade_strategies.RandomStrategy(): 0.7,
      trade_strategies.BandedMomentumStrategy(): 0.3,
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

  print '\ndone.'


if __name__ == '__main__':
  main(sys.argv[1:])
