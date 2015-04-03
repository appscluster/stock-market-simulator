
class Agent(object):
    def __init__(self, *args, **kwargs):
        pass

    def GetExchange(self, *args):
        """Gets the exchange the trader wants to trade on"""
        raise NotImplementedError()

    def GetWallet(self):
        """Gets the wallet of assets specific to this trader"""
        raise NotImplementedError()



