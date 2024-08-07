from datetime import datetime
import os
import click
import configparser
import tempfile
import logging

from excel_output.user import User
from excel_output.HorosDBExtract import HorosDBExtract
from excel_output.EmailClient import EmailClient

# ESTABLISH DEFAULTS
# ESTABLISH DEFAULTS
config = configparser.ConfigParser()
config_file = os.path.expanduser("~/.db_excel_config.cfg")




def initialize_config():
    if not os.path.exists(config_file):
        config["paths"] = {
            "database_path": "~/Documents/Horos Data/Database.sql",
            "users_db": "~/Library/Application Support/Horos/WebUsers.sql",
            "master_dest": "~/Downloads"
        }
        with open(config_file, "w") as f:
            config.write(f)

def read_config():
    if not os.path.exists(config_file):
        initialize_config()
    config.read(config_file)

read_config()

DBPATH = os.path.expanduser(config["paths"]["database_path"])
USER_DBPATH = os.path.expanduser(config["paths"]["users_db"])
MASTER_LOG_DEST = os.path.expanduser(config["paths"]["master_dest"])

EMAIL = 'ryan.apfel.nirc@gmail.com'
LEVEL = logging.INFO
NIRC_URL = "https://strokedrop.neurology.ucla.edu:7777/"

logging.basicConfig(level=LEVEL)
"""
Returns dataframe to do work directly from hors database
"""
def ensure_directory(path):
    """Ensure that the directory exists. Create it if it doesn't."""
    if not os.path.exists(path):
        os.makedirs(path)
        logging.info(f"Created directory: {path}")
    else:
        logging.info(f"Directory already exists: {path}")

# Ensure the master log destination directory exists

@click.group()
def cli():
    pass


@cli.command()
@click.argument("email")
def new_user(email):
    logging.info(f"Checking user with email: {email} at {USER_DBPATH}")
    user_client = User(USER_DBPATH)
    email_client = EmailClient(EMAIL)

    if user_client.user_exists(email):
        logging.info(f"User with email {email} already exists.")
        print(user_client.find_user_by_email(email))
    else:
        logging.info(f"User with email {email} does not exist. Creating user.")
        user, password = user_client.insert_user(email)
        print(f"User with email {email} created successfully.")
        subject = "StrokeDrop - Account Credentials"
        
        body = (f"Hello,\n\nYour account has been created.\n\nEmail: {user}\n"
                f"Password: {password}\n\nYou can log in at: {NIRC_URL}\n\n"
                "Best Regards,\nNIRC Core Lab")

        email_client.send(user, subject, body)

        logging.info(f"Credentials email sent to {user}.")


@cli.command()
@click.argument("email")
def delete_user(email):
    logging.info(f"Attempting to delete user with email: {email} at {USER_DBPATH}")
    user_client = User(USER_DBPATH)

    if user_client.user_exists(email):
        user_client.delete_user(email)
        logging.info(f"User with email {email} deleted successfully.")
        print(f"User with email {email} deleted successfully.")
    else:
        logging.info(f"User with email {email} does not exist.")
        print(f"User with email {email} does not exist.")


@cli.command()
@click.argument("db_path")
def set_dbpath(db_path):
    """Set the database path and save it to config file."""
    config["paths"]["database_path"] = db_path
    with open(config_file, "w") as f:
        config.write(f)
    global DBPATH
    DBPATH = os.path.expanduser(db_path)
    click.echo(f"Database path set to: {DBPATH}")


@cli.command()
@click.option(
    "-s",
    "--study",
    help="Study name to filter in database for. Case insensitive ",
    required=True,
)
@click.option(
    "--db_path", default=DBPATH, help="Location of Databse Path for HOROS or Osirix"
)
@click.option(
    "--output_path",
    default=MASTER_LOG_DEST,
    help="Directory of Excel spradsheet output. Will only output to this location if ouput directory is not alraedy set in config.cfg",
)
@click.option(
    "-u",
    "--unresolved",
    help="Includes a seperate sheet with all unresolved imaging. Default is True",
    is_flag=True,
)
@click.option(
    "-t",
    "--timepoints",
    help="Includes a seperate sheet with all timepoints listed as a list. Default is False",
    is_flag=True,
)
def study(study, db_path, output_path, date, unresolved, timepoints):
    logging.info(f"Extracting Study: {study}")

    if study in STDUDY_DIRS.keys():
        output_path = STDUDY_DIRS[study]
    else:
        output_path = output_path

    if date:
        now_extension = datetime.now().strftime("%-m_%d_%Y")
        output_file = f"{study}_tracker_{now_extension}.xlsx"
    else:
        output_file = f"{study}_tracker.xlsx"

    path = output_path + output_file
    hdb = HorosDBExtract(dbpath=db_path)
    hdb.ETL(output_path=path, unresolved=unresolved, timepoints=timepoints, study=study)



@cli.command()
@click.option(
    "--db_path", default=DBPATH, help="Location of Databse Path for HOROS or Osirix"
)
@click.option(
    "--output_path",
    default=MASTER_LOG_DEST,
    help="Directory of Excel spradsheet output",
)
@click.option(
    "--output_file", default="master_tracker.xlsx", help="Name of Excel Spreadsheet"
)
@click.option(
    "-u",
    "--unresolved",
    help="Includes a seperate sheet with all unresolved imaging. Default is True",
    is_flag=True,
)
@click.option(
    "-t",
    "--timepoints",
    help="Includes a seperate sheet with all timepoints listed as a list. Default is False",
    is_flag=True,
)
def all(db_path, output_path, output_file, unresolved, timepoints):
    path = output_path + output_file
    hdb = HorosDBExtract(dbpath=db_path)
    hdb.ETL(output_path=path, unresolved=unresolved, timepoints=timepoints)


@cli.command()
@click.option(
    "-s",
    "--study",
    help="Study name to filter in database for. Case insensitive ",
    required=True,

)
@click.option("--to")
def send(study, to):
    output_file = f"{study}_tracker.xlsx"
    logging.info(f'Connecting to {DBPATH}')



    with tempfile.TemporaryDirectory() as temp_dir:
        tracker_location = os.path.join(temp_dir, output_file)
        hdb = HorosDBExtract(dbpath=DBPATH)
        hdb.ETL(output_path=tracker_location, unresolved=True, timepoints=True, study=study)

        emailClient = EmailClient(EMAIL)        
        
        message = f"Hello, \n Attached is an automated tracker update for the study {study}. If you are receiving this message in error please contact davidliebeskind@yahoo.com. \n Thank you, \n NIRC Team"
        subject = f"Updated Core Lab Tracker -- {study}"

        if not os.path.exists(tracker_location):
            raise ValueError(f"{tracker_location} does not contain a tracker)")

        emailClient.send(to, subject, message, attachments=[tracker_location])


if __name__ == "__main__":
    cli()
