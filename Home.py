""" This file contains an implementation of a basic GUI for Alberta's Fire Occurrence Prediction (FOP) model.

    It sits on top of - and interfaces with - two "Controller" methods. One for Dr. Wotton's Lightning FOP
    model, and another for Dr. Woolford's Human FOP model.

    This code is written for the UAlberta FOP project, in collaboration with the Government of Alberta
    and the Canadian Forest Service.

    Author: Matthew Ansell
    2019
"""
import traceback
import configparser  # Used to load and save application state.
import datetime
import os
import sys
import multiprocessing
import pandas as pd
# import math
# from tkinter import Tk  # Used as the GUI framework.
# from tkinter import Menu
# from tkinter import Toplevel
# from tkinter import Entry
# from tkinter import Label
# from tkinter import Button
# from tkinter import Frame
# from tkinter import Text
# from tkinter import Scrollbar
# from tkinter import X
# from tkinter import Y
# from tkinter import LEFT
# from tkinter import RIGHT
# from tkinter import BOTH
# from tkinter import TOP
# from tkinter import YES
# from tkinter import END
# from tkinter import BooleanVar
# from tkinter import IntVar
# from tkinter import StringVar
# from tkinter import Radiobutton
# from tkinter import OptionMenu
# from tkinter.filedialog import askopenfilename
# from tkinter.filedialog import askdirectory
# from tkinter.filedialog import asksaveasfilename
# import tkinter.messagebox as messagebox
# from PIL import ImageTk, Image
from lightning import LightningFireOccurrencePrediction
from human import HumanFireOccurrencePrediction
import sys
# import ctypes # To get the custom taskbar logo icon to show up
import traceback # To get exception information from subprocesses
import FOPConstantsAndFunctions
import streamlit as st
from streamlit.components.v1 import html

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

def runHumanFOPModel(config, date_to_predict_for, float_hmn_fire_confidence_interval, display_historical_fires_on_maps, raw_weather_path, history_path):
    #print("in runHumanFOPModel()")
    #print("human_fop")
    human_fop = HumanFireOccurrencePrediction(raw_weather_path,

                                                  config.get('FilePathsAndLocations', r'ltg_intermediate_data_folder'),

                                                  config.get('FilePathsAndLocations', r'ltg_prediction_output_data_folder'),

                                                  config.get('FilePathsAndLocations', r'ltg_prediction_output_maps_folder'),

                                                  history_path

                                                  )
    #print("controller")
    human_fop.humanFOPController(date_to_predict_for.date(),

                                     float_hmn_fire_confidence_interval,

                                     display_historical_fires_on_maps)
    

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
        #print("runGenerateLightningFireArrivalsCIDiagnosticGraph(): Exception occurred in worker subprocess . . .")
        #traceback.print_exc()
        raise Exception
        #return -1  # Use -1 to indicate abnormal subprocess termination.
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
        #print("runGenerateLightningFireArrivalsCIDiagnosticGraph(): Exception occurred in worker subprocess . . .")
        #traceback.print_exc()
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
        #print("runGenerateHumanFireArrivalsCIDiagnosticGraph(): Exception occurred in worker subprocess . . .")
        #traceback.print_exc()
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
        #print("runGenerateHumanFireMapsPredictionsForDateRange(): Exception occurred in worker subprocess . . .")
        #traceback.print_exc()
        #return -1  # Use -1 to indicate abnormal subprocess termination.
        raise Exception
    return 0  # Use 0 to indicate normal subprocess termination
      
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
    if st.session_state.model == "Human":
        st.sidebar.write("Human model predictions should be between March 01 and October 31, of the same year")
    if st.session_state.model == "Lightning":
        st.sidebar.write("Lightning model predictions should be between May 01 and September 30, of the same year")
    checkbox_value_range = st.sidebar.checkbox("Use Date Range")
    if checkbox_value_range:
        st.session_state.use_range = True
        if st.session_state.model != "Select a model":
            selected_date = st.sidebar.date_input("Select a start date", datetime.date.today())
            if selected_date:
                if is_date_in_range(selected_date, st.session_state.model):
                    st.session_state.selected_date = selected_date
                else:
                    st.warning("Please select a start date in fire occurence range")
            end_date = st.sidebar.date_input("Select an end date", datetime.date.today())
            if end_date >= selected_date and end_date.year == selected_date.year :
                if is_date_in_range(end_date, st.session_state.model):
                    st.session_state.end_date = end_date
                else:
                    st.warning("Please select an end date in fire occurence range")
            else:
                st.warning("Please ensure your end date is the same year and after your start date.")
        else:
            st.warning("Please select a model to begin.")
    else:
        st.session_state.use_range = False
        selected_date = st.sidebar.date_input("Set Single Day Prediction Date", datetime.date.today())
        if st.session_state.model != "Select a model":
            if selected_date:
                if is_date_in_range(selected_date, st.session_state.model):
                    st.session_state.selected_date = selected_date
                else:
                    st.warning("Please select a start date in fire occurence range")
        else:
            st.warning("Please select a model to begin.")
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
     #The date range must be between March 01 and October 31 (inclusive), and are for the same year. 
    try:
        if st.session_state.selected_date and not st.session_state.show_outputs:
            __date_to_predict_for_str = st.session_state.selected_date.strftime("%Y-%m-%d")
            __date_to_predict_for = datetime.datetime.strptime(__date_to_predict_for_str, "%Y-%m-%d")               
            __hmn_fire_confidence_interval = st.session_state.interval
            __display_historical_fires_on_maps = 'True'
            with st.spinner("Running Human FOP Model: This may take up to 10 minutes please do not touch the screen"):
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
                if st.session_state.show_outputs:
                    switch_page('Results')
    except ValueError as e:
        st.warning("Raw weather data columns do not match what is expected.")
    except Exception as e:
        st.warning("The provided date does not exist in the raw weather dataset. Please provide a more up-to-date raw weather data file or adjust the prediction date and try again.")
