from getpass import getuser
from .EmailClient import EmailClient
from .UserExtract import UserExtract
import re
import os
import logging
import time
import traceback


class TrackerEmail:
    def __init__(self, email, userDbPath):
        self.client = EmailClient(email)
        self.userDF = UserExtract(userDbPath, None).extract_user_report()

    def get_message(self, study):
        return f"Hello, \n Attached is an automated tracker update for the study {study}. If you are receiving this message in error please contact davidliebeskind@yahoo.com. \n Thank you, \n NIRC Team"

    def send(self, study, trackerLocations):
        try:
            emails = self.getUsers(study)
            logging.info("Emails Retrieved")
            file = self.getTracker(trackerLocations)
            logging.info("File retrieved")
            message = self.get_message(study)
            subject = f"Updated Core Lab Tracker -- {study}"
            for ithEmail in emails:
                self.client.send(ithEmail, subject, message, attachments=[file])
                logging.info(f"Tracker email sent for study {study} to {ithEmail}")

                # sleep in between so we don't overload smtp server
                time.sleep(1)
        except Exception as e:
            logging.critical("Emails not sent {e}")
            logging.info(traceback.format_exc())

    def getTracker(self, trackerLocations):
        if not os.path.exists(trackerLocations):
            raise ValueError(f"{trackerLocations} does not contain a tracker )")
        return trackerLocations

    def getUsers(self, study):
        user_list = self.userDF[
            (
                self.userDF["study"].str.contains(
                    study, flags=re.IGNORECASE, regex=True, na=False
                )
            )
            & (self.userDF["reports"] == 1)
        ]["email"].to_list()

        if not user_list:
            raise ValueError(f"{study} study contains no users with reports")

        return user_list

    # message = "Hi!\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org"
    # ec = EmailClient(EMAIL)
    # ec.send(destination="rasapfel@gmail.com",
    #             subject='Test',
    #             body=message)
