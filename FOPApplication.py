""" This file contains an implementation of a basic GUI for Alberta's Fire Occurrence Prediction (FOP) model.

    It sits on top of - and interfaces with - two "Controller" methods. One for Dr. Wotton's Lightning FOP
    model, and another for Dr. Woolford's Human FOP model.

    This code is written for the UAlberta FOP project, in collaboration with the Government of Alberta
    and the Canadian Forest Service.

    Author: Matthew Ansell
    2019
"""
import configparser  # Used to load and save application state.
import datetime
import os
import sys
import multiprocessing
import pandas as pd
import math
from tkinter import Tk  # Used as the GUI framework.
from tkinter import Menu
from tkinter import Toplevel
from tkinter import Entry
from tkinter import Label
from tkinter import Button
from tkinter import Frame
from tkinter import Text
from tkinter import Scrollbar
from tkinter import X
from tkinter import Y
from tkinter import LEFT
from tkinter import RIGHT
from tkinter import BOTH
from tkinter import TOP
from tkinter import YES
from tkinter import END
from tkinter import BooleanVar
from tkinter import IntVar
from tkinter import StringVar
from tkinter import Radiobutton
from tkinter import OptionMenu
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
from tkinter.filedialog import asksaveasfilename
import tkinter.messagebox as messagebox
from PIL import ImageTk, Image
from lightning import LightningFireOccurrencePrediction
from human import HumanFireOccurrencePrediction
import ctypes # To get the custom taskbar logo icon to show up
import traceback # To get exception information from subprocesses
import FOPConstantsAndFunctions
import streamlit as st

########################################## CONSTANTS ##########################################

APPLICATION_STATE_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.ini'))
ALBERTA_LOGO_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resource_files\\alberta_wildfire_black_logo_prototype_scaled.png'))
ALBERTA_ICON_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resource_files\\alberta_wildfire_icon.ico'))
FOP_SYSTEM_STATE_DB_PATH = 'resource_files\\fop_system_state_db.csv'
LTG_CUMULATIVE_PROBS_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resource_files\\ltg_fop_probabilities_output.out'))
HMN_CUMULATIVE_PROBS_EXPVALS_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\resource_files\\hmn_fop_probabilities_output.out'))

##########################################  CLASSES  ##########################################
class StdoutRedirect(object):
    # This class redirects stdout to a tkinter widget.
    def __init__(self, widget):
        self.widget = widget

    def write(self, string):
        # Override of stdout.write()
        self.widget.insert('end', string)
        self.widget.see('end')
    
    # Method definition must exist; can pass through.
    def flush(self):
        pass



def runLightningFOPModel(config, date_to_predict_for, int_ltg_fire_holdover_lookback_time, float_ltg_fire_confidence_interval,

                         display_historical_fires_on_maps, raw_weather_path, lightning_path, history_path):

    try:

        lightning_fop = LightningFireOccurrencePrediction(raw_weather_path,

                                                          lightning_path,

                                                          config.get('FilePathsAndLocations', r'ltg_intermediate_data_folder'),

                                                          config.get('FilePathsAndLocations', r'ltg_prediction_output_data_folder'),

                                                          config.get('FilePathsAndLocations', r'ltg_prediction_output_maps_folder'),

                                                          history_path

                                                          )

        lightning_fop.lightningFOPController(date_to_predict_for.date(),

                                             int_ltg_fire_holdover_lookback_time,

                                             float_ltg_fire_confidence_interval,

                                             display_historical_fires_on_maps)

    except Exception:

        print("runLightningFOPModel(): Exception occurred in worker subprocess . . .")

        traceback.print_exc()

        return -1  # Use -1 to indicate abnormal subprocess termination.

    return 0  # Use 0 to indicate normal subprocess termination

def runHumanFOPModel(config, date_to_predict_for, float_hmn_fire_confidence_interval, display_historical_fires_on_maps, raw_weather_path, history_path):

    try:

        print("look here:", type(raw_weather_path))

        human_fop = HumanFireOccurrencePrediction(raw_weather_path,

                                                  config.get('FilePathsAndLocations', r'ltg_intermediate_data_folder'),

                                                  config.get('FilePathsAndLocations', r'ltg_prediction_output_data_folder'),

                                                  config.get('FilePathsAndLocations', r'ltg_prediction_output_maps_folder'),

                                                  history_path

                                                  )

        human_fop.humanFOPController(date_to_predict_for.date(),

                                     float_hmn_fire_confidence_interval,

                                     display_historical_fires_on_maps)
    except ValueError:
        raise ValueError
    except Exception:
        raise Exception

def runGenerateLightningFireMapsPredictionsForDateRange(config, start_day, end_day, int_ltg_fire_holdover_lookback_time, float_ltg_fire_confidence_interval,
                                                        display_historical_fires_on_maps,raw_weather_path,lightning_path, history_path):
    try:
        lightning_fop = LightningFireOccurrencePrediction(raw_weather_path,
                                                          lightning_path,
                                                          config.get('FilePathsAndLocations', r'ltg_intermediate_data_folder'),
                                                          config.get('FilePathsAndLocations', r'ltg_prediction_output_data_folder'),
                                                          config.get('FilePathsAndLocations', r'ltg_prediction_output_maps_folder'), 
                                                          history_path,
                                                          )
        lightning_fop.lightningFOPDateRangeMapperPredictor(start_day,
                                                           end_day,
                                                           int_ltg_fire_holdover_lookback_time,
                                                           float_ltg_fire_confidence_interval,
                                                           display_historical_fires_on_maps)
    except Exception:
        print("runGenerateLightningFireMapsPredictionsForDateRange(): Exception occurred in worker subprocess . . .")
        traceback.print_exc()
        return -1  # Use -1 to indicate abnormal subprocess termination.
    return 0  # Use 0 to indicate normal subprocess termination

def runGenerateLightningFireArrivalsCIDiagnosticGraph(config, start_day, end_day, int_ltg_fire_holdover_lookback_time, float_ltg_fire_confidence_interval):
    try:
        lightning_fop = LightningFireOccurrencePrediction(config.get('FilePathsAndLocations', r'ltg_input_raw_weather_data_file'),
                                                          config.get('FilePathsAndLocations', r'ltg_input_raw_lightning_strike_data_file'),
                                                          config.get('FilePathsAndLocations', r'ltg_intermediate_data_folder'),
                                                          config.get('FilePathsAndLocations', r'ltg_prediction_output_data_folder'),
                                                          config.get('FilePathsAndLocations', r'ltg_prediction_output_maps_folder'), 
                                                          config.get('FilePathsAndLocations', r'ltg_historical_lightning_fire_data_file'),
                                                          )
        lightning_fop.lightningFOPCIGraphGenerator(start_day,
                                                   end_day,
                                                   int_ltg_fire_holdover_lookback_time,
                                                   float_ltg_fire_confidence_interval)
    except Exception:
        print("runGenerateLightningFireArrivalsCIDiagnosticGraph(): Exception occurred in worker subprocess . . .")
        traceback.print_exc()
        return -1  # Use -1 to indicate abnormal subprocess termination.
    return 0  # Use 0 to indicate normal subprocess termination

def runGenerateHumanFireArrivalsCIDiagnosticGraph(config, dates_to_graph, float_hmn_fire_confidence_interval):
    try:
        human_fop = HumanFireOccurrencePrediction(config.get('FilePathsAndLocations', r'ltg_input_raw_weather_data_file'),
                                                  config.get('FilePathsAndLocations', r'ltg_intermediate_data_folder'),
                                                  config.get('FilePathsAndLocations', r'ltg_prediction_output_data_folder'),
                                                  config.get('FilePathsAndLocations', r'ltg_prediction_output_maps_folder'), 
                                                  config.get('FilePathsAndLocations', r'ltg_historical_lightning_fire_data_file'),
                                                  )
        human_fop.humanFOPCIGraphGenerator(dates_to_graph,
                                           float_hmn_fire_confidence_interval)
    except Exception:
        print("runGenerateHumanFireArrivalsCIDiagnosticGraph(): Exception occurred in worker subprocess . . .")
        traceback.print_exc()
        return -1  # Use -1 to indicate abnormal subprocess termination.
    return 0  # Use 0 to indicate normal subprocess termination

def runGenerateHumanFireMapsPredictionsForDateRange(config, start_day, end_day, float_hmn_fire_confidence_interval,
                                                    display_historical_fires_on_maps,raw_weather_path, history_path):
    try:
        human_fop = HumanFireOccurrencePrediction(raw_weather_path,
                                                  config.get('FilePathsAndLocations', r'ltg_intermediate_data_folder'),
                                                  config.get('FilePathsAndLocations', r'ltg_prediction_output_data_folder'),
                                                  config.get('FilePathsAndLocations', r'ltg_prediction_output_maps_folder'), 
                                                  history_path
                                                  )
        human_fop.humanFOPDateRangeMapperPredictor(start_day,
                                                   end_day,
                                                   float_hmn_fire_confidence_interval,
                                                   display_historical_fires_on_maps)

    except Exception:
        print("runGenerateHumanFireMapsPredictionsForDateRange(): Exception occurred in worker subprocess . . .")
        traceback.print_exc()
        return -1  # Use -1 to indicate abnormal subprocess termination.
    return 0  # Use 0 to indicate normal subprocess termination