def clear_files_except_specific_folders(folder_path):
    #print("Clearing PNG files in folder:", folder_path)
    try:
        # Iterate over the items in the folder
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            # Check if the item is a file and ends with ".png"
            if os.path.isfile(item_path) and item.lower().endswith('.png'):
                os.remove(item_path)  # Remove the PNG file
                #print(f'Removed PNG file: {item_path}')

        #print('Cleared PNG and OUT files.')

    except Exception as e:
        print(f'An error occurred: {str(e)}')

def run_lightning_model(__config,folder_path):
    try:
        #The date range must be between May 01 and September 30 of the same year. 
        if st.session_state.selected_date and not st.session_state.show_outputs:
            __date_to_predict_for_str = st.session_state.selected_date.strftime("%Y-%m-%d")
            __date_to_predict_for = datetime.datetime.strptime(__date_to_predict_for_str, "%Y-%m-%d")
            int_ltg_fire_holdover_lookback_time = st.session_state.lookback
            __ltg_fire_confidence_interval = st.session_state.interval
            __display_historical_fires_on_maps = 'True'
            with st.spinner("Running Lightning FOP Model: This may take up to 25 minutes please do not touch the screen"):
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
                if st.session_state.show_outputs:
                    switch_page('Results')
    except ValueError as e:
        st.warning("Raw weather data columns do not match what is expected.")
    except Exception as e:
        st.warning("The provided date does not exist in the raw weather dataset. Please provide a more up-to-date raw weather data file or adjust the prediction date and try again.")

