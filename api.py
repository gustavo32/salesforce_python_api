import json
import pandas as pd
from simple_salesforce import Salesforce, SalesforceLogin, SFType
import os
import re

preference_fname = 'settings/preferences.json'


def read_preferences():
    preferences = {}
    if os.path.isfile(preference_fname):
        preferences = json.load(open(preference_fname))
    return preferences


def save_preferences(preferences):
    with open(preference_fname, 'w') as f:
        json.dump(preferences, f)


class SFApi:

    def __init__(self):
        self.sf = None

    @staticmethod
    def _normalize_records(df):
        if not isinstance(df, pd.Series):
            df = pd.DataFrame(df)

        df = df.apply(pd.Series)
        if len(df) > 0:
            df.drop(labels=['attributes'], axis=1, inplace=True)
        else:
            df = None
        return df

    @staticmethod
    def _get_domain(org):
        if org == 'prod':
            return 'login'
        else:
            return 'test'

    def connect(self):
        self.sf = None
        preferences = read_preferences()
        message = []
        try:
            self.sf = Salesforce(username=preferences['entry_username'],
                                 password=preferences['entry_password'],
                                 security_token=preferences['entry_token_security'],
                                 domain=self._get_domain(preferences['variable_radio']))
            message.append("LOGIN:SUCCESS")
        except Exception as e:
            message.append('LOGIN:FAILED')
            message.append('PROBLEM:MAYBE YOUR CREDENTIALS ARE INCORRECT!')

        return message

    def query(self, soql, iteractive=False):
        response = self.sf.query(soql)
        lst_records = response.get('records')
        if not iteractive:
            nextRecordsUrl = response.get('nextRecordsUrl')

            while not response.get('done'):
                response = sf.query_more(
                    nextRecordsUrl, identifier_is_url=True)
                lst_records.extend(response.get('records'))
                nextRecordsUrl = response.get('nextRecordsUrl')

        df_records = self._normalize_records(lst_records)
        restart = True
        while restart:
            restart = False
            for col in df_records.columns:
                if col[-3:] == '__r':
                    restart = True
                    s = self._normalize_records(
                        df_records[col]).add_prefix(col+'.')
                    df_records.drop(columns=[col], inplace=True)
                    df_records = pd.concat([df_records, s], axis=1, sort=False)

        return df_records

    def upsert(self, obj_api, data_dict, what='Id'):
        return getattr(self.sf.bulk, obj_api).upsert(data_dict, what)

    def update(self, obj_api, data_dict):
        return getattr(self.sf.bulk, obj_api).update(data_dict)

    def insert(self, obj_api, data_dict):
        # sobject = SFType(obj_api, self.sf.session_id, self.sf.sf_instance)
        return getattr(self.sf.bulk, obj_api).insert(data_dict)
