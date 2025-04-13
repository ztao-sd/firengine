from firengine.features.streaming.base_stream import BaseExchangeStream


class MyTradeStream(BaseExchangeStream[Trade]):

    def __init__(self):
        super().__init__()

