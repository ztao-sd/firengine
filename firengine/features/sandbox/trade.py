from collections import defaultdict

from firengine.features.async_stream.base_stream import BaseStream
from firengine.model.data_model import Order, Trade


class OrderRecorder:
    def __init__(self):
        self._orders: defaultdict[str, dict[str, Order]] = defaultdict(dict)

    @property
    def orders(self) -> defaultdict[str, dict[str, Order]]:
        return self._orders

    def handle_order_request(self, order_request ):
        """
        For backtest purpose only
        """
        order = Order()
        self.handle_order(order)

    def handle_order(self, order: Order):
        match order.status:
            case "open":
                self._open_orders_per_symbol[order.symbol][order.id] = order
            case "closed":
                self._open_orders_per_symbol[order.symbol].pop(order.id, None)
                self._closed_orders_per_symbol[order.symbol][order.id] = order
            case _:
                self._open_orders_per_symbol[order.symbol].pop(order.id, None)
                self._closed_orders_per_symbol[order.symbol].pop(order.id, None)


class TradeRecorder:
    def __init__(self):
        self._trades: defaultdict[str, dict[str, Trade]] = defaultdict(dict)

    @property
    def trades(self) -> defaultdict[str, dict[str, Trade]]:
        return self._trades


class OHLCVMatcherTradeEngine:
    def __init__(self, trade_stream:  BaseStream[Trade]):
        self._trader_stream = trade_stream
        self._orders

    def match_order(self):
        pass

class Trader:

    def __init__(self, order_stream: BaseStream[Order]):
        self._order_stream = order_stream

    async def submit_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price: float,
    ):
        order_request  = OrderRequest(


        )
        await self._order_stream.asend(order)

    async def modify_order(self):
        order = Order()
        await self._order_stream.asend(order)

    async def cancel_order(self):
        order = Order()
        await self._order_stream.asend(order)

