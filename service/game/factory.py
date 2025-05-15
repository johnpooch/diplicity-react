import factory
from . import models
from django.contrib.auth import get_user_model

User = get_user_model()


class VariantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Variant


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.UserProfile

    name = factory.Faker("name")
    picture = "https://example.com/default_profile_picture.jpg"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    profile = factory.RelatedFactory(
        UserProfileFactory,
        factory_related_name="user",
    )

    @factory.post_generation
    def name(self, create, extracted, **kwargs):
        if extracted:
            self.profile.name = extracted
            if create:
                self.profile.save()


class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Game

    variant = factory.SubFactory(VariantFactory)
    name = factory.Faker("sentence", nb_words=3)

    @factory.post_generation
    def create_phase(self, create, extracted, **kwargs):
        if not create:
            return

        if self.status == models.Game.PENDING:
            PhaseFactory(
                game=self,
                status=models.Phase.PENDING,
            )

        if self.status == models.Game.ACTIVE:
            PhaseFactory(
                game=self,
                status=models.Phase.ACTIVE,
            )

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        # Create a Member for each user in the extracted list
        for user in extracted:
            MemberFactory(game=self, user=user)


class MemberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Member

    user = factory.SubFactory(UserFactory)
    game = factory.SubFactory(GameFactory)


class PhaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Phase

    game = factory.SubFactory(GameFactory)
    status = models.Phase.PENDING
    season = "Spring"
    year = 1901
    type = "Movement"

    @factory.post_generation
    def supply_centers(self, create, extracted, **kwargs):
        print(self.game.variant)
        if not create:
            return
        if not extracted:
            self.supply_centers = self.game.variant.start["supply_centers"]

    @factory.post_generation
    def units(self, create, extracted, **kwargs):
        if not create:
            return
        if not extracted:
            self.units = self.game.variant.start["units"]

    @factory.post_generation
    def create_phase_states(self, create, extracted, **kwargs):
        if not create:
            return

        if self.status == models.Phase.ACTIVE:
            print("Creating phase states")
            for member in self.game.members.all():
                models.PhaseState.objects.create(member=member, phase=self)
                print(
                    f"PhaseState created for member {member.user.username} in phase {self.season} {self.year} {self.type}"
                )


class PhaseStateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PhaseState

    member = factory.SubFactory(MemberFactory)
    phase = factory.SubFactory(PhaseFactory)


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Order

    phase = factory.SubFactory(PhaseFactory)
    member = factory.SubFactory(MemberFactory)
