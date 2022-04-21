
from doctest import OutputChecker
import email
from email import message
from email.policy import default
import pandas as pd
from datetime import datetime
import shutil
import os
import sqlite3 as sql
import xlsxwriter
import re
import click
import configparser
from src.UserExtract import UserExtract
from src.HorosDBExtract import HorosDBExtract
from src.AutomaticEmail import TrackerEmail

import logging


# ESTABLISH DEFAULTS
config = configparser.ConfigParser()
relativePath = os.path.dirname(os.path.abspath(__file__))
config.read(f'{relativePath}/config.cfg')
USER = os.path.expanduser('~')
DBPATH = USER + config['database']['database_path']

MASTER_LOG_DEST = USER + config['master']['destination'] 
DEFAULT_STUDY_DEST = USER + config['master']['destination']
STDUDY_DIRS =  {k: USER + v for k,v in dict(config['studyDirs']).items()}
USER_DB = USER + config['database']['users_db']
USER_OUTPUT = USER + config['master']['destination'] + 'user_tracker.xlsx'
DB_PATH = f'{USER}/Documents/Horos Data/Database.sql'
LEVEL = logging.INFO 
EMAIL = config['email']['email']
logging.basicConfig(level=LEVEL)


'''
Returns dataframe to do work directly from hors database
'''



@click.group()
def cli():
    pass

@cli.command()
@click.option('--output_path', default=USER_OUTPUT)
def users(output_path):
    ue = UserExtract(USER_DB, output_path)
    ue.retrieve()


@cli.command()
@click.option('-s','--study',help='Study name to filter in database for. Case insensitive ', required=True)
@click.option('--db_path', default=DBPATH,  help='Location of Databse Path for HOROS or Osirix')
@click.option('--output_path', default=MASTER_LOG_DEST, help='Directory of Excel spradsheet output. Will only output to this location if ouput directory is not alraedy set in config.cfg')
@click.option('-dt', '--date', is_flag=True)
@click.option('-u','--unresolved', help='Includes a seperate sheet with all unresolved imaging. Default is True',is_flag=True)
@click.option('-t','--timepoints', help='Includes a seperate sheet with all timepoints listed as a list. Default is False', is_flag=True)
def study(study, db_path, output_path, date, unresolved, timepoints):
    logging.info(f"Extracting Study: {study}")

    if study in STDUDY_DIRS.keys():
        output_path = STDUDY_DIRS[study]
    else:
        output_path = output_path

    
    if date:
        now_extension = datetime.now().strftime("%-m_%d_%Y")
        output_file = f'{study}_tracker_{now_extension}.xlsx'
    else:
        output_file = f'{study}_tracker.xlsx'


    path = output_path + output_file
    hdb = HorosDBExtract(dbpath=db_path)
    hdb.ETL(output_path=path, unresolved=unresolved, timepoints=timepoints, study=study)




@cli.command()
def ls():
    for i in STDUDY_DIRS:
        print(i)




@cli.command()
@click.option('--db_path', default=DBPATH,  help='Location of Databse Path for HOROS or Osirix')
@click.option('--output_path', default=MASTER_LOG_DEST, help='Directory of Excel spradsheet output')
@click.option('--output_file', default='master_tracker.xlsx', help='Name of Excel Spreadsheet')
@click.option('-u','--unresolved', help='Includes a seperate sheet with all unresolved imaging. Default is True',is_flag=True)
@click.option('-t','--timepoints', help='Includes a seperate sheet with all timepoints listed as a list. Default is False', is_flag=True)
def all(db_path, output_path, output_file, unresolved, timepoints):
    path = output_path + output_file
    hdb = HorosDBExtract(dbpath=db_path)
    hdb.ETL(output_path=path, unresolved=unresolved, timepoints=timepoints)



@cli.command()
@click.option('-s','--study',help='Study name to filter in database for. Case insensitive ', default='admin')
@click.option('--output_path', default=MASTER_LOG_DEST, help='Directory of Excel spradsheet that we want to send')
@click.option('--output_file', default='', help='Name of Excel Spreadsheet that we want to send')
def send(study,  output_path, output_file,):
    if study in STDUDY_DIRS.keys():
        output_path = STDUDY_DIRS[study]
    else:
        output_path = output_path

    if output_file == '':
        output_file = f'{study}_tracker.xlsx'

    tracker_location = output_path + output_file

    s = TrackerEmail(EMAIL, USER_DB)
    s.send(study, trackerLocations=tracker_location)
# @cli.command()
# @click.option('--path', help='Directory to search for studies')
# @click.option('--output_path', default='', help='Ouput path, defaults to location of files')
# def directory(path, output_path):
#     print("Dirnames --> Spreadsheet")
#     if output_path=='':
#         output_path = path + 'log.xlsx'
#     else:
#         output_path += 'log.xlsx'


#     # DirList = []
#     # for files in os.listdir(path):
#     #     if os.path.isdir(os.path.join(path,files)):
#     #         DirList.append(files)
#     # df = pd.DataFrame(DirList, columns=['patient_name'])
#     # df = df.apply(split_patient_name, axis=1)
#     # load(df[['Study','Site_id','Subject_id','Timepoint','Other','patient_name']], output_path)
#     # print("Done!")




if __name__ == '__main__':
    cli()
