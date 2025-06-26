from .. import models


class UserProfileService:
    def __init__(self, user):
        self.user = user

    def retrieve(self):
        return models.UserProfile.objects.get(user=self.user)
