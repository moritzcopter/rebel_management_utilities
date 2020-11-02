import pandas as pd
from openpyxl import load_workbook


def append_df_to_excel(filename, df, **to_excel_kwargs):
    if 'engine' in to_excel_kwargs:
        to_excel_kwargs.pop('engine')

    writer = pd.ExcelWriter(filename, engine='openpyxl')

    try:
        writer.book = load_workbook(filename)

        sheet_name = writer.book.sheetnames[0]
        startrow = writer.book[sheet_name].max_row
        writer.sheets = {ws.title: ws for ws in writer.book.worksheets}
    except FileNotFoundError:
        sheet_name = 'Sheet1'
        startrow = 0

    df.to_excel(writer, sheet_name, startrow=startrow, **to_excel_kwargs)
    writer.save()
