import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config.settings import get_settings
from app.integrations.base_adapter import integration_safe_call


class EmailClient:
  def __init__(self, host, port, user, password, use_tls, timeout):
    self.host = host
    self.port = port
    self.user = user
    self.password = password
    self.use_tls = use_tls
    self.timeout = timeout

  def send_email(self, to_addr: str, subject: str, body: str) -> None:
    msg = MIMEMultipart()
    msg['From'] = self.user
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
    try:
      if self.use_tls:
        server.starttls()
      if self.user and self.password:
        server.login(self.user, self.password)
      server.sendmail(self.user, to_addr, msg.as_string())
    finally:
      server.quit()


def get_email_client():
  settings = get_settings()
  return EmailClient(
    host=settings.SMTP_HOST,
    port=settings.SMTP_PORT,
    user=settings.SMTP_USER,
    password=settings.SMTP_PASSWORD,
    use_tls=settings.SMTP_USE_TLS,
    timeout=10
  )

def email_safe_call(func, *args, max_retries: int = 3, **kwargs):
  return integration_safe_call(
    func, *args, max_retries=max_retries,
    timeout_exc=(socket.timeout, smtplib.SMTPServerDisconnected),
    connection_exc=(smtplib.SMTPConnectError, ConnectionError),
    service_exc=(smtplib.SMTPAuthenticationError, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused),
    **kwargs
  )