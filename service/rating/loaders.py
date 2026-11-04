from common.loaders import Loader

from .models import Rating, RatingPairing, RatingResult


class LeaderboardEntryLoader(Loader):
    queryset = Rating.objects.select_related("user__profile__uploaded_picture")


class RatingPairingLoader(Loader):
    queryset = RatingPairing.objects.select_related(
        "opponent__nation",
        "opponent__user__profile__uploaded_picture",
    ).order_by("-score", "opponent__nation__name")


class RatingResultLoader(Loader):
    queryset = RatingResult.objects.all()
    nested = {"pairings": RatingPairingLoader}
