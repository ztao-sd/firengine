from collections import defaultdict, deque
from dataclasses import replace
from random import randint

import ccxt
import shortuuid

from firengine.features.async_stream.base_stream import BaseStream
from firengine.lib.enumeration import OrderStatus, OrderType, TakerOrMaker, TimeInForce, TradeSide
from firengine.lib.logger.debug_logger import debug
from firengine.model.data_model import OHLCV, Order, PrivateTrade


def create_mock_open_order(
    timestamp: int,
    symbol: str,
    order_type: OrderType,
    side: TradeSide,
    amount: float,
    price: float,
) -> Order:
    return Order(
        id=shortuuid.uuid(),
        clientOrderId=shortuuid.uuid(),
        datetime=ccxt.Exchange.iso8601(timestamp),
        timestamp=timestamp,
        lastTradeTimestamp=-1,
        status=OrderStatus.open,
        symbol=symbol,
        type=order_type,
        timeInForce=TimeInForce.good_till_cancel,
        side=side,
        price=price,
        average=price,
        amount=amount,
        filled=0.0,
        remaining=amount,
        cost=0.0,
        trades=[],
        fee={},
    )


class BacktestTrader:
    def __init__(self, order_stream: BaseStream[Order]):
        self._order_stream = order_stream

        # State
        self._ohlcv_queues: defaultdict[str, deque[OHLCV]] = defaultdict(lambda: deque(maxlen=1_000))
        self._orders: defaultdict[str, dict[str, Order]] = defaultdict(dict)
        self._open_orders: defaultdict[str, dict[str, Order]] = defaultdict(dict)
        self._close_orders: defaultdict[str, dict[str, Order]] = defaultdict(dict)
        self._canceled_orders: defaultdict[str, dict[str, Order]] = defaultdict(dict)

        self._trades: defaultdict[str, dict[str, PrivateTrade]] = defaultdict(dict)

    async def submit_order(
        self,
        symbol: str,
        order_type: OrderType,
        side: TradeSide,
        amount: float,
        price: float,
    ):
        timestamp = self._ohlcv_queues[symbol][-1].timestamp
        order = create_mock_open_order(timestamp, symbol, order_type, side, amount, price)
        debug(f"Submit {order}")
        await self._order_stream.asend(order)

    async def modify_order(
        self,
        order: Order,
        /,
        **kwargs,
    ):
        order = replace(order, **kwargs)
        await self._order_stream.asend(order)

    async def cancel_order(self, order: Order):
        order = replace(order, status=OrderStatus.canceled)
        await self._order_stream.asend(order)

    async def handle_order(self, order: Order):
        self._orders[order.symbol][order.id] = order
        match order.status:
            case OrderStatus.open:
                self._open_orders[order.symbol][order.id] = order
            case OrderStatus.close:
                debug(f"Close {order}")
                self._open_orders[order.symbol].pop(order.id, None)
                self._close_orders[order.symbol][order.id] = order
            case _:
                self._open_orders[order.symbol].pop(order.id, None)
                self._canceled_orders[order.symbol][order.id] = order

    async def handle_trade(self, trade: PrivateTrade):
        debug(f"Fill {trade}")
        self._trades[trade.symbol][trade.id] = trade

    async def match_open_order(self, ohlcv: OHLCV):
        for order in list(self._open_orders[ohlcv.symbol].values()):
            if order.timestamp < ohlcv.timestamp:
                trade = None
                match order.type:
                    case OrderType.market:
                        price = (
                            max(ohlcv.low, order.price) if order.side == TradeSide.buy else min(ohlcv.high, order.price)
                        )
                        taker_or_maker = TakerOrMaker.taker
                        trade = PrivateTrade(
                            id=shortuuid.uuid(),
                            timestamp=ohlcv.timestamp,
                            datetime=ccxt.Exchange.iso8601(ohlcv.timestamp),
                            symbol=ohlcv.symbol,
                            order=order.id,
                            type=order.type,
                            side=order.side,
                            takerOrMaker=taker_or_maker,
                            price=price,
                            amount=order.amount,
                            cost=price * order.amount,
                            fee={},
                            fees={},
                        )
                    case OrderType.limit:
                        if (order.side == TradeSide.buy and ohlcv.low <= order.price) or (
                            order.side == TradeSide.sell and ohlcv.high >= order.price
                        ):
                            price = (
                                max(ohlcv.low, order.price)
                                if order.side == TradeSide.buy
                                else min(ohlcv.high, order.price)
                            )
                            taker_or_maker = TakerOrMaker.maker
                            trade = PrivateTrade(
                                id=shortuuid.uuid(),
                                timestamp=ohlcv.timestamp,
                                datetime=ccxt.Exchange.iso8601(ohlcv.timestamp),
                                symbol=ohlcv.symbol,
                                order=order.id,
                                type=order.type,
                                side=order.side,
                                takerOrMaker=taker_or_maker,
                                price=price,
                                amount=order.amount,
                                cost=price * order.amount,
                                fee={},
                                fees={},
                            )
                if trade is not None:
                    await self.handle_trade(trade)
                    await self.modify_order(
                        order,
                        status=OrderStatus.close,
                        filled=order.amount,
                        remaining=0.0,
                        cost=order.amount * order.price,
                    )

    async def handle_ohlcv(self, ohlcv: OHLCV):
        debug(f"Received {ohlcv}")
        self._ohlcv_queues[ohlcv.symbol].append(ohlcv)
        buy_or_sell = randint(0, 1)
        if True:
            await self.submit_order(
                ohlcv.symbol,
                OrderType.limit,
                TradeSide.buy,
                0.01,
                ohlcv.low,
            )
        else:
            pass
