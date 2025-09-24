from django.db import models
from django.db.models import Q, ObjectDoesNotExist
from django.core import exceptions

from common.constants import UnitType, OrderType, PhaseStatus, OrderResolutionStatus, OrderCreationStep
from common.models import BaseModel

from .utils import get_options_for_order


class OrderQuerySet(models.QuerySet):
    def for_phase(self, phase):
        return self.filter(phase_state__phase=phase)

    def visible_to_user_in_phase(self, user, phase):
        return self.filter(
            Q(phase_state__phase=phase)
            & (Q(phase_state__phase__status=PhaseStatus.COMPLETED) | Q(phase_state__member__user=user))
        )

    def with_related_data(self):
        return self.select_related(
            "phase_state__member__user",
            "phase_state__phase",
            "phase_state__member",
            "phase_state__phase__game__variant",
            "resolution",
        ).prefetch_related("phase_state__member__user__profile")


class OrderManager(models.Manager):
    def get_queryset(self):
        return OrderQuerySet(self.model, using=self._db)

    def for_phase(self, phase):
        return self.get_queryset().for_phase(phase)

    def visible_to_user_in_phase(self, user, phase):
        return self.get_queryset().visible_to_user_in_phase(user, phase)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def create_from_selected(self, user, phase, selected):
        print(selected)
        phase_state = (
            phase.phase_states.select_related("member__user", "phase", "member", "phase__game__variant")
            .filter(member__user=user)
            .first()
        )

        try:
            source = phase.variant.provinces.get(province_id=selected[0])
        except ObjectDoesNotExist:
            raise exceptions.ValidationError(f"Source province {selected[0]} not found")

        order = Order(phase_state=phase_state, source=source)

        if len(selected) <= 1:
            return order

        order.order_type = selected[1]

        if order.order_type == OrderType.BUILD:
            if len(selected) >= 3:
                order.unit_type = selected[2]
        elif order.order_type == OrderType.MOVE:
            if len(selected) >= 3:
                try:
                    order.target = phase.variant.provinces.get(province_id=selected[2])
                except ObjectDoesNotExist:
                    raise exceptions.ValidationError(f"Target province {selected[2]} not found")
        elif order.order_type == OrderType.SUPPORT:
            if len(selected) >= 3:
                try:
                    order.aux = phase.variant.provinces.get(province_id=selected[2])
                except ObjectDoesNotExist:
                    raise exceptions.ValidationError(f"Auxiliary province {selected[2]} not found")
            if len(selected) >= 4:
                try:
                    order.target = phase.variant.provinces.get(province_id=selected[3])
                except ObjectDoesNotExist:
                    raise exceptions.ValidationError(f"Target province {selected[3]} not found")
        elif order.order_type == OrderType.CONVOY:
            if len(selected) >= 3:
                try:
                    order.aux = phase.variant.provinces.get(province_id=selected[2])
                except ObjectDoesNotExist:
                    raise exceptions.ValidationError(f"Auxiliary province {selected[2]} not found")
            if len(selected) >= 4:
                try:
                    order.target = phase.variant.provinces.get(province_id=selected[3])
                except ObjectDoesNotExist:
                    raise exceptions.ValidationError(f"Target province {selected[3]} not found")

        print(order)
        return order


class Order(BaseModel):

    objects = OrderManager()

    phase_state = models.ForeignKey("game.PhaseState", on_delete=models.CASCADE, related_name="orders")
    order_type = models.CharField(max_length=50, choices=OrderType.ORDER_TYPE_CHOICES, null=True, blank=True)
    source = models.ForeignKey(
        "province.Province", on_delete=models.CASCADE, related_name="source_orders", null=True, blank=True
    )
    target = models.ForeignKey(
        "province.Province", on_delete=models.CASCADE, related_name="target_orders", null=True, blank=True
    )
    aux = models.ForeignKey(
        "province.Province", on_delete=models.CASCADE, related_name="aux_orders", null=True, blank=True
    )
    unit_type = models.CharField(max_length=50, choices=UnitType.UNIT_TYPE_CHOICES, null=True, blank=True)

    @property
    def variant(self):
        return self.phase_state.phase.variant

    @property
    def nation(self):
        return self.phase_state.member.nation

    @property
    def options(self):
        phase = self.phase_state.phase
        return get_options_for_order(phase.options_dict, self)

    @property
    def options_display(self):
        self.options
        display_options = []
        for option in self.options:
            try:
                province = self.variant.provinces.get(province_id=option)
            except ObjectDoesNotExist:
                province = None
            if province is not None:
                display_options.append({"value": option, "label": province.name})
            else:
                display_options.append({"value": option, "label": option})
        return display_options

    @property
    def selected(self):
        return [
            value
            for value in [
                self.source.province_id if self.source else None,
                self.order_type,
                self.unit_type,
                self.aux.province_id if self.aux else None,
                self.target.province_id if self.target else None,
            ]
            if value
        ]

    @property
    def complete(self):
        if not self.order_type:
            return False
        if self.order_type in [OrderType.HOLD, OrderType.DISBAND]:
            return True
        if self.order_type == OrderType.MOVE:
            return self.target is not None
        if self.order_type == OrderType.BUILD:
            return self.unit_type is not None
        if self.order_type in [OrderType.SUPPORT, OrderType.CONVOY]:
            return self.target is not None and self.aux is not None
        return False

    @property
    def step(self):
        if self.complete:
            return OrderCreationStep.COMPLETED
        if not self.order_type:
            return OrderCreationStep.SELECT_ORDER_TYPE
        if self.order_type == OrderType.BUILD:
            return OrderCreationStep.SELECT_UNIT_TYPE
        if self.order_type == OrderType.MOVE:
            return OrderCreationStep.SELECT_TARGET
        if self.order_type in [OrderType.SUPPORT, OrderType.CONVOY]:
            if not self.aux:
                return OrderCreationStep.SELECT_AUX
            if not self.target:
                return OrderCreationStep.SELECT_TARGET
        return None

    @property
    def title(self):
        if not self.order_type:
            return f"Select order type for {self.source.name}"

        if self.order_type == OrderType.HOLD:
            return f"{self.source.name} will hold"
        if self.order_type == OrderType.DISBAND:
            return f"{self.source.name} will be disbanded"
        if self.order_type == OrderType.BUILD:
            if not self.unit_type:
                return f"Select unit type to build in {self.source.name}"
            else:
                return f"{self.unit_type} will be built in {self.source.name}"
        if self.order_type == OrderType.MOVE:
            if not self.target:
                return f"Select province to move {self.source.name} to"
            else:
                return f"{self.source.name} will move to {self.target.name}"
        if self.order_type in [OrderType.SUPPORT, OrderType.CONVOY]:
            if not self.aux:
                return f"Select province for {self.source.name} to {self.order_type.lower()}"
            elif not self.target:
                return f"Select destination for {self.source.name} to {self.order_type.lower()} {self.aux.name} to"
            else:
                return f"{self.source.name} will {self.order_type.lower()} {self.aux.name} to {self.target.name}"
        return None

    def clean(self):
        try:
            get_options_for_order(self.phase_state.phase.options_dict, self)
        except Exception as e:
            raise exceptions.ValidationError(e)


class OrderResolution(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="resolution")
    status = models.CharField(max_length=30, choices=OrderResolutionStatus.STATUS_CHOICES)
    by = models.ForeignKey(
        "province.Province", on_delete=models.CASCADE, related_name="order_resolutions", null=True, blank=True
    )
