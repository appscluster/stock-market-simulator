import src.model.wallet as wallet
import src.model.trader.agent as agent
import random as rand


class ExperimentalAgent(agent.Agent):

    def __init__(self, initialWallet=None, initialExchange=None):
        self.wallet = initialWallet or wallet.Wallet()
        self.exchanges = [initialExchange] or []

    def GetExchanges(self):
        """Gets the exchange the trader wants to trade on"""
        return self.exchanges

    def GetWallet(self):
        """Gets the portfolio of agent"""
        return self.wallet

    def RandomStrategy(self):
        exchangeNumber = rand.randint(0,len(self.exchanges)-1)
        exchange = self.exchanges[exchangeNumber]
        symbols = exchange.GetSymbols()
        symbolNumber = rand.randint(0, len(symbols)-1)
        symbol = symbols[symbolNumber]
        
        price = exchange.GetPrice(symbol)
        #variable that decides whether agent will buy or sell
        buy = rand.getrandbits(1)
        if buy:
            buyPrice = int(rand.gauss(price, 2))
            walletCash = self.wallet.GetAmount('usd')
            if walletCash > price:
                amount = rand.randint(1, walletCash/price)
                exchange.Buy(symbol, amount, wallet, buyPrice)
        if not buy:
            sellPrice = int(rand.gauss(price, 1))
            walletAmount = self.wallet.GetAmount(symbol)
            if walletAmount:
                amount = rand.randint(1, walletAmount)
                print("Wallet Amount is %s" % walletAmount)
                exchange.Sell(symbol, amount, wallet, sellPrice)

    
