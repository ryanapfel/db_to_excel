import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import traceback


class EmailClient:
    def __init__(self, from_email, aws_region="us-west-1"):
        self.ses_client = boto3.client("ses", region_name=aws_region)
        self.from_email = from_email

    def send(self, destination, subject, body, attachments=[]):
        try:
            message = self.build_message(destination, subject, body, attachments)
            response = self.ses_client.send_raw_email(
                Source=self.from_email,
                Destinations=[destination],
                RawMessage={"Data": message.as_string()},
            )
            logging.info(response)
        except (BotoCoreError, ClientError) as e:
            logging.warning("Email not sent")
            logging.error(e)
            logging.debug(traceback.format_exc())

    def build_message(self, destination, subject, body, attachments=[]):
        msg = MIMEMultipart()
        msg["To"] = destination
        msg["From"] = self.from_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        for filename in attachments:
            self.add_attachment(msg, filename)

        return msg

    def add_attachment(self, msg, filename):
        part = MIMEBase("application", "octet-stream")
        with open(filename, "rb") as f:
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(filename)}",
        )
        msg.attach(part)
