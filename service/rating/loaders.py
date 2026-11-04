from common.loaders import Loader

from .models import Rating


class LeaderboardEntryLoader(Loader):
    queryset = Rating.objects.select_related("user__profile__uploaded_picture")
