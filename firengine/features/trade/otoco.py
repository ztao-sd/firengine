from collections import defaultdict
from copy import copy
from typing import TYPE_CHECKING

import shortuuid

from firengine.model.data_model import OTOCO, Order

if TYPE_CHECKING:
    from firengine.features.trade.order_manager import OrderManager


class OTOCOManager:
    def __init__(self, order_manager: "OrderManager"):
        self._order_manager = order_manager
        self._otocos_per_symbol: defaultdict[str, dict[str, OTOCO]] = defaultdict(dict)
        self._otocos_per_order: dict[str, OTOCO] = {}

    async def create_otoco(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        tp_price: float,
        sl_price: float,
    ) -> OTOCO:
        otoco = OTOCO(
            id=shortuuid.uuid(),
            symbol=symbol,
            side=side,
            amount=amount,
            price=price,
            tp_price=tp_price,
            sl_price=sl_price,
        )
        self._otocos_per_symbol[symbol][otoco.id] = otoco
        order_info = await self._order_manager.submit_order(symbol, "limit", side, amount, price)
        otoco.order_id = order_info.id
        self._otocos_per_order[order_info.id] = otoco
        return otoco

    async def modify_otoco(self, target: OTOCO):
        # Check if order is filled
        if otoco := self._otocos_per_symbol[target.symbol].get(target.id):
            if order := copy(self._order_manager.get_open_order(target.symbol, target.order_id)):
                order.amount = target.amount
                order.price = target.price
                # otoco.price = target.price
                # otoco.amount = target.amount
                await self._order_manager.modify_order(order)
            elif self._order_manager.get_closed_order(target.symbol, target.order_id):
                if order := copy(self._order_manager.get_open_order(target.symbol, target.tp_order_id)):
                    order.price = target.tp_price
                    # otoco.tp_price = target.tp_price
                    await self._order_manager.modify_order(order)
                if order := copy(self._order_manager.get_open_order(target.symbol, target.sl_order_id)):
                    order.price = target.sl_price
                    # otoco.sl_price = target.sl_price
                    await self._order_manager.modify_order(order)

    async def cancel_otoco_limit(self, target: OTOCO):
        if target.id in self._otocos_per_symbol[target.symbol]:
            if order := self._order_manager.get_open_order(target.symbol, target.order_id):
                await self._order_manager.cancel_order(order.id, order.symbol)

    async def cancel_otoco_tp(self, target: OTOCO):
        if target.id in self._otocos_per_symbol[target.symbol]:
            if order := self._order_manager.get_open_order(target.symbol, target.tp_order_id):
                await self._order_manager.cancel_order(order.id, order.symbol)

    async def cancel_otoco_sl(self, target: OTOCO):
        if target.id in self._otocos_per_symbol[target.symbol]:
            if order := self._order_manager.get_open_order(target.symbol, target.sl_order_id):
                await self._order_manager.cancel_order(order.id, order.symbol)

    async def on_order_updated(self, order: Order):
        if otoco := self._otocos_per_order[order.id]:
            if order.id == otoco.order_id:
                otoco.price = order.price
                otoco.amount = order.amount
                match order.status:
                    case "open":
                        pass
                    case "closed":
                        side = "buy" if otoco.side == "sell" else "sell"
                        if otoco.sl_order_id is None:
                            order_info = await self._order_manager.submit_order(
                                otoco.symbol, "limit", side, otoco.amount, otoco.sl_price
                            )
                            otoco.sl_order_id = order_info.id
                        if otoco.tp_order_id is None:
                            order_info = await self._order_manager.submit_order(
                                otoco.symbol, "limit", side, otoco.amount, otoco.tp_price
                            )
                            otoco.tp_order_id = order_info.id
                    case _:
                        otoco.order_id = None
            elif order.id == otoco.tp_order_id:
                otoco.tp_price = order.price
                match order.status:
                    case "open":
                        pass
                    case "closed":
                        pass
                    case _:
                        otoco.tp_order_id = None
            elif order.id == otoco.sl_order_id:
                otoco.sl_price = order.price
                match order.status:
                    case "open":
                        pass
                    case "closed":
                        pass
                    case _:
                        otoco.sl_order_id = None
