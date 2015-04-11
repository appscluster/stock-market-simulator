
import src.util.enum as enum


Symbols = enum.enum(
  USD='usd',
  BTC='btc',
)


def GetAllSymbols():
  """Gets the list of all defined symbols."""
  symbols = [getattr(Symbols, name) for name in dir(Symbols)
             if not name.startswith('_')]
  return symbols
