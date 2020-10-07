import pandas as pd
import numpy as np
import os
from datetime import datetime
import re


class Parser:

    def __init__(self, path, file_pattern):
        self.path = path
        self.file_pattern = file_pattern

    def get_list_files(self):
        cleaned_path = []
        for root, dirname, fnames in os.walk(self.path):
            for fname in fnames:
                if fname.upper().startswith(self.file_pattern):
                    cleaned_path.append(
                        (root + '/' + fname).replace('\\', '/'))

        return cleaned_path

    @staticmethod
    def _date_format_f(cell):
        if isinstance(cell, datetime):
            return datetime.strftime(cell.date(), '%Y-%m-%d')
        return cell

    def _normalize_datetime(self, df, c_date, c_time=None):
        df[c_date] = df[c_date].apply(self._date_format_f)

        if c_time is not None:
            df[c_time] = df[c_time].astype(str)
            s = (df[c_date] + ' ' + df[c_time])
        else:
            s = df[c_date]

        dummy_date = '2000-01-01 12:00:00'
        s = pd.to_datetime(s.fillna(dummy_date)).apply(
            datetime.isoformat) + 'Z'
        s = s.replace(datetime.isoformat(
            pd.to_datetime(dummy_date)) + 'Z', np.nan)

        return s.fillna('')

    def _get_oos_from_dates(self, df):
        start_date = pd.to_datetime(df['Start_Date__c'].str[:-1])
        release_date = pd.to_datetime(df['Release_Date__c'].str[:-1])
        return (release_date - start_date) / np.timedelta64(1, 'h')

    def get_unprocessed_files(self):
        need_analysis = []
        paths = self.get_list_files()

        if os.path.isfile('settings/history_files.txt'):
            with open('settings/history_files.txt', 'r') as f:
                history_paths = f.read().split('\n')

            for path in paths:
                if path.replace('ø', 'o').replace('@', 'a') not in history_paths:
                    need_analysis.append(path)
        else:
            need_analysis = paths

        return need_analysis

    def load_file(self, path, converters=None, dtype=None):
        return pd.read_excel(path, converters=converters, dtype=dtype)

    def get_cleaned_df(self, fname):
        raise NotImplementedError

    def get_reference_date(self, fname, length):
        month = None
        year = None
        for part in fname.split('/'):
            if part.isdigit():
                if int(part) > 0 and int(part) <= 12:
                    month = part
                elif int(part) > 2000 and int(part) < 2200:
                    year = part

        return length * ['{}-{}-{}'.format(year, month, '01')]


class AzulParser(Parser):

    def __init__(self, root, file_pattern):
        self.root = root
        self.azul_path = '/5 - LATIN AMERICA/AZUL'
        super(AzulParser, self).__init__(
            self.root + self.azul_path, file_pattern)

    @staticmethod
    def _normalize_oos_time(cell):
        cell_splitted = cell.split(':')
        if len(cell_splitted) > 1:
            return float(cell_splitted[0]) + float(cell_splitted[1]) / 60
        return cell

    def get_cleaned_df(self, fname):

        df = self.load_file(fname)
        cleaned_df = pd.DataFrame()
        cleaned_df['Aircraft_Register__c'] = df['ac'].str.strip()
        cleaned_df['Start_Date__c'] = self._normalize_datetime(
            df, 'data_inicio', 'hora_inicio')
        cleaned_df['Release_Date__c'] = self._normalize_datetime(
            df, 'data_final', 'hora_final')

        df.fillna('', inplace=True)

        cleaned_df['Log_Number__c'] = df['defect'].astype(int)
        cleaned_df['OOS_Total_Time__c'] = df['tempo_evento'].astype(
            str).str.strip().apply(self._normalize_oos_time)
        cleaned_df['Station__c'] = df['station'].str.strip()
        cleaned_df['Operator_ATA_Chapter__c'] = df['chapter']
        cleaned_df['Event_Record_Identifier__c'] = df['status'].fillna(
            '').str.strip()
        cleaned_df['Event_Description__c'] = df['defect_description'].str.replace(
            '\n', '<br>')
        cleaned_df['Action_Description__c'] = df['resolution_description'].str.replace(
            '\n', '<br>')
        cleaned_df['Reference_Date__c'] = self.get_reference_date(
            fname, len(cleaned_df))

        return cleaned_df


