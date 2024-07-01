from datetime import datetime
import os
import click
import configparser
from src.UserExtract import UserExtract
from src.HorosDBExtract import HorosDBExtract
import tempfile

from src.EmailClient import EmailClient
import logging


# ESTABLISH DEFAULTS
config = configparser.ConfigParser()
relativePath = os.path.dirname(os.path.abspath(__file__))

database_path = '~/Documents/Horos Data/Database.sql'
users_db = '~/Library/Application Support/Horos/WebUsers.sql'
master_dest = '~/Downloads'


config.read(f"{relativePath}/config.cfg")
DBPATH = os.path.expanduser(database_path)
USER_DBPATH = os.path.expanduser(users_db)

EMAIL ='ryan.apfel.nirc@gmail.com'

MASTER_LOG_DEST = os.path.expanduser(master_dest)
STDUDY_DIRS = config["studyDirs"]

USER_OUTPUT = config["master"]["destination"] + "user_tracker.xlsx"
LEVEL = logging.INFO



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
@click.option("--output_path", default=USER_OUTPUT)
def users(output_path):
    ue = UserExtract(USER_DBPATH, output_path)
    ue.retrieve()


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
def ls():
    for i in STDUDY_DIRS:
        print(i)


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

    relativePath = os.path.dirname(os.path.abspath(__file__))
    


    ensure_directory(MASTER_LOG_DEST)

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
