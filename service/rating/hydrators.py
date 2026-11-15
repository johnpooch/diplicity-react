from common.loaders import Hydrator
from member.loaders import BaseMemberLoader


class OpponentHydrator(Hydrator):
    def hydrate(self, pairings, actor):
        BaseMemberLoader.hydrate([pairing.opponent for pairing in pairings], actor)
