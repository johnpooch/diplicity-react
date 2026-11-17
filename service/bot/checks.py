from common.checks import Check

from .constants import RunStatus


class IsPendingCheck(Check):
    def check(self, run, actor):
        return run.status == RunStatus.PENDING


class IsRunningCheck(Check):
    def check(self, run, actor):
        return run.status == RunStatus.RUNNING


class IsUnfinishedCheck(Check):
    def check(self, run, actor):
        return run.status in (RunStatus.PENDING, RunStatus.RUNNING)
