from datetime import datetime, timedelta, timezone
from doctest import OutputChecker
from tkinter.tix import DirList
import pandas as pd
import shutil
import os
import sqlite3 as sql
import xlsxwriter
import re
import configparser
import calendar
from dateutil import parser
import logging
import traceback



status_map = {0: 'Not Proccessed',
            1: 'Ready For Review',
            3: 'Unresolved',
            2: 'In Review',
            4: 'Ajudicated'}


class HorosDBExtract:

    def __init__(self, dbpath):
        self.engine  = sql.connect(dbpath)
        self.dbpath = dbpath

    def ETL(self, output_path, **kwargs):
        try:
            df = self.extract()
            logging.info("Extraction Completed")
            df = self.transform(df)
            logging.info("Transformation Completed")
            self.load(df, output_path, **kwargs)
            logging.info(f"Exported Database to {output_path}")
        except Exception as e:
            logging.warning("Unable to run")
            logging.warning(e)
            logging.info(traceback.format_exc())

    def extract(self):
        query = """select datetime(ZDATE,'unixepoch','31 years','localtime') as acquistion_time,
            datetime(ZDATEADDED,'unixepoch','31 years','localtime') as date_added, 
            ZDATE as zt,
            ZNAME as patient_name,
            ZMODALITY as modality,
            ZSTATETEXT as status,
            Z_PK,
            ZCOMMENT as comment
            from ZSTUDY"""

        return pd.read_sql(query, self.engine)
    

    def transform(self, df):
        df = df.apply(self.split_patient_name, axis=1)
        df = df.apply(self.split_date_time, axis=1)

        df['Status'] = df['status'].apply(self.getStatus)

        return df

    def getStatus(self, element):
        try:
            return status_map[int(element)]
        except:
            return 'N/A'

    def trackerLoad(self, df, writer, name):
        df = df[['Study',
                'Site_id', 
                'Subject_id', 
                'Timepoint', 
                'modality', 
                'aq_date', 
                'aq_time', 
                'acquistion_time', 
                'date_added',
                'comment',
                'Status',
                'Study_id']]

        df.to_excel(writer, sheet_name=name)
        worksheet = writer.sheets[name]
        (max_row, max_col) = df.shape
        # Set the column widths, to make the dates clearer.
        worksheet.set_column(1, max_col, 20)
        worksheet.autofilter(0, 0, max_row, max_col - 1)

    def unresolvedLoad(self, df, writer, name):
        df = df[df['Status'] == 'Unresolved']
        df = df[['Study','Timepoint','modality','aq_date','aq_time','comment']]
        # create column for notes
        df['Resolution Notes'] = ''

        df.to_excel(writer, sheet_name=name)
        worksheet = writer.sheets[name]
        (max_row, max_col) = df.shape
        # Set the column widths, to make the dates clearer.
        worksheet.set_column(1, max_col, 20)
        worksheet.autofilter(0, 0, max_row, max_col - 1)

    def timepointsLoad(self, df, writer, name):
        df = df.groupby(by='Study_id')['Timepoint'].apply(list).reset_index(name='Timepoints')

        df.to_excel(writer, sheet_name=name)
        worksheet = writer.sheets[name]
        (max_row, max_col) = df.shape
        # Set the column widths, to make the dates clearer.
        worksheet.set_column(1, max_col, 20)
        worksheet.autofilter(0, 0, max_row, max_col - 1)



    # https://xlsxwriter.readthedocs.io/example_pandas_conditional.html#ex-pandas-conditional
    def load(self, df, file_path, **kwargs):
        if 'study' in kwargs:
            study = kwargs['study']
            
            df = df[df['Study'].str.contains(study, flags=re.IGNORECASE, regex=True, na=False)]

            if df.empty:
                raise ValueError(f'Invalid study name: {study} does not exist in the Database.')
    

        # each possible sheet will be a k/v pair in dictionary. Value true if it's to be included
        sheets = {"Tracker":True}

        sheets['Unresolved'] = True if 'unresolved' in kwargs and kwargs['unresolved'] else False
        sheets['Timepoints'] = True if 'timepoints' in kwargs and kwargs['timepoints'] else False

        writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
        # Get the dimensions of the dataframe.
        for sheetname, isIncluded in sheets.items():
            try: 
                if sheetname == 'Tracker' and isIncluded:
                    self.trackerLoad(df, writer, sheetname)
                    logging.info("Tracker sheet written")
                elif sheetname == 'Unresolved' and isIncluded:
                    self.unresolvedLoad(df, writer, sheetname)
                    logging.info("Unresolved sheet written")
                elif sheetname == 'Timepoints' and isIncluded:
                    self.timepointsLoad(df, writer, sheetname)
                    logging.info("Timepoints sheet written")
            except Exception as e:
                logging.warning("Unable to proccess a sheet")
                logging.info(traceback.format_exc())
                       
        writer.save()



    def is_int(self, element: any) -> bool:
        try:
            int(element)
            return True
        except ValueError:
            return False

    def split_patient_name(self, row):
        split_data = re.split('[-_]', row['patient_name'])
        other = []
        for idx, splitItem in enumerate(split_data):
            try:
                if idx == 0:
                    row['Study'] = splitItem
                elif idx == 1 and self.is_int(splitItem):
                    row['Site_id'] = int(splitItem)
                elif idx == 2 and self.is_int(splitItem):
                    row['Subject_id'] = int(splitItem)
                    row['Study_id'] = f'{split_data[1]}-{splitItem}'
                elif idx == 3:
                    row['Timepoint'] = splitItem
                    
            except:
                logging.warning(f"Could not parse patient name for f{row['patient_name']}")

        return row




    def split_date_time(self, row):
        if isinstance(row.acquistion_time, str):
            dt = datetime.strptime(row.acquistion_time, '%Y-%m-%d %H:%M:%S')
            # row['pdate'] = datetime.fromtimestamp(row.zt,  tz=timezone.utc)
            row['aq_date'] = dt.date()
            row['aq_time'] = dt.time()
            return row
        else:
            return None


