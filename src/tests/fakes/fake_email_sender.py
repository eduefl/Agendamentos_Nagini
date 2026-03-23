from domain.notification.email_sender_interface import EmailSenderInterface


class FakeEmailSender(EmailSenderInterface):
    def __init__(self):
        self.sent_emails = []

    def send_activation_email(self, to_email: str, activation_code: str) -> None:
        self.sent_emails.append((to_email, activation_code))