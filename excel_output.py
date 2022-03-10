
from doctest import OutputChecker
from tkinter.tix import DirList
import pandas as pd
from datetime import datetime
import shutil
import os
import sqlite3 as sql
import xlsxwriter
import re
import click
import configparser
from src.extract import *


# ESTABLISH DEFAULTS
config = configparser.ConfigParser()
relativePath = os.path.dirname(os.path.abspath(__file__))
config.read(f'{relativePath}/config.cfg')
USER = os.path.expanduser('~')
DBPATH = USER + config['database']['database_path']

MASTER_LOG_DEST = USER + config['master']['destination'] + 'master_tracker.xlsx'
DEFAULT_STUDY_DEST = USER + config['master']['destination']
STDUDY_DIRS =  {k: USER + v for k,v in dict(config['studyDirs']).items()}
USER_DB = USER + config['database']['users_db']
USER_OUTPUT = USER + config['master']['destination'] + 'user_tracker.xlsx'
DB_PATH = f'{USER}/Documents/Horos Data/Database.sql'

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
@click.option('--db_path', default=DBPATH,  help='Location of Databse Path for HOROS or Osirix')
@click.option('--study', help='Get a tracker output of all items for a particular study')
@click.option('--output_path', default=DEFAULT_STUDY_DEST)
def study(db_path, study, output_path):
    print(f"Executing DB --> Spreadsheet for  {study}")
    extension = f'{study}_tracker.xlsx'
    path = output_path + extension
    df = extract(db_path)
    df = transform(df)
    tdf = df[df['patient_name'].str.contains('timeless')]
    load(tdf, path)
    print("Done!")



@cli.command()
def ls():
    for i in STDUDY_DIRS:
        print(i)




@cli.command()
@click.option('--db_path', default=DBPATH,  help='Location of Databse Path for HOROS or Osirix')
@click.option('--output_path', default=MASTER_LOG_DEST, help='Location of Excel spradsheet output')
def all(db_path, output_path):
    print("Executing DB --> Spreadsheet")
    df = extract(db_path)
    df = transform(df)
    load(df, output_path)
    print("Done!")


@cli.command()
@click.option('--path', help='Directory to search for studies')
@click.option('--output_path', default='', help='Ouput path, defaults to location of files')
def directory(path, output_path):
    print("Dirnames --> Spreadsheet")
    if output_path=='':
        output_path = path + 'log.xlsx'
    else:
        output_path += 'log.xlsx'


    DirList = []
    for files in os.listdir(path):
        if os.path.isdir(os.path.join(path,files)):
            DirList.append(files)
    df = pd.DataFrame(DirList, columns=['patient_name'])
    df = df.apply(split_patient_name, axis=1)
    load(df[['Study','Site_id','Subject_id','Timepoint','Other','patient_name']], output_path)
    print("Done!")

@cli.command()
def diff():
    pass



if __name__ == '__main__':
    cli()
