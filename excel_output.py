
import pandas as pd
from datetime import datetime
import shutil
import os
import sqlite3 as sql
import xlsxwriter
import re
import click


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


def split_patient_name(row):
    try:
        split_data = re.split('[-_]', row.patient_name)
        other = []
        for idx, splitItem in enumerate(split_data):
            if idx == 0:
                row['Study'] = splitItem
            elif idx == 1:
                row['Site_id'] = splitItem
            elif idx == 2:
                row['Subject_id'] = splitItem
            elif idx == 3:
                row['Timepoint'] = splitItem
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
    return df[['Study', 'Site_id', 'Subject_id', 'Timepoint', 'modality', 'aq_date', 'aq_time', 'acquistion_time', 'Status', 'patient_name', 'date_added']]


# https://xlsxwriter.readthedocs.io/example_pandas_conditional.html#ex-pandas-conditional
def write_excel(df, file_path):
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Tracker')
    writer.save()


def load(df, file_path):
    write_excel(df, file_path)


@click.command()
@click.option('--db_path', default=DB_PATH,  help='Location of Databse Path for HOROS or Osirix')
@click.option('--output_path', default=EXCEL_PATH, help='Location of Databse Path for HOROS or Osirix')
def run(db_path, output_path):
    df = extract(db_path)
    df = transform(df)
    load(df, output_path)
    print("Done!")


if __name__ == '__main__':
    print("Executing DB --> Spreadsheet")
    run()
