from django.db import models
from django.core import exceptions
from .base import BaseModel
from .phase_state import PhaseState


class Order(BaseModel):
    phase_state = models.ForeignKey(
        PhaseState, on_delete=models.CASCADE, related_name="orders"
    )
    order_type = models.CharField(max_length=50)
    source = models.CharField(max_length=50)
    target = models.CharField(max_length=50, null=True, blank=True)
    aux = models.CharField(max_length=50, null=True, blank=True)

    @property
    def nation(self):
        return self.phase_state.member.nation

    def clean(self):
        options_json = self.phase_state.options

        try:
            if self.source not in options_json:
                raise exceptions.ValidationError(
                    f"Source province {self.source} is not valid."
                )

            order_type_options = options_json[self.source]["Next"]
            if self.order_type not in order_type_options:
                raise exceptions.ValidationError(
                    f"Order type {self.order_type} is not valid for source province {self.source}."
                )

            if self.order_type in ["Move"]:
                target_options = order_type_options[self.order_type]["Next"][
                    self.source
                ]["Next"]
                if self.target not in target_options:
                    raise exceptions.ValidationError(
                        f"Target province {self.target} is not valid for {self.order_type} order from {self.source}."
                    )

            if self.order_type in ["Support", "Convoy"]:
                # Check if aux is valid for the order type and source
                aux_options = order_type_options[self.order_type]["Next"][self.source][
                    "Next"
                ]
                if self.aux not in aux_options:
                    raise exceptions.ValidationError(
                        f"Auxiliary province {self.aux} is not valid for {self.order_type} order from {self.source}."
                    )

                # Check if target is valid for the order type, source, and aux
                target_options = aux_options[self.aux]["Next"]
                if self.target not in target_options:
                    raise exceptions.ValidationError(
                        f"Target province {self.target} is not valid for {self.order_type} order from {self.source} with auxiliary {self.aux}."
                    )

        except (KeyError, TypeError):
            # If any key is missing in the tree or there's another issue
            raise exceptions.ValidationError(
                detail="Invalid order data. Please check the order type and source."
            )
