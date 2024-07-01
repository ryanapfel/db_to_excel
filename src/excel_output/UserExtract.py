import pandas as pd
import sqlite3 as sql
import xlsxwriter


class UserExtract:
    def __init__(self, path, output_path):
        self.path = path
        self.output_path = output_path

    def retrieve(self):
        dfh = self.extract_user(self.path)
        self.write_excel(dfh, self.output_path)

    def write_excel(self, df, file_path):
        writer = pd.ExcelWriter(file_path, engine="xlsxwriter")
        # Get the dimensions of the dataframe.
        (max_row, max_col) = df.shape
        df.to_excel(writer, sheet_name="Users")
        worksheet = writer.sheets["Users"]

        # Set the column widths, to make the dates clearer.
        worksheet.set_column(1, max_col, 20)
        worksheet.autofilter(0, 0, max_row, max_col - 1)
        writer.save()

    def extract_user_report(self):
        horoscon = sql.connect(self.path)
        query = """SELECT ZNAME as user,
                    ZPHONE as study,
                    ZEMAIL as email,
                    ZSTUDYPREDICATE as permission,
                    ZDOWNLOADREPORT as reports
                    FROM ZUSER
                    """

        dfh = pd.read_sql(query, horoscon)
        return dfh

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
