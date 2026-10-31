from report.querysets import ReportQuerySet

from .policies import ModeratorPolicy


class ModerationReportQuerySet(ReportQuerySet):
    def visible_to(self, actor):
        if not ModeratorPolicy.decide(None, actor):
            return self.none()
        return self