class FOPApplication(Tk):
    """ Creates a GUI that allows a user to provide input and execution of the FOP models."""

    def __init__(self, parent):

        # Call the superconstructor.
        Tk.__init__(self, parent)

        # Some hacky code to set the Alberta wildfire icon as the taskbar icon in Windows.
        myappid = 'mycompany.myproduct.subproduct.version' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # Main window details.
        self.parent = parent
        self.title('Province of Alberta - Fire Occurrence Prediction')
        self.resizable(False, False)
        self.iconbitmap(ALBERTA_ICON_FILE)

        # Config file for the application state and file paths.
        self.__config = configparser.ConfigParser()
        self.__config.read(APPLICATION_STATE_FILE)

        # GUI parameter variables.
        self.__date_to_predict_for = datetime.datetime.strptime(self.__config.get('ApplicationSettings', 'date_to_predict_for'), "%Y-%m-%d")
        self.__display_historical_fires_on_maps = BooleanVar(value=self.__config.get('ApplicationSettings', 'display_historical_fires_on_maps'))

        # Lightning FOP model, lightning fire holdover lookback time in days, < 0 indicates auto mode.
        self.__ltg_fire_holdover_lookback_time = StringVar(value=self.__config.get('ApplicationSettings', 'ltg_fire_holdover_lookback_time'))

        # Lightning FOP model, lightning fire confidence interval.
        self.__ltg_fire_confidence_interval = StringVar(value=self.__config.get('ApplicationSettings', 'ltg_fire_confidence_interval'))
        
        # Human FOP model, human fire confidence interval.
        self.__hmn_fire_confidence_interval = StringVar(value=self.__config.get('ApplicationSettings', 'hmn_fire_confidence_interval'))        

        # Set string trace variables for the paths in the config file.
        print("FOPApplication(): APPLICATION_STATE_FILE is %s" % APPLICATION_STATE_FILE)

        # Menu-related enable and disable methods.
        def disable_menu_items_while_subprocess_is_running():
            # This helper method disables the Tools, Options and Run menu items while the model is running.
            self.__menu.entryconfig("Tools", state="disabled")
            self.__menu.entryconfig("Options", state="disabled")
            self.__menu.entryconfig("Run", state="disabled")
        
        def enable_menu_items_when_subprocess_is_finished():
            # This helper method enabled the Tools, Options and Run menu items while the model is finished.
            self.__menu.entryconfig("Tools", state="normal")
            self.__menu.entryconfig("Options", state="normal")
            self.__menu.entryconfig("Run", state="normal")
        
        def set_historical_fire_data_state():
            # This helper method disables or enables the "Load historical fire data input..." menu item when self.__display_historical_fires_on_maps is set to False or True.
            # The ability to generate CI Diagnostics Graphs also depends on the state of this menu option.
            if self.__display_historical_fires_on_maps.get() is True:
                self.__file.entryconfig(index=2, state="normal")  # "2" corresponds to the File -> "Load historical fire data input..." menu option.
                self.__tools.entryconfig(index=3, state="normal")  # "3" corresponds to the Tools -> "Generate Human FOP arrivals CI diagnostic graph..." menu option.
                self.__tools.entryconfig(index=4, state="normal")  # "4" corresponds to the Tools -> "Generate Lightning FOP arrivals CI diagnostic graph..." menu option.
                self.ltg_historical_lightning_fire_data_file_label1.config(text='Path to the historical fire data input file:', fg='black')
            else:
                self.__file.entryconfig(index=2, state="disabled")
                self.__tools.entryconfig(index=3, state="disabled")
                self.__tools.entryconfig(index=4, state="disabled")
                self.ltg_historical_lightning_fire_data_file_label1.config(text='(Historical fire data file not being used)', fg='gray')   

        # Submenu dialogs.
        def _exit():
            """ Save the current application state and close the program. """

            # Set any last values of GUI widgets.
            self.__config.set('ApplicationSettings', 'display_historical_fires_on_maps', str(self.__display_historical_fires_on_maps.get()))

            # TODO: Add a boolean to warn the user if the prediction is currently running.
            with open(APPLICATION_STATE_FILE, 'w') as config_file:
                self.__config.write(config_file)
            self.winfo_toplevel().quit()
            self.winfo_toplevel().destroy()
        
        # Intercept window close protocol.
        self.protocol("WM_DELETE_WINDOW", _exit)

        def ask_load_raw_weather_data_input():
            """ Prompt the user to specify a location for the raw weather input file. """
            file_name = askopenfilename(title="Load raw weather data input...")

            # If a valid path to the file is obtained, update the config object and the GUI text label.
            if file_name:
                self.__config.set('FilePathsAndLocations', 'ltg_input_raw_weather_data_file', file_name)
                self.raw_weather_data_input_label2.config(text=file_name)

        def ask_load_raw_lightning_strike_data_input():
            """ Prompt the user to specify a location for the raw lightning strike data input file. """
            file_name = askopenfilename(title="Load raw lightning strike data input...")

            # If a valid path to the file is obtained, update the config object and the GUI text label.
            if file_name:
                self.__config.set('FilePathsAndLocations', 'ltg_input_raw_lightning_strike_data_file', file_name)
                self.raw_lightning_strike_data_input_label2.config(text=file_name)
        
        def ask_choose_historical_fire_data_file():
            """ Prompt the user to specify a location for the historical fire arrivals file. """
            file_name = askopenfilename(title="Load historical fire data input...")
            
            # If a valid path to the file is obtained, update the config object and the GUI text label.
            if file_name:
                self.__config.set('FilePathsAndLocations', 'ltg_historical_lightning_fire_data_file', file_name)
                self.ltg_historical_lightning_fire_data_file_label2.config(text=file_name)
        
        def ask_choose_intermediate_output_files_path():
            """ Prompt the user to specify a location to place the intermediate output data files. """
            file_name = askdirectory(title="Choose intermediate output files location...")

            # If a valid path to the file is obtained, update the config object and the GUI text label.
            if file_name:
                self.__config.set('FilePathsAndLocations', 'ltg_intermediate_data_folder', file_name)
                self.intermediate_output_files_path_label2.config(text=file_name)
        
        def ask_choose_prediction_output_files_path():
            """ Prompt the user to specify a location to place the prediction output data files. """
            file_name = askdirectory(title="Choose prediction output files location...")

            # If a valid path to the file is obtained, update the config object and the GUI text label.
            if file_name:
                self.__config.set('FilePathsAndLocations', 'ltg_prediction_output_data_folder', file_name)
                self.prediction_output_files_path_label2.config(text=file_name)
        
        def ask_choose_prediction_maps_output_path():
            """ Prompt the user to specify a location to place the prediction output maps files. """
            file_name = askdirectory(title="Choose prediction output maps location...")
            
            # If a valid path to the file is obtained, update the config object and the GUI text label.
            if file_name:
                self.__config.set('FilePathsAndLocations', 'ltg_prediction_output_maps_folder', file_name)
                self.prediction_maps_output_path_label2.config(text=file_name)
        
        def ask_clear_fop_system_state_db():
            result = messagebox.askquestion("Confirm operation", "Are you sure you want to clear the FOP system state DB and cumulative probability files?", icon='warning')
            if result == 'yes':
                self.clearSystemStateDB()
        
        def ask_set_prediction_date():
            window = Toplevel()
            window.title("Set single-day prediction date")
            window.resizable(False, False)

            def set_text(text):                
                entry1.delete(0, END)
                entry1.insert(0, text)
                return
            
            def close():
                window.destroy()
            
            def select_value():
                # Perform a data entry check before we close the window.
                try:
                    parsed_date = datetime.datetime.strptime(entry1.get(), "%Y-%m-%d")

                    # If the parsed date is before March 01 or beyond October 31, we will not map for it.
                    if parsed_date < datetime.datetime(parsed_date.year, 3, 1) or parsed_date > datetime.datetime(parsed_date.year, 10, 31):
                        messagebox.showerror("Invalid date entered", "Please enter a date between March 01 and October 31 and try again.")
                        window.destroy()
                        return
                    
                    # We need to make sure that the prediction date has the same year as the years currently in the FOP system state DB.
                    # Load up the FOP system state DB.
                    fop_system_state_db_df = pd.read_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', header=0, parse_dates=['DATE'])

                    # For this check, we will simply just find whatever the minimum date is (predicted for or not) and check its year.
                    # This is sufficient because either the FOP system state DB is empty, or it contains dates that are all the same year.
                    fop_system_state_db_mindate = fop_system_state_db_df['DATE'].min()

                    # If we have a valid min date, then perform the check. Otherwise, we assume the DB is empty and continue onward.
                    if not pd.isnull(fop_system_state_db_mindate) and (fop_system_state_db_mindate.year != parsed_date.year):                    
                        messagebox.showerror("Invalid year entered", "The year of the prediction date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (parsed_date.year, fop_system_state_db_mindate.year))
                        return
                    
                    self.__date_to_predict_for = datetime.datetime.strptime(entry1.get(), "%Y-%m-%d")
                    self.date_to_predict_for_label2.config(text=self.__date_to_predict_for.strftime("%Y-%m-%d"))
                    self.__config.set('ApplicationSettings', 'date_to_predict_for', self.__date_to_predict_for.strftime("%Y-%m-%d"))
                    print("ask_set_prediction_date(): self.__date_to_predict_for set to %s" % self.__date_to_predict_for.strftime("%Y-%m-%d"))
                    close()

                except ValueError as e:
                    print("ask_model_settings(): ValueError caught! ... ", e)
                    messagebox.showerror("Invalid date entered", "Please enter a valid date in the correct format and try again.")

            label1 = Label(window, text="Specify a single day to produce a Human- or Lightning-caused fire occurrence prediction for below.", font='Arial 8 bold')
            label1.grid(row=0, columnspan=3)

            label2 = Label(window, text="Human-caused fire season: March 01 through October 31.")
            label2.grid(row=1, columnspan=3)

            label3 = Label(window, text="Lightning-caused fire season: May 01 through September 30.")
            label3.grid(row=2, columnspan=3)
            
            # Load up the FOP system state DB.
            fop_system_state_db_df = pd.read_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', header=0, parse_dates=['DATE'])
            fop_system_state_db_df.set_index('DATE')

            """# Determine the min and max days in the FOP system state DB.
            fop_system_state_db_mindate = fop_system_state_db_df['DATE'].min()
            fop_system_state_db_maxdate = fop_system_state_db_df['DATE'].max()

            # If the max and min dates are floating point numbers, assume they are "nan" and display something more sensical to the user.
            if isinstance(fop_system_state_db_mindate, float):
                label4 = Label(window, text="Earliest date in the database: (none)")
            else:
                label4 = Label(window, text="Earliest date in the database: %s" % fop_system_state_db_mindate.strftime("%Y-%m-%d"))
            label4.grid(row=3, columnspan=3)

            if isinstance(fop_system_state_db_maxdate, float):
                label4 = Label(window, text="Most recent date in the database: (none)")
            else:
                label4 = Label(window, text="Most recent date in the database: %s" % fop_system_state_db_maxdate.strftime("%Y-%m-%d"))
            label4.grid(row=4, columnspan=3)"""

            # Prediction date.
            label3 = Label(window, text="Enter a date to predict for (YYYY-MM-DD):")
            label3.grid(row=3, columnspan=3)
            entry1 = Entry(window)
            entry1.grid(row=4, columnspan=3)

            print("ask_model_settings(): self.__date_to_predict_for is currently %s" % self.__date_to_predict_for.strftime("%Y-%m-%d"))
            set_text(self.__date_to_predict_for.strftime("%Y-%m-%d"))

            button1 = Button(window, text="Today", command=lambda:set_text(datetime.datetime.now().strftime("%Y-%m-%d")), padx=1, pady=1)
            button1.grid(row=5, column=0, sticky="e")

            button2 = Button(window, text="Select", command=select_value, padx=1, pady=1)            
            button2.grid(row=5, column=1, sticky="s")

            button3 = Button(window, text="Cancel", command=close, padx=1, pady=1)            
            button3.grid(row=5, column=2, sticky="w")

            # Position the new window, lift the new window above the main one, and put it in focus.
            x = self.winfo_x()
            y = self.winfo_y()
            window.geometry("+%d+%d" % (x + 50, y + 35))
            window.focus()
        
        def ask_set_ltg_fire_holdover_lookback_time():
            
            window = Toplevel()
            window.title("Set lightning fire holdover lookback time")
            window.resizable(False, False)

            def set_text(text):                
                entry1.delete(0, END)
                entry1.insert(0, text)
                return
            
            def close():
                # Perform a data entry check before we close the window.
                try:
                    # If the "auto" mode radiobutton is checked...
                    if ltg_holdover_mode.get() == "auto":
                        self.__ltg_fire_holdover_lookback_time.set("Automatic (DC-dependent)")
                        self.lightning_fire_holdover_lookback_time_label2.config(text="Automatic (DC-dependent)")
                        self.__config.set('ApplicationSettings', 'ltg_fire_holdover_lookback_time', "Automatic (DC-dependent)")                        
                    else:
                        # Cast the entrybox contents as an int temporarily to do some checks.
                        parsed_time = int(entry1.get())

                        # If the parsed time is less than 0 days or greater than 28 days, display a messagebox.
                        if parsed_time < 0 or parsed_time > 28:
                            messagebox.showerror("Invalid duration entered", "Please enter a number of days between 0 and 28 and try again.")
                            window.destroy()
                            return                            
                    
                        # If we get here, we can set the class member variable to the correct value.
                        self.__ltg_fire_holdover_lookback_time.set(str(parsed_time))
                        self.lightning_fire_holdover_lookback_time_label2.config(text=str(parsed_time))
                        self.__config.set('ApplicationSettings', 'ltg_fire_holdover_lookback_time', str(parsed_time))
                    
                    print("ask_set_ltg_fire_holdover_lookback_time(): self.__ltg_fire_holdover_lookback_time set to %s" % self.__ltg_fire_holdover_lookback_time.get())
                    window.destroy()

                except ValueError as e:
                    print("ask_set_ltg_fire_holdover_lookback_time(): ValueError caught! ... ", e)
                    messagebox.showerror("Invalid duration entered", "Please enter an integer between 0 and 28 and try again.")

            # Holdover lookback time.
            label1 = Label(window, text="Choose either automatic time determination mode based on daily DC values, or manually specify\nthe lightning fire holdover lookback time below:", font='Arial 8 bold')
            label1.grid(row=0)            

            entry1 = Entry(window)
            
            ltg_holdover_mode = StringVar()
            # Initialize the StringVar so that the appropriate radio button gets selected when the window appears.
            if self.__ltg_fire_holdover_lookback_time.get() == "Automatic (DC-dependent)":
                ltg_holdover_mode.set("auto")
                entry1.config(state='disabled')
                set_text("")
            else:
                ltg_holdover_mode.set("manual")
                entry1.config(state='normal')
                set_text(str(self.__ltg_fire_holdover_lookback_time.get()))

            # Callback methods to update the entry widget for holdover lookback time.
            def disable_entry_callback():
                entry1.config(state='disabled')
                set_text("")                
            def enable_entry_callback():
                entry1.config(state='normal')
            
            radiobutton1 = Radiobutton(window, text="Automatic (DC-dependent) time determination mode",
                                               variable=ltg_holdover_mode,
                                               value="auto",
                                               command=disable_entry_callback)
            radiobutton1.grid(row=1)
            radiobutton2 = Radiobutton(window, text="Manually specify a duration (between 0 and 28 days):",
                                               variable=ltg_holdover_mode,
                                               value="manual",
                                               command=enable_entry_callback)
            radiobutton2.grid(row=2)

            entry1.grid(row=3)

            button1 = Button(window, text="Select", command=close, padx=1, pady=1)            
            button1.grid(row=4)         

            # Position the new window, lift the new window above the main one, and put it in focus.
            x = self.winfo_x()
            y = self.winfo_y()
            window.geometry("+%d+%d" % (x + 50, y + 35))
            window.focus()
        
        def ask_set_fire_confidence_intervals():

            window = Toplevel()
            window.title("Set fire confidence intervals")
            window.resizable(False, False)

            # Confidence interval.
            label1 = Label(window, text="Select a confidence interval to use for each of the forest fire\nprediction models from the dropdown menus below.", font='Arial 8 bold')
            label1.grid(row=0, columnspan=2)

            # OptionMenus for the confidence interval selection.
            label2 = Label(window, text="Lightning FOP:")
            label2.grid(row=1, column=0)

            ci_option_menu1 = OptionMenu(window, self.__ltg_fire_confidence_interval, '99', '95', '90', '75', '50')
            ci_option_menu1.grid(row=2, column=0)
            
            label3 = Label(window, text="Human FOP:")
            label3.grid(row=1, column=1)

            ci_option_menu2 = OptionMenu(window, self.__hmn_fire_confidence_interval, '99', '95', '90', '75', '50')
            ci_option_menu2.grid(row=2, column=1)

            def close():
                print("ask_set_fire_confidence_intervals(): Setting lightning fire confidence interval to %s%%..." % self.__ltg_fire_confidence_interval.get())
                self.__config.set('ApplicationSettings', 'ltg_fire_confidence_interval', self.__ltg_fire_confidence_interval.get())
                self.lightning_fire_confidence_interval_label2.config(text=self.__ltg_fire_confidence_interval.get() + '%')

                print("ask_set_fire_confidence_intervals(): Setting human fire confidence interval to %s%%..." % self.__hmn_fire_confidence_interval.get())
                self.__config.set('ApplicationSettings', 'hmn_fire_confidence_interval', self.__hmn_fire_confidence_interval.get())
                self.human_fire_confidence_interval_label2.config(text=self.__hmn_fire_confidence_interval.get() + '%')
                window.destroy()

            # Buttons.
            button1 = Button(window, text="Select", command=close, padx=1, pady=1)            
            button1.grid(row=3, columnspan=2)

            # Position the new window, lift the new window above the main one, and put it in focus.
            x = self.winfo_x()
            y = self.winfo_y()
            window.geometry("+%d+%d" % (x + 50, y + 35))
            window.focus()
            
        def ask_generate_ltg_fop_maps_predictions_for_date_range_callback(result):
            enable_menu_items_when_subprocess_is_finished()
            if result == 0:
                print("ask_generate_ltg_maps_predictions_for_date_range_callback(): Lightning FOP maps and predictions generation tool subprocess execution finished succesfully. Application ready.")
                self.model_status_label2.config(text='Lightning FOP maps and predictions generation tool finished successfully. Application ready.')
            else:
                print("ask_generate_ltg_maps_predictions_for_date_range_callback(): Lightning FOP maps and predictions generation tool subprocess encountered an error during execution.")
                self.model_status_label2.config(text='Lightning FOP maps and predictions generation tool encountered an error during execution.')
            return
        
        def ask_generate_ltg_fop_maps_predictions_for_date_range():

            # Load up the FOP system state DB.
            fop_system_state_db_df = pd.read_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', header=0, parse_dates=['DATE'])

            # Determine the man and min days in the FOP system state DB for which Lightning FOP has been performed.
            fop_system_state_db_lightning_fop_mindate = fop_system_state_db_df.loc[fop_system_state_db_df['LIGHTNING_FOP_COMPLETED'] == "Y"]['DATE'].min()
            fop_system_state_db_lightning_fop_maxdate = fop_system_state_db_df.loc[fop_system_state_db_df['LIGHTNING_FOP_COMPLETED'] == "Y"]['DATE'].max()

            # Ensure that we have sane text labels if the DB is empty.            
            if pd.isnull(fop_system_state_db_lightning_fop_mindate):
                fop_system_state_db_lightning_fop_mindate = "(Lightning FOP not yet performed)"
            
            if pd.isnull(fop_system_state_db_lightning_fop_maxdate):
                fop_system_state_db_lightning_fop_maxdate = "(Lightning FOP not yet performed)"

            window = Toplevel()
            window.title("Generate Lightning FOP maps and predictions for date range")
            window.resizable(False, False)

            def set_text(text, entry):      
                entry.delete(0, END)
                entry.insert(0, text)
                return
            
            def close():
                window.destroy()
            
            def do_generate_maps_predictions_for_date_range():
                # Perform some data entry checks. First, try parsing start_date and end_date as datetimes.
                try:
                    start_date = datetime.datetime.strptime(entry1.get(), "%Y-%m-%d")
                    end_date = datetime.datetime.strptime(entry2.get(), "%Y-%m-%d") 
                except ValueError as e:
                    print("doGenerateMapsForDateRange(): ValueError caught! ... ", e)
                    messagebox.showerror("Invalid date entered", "Please enter a date in the correct format and try again.")
                    return
                
                # First, if prediction dates exist already in the FOP system state DB, ensure that the start and end dates' years
                # match what is currently in the DB. Use fop_system_state_db_lightning_fop_mindate.
                if fop_system_state_db_lightning_fop_mindate != "(Lightning FOP not yet performed)":

                    if fop_system_state_db_lightning_fop_mindate.year != start_date.year:                    
                        messagebox.showerror("Invalid year entered", "The year of the start date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (start_date.year, fop_system_state_db_lightning_fop_mindate.year))
                        return
                
                    if fop_system_state_db_lightning_fop_mindate.year != end_date.year:                    
                        messagebox.showerror("Invalid year entered", "The year of the end date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (end_date.year, fop_system_state_db_lightning_fop_mindate.year))
                        return
                
                    # Next, ensure that the date range is valid.
                    """if start_date < fop_system_state_db_lightning_fop_mindate:                    
                        messagebox.showerror("Invalid date entered", "The start date provided (%s) is less than the earliest Lightning FOP date predicted for in the database (%s). Please correct and try again." % (start_date.strftime("%Y-%m-%d"), fop_system_state_db_lightning_fop_mindate.strftime("%Y-%m-%d")))
                        return
                
                    if end_date > fop_system_state_db_lightning_fop_maxdate:                    
                        messagebox.showerror("Invalid date entered", "The end date provided (%s) is beyond the most recent Lightning FOP date predicted for in the database (%s). Please correct and try again." % (end_date.strftime("%Y-%m-%d"), fop_system_state_db_lightning_fop_maxdate.strftime("%Y-%m-%d")))
                        return"""                
                
                fop_system_state_db_mindate = fop_system_state_db_df['DATE'].min()
                if not pd.isnull(fop_system_state_db_mindate):

                    if fop_system_state_db_mindate.year != start_date.year:                    
                        messagebox.showerror("Invalid year entered", "The year of the start date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (start_date.year, fop_system_state_db_mindate.year))
                        return

                    if fop_system_state_db_mindate.year != end_date.year:                    
                        messagebox.showerror("Invalid year entered", "The year of the end date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (end_date.year, fop_system_state_db_mindate.year))
                        return
                
                # These checks do not involve checking any dates in the FOP system state DB.
                if start_date > end_date:                    
                    messagebox.showerror("Invalid date entered", "The start date cannot be more recent than the end date. Please correct and try again.")
                    return
                
                if start_date < pd.Timestamp(start_date.year, 5, 1):                    
                    messagebox.showerror("Invalid date entered", "The start date provided cannot be prior to May 1 (start of the lightning fire season). Please correct and try again.")
                    return
                
                if end_date > pd.Timestamp(end_date.year, 9, 30):                    
                    messagebox.showerror("Invalid date entered", "The end date provided cannot be beyond September 30 (end of the lightning fire season). Please correct and try again.")
                    return
                
                # An interesting corner case is if the DB is empty and the user enters dates that do not have the same year.
                # This will not be caught by checking the dates in the DB, because no dates exist there yet.
                if start_date.year != end_date.year:
                    messagebox.showerror("Invalid year entered", "The year of the start date provided (%d) and end date provided (%d) must be the same. Please correct and try again." % (start_date.year, end_date.year))
                    return
                
                # Ensure that all of the user-specified files and paths exist, and are well-formed.
                if self.filePathChecker() == 'ok':

                    # Ensure that we pass the correct value for the lightning fire holdover lookback time.
                    if self.__ltg_fire_holdover_lookback_time.get() == "Automatic (DC-dependent)":
                        int_ltg_fire_holdover_lookback_time = -1
                    else:
                        # ASSUMPTION: self.__ltg_fire_holdover_lookback_time.get() will successfully be cast as an integer value.
                        int_ltg_fire_holdover_lookback_time = int(self.__ltg_fire_holdover_lookback_time.get())
                    
                    # If the FOP system state DB is empty, we need to set the single-day prediction date to be one from the currently-
                    # desired year we want to generate maps and predictions for. This is essentially an additional validation check.
                    if pd.isnull(fop_system_state_db_mindate):
                        self.__date_to_predict_for = start_date
                        self.date_to_predict_for_label2.config(text=self.__date_to_predict_for.strftime("%Y-%m-%d"))
                        self.__config.set('ApplicationSettings', 'date_to_predict_for', self.__date_to_predict_for.strftime("%Y-%m-%d"))
                        print("ask_generate_ltg_fop_maps_predictions_for_date_range(): self.__date_to_predict_for set to %s" % self.__date_to_predict_for.strftime("%Y-%m-%d"))
                
                    # If we get here, we can proceed with the map generation.                
                    print("generateMaps(): Generating lightning fire prediction maps and predictions for the date range %s to %s with a lightning fire holdover lookback time of %s and a confidence interval of %s ..." % (start_date.strftime("%Y-%m-%d"),
                                                                                                                                                                                  end_date.strftime("%Y-%m-%d"),
                                                                                                                                                                                  self.__ltg_fire_holdover_lookback_time.get(),
                                                                                                                                                                                  self.__ltg_fire_confidence_interval.get()))
                    self.model_status_label2.config(text='Lightning-caused fire map generation and prediction tool executing...')
                    disable_menu_items_while_subprocess_is_running()
                    
                    pool = multiprocessing.Pool(processes=1)
                    pool.apply_async(func=runGenerateLightningFireMapsPredictionsForDateRange, args=(self.__config,
                                                                                                     start_date,
                                                                                                     end_date,
                                                                                                     int_ltg_fire_holdover_lookback_time,
                                                                                                     float(self.__ltg_fire_confidence_interval.get()),
                                                                                                     self.__display_historical_fires_on_maps.get()),
                                                                                                     callback=ask_generate_ltg_fop_maps_predictions_for_date_range_callback
                                                                                                     )
                    window.destroy()
                
                else:
                    messagebox.showerror("Invalid file and folder paths", "An error was encountered in validating the input/output file and folder paths. Please correct and try again.")
                    window.destroy()

            label1 = Label(window, text="Use this tool to produce a series of Lightning FOP maps and predictions for a date range.", font='Arial 8 bold')
            label1.grid(row=0, columnspan=2)

            if fop_system_state_db_lightning_fop_mindate == "(Lightning FOP not yet performed)":
                label2 = Label(window, text="Earliest Lightning FOP date in the database: (Lightning FOP not yet performed)")
            else:
                label2 = Label(window, text="Earliest Lightning FOP date in the database: %s" % fop_system_state_db_lightning_fop_mindate.strftime("%Y-%m-%d"))            
            label2.grid(row=1, columnspan=2)

            if fop_system_state_db_lightning_fop_maxdate == "(Lightning FOP not yet performed)":
                label3 = Label(window, text="Most recent Lightning FOP date in the database: (Lightning FOP not yet performed)")
            else:
                label3 = Label(window, text="Most recent Lightning FOP date in the database: %s" % fop_system_state_db_lightning_fop_maxdate.strftime("%Y-%m-%d"))
            label3.grid(row=2, columnspan=2)

            label4 = Label(window, text="Start date (YYYY-MM-DD):")
            label4.grid(row=3, column=0)
            entry1 = Entry(window)

            if fop_system_state_db_lightning_fop_mindate != "(Lightning FOP not yet performed)":
                set_text(fop_system_state_db_lightning_fop_mindate.strftime("%Y-%m-%d"), entry1)
                
            entry1.grid(row=4, column=0)
            label5 = Label(window, text="End date (YYYY-MM-DD):")
            label5.grid(row=3, column=1)
            entry2 = Entry(window)

            if fop_system_state_db_lightning_fop_maxdate != "(Lightning FOP not yet performed)":
                set_text(fop_system_state_db_lightning_fop_maxdate.strftime("%Y-%m-%d"), entry2)

            entry2.grid(row=4, column=1)

            button1 = Button(window, text="Generate", command=do_generate_maps_predictions_for_date_range, padx=1, pady=1)
            button1.grid(row=5, column=0, sticky="e")

            button2 = Button(window, text="Close", command=close, padx=1, pady=1)            
            button2.grid(row=5, column=1, sticky="w")

            # Position the new window, lift the new window above the main one, and put it in focus.
            x = self.winfo_x()
            y = self.winfo_y()
            window.geometry("+%d+%d" % (x + 50, y + 35))
            window.focus()
            
        def ask_generate_hmn_maps_predictions_for_date_range_callback(result):
            enable_menu_items_when_subprocess_is_finished()
            if result == 0:
                print("ask_generate_hmn_maps_predictions_for_date_range_callback(): Human FOP maps and predictions generation tool subprocess execution finished. Application ready.")
                self.model_status_label2.config(text='Human FOP maps and predictions generation tool finished successfully. Application ready.')
            else:
                print("ask_generate_hmn_maps_predictions_for_date_range_callback(): Human FOP maps and predictions generation tool subprocess encountered an error during execution.")
                self.model_status_label2.config(text='Human FOP maps and predictions generation tool encountered an error during execution.')
            return
        
        def ask_generate_hmn_fop_maps_predictions_for_date_range():

            # Load up the FOP system state DB.
            fop_system_state_db_df = pd.read_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', header=0, parse_dates=['DATE'])

            # Determine the man and min days in the FOP system state DB for which Human FOP has been performed.
            # Unlike for Lightning FOP, there could be days within the max and min days for which Human FOP has not been performed, and this is okay.
            fop_system_state_db_human_fop_mindate = fop_system_state_db_df.loc[fop_system_state_db_df['HUMAN_FOP_COMPLETED'] == "Y"]['DATE'].min()
            fop_system_state_db_human_fop_maxdate = fop_system_state_db_df.loc[fop_system_state_db_df['HUMAN_FOP_COMPLETED'] == "Y"]['DATE'].max()

            # Ensure that we have sane text labels if the DB is empty.            
            if pd.isnull(fop_system_state_db_human_fop_mindate):
                fop_system_state_db_human_fop_mindate = "(Human FOP not yet performed)"
            
            if pd.isnull(fop_system_state_db_human_fop_maxdate):
                fop_system_state_db_human_fop_maxdate = "(Human FOP not yet performed)"

            window = Toplevel()
            window.title("Generate Human FOP maps and predictions for date range")
            window.resizable(False, False)

            def set_text(text, entry):      
                entry.delete(0, END)
                entry.insert(0, text)
                return
            
            def close():
                window.destroy()
            
            def do_generate_maps_predictions_for_date_range():
                # Perform some data entry checks. First, try parsing start_date and end_date as datetimes.
                try:
                    start_date = datetime.datetime.strptime(entry1.get(), "%Y-%m-%d")
                    end_date = datetime.datetime.strptime(entry2.get(), "%Y-%m-%d") 
                except ValueError as e:
                    print("doGenerateMapsForDateRange(): ValueError caught! ... ", e)
                    messagebox.showerror("Invalid date entered", "Please enter a date in the correct format and try again.")
                    return
                
                # First, if prediction dates exist already in the FOP system state DB, ensure that the start and end dates' years
                # match what is currently in the DB. Use fop_system_state_db_human_fop_mindate.
                if fop_system_state_db_human_fop_mindate != "(Human FOP not yet performed)":
                    
                    if fop_system_state_db_human_fop_mindate.year != start_date.year:                    
                        messagebox.showerror("Invalid year entered", "The year of the start date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (start_date.year, fop_system_state_db_human_fop_mindate.year))
                        return
                
                    if fop_system_state_db_human_fop_mindate.year != end_date.year:                    
                        messagebox.showerror("Invalid year entered", "The year of the end date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (end_date.year, fop_system_state_db_human_fop_mindate.year))
                        return
                
                fop_system_state_db_mindate = fop_system_state_db_df['DATE'].min()
                if not pd.isnull(fop_system_state_db_mindate):

                    if fop_system_state_db_mindate.year != start_date.year:                    
                        messagebox.showerror("Invalid year entered", "The year of the start date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (start_date.year, fop_system_state_db_mindate.year))
                        return

                    if fop_system_state_db_mindate.year != end_date.year:                    
                        messagebox.showerror("Invalid year entered", "The year of the end date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (end_date.year, fop_system_state_db_mindate.year))
                        return
                
                # Next, ensure that the date range is valid.
                if start_date < pd.Timestamp(start_date.year, 3, 1):                  
                    messagebox.showerror("Invalid date entered", "The start date provided cannot be prior to March 1 (the start of the human-caused fire season). Please use a later date and try again.")
                    return
                
                if end_date > pd.Timestamp(end_date.year, 10, 31):                    
                    messagebox.showerror("Invalid date entered", "The end date provided cannot be after October 31 (the end of the human-caused fire season). Please use an earlier date and try again.")
                    return
                
                if start_date > end_date:                    
                    messagebox.showerror("Invalid date entered", "The start date cannot be more recent than the end date. Please correct and try again.")
                    return
                
                # An interesting corner case is if the DB is empty and the user enters dates that do not have the same year.
                # This will not be caught by checking the dates in the DB, because no dates exist there yet.
                if start_date.year != end_date.year:
                    messagebox.showerror("Invalid year entered", "The year of the start date provided (%d) and end date provided (%d) must be the same. Please correct and try again." % (start_date.year, end_date.year))
                    return
                
                # Ensure that all of the user-specified files and paths exist, and are well-formed.
                if self.filePathChecker() == 'ok':

                    # If the FOP system state DB is empty, we need to set the single-day prediction date to be one from the currently-
                    # desired year we want to generate maps and predictions for. This is essentially an additional validation check.
                    if pd.isnull(fop_system_state_db_mindate):
                        self.__date_to_predict_for = start_date
                        self.date_to_predict_for_label2.config(text=self.__date_to_predict_for.strftime("%Y-%m-%d"))
                        self.__config.set('ApplicationSettings', 'date_to_predict_for', self.__date_to_predict_for.strftime("%Y-%m-%d"))
                        print("ask_generate_hmn_fop_maps_predictions_for_date_range(): self.__date_to_predict_for set to %s" % self.__date_to_predict_for.strftime("%Y-%m-%d"))
                
                    # If we get here, we can proceed with the map generation.                
                    print("generateMaps(): Generating human fire prediction maps for the date range %s to %s . . ." % (start_date.strftime("%Y-%m-%d"),
                                                                                                                       end_date.strftime("%Y-%m-%d")))

                    self.model_status_label2.config(text='Human-caused fire map generation and prediction tool executing...')
                    disable_menu_items_while_subprocess_is_running()
                    
                    pool = multiprocessing.Pool(processes=1)
                    pool.apply_async(func=runGenerateHumanFireMapsPredictionsForDateRange,
                                     args=(self.__config,
                                           start_date,
                                           end_date,
                                           float(self.__hmn_fire_confidence_interval.get()),
                                           self.__display_historical_fires_on_maps.get()),
                                     callback=ask_generate_hmn_maps_predictions_for_date_range_callback)
                    window.destroy()
                
                else:
                    messagebox.showerror("Invalid file and folder paths", "An error was encountered in validating the input/output file and folder paths. Please correct and try again.")
                    window.destroy()

            label1 = Label(window, text="Use this tool to produce a series of Human FOP maps and predictions for a date range.", font='Arial 8 bold')
            label1.grid(row=0, columnspan=2)
            
            if fop_system_state_db_human_fop_mindate == "(Human FOP not yet performed)":
                label2 = Label(window, text="Earliest Human FOP date in the database: (Human FOP not yet performed)")
            else:
                label2 = Label(window, text="Earliest Human FOP date in the database: %s" % fop_system_state_db_human_fop_mindate.strftime("%Y-%m-%d"))            
            label2.grid(row=1, columnspan=2)

            if fop_system_state_db_human_fop_maxdate == "(Human FOP not yet performed)":
                label3 = Label(window, text="Most recent Human FOP date in the database: (Human FOP not yet performed)")
            else:
                label3 = Label(window, text="Most recent Human FOP date in the database: %s" % fop_system_state_db_human_fop_maxdate.strftime("%Y-%m-%d"))
            label3.grid(row=2, columnspan=2)

            label4 = Label(window, text="Start date (YYYY-MM-DD):")
            label4.grid(row=3, column=0)
            entry1 = Entry(window)

            if fop_system_state_db_human_fop_mindate != "(Human FOP not yet performed)":
                set_text(fop_system_state_db_human_fop_mindate.strftime("%Y-%m-%d"), entry1)
            
            entry1.grid(row=4, column=0)
            label5 = Label(window, text="End date (YYYY-MM-DD):")
            label5.grid(row=3, column=1)
            entry2 = Entry(window)

            if fop_system_state_db_human_fop_maxdate != "(Human FOP not yet performed)":
                set_text(fop_system_state_db_human_fop_maxdate.strftime("%Y-%m-%d"), entry2)
                
            entry2.grid(row=4, column=1)

            button1 = Button(window, text="Generate", command=do_generate_maps_predictions_for_date_range, padx=1, pady=1)
            button1.grid(row=5, column=0, sticky="e")

            button2 = Button(window, text="Close", command=close, padx=1, pady=1)            
            button2.grid(row=5, column=1, sticky="w")

            # Position the new window, lift the new window above the main one, and put it in focus.
            x = self.winfo_x()
            y = self.winfo_y()
            window.geometry("+%d+%d" % (x + 50, y + 35))
            window.focus()
        
        def run_lightning_fop_callback(result):
            enable_menu_items_when_subprocess_is_finished()
            if result == 0:
                print("run_lightning_fop_callback(): Lightning FOP model subprocess execution finished. Application ready.")
                self.model_status_label2.config(text='Lightning FOP model finished successfully. Application ready.')
            else:
                print("run_lightning_fop_callback(): Lightning FOP model subprocess encountered an error during execution.")
                self.model_status_label2.config(text='Lightning FOP model encountered an error during execution.')
            return
        
        def run_lightning_fop():            
            # Run the Lightning FOP part of the model.

            # First, we need to make sure that the prediction date has the same year as the years currently in the FOP system state DB.
            # Load up the FOP system state DB.
            fop_system_state_db_df = pd.read_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', header=0, parse_dates=['DATE'])

            # For this check, we will simply just find whatever the minimum date is (predicted for or not) and check its year.
            # This is sufficient because either the FOP system state DB is empty, or it contains dates that are all the same year.
            fop_system_state_db_mindate = fop_system_state_db_df['DATE'].min()

            # If we have a valid min date, then perform the check. Otherwise, we assume the DB is empty and continue onward.
            if not pd.isnull(fop_system_state_db_mindate) and (fop_system_state_db_mindate.year != self.__date_to_predict_for.year):                    
                messagebox.showerror("Invalid year entered", "The year of the prediction date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (self.__date_to_predict_for.year, fop_system_state_db_mindate.year))
                return

            # Ensure that the prediction date is within the range for the lightning fire season.
            if self.__date_to_predict_for < pd.Timestamp(self.__date_to_predict_for.year, 5, 1):                    
                messagebox.showerror("Invalid date entered", "The prediction date provided cannot be prior to May 1 (start of the lightning-caused fire season). Please correct and try again.")
                return
            
            if self.__date_to_predict_for > pd.Timestamp(self.__date_to_predict_for.year, 9, 30):                    
                messagebox.showerror("Invalid date entered", "The prediction date provided cannot be after September 30 (end of the lightning-caused fire season). Please correct and try again.")
                return

            # Ensure that we pass the correct value for the lightning fire holdover lookback time.
            if self.__ltg_fire_holdover_lookback_time.get() == "Automatic (DC-dependent)":
                int_ltg_fire_holdover_lookback_time = -1
            else:
                # ASSUMPTION: self.__ltg_fire_holdover_lookback_time.get() will successfully be cast as an integer value.
                int_ltg_fire_holdover_lookback_time = int(self.__ltg_fire_holdover_lookback_time.get())
                
            # Ensure that all of the user-specified files and paths exist, and are well-formed.
            if self.filePathChecker() == 'ok':

                print("FOPApplication.run_lightning_fop(): Creating LightningFOPController object and calling lightningFOPController() in process pool with date %s, a lightning fire holdover lookback time of %s, and a confidence interval of %s . . ." % (self.__date_to_predict_for.strftime("%Y-%m-%d"),
                                                                                                                                                                                                                                                           self.__ltg_fire_holdover_lookback_time.get(),
                                                                                                                                                                                                                                                           self.__ltg_fire_confidence_interval.get()))
                self.model_status_label2.config(text='Lightning FOP model executing...')
                disable_menu_items_while_subprocess_is_running()

                pool = multiprocessing.Pool(processes=1)
                result = pool.apply_async(func=runLightningFOPModel,
                                          args=(self.__config,
                                                self.__date_to_predict_for,
                                                int_ltg_fire_holdover_lookback_time,
                                                float(self.__ltg_fire_confidence_interval.get()),
                                                self.__display_historical_fires_on_maps.get()),
                                          callback=run_lightning_fop_callback)
        
        def run_human_fop_callback(result):
            enable_menu_items_when_subprocess_is_finished()
            if result == 0:
                print("run_human_fop_callback(): Human FOP model subprocess finished executing. Application ready.")
                self.model_status_label2.config(text='Human FOP model finished successfully. Application ready.')
            else:
                print("run_human_fop_callback(): Human FOP model subprocess encountered an error during execution.")
                self.model_status_label2.config(text='Human FOP model encountered an error during execution.')
            return
        
        def run_human_fop():            
            # Run the Human FOP part of the model.

            # First, we need to make sure that the prediction date has the same year as the years currently in the FOP system state DB.
            # Load up the FOP system state DB.
            fop_system_state_db_df = pd.read_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', header=0, parse_dates=['DATE'])

            # For this check, we will simply just find whatever the minimum date is (predicted for or not) and check its year.
            # This is sufficient because either the FOP system state DB is empty, or it contains dates that are all the same year.
            fop_system_state_db_mindate = fop_system_state_db_df['DATE'].min()

            # If we have a valid min date, then perform the check. Otherwise, we assume the DB is empty and continue onward.
            if not pd.isnull(fop_system_state_db_mindate) and (fop_system_state_db_mindate.year != self.__date_to_predict_for.year):                    
                messagebox.showerror("Invalid year entered", "The year of the prediction date provided (%d) must match the current year being used in the FOP system state DB (%d). Please correct, or clear the FOP system state DB, and try again." % (self.__date_to_predict_for.year, fop_system_state_db_mindate.year))
                return
            
            # Next, ensure that the date range is valid; ensure that the date falls within the human-caused fire season.  
            if self.__date_to_predict_for < pd.Timestamp(self.__date_to_predict_for.year, 3, 1):                  
                messagebox.showerror("Invalid date entered", "The start date provided cannot be prior to March 1 (the start of the human-caused fire season). Please use a later date and try again.")
                return
            
            if self.__date_to_predict_for > pd.Timestamp(self.__date_to_predict_for.year, 10, 31):                    
                messagebox.showerror("Invalid date entered", "The end date provided cannot be after October 31 (the end of the human-caused fire season). Please use an earlier date and try again.")
                return
                
            # Ensure that all of the user-specified files and paths exist, and are well-formed.
            if self.filePathChecker() == 'ok':

                print("FOPApplication.run_human_fop(): Creating HumanFOPController object and calling humanFOPController() in process pool with date %s . . ." % (self.__date_to_predict_for.strftime("%Y-%m-%d")))
                self.model_status_label2.config(text='Human FOP model executing...')
                disable_menu_items_while_subprocess_is_running()

                pool = multiprocessing.Pool(processes=1)
                result = pool.apply_async(func=runHumanFOPModel,
                                          args=(self.__config,
                                                self.__date_to_predict_for,
                                                float(self.__hmn_fire_confidence_interval.get()),
                                                self.__display_historical_fires_on_maps.get()),
                                          callback=run_human_fop_callback)
        
        def generate_lightning_fire_arrivals_ci_diagnostic_graph_callback(result):
            enable_menu_items_when_subprocess_is_finished()
            if result == 0:
                print("generate_lightning_fire_arrivals_ci_diagnostic_graph_callback(): Lightning CI diagnostic graph generation subprocess finished executing. Application ready.")
                self.model_status_label2.config(text='Lightning CI diagnostic graph generation tool finished executing. Application ready.')
            else:
                print("generate_lightning_fire_arrivals_ci_diagnostic_graph_callback(): Lightning CI diagnostic graph generation subprocess encountered an error during execution.")
                self.model_status_label2.config(text='Lightning CI diagnostic graph generation tool encountered an error during execution.')
            return
        
        def ask_generate_lightning_fire_arrivals_ci_diagnostic_graph():
            
            # Load up the FOP system state DB to determine the most recent date predicted for.
            fop_system_state_db_df = pd.read_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', header=0, parse_dates=['DATE'])

            # Determine the man and min days in the FOP system state DB for which Lighting FOP has been performed.
            # We can be assured that the range of dates within the max and min days have had Lighting FOP performed.
            fop_system_state_db_lightning_fop_mindate = fop_system_state_db_df.loc[fop_system_state_db_df['LIGHTNING_FOP_COMPLETED'] == "Y"]['DATE'].min()
            fop_system_state_db_lightning_fop_maxdate = fop_system_state_db_df.loc[fop_system_state_db_df['LIGHTNING_FOP_COMPLETED'] == "Y"]['DATE'].max()
            
            if pd.isnull(fop_system_state_db_lightning_fop_mindate):
                messagebox.showinfo("No predictions exist", "Cannot produce CI diagnostics graph because Lightning FOP has not yet been performed for any date.")
                return
            
            if pd.isnull(fop_system_state_db_lightning_fop_maxdate):
                messagebox.showinfo("No predictions exist", "Cannot produce CI diagnostics graph because Lightning FOP has not yet been performed for any date.")
                return
            
            def close():
                window.destroy()
            
            def do_generate_lightning_fire_arrivals_ci_diagnostic_graph():
                
                # Ensure that all of the user-specified files and paths exist, and are well-formed.
                if self.filePathChecker() == 'ok':

                    # Ensure that we pass the correct value for the lightning fire holdover lookback time.
                    if self.__ltg_fire_holdover_lookback_time.get() == "Automatic (DC-dependent)":
                        int_ltg_fire_holdover_lookback_time = -1
                    else:
                        # ASSUMPTION: self.__ltg_fire_holdover_lookback_time.get() will successfully be cast as an integer value.
                        int_ltg_fire_holdover_lookback_time = int(self.__ltg_fire_holdover_lookback_time.get())
                    
                    # Proceed with the CI diagnostic graph generation.
                    print("do_generate_lightning_fire_arrivals_ci_diagnostic_graph(): Generating CI diagnostic graph for dates %s to %s with a lightning fire holdover lookback time of %d and a confidence interval of %s ..." % (fop_system_state_db_lightning_fop_mindate.strftime("%Y-%m-%d"),
                                                                                                                                                                                                                                   fop_system_state_db_lightning_fop_maxdate.strftime("%Y-%m-%d"),
                                                                                                                                                                                                                                   int_ltg_fire_holdover_lookback_time,
                                                                                                                                                                                                                                   self.__ltg_fire_confidence_interval.get()))
                    self.model_status_label2.config(text='Lightning fire arrival CI diagnostic graph generation tool executing...')
                    disable_menu_items_while_subprocess_is_running()
                    
                    pool = multiprocessing.Pool(processes=1)
                    pool.apply_async(func=runGenerateLightningFireArrivalsCIDiagnosticGraph,
                                     args=(self.__config,
                                           fop_system_state_db_lightning_fop_mindate,
                                           fop_system_state_db_lightning_fop_maxdate,
                                           int_ltg_fire_holdover_lookback_time,
                                           float(self.__ltg_fire_confidence_interval.get())),
                                     callback=generate_lightning_fire_arrivals_ci_diagnostic_graph_callback)
                    window.destroy()
                
                else:
                    messagebox.showerror("Invalid file and folder paths", "An error was encountered in validating the input/output file and folder paths. Please correct and try again.")
                    window.destroy()

            window = Toplevel()
            window.title("Generate Lightning FOP arrival CI diagnostics graph")
            window.resizable(False, False)

            label1 = Label(window, text="Use this tool to produce a graph of predicted lightning fire Confidence Intervals (CIs)\nalong with actual historical lightning fire arrivals. This is a useful diagnostic for\nobserving Lightning FOP model performance.", font='Arial 8 bold')
            label1.grid(row=0, columnspan=2)    
            label2 = Label(window, text="A graph will be generated based on a simulation run of all days\nfor which Lightning FOP has been performed in the FOP system state DB.", font='Arial 8 bold')
            label2.grid(row=1, columnspan=2)    
            label3 = Label(window, text="Earliest Lightning FOP date in the database: %s" % fop_system_state_db_lightning_fop_mindate.strftime("%Y-%m-%d"))
            label3.grid(row=2, columnspan=2)
            label4 = Label(window, text="Most recent Lightning FOP date in the database: %s" % fop_system_state_db_lightning_fop_maxdate.strftime("%Y-%m-%d"))
            label4.grid(row=3, columnspan=2)

            button1 = Button(window, text="Generate", command=do_generate_lightning_fire_arrivals_ci_diagnostic_graph, padx=1, pady=1)
            button1.grid(row=4, column=0, sticky="e")

            button2 = Button(window, text="Close", command=close, padx=1, pady=1)            
            button2.grid(row=4, column=1, sticky="w")

            # Position the new window, lift the new window above the main one, and put it in focus.
            x = self.winfo_x()
            y = self.winfo_y()
            window.geometry("+%d+%d" % (x + 50, y + 35))
            window.focus()
        
        def generate_human_fire_arrivals_ci_diagnostic_graph_callback(result):
            enable_menu_items_when_subprocess_is_finished()
            if result == 0:
                print("generate_human_fire_arrivals_ci_diagnostic_graph_callback(): Human CI diagnostic graph generation subprocess finished executing. Application ready.")
                self.model_status_label2.config(text='Human CI diagnostic graph generation tool finished executing. Application ready.')
            else:
                print("generate_human_fire_arrivals_ci_diagnostic_graph_callback(): Human CI diagnostic graph generation subprocess encountered an error during execution.")
                self.model_status_label2.config(text='Human CI diagnostic graph generation tool encountered an error during execution.')
            return
        
        def ask_generate_human_fire_arrivals_ci_diagnostic_graph():
            
            # Load up the FOP system state DB to determine the dates for which Human FOP has been performed.
            fop_system_state_db_df = pd.read_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', header=0, parse_dates=['DATE'])

            # Determine the man and min days in the FOP system state DB for which Human FOP has been performed.
            # Unlike for Lightning FOP, there could be days within the max and min days for which Human FOP has not been performed, and this is okay.
            fop_system_state_db_human_fop_mindate = fop_system_state_db_df.loc[fop_system_state_db_df['HUMAN_FOP_COMPLETED'] == "Y"]['DATE'].min()
            fop_system_state_db_human_fop_maxdate = fop_system_state_db_df.loc[fop_system_state_db_df['HUMAN_FOP_COMPLETED'] == "Y"]['DATE'].max()
            
            if pd.isnull(fop_system_state_db_human_fop_mindate):
                messagebox.showinfo("No predictions exist", "Cannot produce CI diagnostics graph because Human FOP has not yet been performed for any date.")
                return
            
            if pd.isnull(fop_system_state_db_human_fop_maxdate):
                messagebox.showinfo("No predictions exist", "Cannot produce CI diagnostics graph because Human FOP has not yet been performed for any date.")
                return
            
            def close():
                window.destroy()
            
            def do_generate_human_fire_arrivals_ci_diagnostic_graph():
                
                # Ensure that all of the user-specified files and paths exist, and are well-formed.
                if self.filePathChecker() == 'ok':
                    
                    # Proceed with the CI diagnostic graph generation.
                    print("do_generate_human_fire_arrivals_ci_diagnostic_graph(): Generating CI diagnostic graph with a confidence interval of %s%% ..." % (self.__hmn_fire_confidence_interval.get()))
                    self.model_status_label2.config(text='Human fire arrival CI diagnostic graph generation tool executing...')
                    disable_menu_items_while_subprocess_is_running()
                    
                    pool = multiprocessing.Pool(processes=1)
                    pool.apply_async(func=runGenerateHumanFireArrivalsCIDiagnosticGraph,
                                     args=(self.__config,
                                           list(fop_system_state_db_df.loc[fop_system_state_db_df['HUMAN_FOP_COMPLETED'] == "Y"]['DATE']),
                                           float(self.__hmn_fire_confidence_interval.get())),
                                     callback=generate_human_fire_arrivals_ci_diagnostic_graph_callback)
                    window.destroy()                
                else:
                    messagebox.showerror("Invalid file and folder paths", "An error was encountered in validating the input/output file and folder paths. Please correct and try again.")
                    window.destroy()

            window = Toplevel()
            window.title("Generate Human FOP arrival CI diagnostics graph")
            window.resizable(False, False)

            label1 = Label(window, text="Use this tool to produce a graph of predicted human-caused fire Confidence Intervals (CIs)\nalong with actual historical human-caused fire arrivals. This is a useful diagnostic for\nobserving Human FOP model performance.", font='Arial 8 bold')
            label1.grid(row=0, columnspan=2)    
            label2 = Label(window, text="A graph will be generated based on a simulation run of all days\nfor which Human FOP has been performed in the FOP system state DB.", font='Arial 8 bold')
            label2.grid(row=1, columnspan=2)    
            label3 = Label(window, text="Earliest Human FOP date in the database: %s" % fop_system_state_db_human_fop_mindate.strftime("%Y-%m-%d"))
            label3.grid(row=2, columnspan=2)
            label4 = Label(window, text="Most recent Human FOP date in the database: %s" % fop_system_state_db_human_fop_maxdate.strftime("%Y-%m-%d"))
            label4.grid(row=3, columnspan=2)

            button1 = Button(window, text="Generate", command=do_generate_human_fire_arrivals_ci_diagnostic_graph, padx=1, pady=1)
            button1.grid(row=4, column=0, sticky="e")

            button2 = Button(window, text="Close", command=close, padx=1, pady=1)            
            button2.grid(row=4, column=1, sticky="w")

            # Position the new window, lift the new window above the main one, and put it in focus.
            x = self.winfo_x()
            y = self.winfo_y()
            window.geometry("+%d+%d" % (x + 50, y + 35))
            window.focus()

        def show_about_box():            

            window = Toplevel()
            window.title("About Alberta FOP Application")
            window.resizable(False, False)            

            alberta_logo_label = Label(window, bg="grey", borderwidth=2,
                                       highlightcolor="grey", highlightbackground="grey",
                                       relief="flat")
            alberta_logo_label.image = ImageTk.PhotoImage(file=ALBERTA_LOGO_FILE)
            alberta_logo_label['image'] = alberta_logo_label.image
            alberta_logo_label.grid(row=0, sticky="n")

            label1 = Label(window,
                           text=("This FOP Application implements lightning fire occurrence prediction\n"
                                 "models by Dr. Wotton of the University of Toronto, and human fire\n"
                                 "occurrence prediction models by Dr. Woolford of Western University.\n"
                                 ),
                           anchor="e")
            label1.grid(row=1)

            label2 = Label(window,
                           text="Government of Alberta, 2019.\n",
                           anchor="e",
                           font="Arial 9 bold")
            label2.grid(row=2)  

            def close():
                window.destroy()

            button1 = Button(window, text="Close", command=close, padx=1, pady=1)
            button1.grid(row=3)

            # Position the new window, lift the new window above the main one, and put it in focus.
            x = self.winfo_x()
            y = self.winfo_y()
            window.geometry("+%d+%d" % (x + 75, y + 35))
            window.focus()
        
        # Menu bar; File menu.
        self.__menu = Menu(self)
        self.__file = Menu(self.__menu, tearoff=False)
        self.__file.add_command(label="Load raw weather data input...", command=ask_load_raw_weather_data_input)
        self.__file.add_command(label="Load raw lightning strike data input...", command=ask_load_raw_lightning_strike_data_input)
        self.__file.add_command(label="Load historical fire data input...", command=ask_choose_historical_fire_data_file)
        self.__file.add_command(label="Choose intermediate output files location...", command=ask_choose_intermediate_output_files_path)
        self.__file.add_command(label="Choose prediction output files location...", command=ask_choose_prediction_output_files_path)
        self.__file.add_command(label="Choose prediction maps output location...", command=ask_choose_prediction_maps_output_path)
        self.__file.add_command(label="Exit", command=_exit)
        self.__menu.add_cascade(label="File", menu=self.__file)
        
        # Tools menu.
        self.__tools = Menu(self.__menu, tearoff=False)
        self.__tools.add_command(label="Clear FOP system state DB and cumulative probability files...", command=ask_clear_fop_system_state_db)
        self.__tools.add_command(label="Generate Human FOP maps and predictions for date range...", command=ask_generate_hmn_fop_maps_predictions_for_date_range)   
        self.__tools.add_command(label="Generate Lightning FOP maps and predictions for date range...", command=ask_generate_ltg_fop_maps_predictions_for_date_range)        
        self.__tools.add_command(label="Generate Human FOP arrivals CI diagnostic graph...", command=ask_generate_human_fire_arrivals_ci_diagnostic_graph)
        self.__tools.add_command(label="Generate Lightning FOP arrivals CI diagnostic graph...", command=ask_generate_lightning_fire_arrivals_ci_diagnostic_graph)        
        self.__menu.add_cascade(label="Tools", menu=self.__tools)

        # Options menu.
        self.__options = Menu(self.__menu, tearoff=False)
        self.__options.add_command(label="Set single-day prediction date...", command=ask_set_prediction_date)
        self.__options.add_command(label="Set lightning fire holdover lookback time...", command=ask_set_ltg_fire_holdover_lookback_time)
        self.__options.add_command(label="Set FOP confidence intervals...", command=ask_set_fire_confidence_intervals)
        self.__options.add_checkbutton(label="Use historical fire data and display on maps",
                                       onvalue=True,
                                       offvalue=False,
                                       variable=self.__display_historical_fires_on_maps,
                                       command=set_historical_fire_data_state)
        self.__menu.add_cascade(label="Options", menu=self.__options)
        
        # Run menu.
        self.__run = Menu(self.__menu, tearoff=False)
        self.__run.add_command(label="Run Human FOP model", command=run_human_fop)
        self.__run.add_command(label="Run Lightning FOP model", command=run_lightning_fop)
        self.__menu.add_cascade(label="Run", menu=self.__run)

        # About menu.
        self.__about = Menu(self.__menu, tearoff=False)
        self.__about.add_command(label="About...", command=show_about_box)
        self.__menu.add_cascade(label="About", menu=self.__about)         

        # Add the menubar to the GUI.
        self.config(menu=self.__menu)

        # Top frame, left side.
        self.top_frame = Frame(self)

        self.raw_weather_data_input_label1 = Label(self.top_frame, text="Path to the raw weather data file:", font='Arial 10 bold')
        self.raw_weather_data_input_label1.grid(row=0, column=1, sticky="w")
        self.raw_weather_data_input_label2 = Label(self.top_frame, text=self.__config.get('FilePathsAndLocations', 'ltg_input_raw_weather_data_file'), borderwidth=2, relief="groove")
        self.raw_weather_data_input_label2.grid(row=1, column=1, sticky="w")

        self.raw_lightning_strike_data_input_label1 = Label(self.top_frame, text="Path to the raw lightning strike data file:", font='Arial 10 bold')
        self.raw_lightning_strike_data_input_label1.grid(row=2, column=1, sticky="w")
        self.raw_lightning_strike_data_input_label2 = Label(self.top_frame, text=self.__config.get('FilePathsAndLocations', 'ltg_input_raw_lightning_strike_data_file'), borderwidth=2, relief="groove")
        self.raw_lightning_strike_data_input_label2.grid(row=3, column=1, sticky="w")

        self.ltg_historical_lightning_fire_data_file_label1 = Label(self.top_frame, text="Path to the historical fire data input file:", font='Arial 10 bold')
        self.ltg_historical_lightning_fire_data_file_label1.grid(row=4, column=1, sticky="w")
        self.ltg_historical_lightning_fire_data_file_label2 = Label(self.top_frame, text=self.__config.get('FilePathsAndLocations', 'ltg_historical_lightning_fire_data_file'), borderwidth=2, relief="groove")
        self.ltg_historical_lightning_fire_data_file_label2.grid(row=5, column=1, sticky="w")

        self.intermediate_output_files_path_label1 = Label(self.top_frame, text="Path to the intermediate output files location:", font='Arial 10 bold')
        self.intermediate_output_files_path_label1.grid(row=6, column=1, sticky="w")
        self.intermediate_output_files_path_label2 = Label(self.top_frame, text=self.__config.get('FilePathsAndLocations', 'ltg_intermediate_data_folder'), borderwidth=2, relief="groove")
        self.intermediate_output_files_path_label2.grid(row=7, column=1, sticky="w")

        self.prediction_output_files_path_label1 = Label(self.top_frame, text="Path to the prediction data output files location:", font='Arial 10 bold')
        self.prediction_output_files_path_label1.grid(row=8, column=1, sticky="w")
        self.prediction_output_files_path_label2 = Label(self.top_frame, text=self.__config.get('FilePathsAndLocations', 'ltg_prediction_output_data_folder'), borderwidth=2, relief="groove")
        self.prediction_output_files_path_label2.grid(row=9, column=1, sticky="w")

        self.prediction_maps_output_path_label1 = Label(self.top_frame, text="Path to the prediction maps output location:", font='Arial 10 bold')
        self.prediction_maps_output_path_label1.grid(row=10, column=1, sticky="w")
        self.prediction_maps_output_path_label2 = Label(self.top_frame, text=self.__config.get('FilePathsAndLocations', 'ltg_prediction_output_maps_folder'), borderwidth=2, relief="groove")
        self.prediction_maps_output_path_label2.grid(row=11, column=1, sticky="w")

        # Top frame, left side.
        self.date_to_predict_for_label1 = Label(self.top_frame, text="Date to produce single-day prediction for:", font='Arial 10 bold')
        self.date_to_predict_for_label1.grid(row=0, column=2, sticky="w")
        self.date_to_predict_for_label2 = Label(self.top_frame, text=self.__config.get('ApplicationSettings', 'date_to_predict_for'), borderwidth=2, relief="groove")
        self.date_to_predict_for_label2.grid(row=1, column=2, sticky="w")

        self.lightning_fire_holdover_lookback_time_label1 = Label(self.top_frame, text="Lightning fire holdover lookback time (days):", font='Arial 10 bold')
        self.lightning_fire_holdover_lookback_time_label1.grid(row=2, column=2, sticky="w")
        self.lightning_fire_holdover_lookback_time_label2 = Label(self.top_frame, text=self.__config.get('ApplicationSettings', 'ltg_fire_holdover_lookback_time'), borderwidth=2, relief="groove")
        self.lightning_fire_holdover_lookback_time_label2.grid(row=3, column=2, sticky="w")

        self.lightning_fire_confidence_interval_label1 = Label(self.top_frame, text="Lightning fire confidence interval:", font='Arial 10 bold')
        self.lightning_fire_confidence_interval_label1.grid(row=4, column=2, sticky="w")
        self.lightning_fire_confidence_interval_label2 = Label(self.top_frame, text=self.__config.get('ApplicationSettings', 'ltg_fire_confidence_interval') + '%', borderwidth=2, relief="groove")
        self.lightning_fire_confidence_interval_label2.grid(row=5, column=2, sticky="w")

        self.human_fire_confidence_interval_label1 = Label(self.top_frame, text="Human fire confidence interval:", font='Arial 10 bold')
        self.human_fire_confidence_interval_label1.grid(row=6, column=2, sticky="w")
        self.human_fire_confidence_interval_label2 = Label(self.top_frame, text=self.__config.get('ApplicationSettings', 'hmn_fire_confidence_interval') + '%', borderwidth=2, relief="groove")
        self.human_fire_confidence_interval_label2.grid(row=7, column=2, sticky="w")

        # Add the model status labels here so that they can be referenced by callback functions.        
        self.model_status_label1 = Label(self.top_frame, text="Model execution status:", font='Arial 10 bold')
        self.model_status_label1.grid(row=8, column=2, sticky="w")
        self.model_status_label2 = Label(self.top_frame, text='Application ready.', borderwidth=2, relief="groove")
        self.model_status_label2.grid(row=9, column=2, sticky="w")
        
        self.top_frame.grid(sticky="w", padx=1, pady=1)

        # Bottom frame.
        self.bottom_frame = Frame(self)
        
        self.textbox_stdout_scrollbar = Scrollbar(self.bottom_frame)
        self.textbox_stdout_scrollbar.grid(row=0, column=2, sticky="nws")
        self.textbox_stdout = Text(self.bottom_frame, wrap='word', height=15, width=150,
                                   yscrollcommand=self.textbox_stdout_scrollbar.set, bg="black",
                                   fg="salmon", font="Courier 10 bold", borderwidth=2,
                                   highlightcolor="gray", highlightbackground="gray",
                                   relief="groove")
        self.textbox_stdout.grid(row=0, column=1, sticky="w", padx=1, pady=1)
        self.textbox_stdout_scrollbar.config(command=self.textbox_stdout.yview)

        old_stdout = sys.stdout
        sys.stdout = StdoutRedirect(self.textbox_stdout)

        self.bottom_frame.grid()
        self.lift()
        self.focus()

        # Set the state of any last GUI widgets before we declare the application ready.
        set_historical_fire_data_state()

        print("FOPApplication.__init__(): Application ready.")
    
    def clearSystemStateDB(self):
        """ This method attempts to open up the FOP system state DB and clears it; otherwise, creates a new DB file. """

        # Check if the FOP system state DB exists; if it doesn't, create it and set it up as blank.
        if os.path.isfile(FOP_SYSTEM_STATE_DB_PATH):
            try:
                os.remove(FOP_SYSTEM_STATE_DB_PATH)
            except OSError:
                messagebox.showerror("Error deleting DB file", "There was an issue attempting to delete the FOP system state DB file.\nEnsure this file is not open in another program and try again.")
                return

        # Create a blank FOP system state DB dataframe.
        fop_system_state_db_df = pd.DataFrame(columns=FOPConstantsAndFunctions.FOP_SYSTEM_STATE_DB_HEADERS)
        fop_system_state_db_df.set_index('DATE', inplace=True)

        # Write the fresh dataframe to disk.
        fop_system_state_db_df.to_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', index=True)

        # Clear the saved computed probabilities and expected values files for Human FOP.
        if os.path.isfile(HMN_CUMULATIVE_PROBS_EXPVALS_PATH):
            try:
                os.remove(HMN_CUMULATIVE_PROBS_EXPVALS_PATH)
            except OSError:
                messagebox.showerror("Error deleting file", "There was an issue attempting to delete the saved Human FOP cumulative probabilities and expected values file.\nEnsure this file is not open in another program and try again.")
                return
        
        # Clear the saved computed probabilities and expected values files for Lightning FOP.
        if os.path.isfile(LTG_CUMULATIVE_PROBS_PATH):
            try:
                os.remove(LTG_CUMULATIVE_PROBS_PATH)
            except OSError:
                messagebox.showerror("Error deleting file", "There was an issue attempting to delete the saved Lightning FOP cumulative arrivals and holdovers probabilities file.\nEnsure this file is not open in another program and try again.")
                return
        
        # Create an empty cumulative Human FOP probabilities and expected values file.
        # We do not need to create an empty cumulative arrivals and holdovers probabilities file for Lightning FOP because
        # that method uses Python's built-in CSV library and not pandas.
        hmn_cumulative_probs_expvals_df = pd.DataFrame(columns=FOPConstantsAndFunctions.HMN_PROBABILITIES_EXPECTED_VALUES_HEADERS)
        hmn_cumulative_probs_expvals_df.to_csv(HMN_CUMULATIVE_PROBS_EXPVALS_PATH, sep=',', index=False)

        print("FOPApplication.clearSystemStateDB(): FOP system state DB cleared, and saved computed probabilities and expected values files deleted.")
        return
    
    def filePathChecker(self):
        """ This method performs a check to ensure that the input files and paths exist and are well-formed. """

        if not os.path.isfile(FOP_SYSTEM_STATE_DB_PATH):
            messagebox.showerror("FOP system state DB does not exist", "There was an issue attempting to read the FOP system state DB.\nUse the FOP system state DB clearing tool to initialize the DB and try again.")
            return
        elif not os.path.isfile(self.__config.get('FilePathsAndLocations', r'ltg_input_raw_weather_data_file')):
            messagebox.showerror("Invalid path entered", "Please ensure that the path to the raw weather input data file is correct and try again.")
            return
        elif not os.path.isfile(self.__config.get('FilePathsAndLocations', r'ltg_input_raw_lightning_strike_data_file')):
            messagebox.showerror("Invalid path entered", "Please ensure that the path to the raw lightning strike input data file is correct and try again.")
            return
        elif not os.path.isdir(self.__config.get('FilePathsAndLocations', r'ltg_intermediate_data_folder')):
            messagebox.showerror("Invalid path entered", "Please ensure that the path to the intermediate data folder is correct and try again.")
            return
        elif not os.path.isdir(self.__config.get('FilePathsAndLocations', r'ltg_prediction_output_data_folder')):
            messagebox.showerror("Invalid path entered", "Please ensure that the path to the prediction data output folder is correct and try again.")
            return
        elif not os.path.isdir(self.__config.get('FilePathsAndLocations', r'ltg_prediction_output_maps_folder')):
            messagebox.showerror("Invalid path entered", "Please ensure that the path to the prediction maps output folder is correct and try again.")
            return
        
        # If we are to use and display historical fire data, then ensure the file path exists; otherwise, we can skip this step.
        if self.__display_historical_fires_on_maps.get() is True:
            if not os.path.isfile(self.__config.get('FilePathsAndLocations', r'ltg_historical_lightning_fire_data_file')):
                messagebox.showerror("Invalid path entered", "Please ensure that the path to the historical lightning fire arrivals file is correct and try again.")
                return            
            print("filePathChecker(): Using historical data and displaying on maps. . .")
        else:            
            print("filePathChecker(): Do not use historical data nor display it on maps. . .")

        # If we've made it here, we've confirmed that all of the paths exist and are well-formed.
        print("filePathChecker(): File and directory paths and checks are OK.")
        return 'ok'
    
        
def make_menu():
    if "model_run" not in st.session_state:
        st.session_state.model_run = False
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = None
    if "raw_weather" not in st.session_state:
        st.session_state.raw_weather = None
    if "lightning" not in st.session_state:
        st.session_state.lightning = None
    if "history" not in st.session_state:
        st.session_state.history = None
    if 'options' not in st.session_state:
        st.session_state.options = None
    if 'interval' not in st.session_state:
        st.session_state.interval = None
    if 'show_outputs' not in st.session_state:
        st.session_state.show_outputs = False
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'lookback' not in st.session_state:
        st.session_state.lookback = None
    if "end_date" not in st.session_state:
        st.session_state.end_date = None
    if "use_range" not in st.session_state:
        st.session_state.use_range = None

    st.sidebar.title("Model Parameters")   
    choices = ("Select a model","Human", "Lightning")
    model = st.sidebar.selectbox("Select a model", choices)
    if model:
        st.session_state.model = model 
    checkbox_value_range = st.sidebar.checkbox("Use Date Range")
    if checkbox_value_range:
        st.session_state.use_range = True
        selected_date = st.sidebar.date_input("Select a start date", datetime.date.today())
        if selected_date:
            st.session_state.selected_date = selected_date
        end_date = st.sidebar.date_input("Select an end date", datetime.date.today())
        if end_date >= selected_date:
            st.session_state.end_date = end_date
        else:
            st.warning("Please select a date after your selected date")
    else:
        selected_date = st.sidebar.date_input("Set Single Day Prediction Date", datetime.date.today())
        if selected_date:
            st.session_state.selected_date = selected_date
    interval = st.sidebar.number_input("Select a confidence interval",min_value=50, max_value=99, value=95,step=5)
    if interval:
        st.session_state.interval = interval
    if st.session_state.model == 'Lightning':
        lookback = st.sidebar.number_input("Select a lightning fire holdover lookback time",min_value=0, max_value=28, value=12)
        if lookback:
            st.session_state.lookback = lookback

    raw_weather_file = st.file_uploader("Load raw weather data input...", type=["csv", "txt"])
    if raw_weather_file:
        file_contents = raw_weather_file .read()
        with open("temp_weather.csv", "w") as temp_file:
            temp_file.write(file_contents.decode("utf-8"))
        st.session_state.raw_weather = "temp_weather.csv"

    history_file = st.file_uploader("Load historical fire data input...", type=["csv", "txt"])
    if history_file:
        file_contents =  history_file.read()
        with open("temp_history.csv", "w") as temp_file:
            temp_file.write(file_contents.decode("utf-8"))
        st.session_state.history = "temp_history.csv"
    
    if st.session_state.model == 'Lightning':
        lightning_strike_file = st.file_uploader("Load lightning strike data input...", type=["csv", "txt"])
        if lightning_strike_file:
            file_contents = lightning_strike_file.read()
            with open("temp_lightning.csv", "w") as temp_file:
                temp_file.write(file_contents.decode("utf-8"))
            st.session_state.lightning = "temp_lightning.csv"

    if st.sidebar.button("Run"):
        st.session_state.model_run = True
        st.session_state.show_outputs = False
        

def run_human_fop_model( __config,folder_path):
    try:
        if st.session_state.selected_date and not st.session_state.show_outputs:
            __date_to_predict_for_str = st.session_state.selected_date.strftime("%Y-%m-%d")
            __date_to_predict_for = datetime.datetime.strptime(__date_to_predict_for_str, "%Y-%m-%d")               
            __hmn_fire_confidence_interval = st.session_state.interval
            __display_historical_fires_on_maps = 'True'
            with st.spinner("Running Human FOP Model..."):
                clear_files_except_specific_folders(folder_path)
                pool = multiprocessing.Pool(processes=1)
                if st.session_state.use_range:
                    __end_date_str = st.session_state.end_date.strftime("%Y-%m-%d")
                    __end_date = datetime.datetime.strptime(__end_date_str, "%Y-%m-%d")   
                    result = pool.apply_async(func=runGenerateHumanFireMapsPredictionsForDateRange,
                    args=(__config,
                       __date_to_predict_for,
                        __end_date,
                        float(__hmn_fire_confidence_interval),
                         __display_historical_fires_on_maps,st.session_state.raw_weather,st.session_state.history
                        ))

                #no date range:
                else:
                    result = pool.apply_async(func=runHumanFOPModel,
                            args=(__config,
                                __date_to_predict_for,
                                float(__hmn_fire_confidence_interval),
                                __display_historical_fires_on_maps,
                                st.session_state.raw_weather,
                                st.session_state.history))

                result.get()
                st.session_state.show_outputs = True
    except ValueError as e:
        st.warning("Raw weather data columns do not match what is expected.")
    except Exception as e:
        st.warning("The provided date does not exist in the raw weather dataset. Please provide a more up-to-date raw weather data file or adjust the prediction date and try again.")




def get_png_files_in_folder(folder_path):
    png_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
    return png_files

def show_outputs(folder_path):
    png_files = get_png_files_in_folder(folder_path)
    if png_files:
        options = st.multiselect(
        'Which map(s) do you want displayed?',
        png_files)
        st.session_state.options = options
        show(folder_path)
    else:
        st.write("No output created.")


def show(folder_path):
    for idx, png_file in enumerate(st.session_state.options):
        with open(os.path.join(folder_path, png_file), 'rb') as f:
            png_image = f.read()
            st.image(png_image, caption=png_file, use_column_width=True)
            download_button_key = f"download_button_{idx}"
            st.download_button(
                label=f"Download {png_file}",
                data=png_image,
                file_name=png_file,
                key=download_button_key,
            )


def clear_files_except_specific_folders(folder_path):
    print("Clearing PNG files in folder:", folder_path)
    try:
        # Iterate over the items in the folder
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            # Check if the item is a file and ends with ".png"
            if os.path.isfile(item_path) and item.lower().endswith('.png'):
                os.remove(item_path)  # Remove the PNG file
                print(f'Removed PNG file: {item_path}')
            elif os.path.isfile(item_path) and item.lower().endswith('.out'):
                os.remove(item_path)

        print('Cleared PNG and OUT files.')

    except Exception as e:
        print(f'An error occurred: {str(e)}')
def run_lightning_model(__config,folder_path):
    if st.session_state.selected_date and not st.session_state.show_outputs:
        __date_to_predict_for_str = st.session_state.selected_date.strftime("%Y-%m-%d")
        __date_to_predict_for = datetime.datetime.strptime(__date_to_predict_for_str, "%Y-%m-%d")
        int_ltg_fire_holdover_lookback_time = st.session_state.lookback
        __ltg_fire_confidence_interval = st.session_state.interval
        __display_historical_fires_on_maps = 'True'
        with st.spinner("Running Lightning FOP Model..."):
            clear_files_except_specific_folders(folder_path)
            pool = multiprocessing.Pool(processes=1)
            if st.session_state.use_range:
                    __end_date_str = st.session_state.end_date.strftime("%Y-%m-%d")
                    __end_date = datetime.datetime.strptime(__end_date_str, "%Y-%m-%d")
                    result = pool.apply_async(func=runGenerateLightningFireMapsPredictionsForDateRange,
                                     args=(__config,
                                            __date_to_predict_for,
                                           __end_date,
                                           int_ltg_fire_holdover_lookback_time,
                                           float(__ltg_fire_confidence_interval),
                        __display_historical_fires_on_maps,
                        st.session_state.raw_weather,
                        st.session_state.lightning,
                        st.session_state.history))


            else:
                result = pool.apply_async(func=runLightningFOPModel,
                        args=(__config,
                            __date_to_predict_for,
                            int_ltg_fire_holdover_lookback_time,
                            float(__ltg_fire_confidence_interval),
                            __display_historical_fires_on_maps,
                            st.session_state.raw_weather,
                            st.session_state.lightning,
                            st.session_state.history))
            result.get()
            st.session_state.show_outputs = True

def clearSystemStateDB():
        """ This method attempts to open up the FOP system state DB and clears it; otherwise, creates a new DB file. """
        # Check if the FOP system state DB exists; if it doesn't, create it and set it up as blank.
        if os.path.isfile(FOP_SYSTEM_STATE_DB_PATH):
            try:
                os.remove(FOP_SYSTEM_STATE_DB_PATH)
            except OSError:
                messagebox.showerror("Error deleting DB file", "There was an issue attempting to delete the FOP system state DB file.\nEnsure this file is not open in another program and try again.")
                return

        # Create a blank FOP system state DB dataframe.
        fop_system_state_db_df = pd.DataFrame(columns=FOPConstantsAndFunctions.FOP_SYSTEM_STATE_DB_HEADERS)
        fop_system_state_db_df.set_index('DATE', inplace=True)
        # Write the fresh dataframe to disk.
        fop_system_state_db_df.to_csv(FOP_SYSTEM_STATE_DB_PATH, sep=',', index=True)
        # Clear the saved computed probabilities and expected values files for Human FOP.
        if os.path.isfile(HMN_CUMULATIVE_PROBS_EXPVALS_PATH):
            try:
                os.remove(HMN_CUMULATIVE_PROBS_EXPVALS_PATH)
            except OSError:
                messagebox.showerror("Error deleting file", "There was an issue attempting to delete the saved Human FOP cumulative probabilities and expected values file.\nEnsure this file is not open in another program and try again.")
                return
        # Clear the saved computed probabilities and expected values files for Lightning FOP.
        if os.path.isfile(LTG_CUMULATIVE_PROBS_PATH):
            try:
                os.remove(LTG_CUMULATIVE_PROBS_PATH)
            except OSError:
                messagebox.showerror("Error deleting file", "There was an issue attempting to delete the saved Lightning FOP cumulative arrivals and holdovers probabilities file.\nEnsure this file is not open in another program and try again.")
                return
        # Create an empty cumulative Human FOP probabilities and expected values file.
        # We do not need to create an empty cumulative arrivals and holdovers probabilities file for Lightning FOP because
        # that method uses Python's built-in CSV library and not pandas.
        hmn_cumulative_probs_expvals_df = pd.DataFrame(columns=FOPConstantsAndFunctions.HMN_PROBABILITIES_EXPECTED_VALUES_HEADERS)
        hmn_cumulative_probs_expvals_df.to_csv(HMN_CUMULATIVE_PROBS_EXPVALS_PATH, sep=',', index=False)

        print("FOPApplication.clearSystemStateDB(): FOP system state DB cleared, and saved computed probabilities and expected values files deleted.")
        return
######################################### ENTRYPOINT #########################################

# Entrypoint for application execution.
if __name__ == "__main__":
    #FOPApplication(None).mainloop()
    # Call the main method.
    # Example: Fetching a configuration value
    st.title('Province of Alberta - Fire Occurrence Prediction')
    st.write('About: This tool employs two models: one for human-caused fires and another for lightning-caused fires. To forecast fires in Alberta, fill in the data below, customize model parameters on the left, and click run when finished.')
    
    st.title('Input')
    __config = configparser.ConfigParser()
    __config.read('config.ini')
    clearSystemStateDB()
    make_menu()

    if st.session_state.model == "Human":
        if (
            st.session_state.model is not None and
            st.session_state.raw_weather is not None and
            st.session_state.history is not None and  
            st.session_state.selected_date is not None and
            st.session_state.model_run == True
        ):
            run_human_fop_model( __config,"intermediate_output")
            show_outputs("intermediate_output")
        else:
            st.warning("Please select files and choose a date.")

    elif st.session_state.model == "Lightning":
        if (
            st.session_state.model is not None and
            st.session_state.raw_weather is not None and
            st.session_state.lightning is not None and
            st.session_state.history is not None and  
            st.session_state.selected_date is not None and
            st.session_state.lookback is not None and
            st.session_state.model_run == True
        ):
            run_lightning_model(__config,"intermediate_output")
            show_outputs("intermediate_output")
        else:
            st.warning("Please select files and choose a date.")
