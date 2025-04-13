from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from firengine.model.data_model import Order

class SingleOrderPosition:

    def __init__(self, order: "Order", take_profit_order, stop_loss_order):
        self._order = order
        self._take_profit_order = take_profit_order
        self._stop_loss_order = stop_loss_order


class PositionOpener:

    def __init__(self):
        pass


class SimplePositionEvaluator:

    def __init__(self):
        pass