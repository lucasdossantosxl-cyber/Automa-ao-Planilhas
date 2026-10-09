import os
import smtplib
from email.message import EmailMessage


def enviar_email(valor):
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    destinatario = os.environ["EMAIL_TO"]

    mensagem = EmailMessage()
    mensagem["Subject"] = "Relatório Diário de Vendas"
    mensagem["From"] = os.getenv("EMAIL_FROM", smtp_user)
    mensagem["To"] = destinatario
    mensagem.set_content(f"Olá, o valor extraído da nota fiscal foi {valor}")

    with smtplib.SMTP(smtp_host, smtp_port) as servidor:
        servidor.starttls()
        servidor.login(smtp_user, smtp_password)
        servidor.send_message(mensagem)

    print("E-mail enviado com sucesso!")


if __name__ == "__main__":
    enviar_email("R$ 1500,00")