import json
import pandas as pd
import os
import re

from simple_salesforce import Salesforce, SalesforceLogin, SFType
from api import SFApi
import parsers as ps
from datetime import datetime
import openpyxl as op


def dict_from_df(df):
    if isinstance(df, pd.Series):
        df = df.to_frame()
    records_dict = df.to_dict('records')
    for record in records_dict:
        coppied_record = record.copy()
        for key, value in coppied_record.items():
            if value is None or value == '':
                del record[key]
    return records_dict


def split_dataframe(df_new, df, col, remove_prefix):
    df_new = pd.concat(
        [df_new, df[col]], axis=1, sort=False)
    df_new = df_new.rename(
        columns={col: col.replace(remove_prefix, '')})
    return df_new


def auto_update_records_from_operators_sheets():
    records = []
    ac_registers = []
    analyzed_files = []
    for parser_model in [ps.AzulParser, ps.WideroeParser, ps.HelveticParser, ps.AstanaParser]:
        p = parser_model('../1 - OPERADORES/1 - Dados recebidos', 'OOS_DATA')
        for fname in p.get_unprocessed_files():
            analyzed_files.append(fname.replace('ø', 'o').replace('@', 'a'))
            df = p.get_cleaned_df(fname).fillna('')
            ac_registers.extend(df['Aircraft_Register__c'].tolist())
            records.extend(dict_from_df(df))

    ac_registers = tuple(set(ac_registers))
    if len(records) > 0:
        print('--- STATUS ---')
        sf_api = SFApi()
        sf_api.connect()

        ac_ids = sf_api.query(
            "SELECT Registration__c, Id FROM Aircraft__c WHERE Registration__c IN {}".format(ac_registers))

        ac_ids = dict(zip(ac_ids['Registration__c'], ac_ids['Id']))

        for record in records:
            record['Serial_Number__c'] = ac_ids[record['Aircraft_Register__c']]
            del record['Aircraft_Register__c']

        results = sf_api.insert('Out_of_service__c', records)
        with open('history_files.txt', 'a+') as f:
            f.write('\n'.join(analyzed_files) + '\n')

        errors = []
        for result in results:
            if len(result['errors']) > 0:
                errors.append(result['errors'].upper())
        if len(errors) > 0:
            print('UPLOAD: FAILED')
            print('PROBLEM:\n\t'+'\n\t'.join(errors))
        else:
            print('UPLOAD: SUCCESS')

        print('--------------')

    else:
        print('Everything is up-to-date!')


def download_records_as_sheet():
    sf_api = SFApi()
    sf_api.connect()

    df = sf_api.query(
        '''
            SELECT Id, Aircraft_Register__c, Project__c, Operator__c, Station__c, Flight_Number__c,
            Event_Record_Identifier__c, Inter_ID__c, Log_Number__c, Reference_Date__c, Header__c, Event_Description__c,
            Action_Description__c, Start_Date__c, Release_Date__c, OOS_Total_Time__c, Chargeable__c, Exclusion_Code__c,
            Dispatched_On_MEL__c, Remove_Availability_Market__c, Parts_Unavailability__c, Customer_Operation__c,
            Time_to_Receive_Supplier_Disposition__c, Time_to_Receive_Embraer_Disposition__c, Expected_Time_For_Troubleshooting__c,
            Others__c, TechRep_Comments__c, Solution_Description__c, Solution_Release_Date__c, Issue_Status__c,
            Before_Event_Date__c, PCR__c, EPR__c, JIRA__c, eFleet__c, CMC_Message__c, EFTC_Comments__c,
            Component_Serial_Number__c, Component_Part_Number__c FROM Out_of_service__c
        ''')

    df_fc = sf_api.query('''
                         SELECT Fail_Code__r.Id, Fail_Code__r.Name, Fail_Code__r.ATA__c, Fail_Code__r.Technology__c,
                         Out_of_service__r.Id FROM FC_OOS_Association__c WHERE Out_of_service__c IN (\'{}\')
                         '''.format('\', \''.join(df.Id.to_numpy())))

    df_fc = df_fc.groupby(by=['Out_of_service__r.Id']).first()
    df = pd.merge(df, df_fc, how='left', left_on='Id',
                  right_on='Out_of_service__r.Id')

    df_rc = sf_api.query('''
                         SELECT Root_Code__r.Name, Root_Code__r.ATA__c, Root_Code__r.Supplier__r.Name,
                         Out_of_service__r.Id FROM RC_OOS_Association__c WHERE Out_of_service__c IN (\'{}\')
                         '''.format('\', \''.join(df.Id.to_numpy())))

    df_rc = df_rc.groupby(by=['Out_of_service__r.Id']).first()

    df = pd.merge(df, df_rc, how='left', left_on='Id',
                  right_on='Out_of_service__r.Id')

    cols = list(df.columns)
    for c_name in ['Fail_Code__r.Id', 'Fail_Code__r.Name', 'Fail_Code__r.ATA__c', 'Fail_Code__r.Technology__c']:
        cols.pop(cols.index(c_name))
        # print(cols.index('Solution_Description__c'))
        cols.insert(cols.index('Solution_Description__c'), c_name)

    df[cols].to_excel('EXPORTED_OOS_DATA_' +
                      re.sub(r'[^A-z0-9_]', '_', datetime.now().isoformat()
                             ) + '.xlsx', index=False)

    # SAVE
    # writer = pd.ExcelWriter('EXPORTED_OOS_DATA_' +
    #                         re.sub(r'[^A-z0-9_]', '_', datetime.now().isoformat()
    #                                ) + '.xlsx', engine='openpyxl')

    # df.to_excel(writer, index=False)
    # workbook = writer.book
    # worksheet = writer.sheets['Sheet1']
    # for idx, col in enumerate(df.columns):
    #     if re.findall(r'(id)$', col, re.IGNORECASE):
    #         worksheet.column_dimensions[op.utils.get_column_letter(
    #             idx+1)].hidden = True

    # writer.save()


