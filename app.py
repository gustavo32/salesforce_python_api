from tkinter import *
from tkinter.ttk import Separator
from tkcalendar import Calendar, DateEntry
from api import SFApi, read_preferences, save_preferences

import json
import os


class Application:

    def message(self, master, msgs):
        message_window = Toplevel(master, background='#e8e8e8')
        message_window.title("STATUS")
        # message_window.geometry("400x150")
        counter = 0
        for msg in msgs:
            label, desc = msg.split(':')
            Label(message_window, text=label, fg='#145374', background='#e8e8e8', font=[
                  'Calibri', '10']).grid(row=counter, column=0, sticky=W, padx=(20, 10), pady=(5, 5))
            Label(message_window, text=desc, fg='#145374', background='#e8e8e8', font=[
                  'Calibri', '12']).grid(row=counter, column=1, sticky=W, padx=(10, 20), pady=(5, 5))
            counter += 1
            # label_message.grid(row=0, column=0, sticky=W, padx=10, pady=10)
        # self._set_styles({'label_message': {'fg': '#145374',
        #                                     'background': '#e8e8e8',
        #                                     'font': ['Calibri', '14']},
        #                   })

    def on_focus_out(self, element):
        preferences = read_preferences()
        preferences[element] = getattr(self, element).get()
        save_preferences(preferences)

    def on_left_click(self, element):
        preferences = read_preferences()
        preferences[element] = getattr(self, element).get()
        save_preferences(preferences)

    def _set_default_styles(self):
        default_options = {
            'font': ['Calibri', '14'], 'borderwidth': 0, 'highlightthickness': 0}
        for attr in list(self.__dict__.keys()):
            for key, value in default_options.items():
                try:
                    if not isinstance(getattr(self, attr), StringVar) and not isinstance(getattr(self, attr), str):
                        getattr(self, attr)[key] = value
                except AttributeError:
                    pass

    def _set_styles(self, elements):
        for element, styles in elements.items():
            for attr in list(self.__dict__.keys()):
                if not isinstance(getattr(self, attr), StringVar) and not isinstance(getattr(self, attr), str) and attr.startswith(element):
                    for key, value in styles.items():
                        getattr(self, attr)[key] = value

    def _default_actions(self):
        preferences = read_preferences()
        for attr in list(self.__dict__.keys()):
            obj = getattr(self, attr)
            if getattr(obj, "insert", False):
                obj.delete(0, 'end')
                obj.insert(0, preferences.get(attr, ''))
                obj.bind('<FocusOut>', lambda event,
                         x=attr: self.on_focus_out(x))
            elif isinstance(obj, StringVar):
                obj.set(preferences.get(attr, ''))

    def _define_defaults(self):
        self._set_default_styles()
        self._set_styles({
            'label': {
                'fg': '#145374',
                'background': '#e8e8e8',
                'font': ['Calibri', '10']
            },
            'entry': {
                'width': 30,
                'fg': '#00334e',
                'bd': 5,
                'relief': FLAT
            },
            'label_header': {
                'font': ['Calibri', '18', 'bold'],
                'fg': '#00334e'
            },
            'label_info': {
                'font': ['Calibri', '14']
            },
            'button_menu': {
                'background': '#e8e8e8',
                'relief': FLAT,
                'overrelief': FLAT
            },
            'radio': {
                'background': '#e8e8e8',
                'relief': FLAT,
                'overrelief': FLAT,
                'fg': '#00334e',
                'indicatoron': 0
            },
            'button_download_folder': {
                'bd': '1'
            },
            'button_upload_file': {
                'bd': '1'
            },
            'date_entry': {
                'foreground': '#e8e8e8',
                'background': '#00334e',
                'disabledbackground': '#e8e8e8',
                'disabledforeground': '#e8e8e8',
                'headersbackground': '#e8e8e8',
                'weekendbackground': '#fff',
                'weekendforeground': '#555',
                'normalforeground': '#555',
                'othermonthwebackground': '#e8e8e8',
                'othermonthweforeground': '#555',
                'othermonthbackground': '#e8e8e8',
                'othermonthforeground': '#555'
            },
            'entry_interval': {
                'width': 8
            }
        })

    def build_scheduled_task(self):
        frame_st = Frame(background='#e8e8e8')
        self.label_header_scheduled_task = Label(frame_st,
                                                 text='SCHEDULED UPLOAD')

        self.label_pattern = Label(frame_st, text='FILES START WITH')
        self.entry_pattern = Entry(frame_st)

        self.label_interval = Label(frame_st, text='INTERVAL TIME (HOURS)')
        self.entry_interval = Entry(frame_st)

        self.label_upload_since = Label(frame_st, text='UPLOAD DATA SINCE')
        self.date_entry_upload_since = DateEntry(
            frame_st, date_pattern='dd/mm/yyyy')
        # self.date_entry_upload_since = Entry(frame_st)

        self.label_last_upload = Label(frame_st, text='LAST UPLOAD: ')
        self.label_info_last_upload = Label(
            frame_st, text='12/01/2020 10:20:36')

        self.button_error_logs = Button(
            frame_st, text="Open Error Logs", fg='#e8e8e8', background='#00334e', relief=FLAT)
        self.button_upload = Button(
            frame_st, text="Upload", fg='#00334e', background='#fff')

        self._define_defaults()

        frame_st.grid(row=0, column=1, rowspan=1, columnspan=1)
        self.label_header_scheduled_task.grid(
            row=0, column=1, pady=(20, 20), padx=20)
        self.label_pattern.grid(
            row=1, column=1, pady=(10, 0), padx=20, sticky=W)
        self.entry_pattern.grid(
            row=2, column=1, pady=(0, 10), padx=20, sticky=W)

        self.label_interval.grid(
            row=3, column=1, pady=(10, 0), padx=20, sticky=W)
        self.entry_interval.grid(
            row=4, column=1, pady=(0, 10), padx=20, sticky=W)

        self.label_upload_since.grid(
            row=5, column=1, pady=(10, 0), padx=20, sticky=W)
        self.date_entry_upload_since.grid(
            row=6, column=1, pady=(0, 10), padx=20, sticky=W)

        self.label_last_upload.grid(
            row=7, column=1, pady=(20, 0), padx=20, sticky=W)
        self.label_info_last_upload.grid(
            row=7, column=1, pady=(20, 0), padx=20, sticky=E)

        self.button_error_logs.grid(
            row=8, column=1, pady=(30, 20), padx=20, sticky=W)
        self.button_upload.grid(
            row=8, column=1, pady=(30, 20), padx=20, sticky=E)

        return frame_st

    def build_settings(self):
        frame_st = Frame(background='#e8e8e8')
        self.label_header_config = Label(frame_st, text='SETTINGS')

        self.label_username = Label(frame_st, text='USERNAME')
        self.entry_username = Entry(frame_st)

        self.label_password = Label(frame_st, text='PASSWORD')
        self.entry_password = Entry(frame_st, show="*")

        self.label_token_security = Label(frame_st, text='TOKEN SECURITY')
        self.entry_token_security = Entry(frame_st, show="*")

        self.label_organization = Label(frame_st, text='ORGANIZATION')
        self.variable_radio = StringVar()
        self.radio_production = Radiobutton(
            frame_st, text='PROD', value='prod', variable=self.variable_radio, command=lambda: self.on_left_click('variable_radio'))
        self.radio_qa = Radiobutton(
            frame_st, text='QA', value='qa', variable=self.variable_radio, command=lambda: self.on_left_click('variable_radio'))
        self.radio_sandbox = Radiobutton(
            frame_st, text='SANDBOX', value='dev', variable=self.variable_radio, command=lambda: self.on_left_click('variable_radio'))

        self.button_check_login = Button(
            frame_st, text="Check Login", fg='#e8e8e8', background='#00334e', relief=FLAT,
            command=lambda: self.message(frame_st, SFApi().connect()))

        self._define_defaults()

        frame_st.grid(row=0, column=1, rowspan=1, columnspan=1)
        self.label_header_config.grid(
            row=0, column=1, pady=(20, 20), padx=20)
        self.label_username.grid(
            row=1, column=1, pady=(10, 0), padx=20, sticky=W)
        self.entry_username.grid(
            row=2, column=1, pady=(0, 10), padx=20, sticky=W)

        self.label_password.grid(
            row=3, column=1, pady=(10, 0), padx=20, sticky=W)
        self.entry_password.grid(
            row=4, column=1, pady=(0, 10), padx=20, sticky=W)

        self.label_token_security.grid(
            row=5, column=1, pady=(10, 0), padx=20, sticky=W)
        self.entry_token_security.grid(
            row=6, column=1, pady=(0, 10), padx=20, sticky=W)

        self.label_organization.grid(
            row=7, column=1, pady=(10, 0), padx=20, sticky=W)
        self.radio_production.grid(
            row=8, column=1, pady=(0, 0), padx=(20, 0), ipadx=10, sticky=W)
        self.radio_qa.grid(
            row=8, column=1, pady=(0, 0), padx=(120, 0), ipadx=10, sticky=W)
        self.radio_sandbox.grid(
            row=8, column=1, pady=(0, 0), padx=(200, 0), ipadx=10, sticky=W)

        self.button_check_login.grid(
            row=9, column=1, pady=(30, 20), padx=20, sticky=E)

        return frame_st
        # self.button_upload.grid(
        #     row=8, column=1, pady=(30, 20), padx=20, sticky=E)

    def build_transfer(self):
        frame_st = Frame(background='#e8e8e8')
        self.label_header_config = Label(frame_st, text='DATA TRANSFER')

        self.label_reference_date = Label(
            frame_st, text='REFERENCE DATE (Optional)')

        self.label_reference_from = Label(
            frame_st, text='FROM')
        self.date_entry_reference_from = DateEntry(
            frame_st, date_pattern='dd/mm/yyyy')

        self.label_reference_to = Label(frame_st, text='TO')
        self.date_entry_reference_to = DateEntry(
            frame_st, date_pattern='dd/mm/yyyy')

        self.label_download_folder = Label(frame_st, text='FOLDER')
        self.entry_download_folder = Entry(frame_st, text='TEST')
        self.button_download_folder = Button(frame_st, text='...')

        self.button_download = Button(
            frame_st, text="Download", fg='#e8e8e8', background='#00334e', relief=FLAT)

        self.label_upload_file = Label(frame_st, text='UPLOAD FILE')
        self.entry_upload_file = Entry(frame_st)
        self.button_upload_file = Button(frame_st, text='...')

        self.button_upload = Button(
            frame_st, text="Upload", fg='#e8e8e8', background='#00334e', relief=FLAT)

        self._define_defaults()

        frame_st.grid(row=0, column=1, rowspan=1, columnspan=1)
        self.label_header_config.grid(
            row=0, column=1, pady=(20, 20), padx=20)

        self.label_reference_date.grid(
            row=1, column=1, pady=(10, 0), padx=20, sticky=N)

        self.label_reference_from.grid(
            row=2, column=1, pady=(0, 0), padx=20, sticky=W)
        self.label_reference_to.grid(
            row=2, column=1, pady=(0, 0), padx=20, sticky=E)
        self.date_entry_reference_from.grid(
            row=3, column=1, pady=(0, 10), padx=20, sticky=W)
        self.date_entry_reference_to.grid(
            row=3, column=1, pady=(0, 10), padx=20, sticky=E)

        self.label_download_folder.grid(
            row=4, column=1, pady=(10, 0), padx=20, sticky=W)
        self.entry_download_folder.grid(
            row=5, column=1, pady=(0, 10), padx=20, sticky=W)
        self.button_download_folder.grid(
            row=5, column=1, pady=(0, 10), padx=20, sticky=E)

        self.button_download.grid(
            row=6, column=1, pady=(10, 20), padx=20, sticky=E)

        self.label_upload_file.grid(
            row=7, column=1, pady=(20, 0), padx=20, sticky=W)
        self.entry_upload_file.grid(
            row=8, column=1, pady=(0, 10), padx=20, sticky=W)
        self.button_upload_file.grid(
            row=8, column=1, pady=(0, 10), padx=20, sticky=E)
        self.button_upload.grid(
            row=9, column=1, pady=(10, 20), padx=20, sticky=E)

        return frame_st

    def on_closing(self, frame_home):
        frame_home.focus_set()
        root.destroy()

    def __init__(self, master=None):
        # FRAME BUTTONS
        frame_home = Frame(background='#e8e8e8')
        photo = PhotoImage(file="images/config_icon.png")
        self.button_menu_config = Button(
            frame_home, image=photo)
        self.button_menu_config.image = photo

        photo_scheduled = PhotoImage(file="images/scheduled_icon.png")
        self.button_menu_scheduled = Button(
            frame_home, image=photo_scheduled)
        self.button_menu_scheduled.image = photo_scheduled

        photo_transfer = PhotoImage(file="images/transfer_icon.png")
        self.button_menu_transfer = Button(
            frame_home, image=photo_transfer)
        self.button_menu_transfer.image = photo_transfer

        # command=lambda:
        Separator(frame_home, orient=VERTICAL).grid(
            column=1, row=0, rowspan=3, sticky='ns')

        self.button_menu_scheduled['background'] = '#d8d8d8'

        frame_home.grid(row=0, column=0, rowspan=1, columnspan=1)

        self.button_menu_config.grid(
            row=0, column=0, ipadx=20, ipady=20)
        self.button_menu_scheduled.grid(
            row=1, column=0, ipadx=20, ipady=20)
        self.button_menu_transfer.grid(
            row=2, column=0, ipadx=20, ipady=20)

        frame_transfer = self.build_transfer()
        frame_transfer.grid_forget()
        frame_scheduled = self.build_scheduled_task()
        frame_scheduled.grid_forget()
        frame_settings = self.build_settings()

        self.button_menu_config['command'] = lambda: self.switch_frames(
            frame_settings, [frame_scheduled, frame_transfer])
        self.button_menu_scheduled['command'] = lambda: self.switch_frames(
            frame_scheduled, [frame_settings, frame_transfer])
        self.button_menu_transfer['command'] = lambda: self.switch_frames(
            frame_transfer, [frame_settings, frame_scheduled])

        self._default_actions()
        master.protocol("WM_DELETE_WINDOW",
                        lambda: self.on_closing(frame_transfer))

    @staticmethod
    def switch_frames(render_frame, other_frames=[]):
        for frame in other_frames:
            frame.grid_forget()
        render_frame.focus_set()
        render_frame.grid(row=0, column=1, rowspan=1, columnspan=1)


root = Tk()
root.configure(background='#e8e8e8')
Application(root)
root.title('SalesForce API')
root.mainloop()
