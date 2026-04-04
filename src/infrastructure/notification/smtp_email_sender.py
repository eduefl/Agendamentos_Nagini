import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Optional

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

    def send_service_request_notification_email(
        self,
        to_email: str,
        provider_name: str,
        service_name: str,
        desired_datetime: datetime,
        address: Optional[str],
        expires_at: Optional[datetime],
    ) -> None:
        try:
            remetente = os.environ["EMAIL_SENDER_ADDRESS"]
            senha = os.environ["EMAIL_SENDER_PASSWORD"]

            endereco = address or "Não informado"
            expiracao = (
                expires_at.strftime("%d/%m/%Y %H:%M") if expires_at else "Não informada"
            )
            data_desejada = desired_datetime.strftime("%d/%m/%Y %H:%M")

            assunto = "Nova solicitação de serviço disponível para aceite"
            mensagem = f"""
Olá, {provider_name}!

Uma nova solicitação de serviço está disponível para você.

Serviço: {service_name}
Data desejada: {data_desejada}
Endereço: {endereco}
Disponível para aceite até: {expiracao}

Acesse a plataforma para avaliar e aceitar a solicitação.
""".strip()

            msg = EmailMessage()
            msg["From"] = remetente
            msg["To"] = to_email
            msg["Subject"] = assunto
            msg.set_content(mensagem)

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as email:
                email.login(remetente, senha)
                email.send_message(msg)
        except Exception as exc:
            raise EmailDeliveryError(
                "Falha ao enviar email de notificação de solicitação"
            ) from exc