def upload_modified_sheet(fname):
    sf_api = SFApi()
    sf_api.connect()

    df = pd.read_excel(fname)
    df_supplier = pd.DataFrame()
    df_root_code = pd.DataFrame()
    df_fail_code = pd.DataFrame()
    df_oos = pd.DataFrame()

    for col in df.columns:
        if 'Supplier__r' in col:
            df_supplier = split_dataframe(
                df_supplier, df, col, 'Root_Code__r.Supplier__r.')
        if col.startswith('Root_Code__r'):
            df_root_code = split_dataframe(
                df_root_code, df, col, 'Root_Code__r.')
        elif col.startswith('Fail_Code__r'):
            df_fail_code = split_dataframe(
                df_fail_code, df, col, 'Fail_Code__r.')
        else:
            df_oos = split_dataframe(df_oos, df, col, '')

    df_supplier.dropna(inplace=True)
    df_root_code = df_root_code.dropna(axis=0, how='all').fillna('')
    df_fail_code = df_fail_code.dropna(axis=0, how='all').fillna(
        '').drop(columns=['Technology__c'])
    df_oos = df_oos.dropna(axis=0, how='all').fillna('').drop(columns=[
        'Operator__c', 'Before_Event_Date__c', 'Project__c', 'Remove_Availability_Market__c', 'Aircraft_Register__c'])

    # supplier upsert
    records_supplier = dict_from_df(df_supplier)
    results = sf_api.upsert('Supplier__c', records_supplier, 'Name')
    df_name_and_id = pd.concat([pd.DataFrame(results).apply(pd.Series),
                                df_supplier.reset_index(drop=True)], axis=1, sort=False)[['id', 'Name']].rename(columns={'id': 'Supplier__r.Id', 'Name': 'Supplier__r.Name'})

    # root code upsert
    df_root_code['ATA__c'] = df_root_code['ATA__c'].astype(
        int).astype(str).apply(lambda x: '0' + x if len(x) == 1 else x)

    df_rc_oos_association = df_root_code.copy()

    df_root_code = pd.merge(df_root_code, df_name_and_id, how='left',
                            on='Supplier__r.Name').drop(columns=['Supplier__r.Name']).rename(columns={'Supplier__r.Id': 'Supplier__c'})

    records_root_code = dict_from_df(df_root_code)
    results_root_code = sf_api.upsert(
        'Root_Codes__c', records_root_code, 'Name')

    # root code and oos association insert
    df_results_root_code = pd.DataFrame(results_root_code).apply(pd.Series)
    df_rc_oos_association = pd.concat([
        df['Id'], df_rc_oos_association], axis=1, join='inner').reset_index(drop=True).rename(columns={'Id': 'Out_of_service__c'})
    df_rc_oos_association = pd.concat([
        df_results_root_code, df_rc_oos_association], sort=False, axis=1).rename(columns={'id': 'Root_Code__c'})

    df_new_associations = df_rc_oos_association[df_rc_oos_association['created'] == True][[
        'Root_Code__c', 'Out_of_service__c']]

    if len(df_new_associations) > 0:
        results_rc_oos_association = sf_api.insert(
            'RC_OOS_Association__c', dict_from_df(df_new_associations))
        print(results_rc_oos_association)

    # fail code update
    df_fail_code['ATA__c'] = df_fail_code['ATA__c'].astype(
        int).astype(str).apply(lambda x: '0' + x if len(x) == 1 else x)
    records_fail_code = dict_from_df(df_fail_code)
    results_fail_code = sf_api.update(
        'Fail_Codes__c', records_fail_code)

    # oos update
    records_oos = dict_from_df(df_oos)
    results_oos = sf_api.update(
        'Out_of_service__c', records_oos)


# download_records_as_sheet()
upload_modified_sheet('EXPORTED_OOS_DATA_2020_09_30T13_46_44_748803.xlsx')
