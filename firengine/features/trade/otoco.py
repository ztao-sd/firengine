from collections import defaultdict
from copy import copy
from datetime import datetime
from typing import TYPE_CHECKING

import shortuuid

from firengine.model.data_model import OTOCO, Order

if TYPE_CHECKING:
    from firengine.features.trade.order_manager import OrderManager


class OTOCOManager:
    def __init__(self, order_manager: "OrderManager"):
        self._order_manager = order_manager
        self._otocos: dict[str, OTOCO] = {}
        self._otocos_per_symbol: defaultdict[str, dict[str, OTOCO]] = defaultdict(dict)
        self._otocos_per_order: dict[str, OTOCO] = {}

    def get_otoco(self, otoco_id: str) -> OTOCO | None:
        return self._otocos.get(otoco_id)

    def get_order_per_otoco(self, otoco_id: str) -> Order | None:
        if otoco := self._otocos.get(otoco_id):
            if order := self._order_manager.get_order(otoco.symbol, otoco.order_id):
                return order
        return None

    def get_tp_order_per_otoco(self, otoco_id: str) -> Order | None:
        if otoco := self._otocos.get(otoco_id):
            if order := self._order_manager.get_order(otoco.symbol, otoco.tp_order_id):
                return order
        return None

    def get_sl_order_per_otoco(self, otoco_id: str) -> Order | None:
        if otoco := self._otocos.get(otoco_id):
            if order := self._order_manager.get_order(otoco.symbol, otoco.sl_order_id):
                return order
        return None

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
        self._otocos[otoco.id] = otoco
        order_info = await self._order_manager.submit_order(symbol, "limit", side, amount, price)
        otoco.order_id = order_info.id
        self._otocos_per_order[order_info.id] = otoco
        return otoco

    async def modify_otoco(self, target: OTOCO):
        # Check if order is filled
        if target.id in self._otocos:
            if order := copy(self._order_manager.get_open_order(target.symbol, target.order_id)):
                if order.amount != target.amount or order.price != target.price:
                    order.amount = target.amount
                    order.price = target.price
                    await self._order_manager.modify_order(order)
            elif self._order_manager.get_closed_order(target.symbol, target.order_id):
                if order := copy(self._order_manager.get_open_order(target.symbol, target.tp_order_id)):
                    if order.price != target.tp_price:
                        order.price = target.tp_price
                        await self._order_manager.modify_order(order)
                if order := copy(self._order_manager.get_open_order(target.symbol, target.sl_order_id)):
                    if order.price != target.sl_price:
                        order.price = target.sl_price
                        await self._order_manager.modify_order(order)

    async def cancel_otoco_limit(self, target: OTOCO):
        if target.id in self._otocos:
            if order := self._order_manager.get_open_order(target.symbol, target.order_id):
                await self._order_manager.cancel_order(order.id, order.symbol)

    async def cancel_otoco_tp(self, target: OTOCO):
        if target.id in self._otocos:
            if order := self._order_manager.get_open_order(target.symbol, target.tp_order_id):
                await self._order_manager.cancel_order(order.id, order.symbol)

    async def cancel_otoco_sl(self, target: OTOCO):
        if target.id in self._otocos:
            if order := self._order_manager.get_open_order(target.symbol, target.sl_order_id):
                await self._order_manager.cancel_order(order.id, order.symbol)

    async def on_order_updated(self, order: Order):
        if otoco := self._otocos_per_order.get(order.id):
            if order.id == otoco.order_id:
                otoco.price = order.price
                otoco.amount = order.amount
                match order.status:
                    case "open":
                        pass
                    case "closed":
                        side = "buy" if otoco.side == "sell" else "sell"
                        print("s", datetime.now())
                        if otoco.sl_order_id is None:
                            print('sl')
                            order_info = await self._order_manager.submit_order(
                                otoco.symbol, "limit", side, otoco.amount, otoco.sl_price
                            )
                            otoco.sl_order_id = order_info.id
                            self._otocos_per_order[order_info.id] = otoco
                        if otoco.tp_order_id is None:
                            print("tp")
                            order_info = await self._order_manager.submit_order(
                                otoco.symbol, "limit", side, otoco.amount, otoco.tp_price
                            )
                            otoco.tp_order_id = order_info.id
                            self._otocos_per_order[order_info.id] = otoco
                        print("ff", datetime.now())
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
