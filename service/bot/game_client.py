from order.models import Order
from order.utils import flatten_options


class BotGameClient:
    def __init__(self, phase, member):
        self.phase = phase
        self.member = member
        self._province_lookup = {p.province_id: p for p in phase.variant.provinces.all()}

    def get_options(self):
        nation_options = self.phase.transformed_options.get(self.member.nation.name, {})
        return flatten_options(nation_options, self._province_lookup)

    def submit_orders(self, selections):
        orders = []
        for selected in selections:
            order = Order.objects.create_from_selected(
                self.member.user, self.phase, selected, self._province_lookup
            )
            order.save()
            orders.append(order)
        return orders