class WideroeParser(Parser):

    def __init__(self, root, file_pattern):
        self.root = root
        self.wideroe_path = '/4 - EMEA/WIDEROE'
        super(WideroeParser, self).__init__(
            self.root + self.wideroe_path, file_pattern)

    def get_cleaned_df(self, fname):
        converters = {
            'aircraft': (lambda x: x if x.startswith('LN') else 'LN-' + x.strip())}
        df = self.load_file(fname, converters=converters)

        cleaned_df = pd.DataFrame()
        cleaned_df['Aircraft_Register__c'] = df['aircraft']
        cleaned_df['Start_Date__c'] = self._normalize_datetime(
            df, 'OOS_Start_Date_And_Time')
        cleaned_df['Release_Date__c'] = self._normalize_datetime(
            df, 'OOS_End_Date_And_Time')

        df.fillna('', inplace=True)

        cleaned_df['Log_Number__c'] = df['Workordernumber'].astype(
            int)
        cleaned_df['OOS_Total_Time__c'] = df['OOS_Total_Hrs_Downtime'].astype(
            float)
        cleaned_df['Station__c'] = df['station'].str.strip()
        cleaned_df['Operator_ATA_Chapter__c'] = df['workorder_ATA']
        cleaned_df['Event_Record_Identifier__c'] = df['OPS_CODE'].str.strip()
        cleaned_df['Event_Description__c'] = df['Workorder_Desc_text'].str.replace(
            '\n', '<br>')
        cleaned_df['Action_Description__c'] = df['Workorder_Action_text'].str.replace(
            '\n', '<br>')
        cleaned_df['Header__c'] = df['event_header']
        cleaned_df['Flight_Number__c'] = df['FlightNumber'].astype(str)
        cleaned_df['Reference_Date__c'] = self.get_reference_date(
            fname, len(cleaned_df))

        return cleaned_df


class HelveticParser(Parser):

    def __init__(self, root, file_pattern):
        self.root = root
        self.helvetic_path = '/4 - EMEA/HELVETIC AIRWAYS'
        super(HelveticParser, self).__init__(
            self.root + self.helvetic_path, file_pattern)

    @staticmethod
    def _get_event_description(s):
        if len(s['Workorder Text'].strip()) > 0:
            return s['Workorder Text']
        else:
            return re.findall(r'(?:(?:Technical)|(?:AOG))\s*Event\:\s*([\s\S]+?)\;', s['Description'], re.IGNORECASE)[0]

    @staticmethod
    def _get_event_action(s):
        if len(s['Workorder Action'].strip()) > 0:
            return s['Workorder Action']
        else:
            return re.findall(r'Solution\:\s*([\s\S]+?)\;', s['Description'], re.IGNORECASE)[0]

    def get_cleaned_df(self, fname):

        converters = {
            'Occurrence Date': self._date_format_f, 'Ready Date': self._date_format_f}
        df = self.load_file(fname, converters=converters)

        cleaned_df = pd.DataFrame()
        cleaned_df['Aircraft_Register__c'] = df['Description'].str.extract(
            r'Aircraft\:\s*(.*?)\;', re.IGNORECASE, expand=False).str.strip()
        cleaned_df['Start_Date__c'] = self._normalize_datetime(
            df, 'Occurrence Date', 'Occurrence Time')
        cleaned_df['Release_Date__c'] = self._normalize_datetime(
            df, 'Ready Date', 'Ready Time')

        df.fillna('', inplace=True)

        cleaned_df['OOS_Total_Time__c'] = self._get_oos_from_dates(cleaned_df)
        cleaned_df['Event_Record_Identifier__c'] = df['Description'].str.extract(
            r'Status\:\s*(.*?)\;', re.IGNORECASE, expand=False).str.strip()

        cleaned_df['Log_Number__c'] = df['Workorder Number'].astype(
            int).apply(lambda x: np.nan if x <= 0 else x)

        cleaned_df['Station__c'] = df['Repair Station'].str.strip()

        cleaned_df['Operator_ATA_Chapter__c'] = df['ATA Chapter']

        cleaned_df['Event_Description__c'] = df[['Workorder Text',
                                                 'Description']].apply(self._get_event_description, axis=1).str.replace('\n', '<br>')
        cleaned_df['Action_Description__c'] = df[['Workorder Action',
                                                  'Description']].apply(self._get_event_action, axis=1).str.replace('\n', '<br>')

        cleaned_df['Header__c'] = df['Header']
        cleaned_df['Flight_Number__c'] = df['Event Flight Number'].astype(str)
        cleaned_df['Reference_Date__c'] = self.get_reference_date(
            fname, len(cleaned_df))

        return cleaned_df


