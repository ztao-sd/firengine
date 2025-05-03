from collections import defaultdict

import ccxt.pro as ccxt

from firengine.model.data_model import Order, OrderInfo, PrivateTrade


class OrderManager:
    def __init__(self, ex: ccxt.Exchange):
        self._exchange = ex
        self._symbols: set[str] = set()
        self._open_orders: defaultdict[str, dict[str, Order]] = defaultdict(dict)
        self._closed_orders: defaultdict[str, dict[str, Order]] = defaultdict(dict)
        self._trades_per_order: defaultdict[str, dict[str, PrivateTrade]] = defaultdict(dict)

        # Signals
        # self._order_closed_signal = Signal[Order]()
        # self._order_opened_signal = Signal[Order]()

    @property
    def exchange(self) -> ccxt.Exchange:
        return self._exchange

    @property
    def symbols(self) -> set[str]:
        return self._symbols

    def get_open_order(self, symbol: str, order_id: str) -> Order | None:
        return self._open_orders[symbol].get(order_id)

    def get_closed_order(self, symbol: str, order_id: str) -> Order | None:
        return self._closed_orders[symbol].get(order_id)

    def get_open_orders_per_symbol(self, symbol: str) -> dict[str, Order]:
        return self._open_orders[symbol]

    def get_closed_orders_per_symbol(self, symbol: str) -> dict[str, Order]:
        return self._closed_orders[symbol]

    def get_trades_per_order(self, order_id: str) -> dict[str, PrivateTrade]:
        return self._trades_per_order[order_id]

    def on_order_updated(self, order: Order):
        match order.status:
            case "open":
                self._open_orders[order.symbol][order.id] = order
            case "closed":
                self._open_orders[order.symbol].pop(order.id, None)
                self._closed_orders[order.symbol][order.id] = order
            case _:
                self._open_orders[order.symbol].pop(order.id, None)
                self._closed_orders[order.symbol].pop(order.id, None)

    def on_trade_updated(self, trade: PrivateTrade):
        self._trades_per_order[trade.order][trade.id] = trade

    async def add_symbol(self, symbol: str):
        if symbol not in self._symbols:
            self._symbols.add(symbol)
            self._open_orders[symbol] |= await self._fetch_open_orders(self._exchange, symbol)
            self._closed_orders[symbol] |= await self._fetch_closed_orders(self._exchange, symbol)

    async def refresh(self, symbol: str):
        if symbol in self._symbols:
            self._open_orders[symbol] |= await self._fetch_open_orders(self._exchange, symbol)
            self._closed_orders[symbol] |= await self._fetch_closed_orders(self._exchange, symbol)

    @staticmethod
    async def _fetch_open_orders(ex: ccxt.Exchange, symbol: str) -> dict[str, Order]:
        ods = await ex.fetch_open_orders(symbol)
        orders = {v["id"]: Order.from_kwargs(**v) for v in ods}
        return orders

    @staticmethod
    async def _fetch_closed_orders(ex: ccxt.Exchange, symbol: str) -> dict[str, Order]:
        ods = await ex.fetch_closed_orders(symbol)
        orders = {v["id"]: Order.from_kwargs(**v) for v in ods}
        return orders

    async def submit_order(
        self,
        symbol: str,
        type: str,
        side: str,
        amount: float,
        price: float,
        time_in_force=None,
        expired_dt=None,
    ) -> OrderInfo:
        od = await self._exchange.create_order(
            symbol=symbol,
            type=type,
            side=side,
            amount=amount,
            price=price,
        )
        info = OrderInfo.from_kwargs(**od)
        info.symbol = symbol
        info.type = type
        info.side = side
        info.amount = amount
        info.price = price
        return info

    async def cancel_order(self, order_id: str, symbol: str):
        await self._exchange.cancel_order(order_id, symbol)

    async def cancel_all_orders(self, symbol: str):
        await self._exchange.cancel_all_orders(symbol)

    async def edit_order(self, order_id: str, symbol: str, type: str, side: str, amount: float, price: float):
        await self._exchange.edit_order(id=order_id, symbol=symbol, type=type, side=side, amount=amount, price=price)

    async def modify_order_info(self, order_info: OrderInfo):
        await self.edit_order(
            order_info.id, order_info.symbol, order_info.type, order_info.side, order_info.amount, order_info.price
        )

    async def modify_order(self, order: Order):
        await self.edit_order(order.id, order.symbol, order.type, order.side, order.amount, order.price)
