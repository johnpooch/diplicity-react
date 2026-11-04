from common.loaders import Loader

from .models import RatingPairing, RatingResult


class RatingPairingLoader(Loader):
    queryset = RatingPairing.objects.select_related(
        "opponent__nation",
        "opponent__user__profile__uploaded_picture",
    ).order_by("-score", "opponent__nation__name")


class RatingResultLoader(Loader):
    queryset = RatingResult.objects.all()
    nested = {"pairings": RatingPairingLoader}