class AstanaParser(Parser):

    def __init__(self, root, file_pattern):
        self.root = root
        self.astana_path = '/4 - EMEA/AIR ASTANA'
        super(AstanaParser, self).__init__(
            self.root + self.astana_path, file_pattern)

    @staticmethod
    def _normalize_oos_time(cell):
        date = pd.to_datetime(cell)
        return ((date.month - 1) * 31 * 24) + (date.day * 24) + date.hour + (date.minute / 60)

    @staticmethod
    def _correlate_columns(df):
        c_correlated = {}
        for col in df.columns:
            if col == 'Other':
                c_correlated[col] = 'Others__c'
            elif col == 'Parts Unavailability':
                c_correlated[col] = 'Parts_Unavailability__c'
            elif 'receive Embraer disposition' in col:
                c_correlated[col] = 'Time_to_Receive_Embraer_Disposition__c'
            elif 'Customer Operations' in col:
                c_correlated[col] = 'Customer_Operation__c'
            elif 'time for troubleshooting' in col:
                c_correlated[col] = 'Time_to_Receive_Supplier_Disposition__c'

        return c_correlated

    def _prepare_df(self, df):
        while df.columns[0] != 'A/C':
            if df.iloc[0, 0] == 'A/C':
                col_names = df.iloc[0]
                df.columns = col_names
            df = df.drop([0], axis=0).reset_index(drop=True)

        category_series = df[['CATEGORY', 'CONTRIB (%)', 'COMMENTS']].groupby(
            by=['CATEGORY']).apply(lambda x: x[['CONTRIB (%)', 'COMMENTS']].to_numpy())
        df = df.replace(r'^\s*$', np.nan, regex=True)
        df = df.dropna(axis='rows', subset=[
            'A/C']).drop(columns=['CATEGORY', 'CONTRIB (%)', 'COMMENTS'])

        t = np.concatenate(category_series.to_numpy()).reshape(
            len(category_series), *category_series[0].shape)
        comments = ['<br>'.join(t[:, i, 1][~pd.isnull(t[:, i, 1])])
                    for i in range(t.shape[1])]

        df[category_series.index] = category_series.to_numpy()
        df['COMMENTS'] = comments

        correlated_columns = self._correlate_columns(df)
        for techrep_col in correlated_columns.keys():
            df[techrep_col] = df[techrep_col].apply(
                lambda x: x*100 if x <= 1 else x).fillna('').astype(str)

        return df, correlated_columns

    def get_cleaned_df(self, fname):

        df = self.load_file(fname)
        df, techrep_cols = self._prepare_df(df)

        cleaned_df = pd.DataFrame()
        cleaned_df['Aircraft_Register__c'] = df['A/C'].str.strip()
        cleaned_df['Start_Date__c'] = self._normalize_datetime(
            df, 'START DATE', 'START TIME(UTC)')
        cleaned_df['Release_Date__c'] = self._normalize_datetime(
            df, 'FINISH DATE', 'FINISH TIME(UTC)')

        df.fillna('', inplace=True)

        cleaned_df['OOS_Total_Time__c'] = df['AOG time'].astype(
            str).str.strip().apply(self._normalize_oos_time)

        cleaned_df['Station__c'] = df['STATION'].str.strip()
        cleaned_df['Event_Description__c'] = df['DEFECT'].str.replace(
            '\n', '<br>')
        cleaned_df['Action_Description__c'] = df['Rectification Action'].str.replace(
            '\n', '<br>')

        for col in df.columns:
            if techrep_cols.get(col, None) is not None:
                cleaned_df[techrep_cols[col]] = df[col]
        cleaned_df['TechRep_Comments__c'] = df['COMMENTS']

        return cleaned_df
