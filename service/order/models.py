from django.db import models
from django.db.models import Q, ObjectDoesNotExist
from django.core import exceptions

from common.constants import UnitType, OrderType, PhaseStatus, OrderResolutionStatus, OrderCreationStep, PhaseType
from common.models import BaseModel

from .utils import get_options_for_order, get_order_data_from_selected


class OrderQuerySet(models.QuerySet):
    def for_phase(self, phase):
        return self.filter(phase_state__phase=phase)

    def visible_to_user_in_phase(self, user, phase):
        return self.filter(
            Q(phase_state__phase=phase)
            & (Q(phase_state__phase__status=PhaseStatus.COMPLETED) | Q(phase_state__member__user=user))
        )

    def for_source_in_phase(self, phase_state, source):
        return self.filter(phase_state=phase_state, source=source)

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

    def for_source_in_phase(self, phase_state, source):
        return self.get_queryset().for_source_in_phase(phase_state, source)

    def with_related_data(self):
        return self.get_queryset().with_related_data()

    def delete_existing_for_source(self, phase_state, source):
        existing_orders = self.for_source_in_phase(phase_state, source)
        existing_orders.delete()

    def try_get_province(self, phase, province_id):
        try:
            return phase.variant.provinces.get(province_id=province_id)
        except ObjectDoesNotExist:
            raise exceptions.ValidationError(f"Province {province_id} not found")

    def create_from_selected(self, user, phase, selected):
        phase_state = (
            phase.phase_states.select_related("member__user", "phase", "member", "phase__game__variant")
            .filter(member__user=user)
            .first()
        )

        order_data = get_order_data_from_selected(selected)
        source = self.try_get_province(phase, order_data["source"])
        order = Order(phase_state=phase_state, source=source)

        if "order_type" in order_data:
            order.order_type = order_data["order_type"]
        if "unit_type" in order_data:
            order.unit_type = order_data["unit_type"]
        if "target" in order_data:
            order.target = self.try_get_province(phase, order_data["target"])
        if "aux" in order_data:
            order.aux = self.try_get_province(phase, order_data["aux"])

        return order


class Order(BaseModel):

    objects = OrderManager()

    phase_state = models.ForeignKey("phase.PhaseState", on_delete=models.CASCADE, related_name="orders")
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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["phase_state", "source"], name="unique_order_per_province_per_phase")
        ]

    @property
    def variant(self):
        return self.phase_state.phase.variant

    @property
    def nation(self):
        return self.phase_state.member.nation

    @property
    def phase(self):
        return self.phase_state.phase

    @property
    def options(self):
        return get_options_for_order(self.phase.options, self)

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
        result = []
        if self.source:
            result.append(self.source.province_id)
        if self.order_type:
            result.append(self.order_type)
        if self.unit_type:
            result.append(self.unit_type)
        if self.aux:
            result.append(self.aux.province_id)
        if self.target:
            result.append(self.target.province_id)
        return result

    @property
    def step(self):
        if not self.order_type:
            return OrderCreationStep.SELECT_ORDER_TYPE

        if self.order_type == OrderType.BUILD and not self.unit_type:
            return OrderCreationStep.SELECT_UNIT_TYPE

        if self.order_type == OrderType.MOVE and not self.target:
            return OrderCreationStep.SELECT_TARGET

        if self.order_type in [OrderType.SUPPORT, OrderType.CONVOY]:
            if not self.aux:
                return OrderCreationStep.SELECT_AUX
            if not self.target:
                return OrderCreationStep.SELECT_TARGET

        return OrderCreationStep.COMPLETED

    @property
    def complete(self):
        return self.step == OrderCreationStep.COMPLETED

    @property
    def title(self):
        step = self.step

        if step == OrderCreationStep.SELECT_ORDER_TYPE:
            return f"Select order type for {self.source.name}"
        elif step == OrderCreationStep.SELECT_UNIT_TYPE and self.order_type == OrderType.BUILD:
            return f"Select unit type to build in {self.source.name}"
        elif step == OrderCreationStep.SELECT_TARGET and self.order_type == OrderType.MOVE:
            return f"Select province to move {self.source.name} to"
        elif step == OrderCreationStep.SELECT_AUX and self.order_type == OrderType.SUPPORT:
            return f"Select province for {self.source.name} to support"
        elif step == OrderCreationStep.SELECT_AUX and self.order_type == OrderType.CONVOY:
            return f"Select province for {self.source.name} to convoy"
        elif step == OrderCreationStep.SELECT_TARGET and self.order_type == OrderType.SUPPORT:
            return f"Select destination for {self.source.name} to support {self.aux.name} to"
        elif step == OrderCreationStep.SELECT_TARGET and self.order_type == OrderType.CONVOY:
            return f"Select destination for {self.source.name} to convoy {self.aux.name} to"
        elif step == OrderCreationStep.COMPLETED and self.order_type == OrderType.HOLD:
            return f"{self.source.name} will hold"
        elif step == OrderCreationStep.COMPLETED and self.order_type == OrderType.DISBAND:
            return f"{self.source.name} will be disbanded"
        elif step == OrderCreationStep.COMPLETED and self.order_type == OrderType.BUILD:
            return f"{self.unit_type} will be built in {self.source.name}"
        elif step == OrderCreationStep.COMPLETED and self.order_type == OrderType.MOVE:
            return f"{self.source.name} will move to {self.target.name}"
        elif step == OrderCreationStep.COMPLETED and self.order_type == OrderType.SUPPORT:
            return f"{self.source.name} will support {self.aux.name} to {self.target.name}"
        elif step == OrderCreationStep.COMPLETED and self.order_type == OrderType.CONVOY:
            return f"{self.source.name} will convoy {self.aux.name} to {self.target.name}"

        return None

    def _count_existing_orders_for_phase_state(self):
        """Count existing complete orders for this phase state, excluding current order."""
        queryset = Order.objects.filter(phase_state=self.phase_state)

        # If this order has an ID (being updated), exclude it from count
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)

        return queryset.count()

    def clean(self):
        try:
            get_options_for_order(self.phase.options, self)
        except Exception as e:
            raise exceptions.ValidationError(e)

        # Add adjustment phase limit validation
        if self.phase_state.phase.type == PhaseType.ADJUSTMENT:
            max_orders = self.phase_state.max_allowed_adjustment_orders()
            existing_orders = self._count_existing_orders_for_phase_state()

            if existing_orders >= max_orders:
                raise exceptions.ValidationError(
                    f"Cannot create order: nation has reached maximum of {max_orders} orders for this adjustment phase"
                )


class OrderResolution(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="resolution")
    status = models.CharField(max_length=30, choices=OrderResolutionStatus.STATUS_CHOICES)
    by = models.ForeignKey(
        "province.Province", on_delete=models.CASCADE, related_name="order_resolutions", null=True, blank=True
    )
