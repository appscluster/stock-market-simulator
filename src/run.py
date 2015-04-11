
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
  prices = {asset.Symbols.BTC: 100}
  ee = sim_exchange.SimulatedExchange(
      symbols=symbols, prices=prices, logger=logger)

  # Create simulated trading environment.
  sim_env = env.TradingEnvironment(
      time=time_obj, exchanges=[ee], logger=logger)

  # Generate agents.
  strategy_dist = {trade_strategies.RandomStrategy(): 1.0}  # 100% random strategy
  initial_funds = {asset.Symbols.USD: 1000, asset.Symbols.BTC: 10}  # distr?
  sim_env.GenerateAgents(args.num_agents, strategy_dist, initial_funds)

  # Run the simulation.
  sim_env.Run(timesteps=args.timesteps)

  print 'final price: %f' % sim_env.exchanges[0].GetPrice(asset.Symbols.BTC)

  print '\ndone.'


if __name__ == '__main__':
  main(sys.argv[1:])
