import logging
import os
import pickle
import traceback
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type
from email import encoders

# Request all access (permission to read/send/receive emails, manage the inbox, and more)
SCOPES = ['https://mail.google.com/']


def gmailAuth(credentials='/secrets/credentials.json', secret_path='/secrets/token.pickle'):
    relpath = os.path.dirname(os.path.realpath(__file__))
    credentials = relpath + credentials
    secret_path = relpath +secret_path

    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists(secret_path):
        with open(secret_path, "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials, SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open(secret_path, "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# get the Gmail API service



class EmailClient:
    def __init__(self, fromEmail):
        self.service = gmailAuth()
        self.fromEmail =  fromEmail

    def send(self, destination, subject, body, attachments=[]):
        try:
            success =  self.service.users().messages().send(
                userId="me",
                body=self.build_message(destination, subject, body, attachments)
                ).execute()
            
            logging.info(success)
        except Exception as E:
            logging.warn("Email not sent")
            logging.info(traceback.format_exc())
            



    def build_message(self, destination, obj, body, attachments=[]):
        if not attachments: # no attachments given
            self.message = MIMEText(body, 'plain')
            self.message['to'] = destination
            self.message['from'] = self.fromEmail
            self.message['subject'] = obj
        else:
            self.message = MIMEMultipart()
            self.message['to'] = destination
            self.message['from'] = self.fromEmail
            self.message['subject'] = obj
            self.message.attach(MIMEText(body, 'plain'))
            for filename in attachments:
                self.add_excel_file(filename)
        return {'raw': urlsafe_b64encode(self.message.as_bytes()).decode()}



    def add_excel_file(self, file):
        part = MIMEBase('application', "octet-stream")
        with open(file, 'rb') as f:
            file_data = f.read()
        part.set_payload(file_data)
        encoders.encode_base64(part)
        header_data = os.path.basename(file)
        part.add_header('Content-Disposition', f'attachment; filename="{header_data}"')
        self.message.attach(part)



    # Adds the attachment with the given filename to the given message
    def add_attachment(self, filename):

        content_type, encoding = guess_mime_type(filename)
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(filename, 'rb')
            msg = MIMEText(fp.read().decode(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(filename, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(filename, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(filename, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(filename)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        self.message.attach(msg)