from django.db import models
from .base import BaseModel
from .game import Game


class Phase(BaseModel):

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
    )

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name="phases")
    ordinal = models.PositiveIntegerField(editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    season = models.CharField(max_length=10)
    year = models.IntegerField()
    phase_type = models.CharField(max_length=10)
    remaining_time = models.DurationField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:  # Check if the instance is being created
            last_ordinal = (
                Phase.objects.filter(game=self.game).aggregate(models.Max("ordinal"))[
                    "ordinal__max"
                ]
                or 0
            )
            self.ordinal = last_ordinal + 1
        super().save(*args, **kwargs)

    @property
    def name(self):
        return f"{self.season} {self.year}, {self.phase_type}"

    def get_orders_for_user(self, user):
        is_current_phase = self.id == self.game.current_phase.id

        phase_states = self.phase_states.all()

        if is_current_phase:
            phase_states = phase_states.filter(member__user=user)

        variant = self.game.variant

        for phase_state in phase_states:
            nation = phase_state.member.nation
            orders = phase_state.orders.all()
            orders = [
                {
                    "nation": nation,
                    "order_type": order.order_type,
                    "source": {
                        "name": next(
                            (
                                p["name"]
                                for p in variant.provinces
                                if p["id"] == order.source
                            ),
                            None,
                        ),
                        "id": order.source,
                    },
                    "target": (
                        None
                        if order.target is None
                        else {
                            "name": next(
                                (
                                    p["name"]
                                    for p in variant.provinces
                                    if p["id"] == order.target
                                ),
                                None,
                            ),
                            "id": order.target,
                        }
                    ),
                    "aux": (
                        None
                        if order.aux is None
                        else {
                            "name": next(
                                (
                                    p["name"]
                                    for p in variant.provinces
                                    if p["id"] == order.aux
                                ),
                                None,
                            ),
                            "id": order.aux,
                        }
                    ),
                }
                for order in phase_state.orders.all()
            ]
        return orders
