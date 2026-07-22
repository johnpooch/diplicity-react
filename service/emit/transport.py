from email_service.tasks import send_email_notification
from email_service.templates import notification_email
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


class Email(Transport):
    def deliver(self, spec, context, recipients):
        if not recipients:
            return
        send_email_notification.defer(
            user_ids=list(recipients),
            subject=spec.get_email_subject(context),
            html=notification_email(
                title=spec.get_title(context),
                body=spec.get_body(context),
                link=spec.get_link(context),
            ),
        )


class Timeline(Transport):
    def deliver(self, spec, context, recipients):
        return
