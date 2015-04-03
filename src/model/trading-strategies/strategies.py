import random as rand

class Strategies():
    """Different types of trading strategies"""

    def __init__(self, initialExchanges):
        self.exchanges = initialExchanges

    def RandomStrategy():
        exchangeNumber = rand.randint(0,len(self.exchanges-1))
        exchange = self.exchanges[exchangeNumber]
        symbols = exchange.GetSymbols()
        price = exchange.GetPrice()
        #variable that decides whether agent will buy or sell
        buy = rand.getrandbits(1)
        if buy:
            
        
