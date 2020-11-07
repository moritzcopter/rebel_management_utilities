import pandas as pd
from openpyxl import load_workbook


def append_df_to_excel(filename, df, deduplicate_column=None, **to_excel_kwargs):
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

    if deduplicate_column:
        data = pd.read_excel(filename)
        df = df[~df[deduplicate_column].isin(data[deduplicate_column])]

    df.to_excel(writer, sheet_name, startrow=startrow, **to_excel_kwargs)
    writer.save()
