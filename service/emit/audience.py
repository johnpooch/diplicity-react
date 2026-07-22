from victory.models import Victory


def victory_members(game):
    victory = Victory.objects.filter(game=game).prefetch_related("members").first()
    return list(victory.members.all()) if victory is not None else []


class Audience:
    def resolve(self, context):
        raise NotImplementedError

    def actor_id(self, actor):
        if actor is None:
            return None
        return getattr(actor, "id", actor)

    def member_user_ids(self, members):
        return {member.user_id for member in members if member.user_id is not None}

    def with_game_master(self, user_ids, game):
        result = set(user_ids)
        if game.game_master_id is not None:
            result.add(game.game_master_id)
        return result


class Explicit(Audience):
    def resolve(self, context):
        return set(context.payload.get("recipients", []))


class Actor(Audience):
    def resolve(self, context):
        actor_id = self.actor_id(context.actor)
        return {actor_id} if actor_id is not None else set()


class Admin(Audience):
    def resolve(self, context):
        admin_id = context.game.admin_id
        return {admin_id} if admin_id is not None else set()


class AllPlayers(Audience):
    def resolve(self, context):
        user_ids = self.member_user_ids(context.game.members.all())
        return self.with_game_master(user_ids, context.game)


class AllPlayersExceptActor(AllPlayers):
    def resolve(self, context):
        user_ids = super().resolve(context)
        user_ids.discard(self.actor_id(context.actor))
        return user_ids


class Winners(Audience):
    def resolve(self, context):
        return self.member_user_ids(victory_members(context.game))


class AllPlayersExceptWinners(AllPlayers):
    def resolve(self, context):
        return super().resolve(context) - self.member_user_ids(victory_members(context.game))


class Active(Audience):
    def resolve(self, context):
        active = context.game.members.filter(
            eliminated=False, kicked=False, civil_disorder=False
        )
        return self.with_game_master(self.member_user_ids(active), context.game)


class ActiveExceptActor(Active):
    def resolve(self, context):
        user_ids = super().resolve(context)
        user_ids.discard(self.actor_id(context.actor))
        return user_ids


class ChannelMembersExceptActor(Audience):
    def resolve(self, context):
        channel = context.channel
        members = channel.members if channel.private else channel.game.members
        user_ids = self.member_user_ids(members.all())
        user_ids.discard(self.actor_id(context.actor))
        return user_ids
