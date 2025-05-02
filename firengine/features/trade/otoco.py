import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Self
from collections import defaultdict

from firengine.model.data_model import Order, OrderInfo

if TYPE_CHECKING:
    from firengine.features.trade.order_manager import OrderManager


@dataclass
class OTOCO:
    limit_order_info: OrderInfo
    tp_order_info: OrderInfo
    sl_order_info: OrderInfo
    id: str = field(default_factory=lambda: str(uuid.uuid1()))
    limit_order: Order | None = None
    tp_order: Order | None = None
    sl_order: Order | None = None

    @classmethod
    def new_order(
        cls,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        tp_trigger_price: float,
        tp_price: float,
        sl_trigger_price: float,
        sl_price: float,
        time_in_force=None,
        expired_dt=None,
    ) -> Self:
        limit_order = OrderInfo(
            symbol=symbol,
            type="limit",
            side=side,
            amount=amount,
            price=price,
        )
        tp_order = OrderInfo(
            symbol=symbol,
            type="limit",
            side=side,
            amount=amount,
            price=tp_price,
            triggerPrice=tp_trigger_price,
        )
        sl_order = OrderInfo(
            symbol=symbol,
            type="limit",
            side=side,
            amount=amount,
            price=sl_price,
            triggerPrice=sl_trigger_price,
        )
        return cls(limit_order, tp_order, sl_order)

    @property
    def status(self):
        return

class OTOCOManager:
    def __init__(self, order_manager: "OrderManager"):
        self._order_manager = order_manager
        self._otocos: dict[str, OTOCO] = {}
        self._otoco_aliases: dict[str, str] = {}
        self._otocos_per_symbol: defaultdict[str, list[OTOCO]] = defaultdict(list)

    def create_new_otoco(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        tp_trigger_price: float,
        tp_price: float,
        sl_trigger_price: float,
        sl_price: float,
    ):
        otoco = OTOCO.new_order(
            symbol, side, amount, price, tp_trigger_price, tp_price, sl_trigger_price, sl_trigger_price, sl_price
        )
        self._otocos[otoco.id] = otoco
        self._otocos_per_symbol[symbol].append(otoco)

    async def submit_limit_order(self, otoco_id: str):
        if otoco := self._otocos.get(otoco_id):
            if otoco.limit_order is None:
                otoco.limit_order = await self._order_manager.submit_order(
                    otoco.limit_order_info.symbol,
                    otoco.limit_order_info.type,
                    otoco.limit_order_info.side,
                    otoco.limit_order_info.amount,
                    otoco.limit_order_info.price,
                )

    def cancel_otoco(self, otoco_id: str):
        if otoco := self._otocos.get(otoco_id):
            if otoco.limit_order:
                pass
            if otoco.tp_order:
                pass
            if otoco.sl_order:
                pass

    def on_limit_order_filled(self, limit_order_id: str):
        pass

    def on_tp_order_filled(self, tp_order_id: str):
        pass

    def on_sl_order_filled(self, sl_order_id: str):
        pass

    def get_otocos_per_symbol(self, symbol: str):
        pass

