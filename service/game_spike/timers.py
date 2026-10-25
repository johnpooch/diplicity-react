from common.constants import DeadlineWarningJob, MusterJob, MusterReminderJob, ResolutionJob
from common.timers import NOW, Timer


class MusterTimer(Timer):
    task = "game_spike.start_if_mustered"
    job_id_field = "muster_job_id"
    live_statuses = MusterJob.LIVE_STATUSES
    eligible = "musterable"
    argument = "game_id"

    def lock(self, game):
        return ResolutionJob.lock_for_game(game.pk)

    def run_at(self, game):
        return NOW if game.is_mustered else game.muster_deadline


class MusterReminderTimer(Timer):
    task = "game_spike.send_muster_reminder"
    job_id_field = "muster_reminder_job_id"
    live_statuses = MusterReminderJob.LIVE_STATUSES
    eligible = "musterable"
    argument = "game_id"

    def run_at(self, game):
        return None if game.is_mustered else game.muster_reminder_at


class ResolutionTimer(Timer):
    task = ResolutionJob.TASK_NAME
    job_id_field = "resolution_job_id"
    live_statuses = (ResolutionJob.TODO,)
    eligible = "armable"
    argument = "phase_id"

    def lock(self, phase):
        return ResolutionJob.lock_for_game(phase.game_id)

    def run_at(self, phase):
        return NOW if phase.is_resolvable else phase.scheduled_resolution


class DeadlineWarningTimer(Timer):
    task = DeadlineWarningJob.TASK_NAME
    job_id_field = "warning_job_id"
    live_statuses = DeadlineWarningJob.LIVE_STATUSES
    eligible = "armable"
    argument = "phase_id"

    def run_at(self, phase):
        return phase.deadline_warning_at
