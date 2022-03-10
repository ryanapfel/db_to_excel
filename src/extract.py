from datetime import datetime
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







status_map = {0: 'Not Proccessed',
              1: 'Ready For Review',
              3: 'Issues with Imaging',
              2: 'In Review',
              4: 'Ajudicated'}

class UserExtract:
    def __init__(self, path, output_path):
        self.path = path
        self.output_path = output_path


    def retrieve(self):
        dfh = self.extract_user(self.path)
        self.write_excel(dfh, self.output_path)

    def write_excel(self, df, file_path):
        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
        # Get the dimensions of the dataframe.
        (max_row, max_col) = df.shape
        df.to_excel(writer, sheet_name='Users')
        worksheet = writer.sheets['Users']


        # Set the column widths, to make the dates clearer.
        worksheet.set_column(1, max_col, 20)
        worksheet.autofilter(0, 0, max_row, max_col - 1)
        writer.save()
    


    def extract_user(self, path):
        horoscon = sql.connect(path)
        horoscur = horoscon.cursor()
        query = """SELECT ZNAME as user,
                ZPHONE as study,
                ZEMAIL as email,
                ZSTUDYPREDICATE as permission
                FROM ZUSER
                """
        
        dfh = pd.read_sql(query, horoscon)
        return dfh





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
    if isinstance(row.acquistion_time, str):
        dt = datetime.strptime(row.acquistion_time, '%Y-%m-%d %H:%M:%S')
        row['aq_date'] = dt.date()
        row['aq_time'] = dt.time()
        return row
    else:
        return None


def transform(df):
    df = df.apply(split_patient_name, axis=1)
    df = df.apply(split_date_time, axis=1)
    df['Status'] = df.apply(lambda x: status_map[x.status] if isinstance(x.status, str) else 'N/A', axis=1)
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