from procrastinate.contrib.django import app as procrastinate_app

NOW = object()


class Timer:
    task = None
    job_id_field = None
    live_statuses = ()
    eligible = None
    argument = None

    def lock(self, instance):
        return None

    def run_at(self, instance):
        raise NotImplementedError

    def sync(self, instance):
        model = type(instance)
        current_job_id = getattr(instance, self.job_id_field)
        eligible = getattr(model.objects, self.eligible)().filter(pk=instance.pk).exists()
        run_at = self.run_at(instance) if eligible else None
        scheduled_at = None if run_at is NOW else run_at

        if current_job_id is not None:
            jobs = procrastinate_app.job_manager.list_jobs(id=current_job_id)
            if (
                run_at is not None
                and jobs
                and jobs[0].status in self.live_statuses
                and jobs[0].scheduled_at == scheduled_at
            ):
                return current_job_id
            procrastinate_app.job_manager.cancel_job_by_id(current_job_id)

        new_job_id = None
        if run_at is not None:
            new_job_id = procrastinate_app.configure_task(
                self.task,
                schedule_at=scheduled_at,
                lock=self.lock(instance),
            ).defer(**{self.argument: instance.pk})

        if new_job_id != current_job_id:
            model.objects.filter(pk=instance.pk).update(**{self.job_id_field: new_job_id})
            setattr(instance, self.job_id_field, new_job_id)
        return new_job_id


class TimedModel:
    timers = ()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.sync_timers()

    def sync_timers(self):
        for timer in self.timers:
            timer().sync(self)
