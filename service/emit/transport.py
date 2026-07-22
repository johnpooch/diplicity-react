from notification.tasks import send_notification


class Transport:
    def deliver(self, spec, context, recipients):
        raise NotImplementedError


class Push(Transport):
    def deliver(self, spec, context, recipients):
        if not recipients:
            return
        send_notification.defer(
            user_ids=list(recipients),
            title=spec.get_title(context),
            body=spec.get_body(context),
            notification_type=context.event_type,
            data=self.data(spec, context),
        )

    def data(self, spec, context):
        if context.game is None:
            return None
        payload = {"game_id": str(context.game.id)}
        link = spec.get_link(context)
        if link is not None:
            payload["link"] = link
        return payload


class Timeline(Transport):
    def deliver(self, spec, context, recipients):
        return
