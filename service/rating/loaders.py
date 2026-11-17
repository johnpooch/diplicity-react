from common.loaders import Loader

from .hydrators import OpponentHydrator
from .models import Rating, RatingPairing, RatingResult


class LeaderboardEntryLoader(Loader):
    queryset = Rating.objects.select_related("user__profile__uploaded_picture")


class RatingPairingLoader(Loader):
    queryset = RatingPairing.objects.select_related(
        "opponent__game",
        "opponent__nation",
        "opponent__user__profile__uploaded_picture",
        "opponent__user__bot",
    ).order_by("-score", "opponent__nation__name")
    hydrators = [
        OpponentHydrator(),
    ]


class RatingResultLoader(Loader):
    queryset = RatingResult.objects.all()
    nested = {"pairings": RatingPairingLoader}
