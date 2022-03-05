
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

# ESTABLISH DEFAULTS
config = configparser.ConfigParser()
relativePath = os.path.dirname(os.path.abspath(__file__))
config.read(f'{relativePath}/config.cfg')
DBPATH = config['database']['database_path']
MASTER_LOG_DEST = config['master']['destination'] + 'master_tracker.xlsx'
DEFAULT_STUDY_DEST = config['master']['destination']
STDUDY_DIRS = dict(config['studyDirs'])

USER = os.path.expanduser('~')
DB_PATH = f'{USER}/Documents/Horos Data/Database.sql'
EXCEL_PATH = 'spreadsheets/master_tracker.xlsx'

'''
Returns dataframe to do work directly from hors database
'''
status_map = {0: 'Not Proccessed',
              1: 'Ready For Review',
              3: 'Issues with Imaging',
              2: 'In Review',
              4: 'Ajudicated'}


def extract(path):
    horoscon = sql.connect(path)
    horoscur = horoscon.cursor()
    query = """select datetime(ZDATE,'unixepoch','31 years','localtime') as acquistion_time,
            datetime(ZDATEADDED,'unixepoch','31 years','localtime') as date_added, 
            ZNAME as patient_name,
            ZMODALITY as modality,
            ZSTATETEXT as status,
            Z_PK,
            ZCOMMENT
            from ZSTUDY"""

    dfh = pd.read_sql(query, horoscon)
    return dfh


def is_int(element: any) -> bool:
    try:
        int(element)
        return True
    except ValueError:
        return False

def split_patient_name(row):
    try:
        split_data = re.split('[-_]', row.patient_name)
        other = []
        for idx, splitItem in enumerate(split_data):
            if idx == 0:
                row['Study'] = splitItem
            elif idx == 1 and is_int(splitItem):
                row['Site_id'] = int(splitItem)
                row['Unresolved'] = False
            elif idx == 2 and is_int(splitItem):
                row['Subject_id'] = int(splitItem)
                row['Unresolved'] = False
            elif idx == 3:
                row['Timepoint'] = splitItem
            elif (idx == 1 or idx == 2) and not is_int(splitItem):
                row['Unresolved'] = True
            else:
                other.append(splitItem)

            row['Other'] = other
    except:
        pass

    return row


def split_date_time(row):
    dt = datetime.strptime(row.acquistion_time, '%Y-%m-%d %H:%M:%S')
    row['aq_date'] = dt.date()
    row['aq_time'] = dt.time()
    return row


def transform(df):
    df = df.apply(split_patient_name, axis=1)
    df = df.apply(split_date_time, axis=1)
    df['Status'] = df.apply(lambda x: status_map[x.status], axis=1)
    return df[['Study', 'Site_id', 'Subject_id', 'Timepoint', 'modality', 'aq_date', 'aq_time', 'acquistion_time', 'Status', 'date_added','Unresolved','patient_name']]


# https://xlsxwriter.readthedocs.io/example_pandas_conditional.html#ex-pandas-conditional
def write_excel(df, file_path):
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
    # Get the dimensions of the dataframe.
    (max_row, max_col) = df.shape
    df.to_excel(writer, sheet_name='Tracker')
    worksheet = writer.sheets['Tracker']


    # Set the column widths, to make the dates clearer.
    worksheet.set_column(1, max_col, 20)
    worksheet.autofilter(0, 0, max_row, max_col - 1)
    writer.save()


def load(df, file_path):
    write_excel(df, file_path)


@click.group()
def cli():
    pass

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