def clearSystemStateDB():
        """ This method attempts to open up the FOP system state DB and clears it; otherwise, creates a new DB file. """
        # Check if the FOP system state DB exists; if it doesn't, create it and set it up as blank.
        if os.path.isfile(FOP_SYSTEM_STATE_DB_PATH):
            try:
                os.remove(FOP_SYSTEM_STATE_DB_PATH)
            except Exception as e:
                print(f'An error occurred: {str(e)}')
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
            except Exception as e:
                print(f'An error occurred: {str(e)}')
                return
        # Clear the saved computed probabilities and expected values files for Lightning FOP.
        if os.path.isfile(LTG_CUMULATIVE_PROBS_PATH):
            try:
                os.remove(LTG_CUMULATIVE_PROBS_PATH)
            except Exception as e:
                print(f'An error occurred: {str(e)}')
                return
        # Create an empty cumulative Human FOP probabilities and expected values file.
        # We do not need to create an empty cumulative arrivals and holdovers probabilities file for Lightning FOP because
        # that method uses Python's built-in CSV library and not pandas.
        hmn_cumulative_probs_expvals_df = pd.DataFrame(columns=FOPConstantsAndFunctions.HMN_PROBABILITIES_EXPECTED_VALUES_HEADERS)
        hmn_cumulative_probs_expvals_df.to_csv(HMN_CUMULATIVE_PROBS_EXPVALS_PATH, sep=',', index=False)

        #print("FOPApplication.clearSystemStateDB(): FOP system state DB cleared, and saved computed probabilities and expected values files deleted.")
        return

def switch_page(page_name, timeout_secs=3):
    """
    Switches the page to the given page name

    :param str page_name: name of the page to switch to
    :param int timeout_secs: timeout in seconds
    """

    nav_script = """
        <script type="text/javascript">
            function attempt_nav_page(page_name, start_time, timeout_secs) {
                var links = window.parent.document.getElementsByTagName("a");
                for (var i = 0; i < links.length; i++) {
                    if (links[i].href.toLowerCase().endsWith("/" + page_name.toLowerCase())) {
                        links[i].click();
                        return;
                    }
                }
                var elasped = new Date() - start_time;
                if (elasped < timeout_secs * 1000) {
                    setTimeout(attempt_nav_page, 100, page_name, start_time, timeout_secs);
                } else {
                    alert("Unable to navigate to page '" + page_name + "' after " + timeout_secs + " second(s).");
                }
            }
            window.addEventListener("load", function() {
                attempt_nav_page("%s", new Date(), %d);
            });
        </script>
    """ % (page_name, timeout_secs)
    html(nav_script)

def is_date_in_range(selected_date, model_type):
    year = selected_date.year

    if model_type == "Human":
        start_date = datetime.date(year, 3, 1)
        end_date = datetime.date(year, 10, 31)
    elif model_type == "Lightning":
        # Define the range for the Lightning model
        start_date = datetime.date(year, 5, 1)
        end_date = datetime.date(year, 9, 30)
    else:
        # If model_type is not "Human" or "Lightning," return True for "None"
        return True

    return start_date <= selected_date <= end_date

######################################### ENTRYPOINT #########################################

# Entrypoint for application execution.
if __name__ == "__main__":
    #st.write("In home.py main")
    #FOPApplication(None).mainloop()
    # Call the main method.
    # Example: Fetching a configuration value
    if 'show_outputs' not in st.session_state:
        st.session_state.show_outputs = False
    if st.session_state.show_outputs:
        st.session_state.show_outputs = False
        st.session_state.model_run = False
        st.session_state.selected_date = None
        st.session_state.raw_weather = None
        st.session_state.lightning = None
        st.session_state.history = None
        st.session_state.options = None
        st.session_state.interval = None
        st.session_state.model = None
        st.session_state.lookback = None
        st.session_state.end_date = None
        st.session_state.use_range = None

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
            st.session_state.selected_date is not None
        ):
            if st.session_state.model_run:
                #print("run_human_fop_model()")
                run_human_fop_model( __config,"intermediate_output")
            else:
                st.warning("Click run!")
        else:
            st.warning("Please select files and choose a date.")

    elif st.session_state.model == "Lightning":
        if (
            st.session_state.model is not None and
            st.session_state.raw_weather is not None and
            st.session_state.lightning is not None and
            st.session_state.history is not None and  
            st.session_state.selected_date is not None and
            st.session_state.lookback is not None
        ):
            if st.session_state.model_run:
                run_lightning_model(__config,"intermediate_output")
            else:
                st.warning("Click run!")
        else:
             st.warning("Please select files and choose a date.")
