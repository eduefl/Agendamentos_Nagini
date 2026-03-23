import os
import smtplib
from email.message import EmailMessage

from domain.notification.notification_exceptions import EmailDeliveryError
from domain.notification.email_sender_interface import EmailSenderInterface


class SMTPEmailSender(EmailSenderInterface):
    def send_activation_email(self, to_email: str, activation_code: str) -> None:
        try:
            remetente = os.environ["EMAIL_SENDER_ADDRESS"]
            senha = os.environ["EMAIL_SENDER_PASSWORD"]

            destinatario = to_email
            assunto = "Código de ativação da sua conta"
            mensagem = f"Seu código de ativação é: {activation_code}"

            msg = EmailMessage()
            msg["From"] = remetente
            msg["To"] = destinatario
            msg["Subject"] = assunto
            msg.set_content(mensagem)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as email:
                email.login(remetente, senha)
                email.send_message(msg)
        except Exception as exc:
            raise EmailDeliveryError("Falha ao enviar email de ativação") from exc
