from domain.notification.email_sender_interface import EmailSenderInterface


class FakeEmailSender(EmailSenderInterface):
    def __init__(self):
        self.sent_emails = []

    def send_activation_email(self, to_email: str, activation_code: str) -> None:
        self.sent_emails.append((to_email, activation_code))

    def send_service_request_notification_email(
        self,
        to_email: str,
        provider_name: str,
        service_name: str,
        desired_datetime,
        address,
        expires_at,
    ) -> None:
        self.sent_emails.append(
            (
                to_email,
                provider_name,
                service_name,
                desired_datetime,
                address,
                expires_at,
            )
        )