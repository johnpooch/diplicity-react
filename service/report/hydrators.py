from common.loaders import Hydrator

from .policies import CanViewReportedGamePolicy


class CanViewGameHydrator(Hydrator):
    def hydrate(self, reports, actor):
        for report in reports:
            report.can_view_game = CanViewReportedGamePolicy.decide(
                report, actor
            ).allowed
