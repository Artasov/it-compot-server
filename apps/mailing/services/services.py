from django.conf import settings
from django.template.loader import render_to_string

from email.message import EmailMessage
import smtplib
from platform import python_version
from django.conf import settings
from django.template.loader import render_to_string


def send_email_by_template(subject: str, to_email: str, template: str, context=None):
    if context is None:
        context = {}
    html_content = render_to_string(template, context=context)
    send_email(to_email, subject, html_content)


def send_text_email(subject: str, to_email: str, text: str):
    send_email(to_email, subject, text)


def send_email(to: str, subject: str, html: str):
    server = settings.EMAIL_HOST
    user = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD

    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from platform import python_version

    sender = user
    subject = subject
    text = subject

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg['Reply-To'] = sender
    msg['Return-Path'] = sender
    msg['X-Mailer'] = 'Python/' + (python_version())

    part_text = MIMEText(text, 'plain')
    part_html = MIMEText(html, 'html')

    msg.attach(part_text)
    msg.attach(part_html)

    mail = smtplib.SMTP_SSL(server)
    mail.login(user, password)
    mail.sendmail(sender, to, msg.as_string())
    mail.quit()
