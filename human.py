""" This file contains a Python harness for Dr. Douglas Woolford's Human Fire Occurrence Prediction (FOP) model.

    It also contains a Controller method that a GUI can interact with to "drive" the Human FOP model.

    This code is written for the UAlberta FOP project, in collaboration with the Government of Alberta
    and the Canadian Forest Service.

    Author: Matthew Ansell
    2019
"""

import os.path  # Used for determining the CWD, and other I/O-related tasks.
import subprocess  # Used for calling Dr. Wotton's compiled exe files.
import pandas as pd  # Used for more complicated (occasionally SQL-like) input / output data processing.
import math  # Used for model calculations.
import datetime  # Used to determine the day of year (Julian), as well as date-based arithmetic.
import geopandas as gpd  # This and the following imports are used for mapping purposes.
import descartes
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from matplotlib import text
import pylab
import matplotlib.dates as mdates
import FOPConstantsAndFunctions
import time  # Time delay for debugging purposes.
from lightning import LightningFireOccurrencePrediction  # Re-use the rawWeatherDataMassager method.
import random
#from matplotlib.dates import MO, TU, WE, TH, FR, SA, SU
import numpy as np
import sys
import streamlit as st
import csv

# Numerical constants.
NO_VALID_DATA_VALUE = -1.0
NUM_SIMULATION_REPLICATIONS = 1000

# Other constants.
USE_SLOPES_MODEL_V2 = True

class HumanFireOccurrencePrediction(object):
    """ This class contains the logic for the Human Fire Occurrence Prediction model itself. """

    def __init__(self,
                 hmn_input_raw_weather_data_file,
                 hmn_intermediate_data_folder,
                 hmn_output_data_folder,
                 hmn_output_maps_folder,
                 hmn_actual_fire_arrivals_file
                ):
    
        # Construct paths to all of the necessary files for the Human FOP flow. Numbered in order of usage for the Human FOP flow.

        # 1. Raw weather data file (path is already constructed, explicit from the GUI).
        self.hmn_input_raw_weather_data_file = hmn_input_raw_weather_data_file
        
        # 2. Massaged weather data file (to be put in the intermediate data folder).
        self.hmn_weather_massaged_output_path = hmn_intermediate_data_folder + '/2_Massaged_Weather.csv'
    
        # 3. Weather interpolation coefficients data file path (to be put in the intermediate data folder).
        self.hmn_weather_interpolation_coefficients_path = hmn_intermediate_data_folder + '/3_weather_interpolation_coefficients'

        # 4. Binned weather data file (to be put in the intermediate data folder).
        self.hmn_weather_binned_output_path = hmn_intermediate_data_folder + '/4_Binned_Weather.csv'

        # 5. Gridded Human FOP probabilities output file path (to be put in the output data folder).
        self.hmn_gridded_predictions_output_path = hmn_output_data_folder + '\\AB-Human_FOP_Grids.out'

        # 6. Human FOP confidence intervals output file path (to be put in the output data folder).
        self.hmn_confidence_intervals_output_path = hmn_output_data_folder + '\\AB-Human_FOP_Predictions.out'

        # Construct paths to the coefficient terms and variables files required by the Human FOP model:

        # Calgary region.
        self.hmn_coefficients_path_calgary = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/calgary'))
       
        self.hmn_coefficients_path_calgary_all_variables = self.hmn_coefficients_path_calgary + '/GRID_Calgary_AllVariables.csv'
        self.hmn_coefficients_path_calgary_all_terms = self.hmn_coefficients_path_calgary + '/Calgary_AllTerms.xlsx'

        # Edson region.
        self.hmn_coefficients_path_edson = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/edson'))
       
        self.hmn_coefficients_path_edson_all_variables = self.hmn_coefficients_path_edson + '/GRID_Edson_AllVariables.csv'
        self.hmn_coefficients_path_edson_all_terms = self.hmn_coefficients_path_edson + '/Edson_AllTerms.xlsx'

        # Fort McMurray region.
        self.hmn_coefficients_path_fort_mcmurray = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/fort_mcmurray'))
       
        self.hmn_coefficients_path_fort_mcmurray_all_variables = self.hmn_coefficients_path_fort_mcmurray + '/GRID_FortMcMurray_AllVariables.csv'
        self.hmn_coefficients_path_fort_mcmurray_all_terms = self.hmn_coefficients_path_fort_mcmurray + '/FortMcMurray_AllTerms.xlsx'

        # Grande Prairie region.
        self.hmn_coefficients_path_grande_prairie = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/grande_prairie'))
       
        self.hmn_coefficients_path_grande_prairie_all_variables = self.hmn_coefficients_path_grande_prairie + '/GRID_GrandePrairie_AllVariables.csv'
        self.hmn_coefficients_path_grande_prairie_all_terms = self.hmn_coefficients_path_grande_prairie + '/GrandePrairie_AllTerms.xlsx'

        # High Level region.
        self.hmn_coefficients_path_high_level = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/high_level'))
       
        self.hmn_coefficients_path_high_level_all_variables = self.hmn_coefficients_path_high_level + '/GRID_HighLevel_AllVariables.csv'
        self.hmn_coefficients_path_high_level_all_terms = self.hmn_coefficients_path_high_level + '/HighLevel_AllTerms.xlsx'

        # Lac la Biche region.
        self.hmn_coefficients_path_lac_la_biche = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/lac_la_biche'))
       
        self.hmn_coefficients_path_lac_la_biche_all_variables = self.hmn_coefficients_path_lac_la_biche + '/GRID_LacLaBiche_AllVariables.csv'
        self.hmn_coefficients_path_lac_la_biche_all_terms = self.hmn_coefficients_path_lac_la_biche + '/LacLaBiche_AllTerms.xlsx'

        # Peace River region.
        self.hmn_coefficients_path_peace_river = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/peace_river'))
       
        self.hmn_coefficients_path_peace_river_all_variables = self.hmn_coefficients_path_peace_river + '/GRID_PeaceRiver_AllVariables.csv'
        self.hmn_coefficients_path_peace_river_all_terms = self.hmn_coefficients_path_peace_river + '/PeaceRiver_AllTerms.xlsx'

        # Rocky Mountain House region.
        self.hmn_coefficients_path_rocky_mountain_house = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/rocky_mountain_house'))
       
        self.hmn_coefficients_path_rocky_mountain_house_all_variables = self.hmn_coefficients_path_rocky_mountain_house + '/GRID_RockyMountainHouse_AllVariables.csv'
        self.hmn_coefficients_path_rocky_mountain_house_all_terms = self.hmn_coefficients_path_rocky_mountain_house + '/RockyMountainHouse_AllTerms.xlsx'

        # Slave Lake region.
        self.hmn_coefficients_path_slave_lake = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/slave_lake'))
       
        self.hmn_coefficients_path_slave_lake_all_variables = self.hmn_coefficients_path_slave_lake + '/GRID_SlaveLake_AllVariables.csv'
        self.hmn_coefficients_path_slave_lake_all_terms = self.hmn_coefficients_path_slave_lake + '/SlaveLake_AllTerms.xlsx'

        # Whitecourt region.
        self.hmn_coefficients_path_whitecourt = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/whitecourt'))
       
        self.hmn_coefficients_path_whitecourt_all_variables = self.hmn_coefficients_path_whitecourt + '/GRID_Whitecourt_AllVariables.csv'
        self.hmn_coefficients_path_whitecourt_all_terms = self.hmn_coefficients_path_whitecourt + '/Whitecourt_AllTerms.xlsx'

        # Slopes region.
        self.hmn_coefficients_path_slopes = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/human/slopes'))
       
        self.hmn_coefficients_path_slopes_all_variables = self.hmn_coefficients_path_slopes + '/GRID_Slopes_AllVariables.csv'
        self.hmn_coefficients_path_slopes_all_terms = self.hmn_coefficients_path_slopes + '/Slopes_AllTerms.xlsx'
    
        # Construct paths to other important files and folders needed by the Human FOP model:

        # Human FOP cumulative expected values and probabilities data file path.
        self.hmn_cumulative_probs_expvals_output_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/hmn_fop_probabilities_output.out'))
        
        # Weather station locations file path.
        self.hmn_weather_station_locations_path = 'resource_files/Alberta_Weather_Stations_2019_new.csv'
        
        # Grid locations file path.
        self.hmn_grid_locations_path = "resource_files/Gridlocations.prn"
        
        # Fishnet NSR file path.
        self.hmn_fishnet_nsr_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/alberta_static.csv'))

        # Alberta basemap shapefile path.
        self.hmn_alberta_basemap_shapefile = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/shapefiles/asrd_mgmt_area/BF_ASRD_MGMT_AREA_POLYGON.shp'))
        
        # Alberta fishnet shapefile path.
        self.hmn_alberta_fishnet_shapefile = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/shapefiles/fishnet/fishnet.shp'))
        
        # Alberta polygon shapefile path.
        self.hmn_alberta_poly_shapefile = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/shapefiles/fishnet/AB_Poly.shp'))

        # Alberta forest area shapefile path.
        self.hmn_alberta_forest_area_shapefile = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'fireoccurrenceprediction/resource_files/shapefiles/fishnet/Forest_Area.shp'))
        
        # FOP system state DB / CSV file path.
        self.fop_system_state_db_path = 'resource_files\\fop_system_state_db.csv'
        
        # Maps output folder path.
        self.hmn_output_maps_folder = hmn_output_maps_folder

        # Actual historical fire arrivals file (for mapping purposes).
        self.hmn_actual_fire_arrivals_file = hmn_actual_fire_arrivals_file

        # Dr. Wotton's C program executable paths.
        # Build the path to the C weather binning executable.
    
    def weatherInterpolationBinnerWrapper(self):
        """ Calls the wrapped weather interpolation and binning tools, feeding it the massaged weather data.
            Here, we use subprocess.call as opposed to subprocess.Popen because subprocess.call
            is blocking; we need the external call to finish before we carry on with other stages of
            the processing flow. """
        st.write("In weatherInterpolationBinnerWrapper()")
        st.write("Doing build")
        subprocess.run([f"{sys.executable}", "lightning/weather/cf-build-AB.py"])
        st.write("Done build and doing use")
        subprocess.run([f"{sys.executable}", "lightning/weather/use_cf2.py"])
        # result2 = subprocess.run([sys.executable, "lightning/weather/use_cf2.py"] capture_output=True, text=True)
        # if result2.returncode != 0:
        #     st.write("Error in the second subprocess call:")
        #     print(result2.stdout)
        #     print(result2.stderr)
        file_path2 = "intermediate_output/3_weather_interpolation_coefficients/CF-dc.ab"
        file_path3 = "intermediate_output/3_weather_interpolation_coefficients/CF-dmc.ab"
        file_path4 = "intermediate_output/3_weather_interpolation_coefficients/CF-fwi.ab"
        file_path1 = "intermediate_output/3_weather_interpolation_coefficients/CF-bui.ab"
        #with open(file_path1, 'r') as file:
            #for line in file:
                #print(line)
        #print("THIS IS CF-dc")
        #with open(file_path2, 'r') as file:
            #for line in file:
                #print(line)
        #print("THIS IS CF-dmc")
        #with open(file_path3, 'r') as file:
            #for line in file:
                #print(line)
        #print("THIS IS CF-fwi.ab")
        #with open(file_path4, 'r') as file:
            #for line in file:
                #print(line)

        
    
    def humanFOPProbabilitiesCalculator(self, date_to_predict_for):
        """ This method computes Human FOP expected values and probabilities per Alberta fishnet cell. """
        # Open the Human FOP cumulative probabilities and expected values file.
        hmn_cumulative_probs_expvals_df = pd.read_csv(self.hmn_cumulative_probs_expvals_output_path, sep=',', parse_dates=['date'])
        hmn_cumulative_probs_expvals_df.columns = FOPConstantsAndFunctions.HMN_PROBABILITIES_EXPECTED_VALUES_HEADERS
        
        # Read in the interpolated and binned weather file.
        interpolated_binned_weather_df = pd.read_csv(self.hmn_weather_binned_output_path, sep=',', header=None)
        interpolated_binned_weather_df.columns = FOPConstantsAndFunctions.INTERPOLATED_BINNED_WEATHER_DATA_HEADERS
        # Read in the Fishnet NSR file.
        hmn_fishnet_nsr_path_df =  pd.read_csv(self.hmn_fishnet_nsr_path, sep=',')

        # Cast the 'fishnet_AB' column as 32-bit integer.
        hmn_fishnet_nsr_path_df['fishnet_AB'] = hmn_fishnet_nsr_path_df['fishnet_AB'].astype('int32')

        # Determine the day of year (Julian) that we are predicting for.
        day_of_year_julian = date_to_predict_for.timetuple().tm_yday

        # Create a dataframe to hold the computed probabilities and expected values.
        self.hmn_fop_probabilities_expected_values_df = pd.DataFrame(columns=FOPConstantsAndFunctions.HMN_PROBABILITIES_EXPECTED_VALUES_HEADERS)

        def do_calculate_probabilities(terms_df, variables_df):        
            # Loop through all of the rows in the variables file and calculate the probabilities and expected values on a per-fishnet ID basis.
            # Load up the Slopes region terms and variables file if we are to use the new version of the Slopes model.
            if USE_SLOPES_MODEL_V2:
                # print("humanFOPProbabilitiesCalculator(): Using Slopes v2 model coefficients . . .")
                slopes_all_terms_df = pd.read_excel(self.hmn_coefficients_path_slopes_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
                slopes_all_variables_df = pd.read_csv(self.hmn_coefficients_path_slopes_all_variables, sep=',')

            i = 0
            for _ , row_variable in variables_df.iterrows():
                i = i + 1
                # if i % 250 == 0:
                    # print("humanFOPProbabilitiesCalculator(): Calculating row #%d. . ." % i)
                
                # Get the NSR (numerical code) for this fishnet.
                nsr_numerical_code = hmn_fishnet_nsr_path_df.loc[hmn_fishnet_nsr_path_df['fishnet_AB'] == row_variable['FISHNET_AB']]['NSR'].values[0]

                # Prepare the terms required for calculating the Human FOP expected value.
                intercept_term = terms_df['INTERCEPT'].index.values[0]
                day_of_year_term = terms_df['DAY_OF_YEAR'].at[day_of_year_julian, 's(DAY_OF_YEAR)']
                spatial_term = terms_df['SPATIAL'].at[row_variable['FISHNET_AB'], 'te(X,Y)']
                # Handle -999.9 value for the interpolated FFMC.
                try:
                    ffmc_term = terms_df['FFMC'].at[round(interpolated_binned_weather_df.loc[((interpolated_binned_weather_df['grid'] == row_variable['FISHNET_AB']) &
                                                                                              (interpolated_binned_weather_df['year'] == date_to_predict_for.year) &
                                                                                              (interpolated_binned_weather_df['month'] == date_to_predict_for.month) &
                                                                                              (interpolated_binned_weather_df['day'] == date_to_predict_for.day))]['ffmc'].values[0], 1), 's(FFMC)']
                except KeyError:
                    # If we except a KeyError, then we were unable to perform a lookup in Dr. Woolford's model for this FFMC value.
                    # Assign the probability and FFMC for this particular cell to be "-1.0".
                    # It will be plotted on our map as a special "No data" datapoint.
                    row_df = pd.DataFrame([[row_variable['FISHNET_AB'],
                                            date_to_predict_for,
                                            day_of_year_julian,
                                            round(terms_df['SPATIAL'].at[row_variable['FISHNET_AB'], 'Y'], 4),
                                            round(terms_df['SPATIAL'].at[row_variable['FISHNET_AB'], 'X'], 4),
                                            row_variable['FOREST_NAME'],
                                            ('Slopes' if row_variable['NATURE_REGION'] in [7, 8, 9, 10, 11, 14, 18] else 'East Boreal' if row_variable['X'] >= -114 else 'West Boreal'),
                                            nsr_numerical_code,
                                            NO_VALID_DATA_VALUE,  # ffmc_interpolated
                                            NO_VALID_DATA_VALUE,  # logit
                                            NO_VALID_DATA_VALUE   # probability
                                         ]])
                
                    row_df.columns = FOPConstantsAndFunctions.HMN_PROBABILITIES_EXPECTED_VALUES_HEADERS
                    self.hmn_fop_probabilities_expected_values_df = self.hmn_fop_probabilities_expected_values_df.append(row_df)
                    continue  # Go to the next grid cell; we are done processing this one.

                # If we have a valid FFMC value that can be looked up, then continue onward with processing this cell.
                dist_road_term = terms_df['DIST_ROAD'].at[(int(round((row_variable['DIST_ROAD'] / 100), 0) * 100)), 's(DIST_ROAD)']
                water_term = terms_df['WATER'].at[round(row_variable['WATER'], 2), 's(WATER)']
                d_1_d_2_term = terms_df['D.1.D.2'].at[round(row_variable['D.1.D.2'], 2), 's(D.1.D.2)']
                wui_term = terms_df['WUI'].at[round(row_variable['WUI'], 2), 's(WUI)']
                wii_term = terms_df['WII'].at[round(row_variable['WII'], 2), 's(WII)']
                inf_term = terms_df['INF'].at[round(row_variable['INF'], 2), 's(INF)']
                logit = (intercept_term +
                         day_of_year_term +
                         spatial_term +
                         ffmc_term +
                         dist_road_term +
                         water_term +
                         d_1_d_2_term +
                         wui_term +
                         wii_term +
                         inf_term
                         )
                
                old_logit = (intercept_term +
                         day_of_year_term +
                         spatial_term +
                         ffmc_term +
                         dist_road_term +
                         water_term +
                         d_1_d_2_term +
                         wui_term +
                         wii_term +
                         inf_term
                         )

                # If we are to use the new version of the Slopes model, then re-calculate the probability for this cell.
                if USE_SLOPES_MODEL_V2 and row_variable['NATURE_REGION'] in [7, 8, 9, 10, 11, 14, 18]:
                    ffmc_term = slopes_all_terms_df['FFMC'].at[round(interpolated_binned_weather_df.loc[((interpolated_binned_weather_df['grid'] == row_variable['FISHNET_AB']) &
                                                                                                         (interpolated_binned_weather_df['year'] == date_to_predict_for.year) &
                                                                                                         (interpolated_binned_weather_df['month'] == date_to_predict_for.month) &
                                                                                                         (interpolated_binned_weather_df['day'] == date_to_predict_for.day))]['ffmc'].values[0], 1), 's(FFMC)']
                    
                    if row_variable['NATURE_REGION'] == 7:
                        day_of_year_term = slopes_all_terms_df['DAY_OF_YEAR'].at[day_of_year_julian, 's(DAY_OF_YEAR):NATURE_REGION7']
                    elif row_variable['NATURE_REGION'] == 8:
                        day_of_year_term = slopes_all_terms_df['DAY_OF_YEAR'].at[day_of_year_julian, 's(DAY_OF_YEAR):NATURE_REGION8']
                    elif row_variable['NATURE_REGION'] == 9:
                        day_of_year_term = slopes_all_terms_df['DAY_OF_YEAR'].at[day_of_year_julian, 's(DAY_OF_YEAR):NATURE_REGION9']
                    elif row_variable['NATURE_REGION'] == 10:
                        day_of_year_term = slopes_all_terms_df['DAY_OF_YEAR'].at[day_of_year_julian, 's(DAY_OF_YEAR):NATURE_REGION10']
                    elif row_variable['NATURE_REGION'] == 11:
                        day_of_year_term = slopes_all_terms_df['DAY_OF_YEAR'].at[day_of_year_julian, 's(DAY_OF_YEAR):NATURE_REGION11']
                    elif row_variable['NATURE_REGION'] == 14:
                        day_of_year_term = slopes_all_terms_df['DAY_OF_YEAR'].at[day_of_year_julian, 's(DAY_OF_YEAR):NATURE_REGION14']
                    elif row_variable['NATURE_REGION'] == 18 and date_to_predict_for.month not in [3, 4]:
                        # If the month we are predicting for is May onward, then set the seasonality effect to be 0.
                        # Do not refer to the s(DAY_OF_YEAR):NATURE_REGION18 column.
                        day_of_year_term = 0
                    
                    static_effects_variables_term = slopes_all_variables_df.loc[row_variable['FISHNET_AB'] == slopes_all_variables_df['FISHNET_AB']]['COMBINED_STATIC_EFFECTS'].values[0]

                    logit = (ffmc_term +
                             day_of_year_term +
                             static_effects_variables_term
                             )
                    
                    if old_logit == logit:
                        ffmc_interp = round(interpolated_binned_weather_df.loc[((interpolated_binned_weather_df['grid'] == row_variable['FISHNET_AB']) &
                                                                                  (interpolated_binned_weather_df['year'] == date_to_predict_for.year) &
                                                                                  (interpolated_binned_weather_df['month'] == date_to_predict_for.month) &
                                                                                  (interpolated_binned_weather_df['day'] == date_to_predict_for.day))]['ffmc'].values[0], 1)
                        # print("cell num: %d, ffmc_interp: %f, day_of_year_julian: %d, NSR: %d, ffmc_term: %f, day_of_year_term: %f, static_effects_variables_term: %f" % (row_variable['FISHNET_AB'], ffmc_interp, day_of_year_julian, row_variable['NATURE_REGION'], ffmc_term, day_of_year_term, static_effects_variables_term))
                        assert(old_logit != logit)
                
                # Calculate the probability for this grid cell using the inverse logit function.
                # If the given cell's natural subregion (NSR) is 18 and we are predicting for a day in March or April, set
                # the probability to be 0.
                if USE_SLOPES_MODEL_V2 and row_variable['NATURE_REGION'] == 18 and date_to_predict_for.month in [3, 4]:
                    probability = 0
                else:
                    probability = math.exp(logit) / (1 + math.exp(logit))
                # Append a new row to the Human FOP expected value and probabilities output file.
                # Column headers:
                # 'fishnet_id', 'date', 'day_of_year', 'latitude', 'longitude', 'region', 'ffmc_interpolated', 'logit', 'probability'
                row_df = pd.DataFrame([[row_variable['FISHNET_AB'],
                                        date_to_predict_for,
                                        day_of_year_julian,
                                        round(terms_df['SPATIAL'].at[row_variable['FISHNET_AB'], 'Y'], 4),
                                        round(terms_df['SPATIAL'].at[row_variable['FISHNET_AB'], 'X'], 4),
                                        row_variable['FOREST_NAME'],
                                        ('Slopes' if row_variable['NATURE_REGION'] in [7, 8, 9, 10, 11, 14, 18] else 'East Boreal' if row_variable['X'] >= -114 else 'West Boreal'),
                                        nsr_numerical_code,
                                        round(interpolated_binned_weather_df.loc[((interpolated_binned_weather_df['grid'] == row_variable['FISHNET_AB']) &
                                                                                  (interpolated_binned_weather_df['year'] == date_to_predict_for.year) &
                                                                                  (interpolated_binned_weather_df['month'] == date_to_predict_for.month) &
                                                                                  (interpolated_binned_weather_df['day'] == date_to_predict_for.day))]['ffmc'].values[0], 1),
                                        round(logit, 12),
                                        round(probability, 12)
                                    ]])
                
                row_df.columns = FOPConstantsAndFunctions.HMN_PROBABILITIES_EXPECTED_VALUES_HEADERS
                self.hmn_fop_probabilities_expected_values_df = self.hmn_fop_probabilities_expected_values_df.append(row_df)
        # Calgary forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the Calgary forest region. . .")
        calgary_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_calgary_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        calgary_all_variables_df = pd.read_csv(self.hmn_coefficients_path_calgary_all_variables, sep=',')
        do_calculate_probabilities(calgary_all_terms_dfs, calgary_all_variables_df)

        # Edson forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the Edson forest region. . .")
        edson_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_edson_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        edson_all_variables_df = pd.read_csv(self.hmn_coefficients_path_edson_all_variables, sep=',')
        do_calculate_probabilities(edson_all_terms_dfs, edson_all_variables_df)

        # Fort McMurray forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the Fort McMurray forest region. . .")
        fort_mcmurray_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_fort_mcmurray_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        fort_mcmurray_all_variables_df = pd.read_csv(self.hmn_coefficients_path_fort_mcmurray_all_variables, sep=',')
        do_calculate_probabilities(fort_mcmurray_all_terms_dfs, fort_mcmurray_all_variables_df)

        # Grande Prairie forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the Grande Prairie forest region. . .")
        grande_prairie_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_grande_prairie_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        grande_prairie_all_variables_df = pd.read_csv(self.hmn_coefficients_path_grande_prairie_all_variables, sep=',')
        do_calculate_probabilities(grande_prairie_all_terms_dfs, grande_prairie_all_variables_df)

        # High Level forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the High Level forest region. . .")
        high_level_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_high_level_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        high_level_all_variables_df = pd.read_csv(self.hmn_coefficients_path_high_level_all_variables, sep=',')
        do_calculate_probabilities(high_level_all_terms_dfs, high_level_all_variables_df)

        # Lac la Biche forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the Lac la Biche forest region. . .")
        lac_la_biche_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_lac_la_biche_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        lac_la_biche_all_variables_df = pd.read_csv(self.hmn_coefficients_path_lac_la_biche_all_variables, sep=',')
        do_calculate_probabilities(lac_la_biche_all_terms_dfs, lac_la_biche_all_variables_df)

        # Peace River forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the Peace River forest region. . .")
        peace_river_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_peace_river_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        peace_river_all_variables_df = pd.read_csv(self.hmn_coefficients_path_peace_river_all_variables, sep=',')
        do_calculate_probabilities(peace_river_all_terms_dfs, peace_river_all_variables_df)

        # Rocky Mountain House forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the Rocky Mountain House forest region. . .")
        rocky_mountain_house_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_rocky_mountain_house_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        rocky_mountain_house_all_variables_df = pd.read_csv(self.hmn_coefficients_path_rocky_mountain_house_all_variables, sep=',')
        do_calculate_probabilities(rocky_mountain_house_all_terms_dfs, rocky_mountain_house_all_variables_df)

        # Slave Lake forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the Slave Lake forest region. . .")
        slave_lake_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_slave_lake_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        slave_lake_all_variables_df = pd.read_csv(self.hmn_coefficients_path_slave_lake_all_variables, sep=',')
        do_calculate_probabilities(slave_lake_all_terms_dfs, slave_lake_all_variables_df)

        # Whitecourt forest region.
        # print("humanFOPProbabilitiesCalculator(): Computing Human FOP probabilities for the Whitecourt forest region. . .")
        whitecourt_all_terms_dfs = pd.read_excel(self.hmn_coefficients_path_whitecourt_all_terms, sheet_name=None, index_col=0, engine='openpyxl')
        whitecourt_all_variables_df = pd.read_csv(self.hmn_coefficients_path_whitecourt_all_variables, sep=',')
        do_calculate_probabilities(whitecourt_all_terms_dfs, whitecourt_all_variables_df)
        
        # Post-probability calculation operations follow below:     

        # Convert the date column to datetime format.
        self.hmn_fop_probabilities_expected_values_df['date'] = pd.to_datetime(self.hmn_fop_probabilities_expected_values_df['date'])
        
        # Output the Human FOP expected values and probabilities for this new prediction run to disk.
        self.hmn_fop_probabilities_expected_values_df.to_csv(self.hmn_gridded_predictions_output_path, sep=',', index=False)

        # Append the new predictions to the cumulative Human FOP expected values and probabilties file.
        hmn_cumulative_probs_expvals_df = hmn_cumulative_probs_expvals_df.append(self.hmn_fop_probabilities_expected_values_df)
        
        # Convert the date column to datetime format.
        hmn_cumulative_probs_expvals_df['date'] = pd.to_datetime(hmn_cumulative_probs_expvals_df['date'])

        # Sort the cumulative Human FOP expected values and probabilties file first by date, and then by fishnet_id.
        hmn_cumulative_probs_expvals_df = hmn_cumulative_probs_expvals_df.sort_values(['date', 'fishnet_id'], ascending=[True, True])

        # Apply rounding operations to specific columns.
        hmn_cumulative_probs_expvals_df['latitude'] = hmn_cumulative_probs_expvals_df['latitude'].apply(lambda x : round(float(x), 4))
        hmn_cumulative_probs_expvals_df['longitude'] = hmn_cumulative_probs_expvals_df['longitude'].apply(lambda x : round(float(x), 4))
        hmn_cumulative_probs_expvals_df['logit'] = hmn_cumulative_probs_expvals_df['logit'].apply(lambda x : round(float(x), 12))
        hmn_cumulative_probs_expvals_df['probability'] = hmn_cumulative_probs_expvals_df['probability'].apply(lambda x : round(float(x), 12))

        # Delete any duplicate rows which may have arisen, in order to maintain integrity of the dataset.
        hmn_cumulative_probs_expvals_df.drop_duplicates(keep='first', inplace=True)

        # Write the updated cumulative Human FOP expected values and probabilties dataframe to disk.
        hmn_cumulative_probs_expvals_df.to_csv(self.hmn_cumulative_probs_expvals_output_path, sep=',', index=False) 

        # We're done!
        return
    
    def humanSimulationConfidenceIntervalGenerator(self, days_to_simulate, hmn_fire_confidence_interval):
        """ This method runs a simulation to produce confidence intervals for the three Alberta regions
            (East Boreal, West Boreal, and Slopes), as well as for the whole Province of Alberta.
        """

        # Load in the Human FOP cumulative probabilities and expected values file.
        hmn_cumulative_probs_expvals_df = pd.read_csv(self.hmn_cumulative_probs_expvals_output_path, sep=',', parse_dates=['date'])

        # Create a dataframe that will hold the final daily confidence interval outputs.
        hmn_confidence_intervals_output_df = pd.DataFrame(columns=FOPConstantsAndFunctions.HMN_CONFIDENCE_INTERVAL_PREDICTIONS_HEADERS)

        # Determine the "array index" for the percentile range based on what the user specifies.
        ci_low = int(round((0 + ((1 - (hmn_fire_confidence_interval / 100)) / 2) * NUM_SIMULATION_REPLICATIONS), 0))
        ci_high = int(round(float((NUM_SIMULATION_REPLICATIONS - ((1 - (hmn_fire_confidence_interval / 100)) / 2) * NUM_SIMULATION_REPLICATIONS))))

        # print("humanSimulationConfidenceIntervalGenerator(): ci_low - 1 (array index) is %d" % int(ci_low - 1))
        # print("humanSimulationConfidenceIntervalGenerator(): ci_high - 1 (array index) is %d" % int(ci_high - 1))
        # Start the simulation.
        for current_day in days_to_simulate:

            # print("humanSimulationConfidenceIntervalGenerator(): Simulating the following day: ", current_day)

            # Determine the day of the year that we are simulating for.
            day_of_year = current_day.timetuple().tm_yday

            # Create a dataframe that will hold each day's confidence interval outputs for all replications.
            """hmn_daily_simulation_headers = ['simulation_replication_num', 'fishnet_id', 'date', 'nsr_numerical_code', 'ab_region', 'calculated_probability', 
                                            'randomly_generated_probability', 'did_a_fire_happen']
            hmn_daily_simulation_df = pd.DataFrame(columns=hmn_daily_simulation_headers)"""

            # Load up a new "view" of probability data from the confidence interval output file for the current day.
            hmn_daily_cumulative_probs_expvals_df = hmn_cumulative_probs_expvals_df.loc[(hmn_cumulative_probs_expvals_df['date'].dt.year == current_day.year) &
                                                                                        (hmn_cumulative_probs_expvals_df['date'].dt.month == current_day.month) &
                                                                                        (hmn_cumulative_probs_expvals_df['date'].dt.day == current_day.day)
                                                                                        ]
            
            # Lists to keep track of the total number of human-caused fires which occur per day for all simulation replications.
            total_fires_slopes = []
            total_fires_east_boreal = []
            total_fires_west_boreal = []
            total_fires_alberta = []
            
            # Start the simulation.
            for sim_num in range(0, NUM_SIMULATION_REPLICATIONS):

                # if sim_num % 50 == 0:
                    # print("humanSimulationConfidenceIntervalGenerator(): Currently on simulation replication %d of %d. . ." % (sim_num, NUM_SIMULATION_REPLICATIONS))
                
                # Variables to keep track of the number of daily human-caused fires which occur per region, and for the entire province,
                # per simulation replication.
                fires_per_sim_slopes = 0
                fires_per_sim_east_boreal = 0
                fires_per_sim_west_boreal = 0
                fires_per_sim_alberta = 0

                # Loop through all of the fishnet_ids that we have.
                for _, row in hmn_daily_cumulative_probs_expvals_df.iterrows():

                    # Generate a random floating point number between 0 and 1.
                    randomly_generated_probability = random.uniform(0, 1)

                    # Determine if a fire started in this cell.
                    if randomly_generated_probability < row['probability']:

                        # Increment the total number of fires for Alberta.
                        fires_per_sim_alberta += 1

                        # Determine which Alberta region this cell is in, and increment the corresponding number of fires per region.
                        if row['nsr_numerical_code'] in [7, 8, 9, 10, 11, 14, 18]:
                            fires_per_sim_slopes += 1
                        else:
                            if row['longitude'] >= -114:
                                fires_per_sim_east_boreal += 1
                            else:
                                fires_per_sim_west_boreal += 1

                    # Add a row to the daily simulation dataframe.
                    """row_data = {'simulation_replication_num':[sim_num],
                                'fishnet_id':['fishnet_id'],
                                'date':[pd.to_datetime(current_day)],
                                'nsr_numerical_code':[row['nsr_numerical_code']],
                                'ab_region':['Slopes' if row['nsr_numerical_code'] in [7, 8, 9, 10, 11, 14, 18] else ('East Boreal' if row['longitude'] >= -114 else 'West Boreal')],
                                'calculated_probability':[row['calculated_probability']],
                                'randomly_generated_probability':[randomly_generated_probability],
                                'did_a_fire_happen':[(True if randomly_generated_probability < row['calculated_probability'] else False)]
                                }
                    
                    # Append this row data to the daily simulation dataframe.
                    hmn_daily_simulation_df.append(row_data)"""
                
                # Append the number of fires which occurred per region to the appropriate totals list.
                total_fires_slopes.append(fires_per_sim_slopes)
                total_fires_east_boreal.append(fires_per_sim_east_boreal)
                total_fires_west_boreal.append(fires_per_sim_west_boreal)
                total_fires_alberta.append(fires_per_sim_alberta)
                
                # Append the number of fires which occurred per region to the appropriate totals list.
                """total_fires_per_sim_slopes.append(len(hmn_daily_simulation_df.loc[((hmn_daily_simulation_df['ab_region'] == 'Slopes') &
                                                                                   (did_a_fire_happen == True))]
                total_fires_per_sim_east_boreal.append(len(hmn_daily_simulation_df.loc[((hmn_daily_simulation_df['ab_region'] == 'East Boreal') &
                                                                                        (did_a_fire_happen == True))]
                total_fires_per_sim_west_boreal.append(len(hmn_daily_simulation_df.loc[((hmn_daily_simulation_df['ab_region'] == 'West Boreal') &
                                                                                        (did_a_fire_happen == True))]
                total_fires_per_sim_alberta.append(len(hmn_daily_simulation_df.loc[did_a_fire_happen == True]))"""
                
            # Calculate the statistics for this simulation run. Sort the lists first.
            total_fires_slopes.sort()
            total_fires_east_boreal.sort()
            total_fires_west_boreal.sort()
            total_fires_alberta.sort()
            # Determine the confidence interval percentiles of these lists based on what the user specified.
            # Slopes.
            totarrSLOPES_ci_low = total_fires_slopes[ci_low - 1]
            totarrSLOPES_ci_high = total_fires_slopes[ci_high - 1]

            # East Boreal.
            totarrEASTBOREAL_ci_low = total_fires_east_boreal[ci_low - 1]
            totarrEASTBOREAL_ci_high = total_fires_east_boreal[ci_high - 1]

            # West Boreal.
            totarrWESTBOREAL_ci_low = total_fires_west_boreal[ci_low - 1]
            totarrWESTBOREAL_ci_high = total_fires_west_boreal[ci_high - 1]

            # Province of Alberta.
            totarrPROV_ci_low = total_fires_alberta[ci_low - 1]
            totarrPROV_ci_high = total_fires_alberta[ci_high - 1]

            """['year', 'today', 'month', 'day', 'totarrPROV_ci_low', 'totarrPROV_ci_high',
                                               'totarrSLOPES_ci_low', 'totarrSLOPES_ci_high', 'totarrWESTBOREAL_ci_low', 'totarrWESTBOREAL_ci_high',
                                               'totarrEASTBOREAL_ci_low', 'totarrEASTBOREAL_ci_high']"""

            # Append a new row to the output dataframe.
            row_data = {'year':[current_day.year],
                        'today':[day_of_year],
                        'month':[current_day.month],
                        'day':[current_day.day],
                        'totarrPROV_ci_low':[totarrPROV_ci_low],
                        'totarrPROV_ci_high':[totarrPROV_ci_high],
                        'totarrSLOPES_ci_low':[totarrSLOPES_ci_low],
                        'totarrSLOPES_ci_high':[totarrSLOPES_ci_high],
                        'totarrWESTBOREAL_ci_low':[totarrWESTBOREAL_ci_low],
                        'totarrWESTBOREAL_ci_high':[totarrWESTBOREAL_ci_high],
                        'totarrEASTBOREAL_ci_low':[totarrEASTBOREAL_ci_low],
                        'totarrEASTBOREAL_ci_high':[totarrEASTBOREAL_ci_high]
                        }
            row_data_df = pd.DataFrame.from_dict(row_data)
            hmn_confidence_intervals_output_df = hmn_confidence_intervals_output_df.append(row_data_df)        

        # We are done the simulation! Output the dataframe to disk.
        hmn_confidence_intervals_output_df.to_csv(self.hmn_confidence_intervals_output_path, sep=' ', index=False, header=False)

        print("humanSimulationConfidenceIntervalGenerator(): Simulation complete.")

    def humanSimulationConfidenceIntervalGeneratorV2(self, days_to_simulate, hmn_fire_confidence_interval):
        """ This method runs a simulation to produce confidence intervals for the three Alberta regions
            (East Boreal, West Boreal, and Slopes), as well as for the whole Province of Alberta.
        """
        # Load in the Human FOP cumulative probabilities and expected values file.
        hmn_cumulative_probs_expvals_df = pd.read_csv(self.hmn_cumulative_probs_expvals_output_path, sep=',', parse_dates=['date'])

        # Create a dataframe that will hold the final daily confidence interval outputs.
        hmn_confidence_intervals_output_df = pd.DataFrame(columns=FOPConstantsAndFunctions.HMN_CONFIDENCE_INTERVAL_PREDICTIONS_HEADERS)

        # Determine the "array index" for the percentile range based on what the user specifies.
        ci_low = int(round((0 + ((1 - (hmn_fire_confidence_interval / 100)) / 2) * NUM_SIMULATION_REPLICATIONS), 0))
        ci_high = int(round(float((NUM_SIMULATION_REPLICATIONS - ((1 - (hmn_fire_confidence_interval / 100)) / 2) * NUM_SIMULATION_REPLICATIONS))))

        # print("humanSimulationConfidenceIntervalGenerator(): ci_low - 1 (array index) is %d" % int(ci_low - 1))
        # print("humanSimulationConfidenceIntervalGenerator(): ci_high - 1 (array index) is %d" % int(ci_high - 1))

        # print("humanSimulationConfidenceIntervalGenerator(): Performing %d replications per day to simulate for." % NUM_SIMULATION_REPLICATIONS)
        # Start the simulation.
        for current_day in days_to_simulate:

            # print("humanSimulationConfidenceIntervalGenerator(): Simulating for the following day: ", current_day)

            # Determine the day of the year that we are simulating for.
            day_of_year = current_day.timetuple().tm_yday

            # Create a dataframe that will hold each day's confidence interval outputs for all replications.
            """hmn_daily_simulation_headers = ['simulation_replication_num', 'fishnet_id', 'date', 'nsr_numerical_code', 'ab_region', 'calculated_probability', 
                                            'randomly_generated_probability', 'did_a_fire_happen']
            hmn_daily_simulation_df = pd.DataFrame(columns=hmn_daily_simulation_headers)"""

            # Load up a new "view" of probability data from the confidence interval output file for the current day.
            hmn_daily_cumulative_probs_expvals_df = hmn_cumulative_probs_expvals_df.loc[(hmn_cumulative_probs_expvals_df['date'].dt.year == current_day.year) &
                                                                                        (hmn_cumulative_probs_expvals_df['date'].dt.month == current_day.month) &
                                                                                        (hmn_cumulative_probs_expvals_df['date'].dt.day == current_day.day)
                                                                                        ]

            # Start the simulation.
            intermediate_sim_df = pd.DataFrame(index=np.arange(NUM_SIMULATION_REPLICATIONS * len(hmn_daily_cumulative_probs_expvals_df.index)),
                                               columns=FOPConstantsAndFunctions.HMN_INTERMEDIATE_SIM_COLUMNS)
            
            # print("humanSimulationConfidenceIntervalGenerator(): Fetching and generating data for the following columns:")
            # print("humanSimulationConfidenceIntervalGenerator(): sim_num. . .")
            intermediate_sim_df['sim_num'] = pd.Series(np.arange(NUM_SIMULATION_REPLICATIONS).repeat(len(hmn_daily_cumulative_probs_expvals_df.index)),
                                                       index=intermediate_sim_df.index)
                                                       
            # print("humanSimulationConfidenceIntervalGenerator(): fishnet_id. . .")
            intermediate_sim_df['fishnet_id'] = pd.Series(np.tile(hmn_daily_cumulative_probs_expvals_df['fishnet_id'], NUM_SIMULATION_REPLICATIONS))

            # print("humanSimulationConfidenceIntervalGenerator(): region_ci. . .")
            intermediate_sim_df['region_ci'] = pd.Series(np.tile(hmn_daily_cumulative_probs_expvals_df['region_ci'], NUM_SIMULATION_REPLICATIONS))

            # print("humanSimulationConfidenceIntervalGenerator(): probability. . .")
            intermediate_sim_df['probability'] = pd.Series(np.tile(hmn_daily_cumulative_probs_expvals_df['probability'], NUM_SIMULATION_REPLICATIONS))

            # print("humanSimulationConfidenceIntervalGenerator(): random_number. . .")
            intermediate_sim_df['random_number'] = pd.Series(np.random.random(NUM_SIMULATION_REPLICATIONS * len(hmn_daily_cumulative_probs_expvals_df.index)))

            # print("humanSimulationConfidenceIntervalGenerator(): fire_alberta. . .")
            intermediate_sim_df['fire_alberta'] = np.where((intermediate_sim_df['random_number'] < intermediate_sim_df['probability']), 1, 0)

            # print("humanSimulationConfidenceIntervalGenerator(): fire_slopes. . .")
            intermediate_sim_df['fire_slopes'] = np.where(((intermediate_sim_df['random_number'] < intermediate_sim_df['probability']) &
                                                           (intermediate_sim_df['region_ci'] == 'Slopes')), 1, 0)

            # print("humanSimulationConfidenceIntervalGenerator(): fire_west_boreal. . .")
            intermediate_sim_df['fire_west_boreal'] = np.where(((intermediate_sim_df['random_number'] < intermediate_sim_df['probability']) &
                                                                (intermediate_sim_df['region_ci'] == 'West Boreal')), 1, 0)

            # print("humanSimulationConfidenceIntervalGenerator(): fire_east_boreal. . .")
            intermediate_sim_df['fire_east_boreal'] = np.where(((intermediate_sim_df['random_number'] < intermediate_sim_df['probability']) &
                                                                (intermediate_sim_df['region_ci'] == 'East Boreal')), 1, 0)

            # Determine the sorted sums of the four CI "regions" of interest.
            # print("humanSimulationConfidenceIntervalGenerator(): Sorting sums of fires for %d replications. . ." % NUM_SIMULATION_REPLICATIONS)
            alberta_ci_sums = np.sort(intermediate_sim_df.groupby('sim_num')['fire_alberta'].sum())
            slopes_ci_sums = np.sort(intermediate_sim_df.groupby('sim_num')['fire_slopes'].sum())
            west_boreal_ci_sums = np.sort(intermediate_sim_df.groupby('sim_num')['fire_west_boreal'].sum())
            east_boreal_ci_sums = np.sort(intermediate_sim_df.groupby('sim_num')['fire_east_boreal'].sum())

            # Assert statements; we should have as many means per CI region as we have simulation replications.
            assert(len(alberta_ci_sums) == NUM_SIMULATION_REPLICATIONS)
            assert(len(slopes_ci_sums) == NUM_SIMULATION_REPLICATIONS)
            assert(len(west_boreal_ci_sums) == NUM_SIMULATION_REPLICATIONS)
            assert(len(east_boreal_ci_sums) == NUM_SIMULATION_REPLICATIONS)

            # Determine the confidence interval percentiles of these lists based on what the user specified.
            # print("humanSimulationConfidenceIntervalGenerator(): Determine the confidence interval percentiles. . .")
            # Province of Alberta.
            totarrPROV_ci_low = alberta_ci_sums[ci_low - 1]
            totarrPROV_ci_high = alberta_ci_sums[ci_high - 1]

            # Slopes.
            totarrSLOPES_ci_low = slopes_ci_sums[ci_low - 1]
            totarrSLOPES_ci_high = slopes_ci_sums[ci_high - 1]

            # West Boreal.
            totarrWESTBOREAL_ci_low = west_boreal_ci_sums[ci_low - 1]
            totarrWESTBOREAL_ci_high = west_boreal_ci_sums[ci_high - 1]

            # East Boreal.
            totarrEASTBOREAL_ci_low = east_boreal_ci_sums[ci_low - 1]
            totarrEASTBOREAL_ci_high = east_boreal_ci_sums[ci_high - 1]

            """['year', 'today', 'month', 'day', 'totarrPROV_ci_low', 'totarrPROV_ci_high',
                'totarrSLOPES_ci_low', 'totarrSLOPES_ci_high', 'totarrWESTBOREAL_ci_low', 'totarrWESTBOREAL_ci_high',
                'totarrEASTBOREAL_ci_low', 'totarrEASTBOREAL_ci_high']"""

            # Append a new row to the output dataframe.
            # print("humanSimulationConfidenceIntervalGenerator(): Appending a new row to the output dataframe. . .")
            row_data = {'year':[current_day.year],
                        'today':[day_of_year],
                        'month':[current_day.month],
                        'day':[current_day.day],
                        'totarrPROV_ci_low':[totarrPROV_ci_low],
                        'totarrPROV_ci_high':[totarrPROV_ci_high],
                        'totarrSLOPES_ci_low':[totarrSLOPES_ci_low],
                        'totarrSLOPES_ci_high':[totarrSLOPES_ci_high],
                        'totarrWESTBOREAL_ci_low':[totarrWESTBOREAL_ci_low],
                        'totarrWESTBOREAL_ci_high':[totarrWESTBOREAL_ci_high],
                        'totarrEASTBOREAL_ci_low':[totarrEASTBOREAL_ci_low],
                        'totarrEASTBOREAL_ci_high':[totarrEASTBOREAL_ci_high]
                        }
            row_data_df = pd.DataFrame.from_dict(row_data)
            hmn_confidence_intervals_output_df = hmn_confidence_intervals_output_df.append(row_data_df) 
            
            # Output the intermediate CI calculation df to disk for debugging purposes.
            # intermediate_sim_df.to_csv('Z:/LightningFireOccurrencePredictionInputs/phase_two/intermediate_data_files/hmn_intermediate_sim_df.csv', index=False)   

        # We are done the simulation! Output the dataframe to disk.
        hmn_confidence_intervals_output_df.to_csv(self.hmn_confidence_intervals_output_path, sep=' ', index=False, header=False)

        # print("humanSimulationConfidenceIntervalGenerator(): Simulation complete.")
    
    def humanFirePredictionMapper(self, map_type, days_to_map, display_historical_fires_on_maps, hmn_fire_confidence_interval):
        """ This method produces a map of human fire predictions overlayed on an Alberta
            weather zone map.
        """
        
        # Read in the Alberta shapefile and set up the plot.
        #alberta_map = alberta_map.to_crs(epsg=4326)
        #fig, ax = plt.subplots(figsize=(15,15))
        #lims = plt.axis('tight')
        #alberta_map = gpd.read_file(self.hmn_alberta_basemap_shapefile)
        alberta_map = gpd.read_file(self.hmn_alberta_poly_shapefile)
        alberta_fishnet = gpd.read_file(self.hmn_alberta_fishnet_shapefile)
        alberta_forest_area = gpd.read_file(self.hmn_alberta_forest_area_shapefile)

        # print("humanFirePredictionMapper(): Alberta shapefile head is: ", alberta_map.head())
        # print("humanFirePredictionMapper(): Alberta crs is: ", alberta_map.crs)
        
        # Only load up the data files that we need to pull information from for our maps.
        # Get a new view for the arrivals, if desired.
        if display_historical_fires_on_maps:
            # Use encoding='cp1252' to deal with the Windows "smart quotes" in the historical fires file, 0x92.
            actual_fires_df = pd.read_csv(self.hmn_actual_fire_arrivals_file, sep=',', parse_dates=['reported_date', 'fire_start_date'], encoding='cp1252')
            # print("humanFirePredictionMapper(): Dropping all duplicate / identical rows from the historical fire arrivals dataframe...")
            actual_fires_df.drop_duplicates(keep='first', inplace=True)
            actual_fires_df.columns = map(str.upper, actual_fires_df.columns)

            # We want all fires which are not "Lightning" fires.
            actual_fires_df = actual_fires_df[(actual_fires_df['GENERAL_CAUSE_DESC'].str.contains("Lightning") == False)]
            # print(actual_fires_df['REPORTED_DATE'])
        
        # Load up the necessary files as specified by the method input parameters, and populate dataframes.

        # Load up the grid predictions file and add column headers.
        gridded_predictions_df = pd.read_csv(self.hmn_cumulative_probs_expvals_output_path, sep=',', parse_dates=['date'])
        gridded_predictions_df.columns = FOPConstantsAndFunctions.HMN_PROBABILITIES_EXPECTED_VALUES_HEADERS

        # Load up the confidence intervals file and add column headers.
        confidence_intervals_df = pd.read_csv(self.hmn_confidence_intervals_output_path, delim_whitespace=True, header=None)
        confidence_intervals_df.columns = FOPConstantsAndFunctions.HMN_CONFIDENCE_INTERVAL_PREDICTIONS_HEADERS

        # If there are no predictions for this date (ie. early in the fire season when there are no FWI values yet),
        # do not generate this map.

        if len(gridded_predictions_df.index) == 0:
            # print("humanFirePredictionMapper(): No prediction data exists in the Human FOP cumulative probabilities and expected values output file; a map will not be generated.")
            return
        
        # print("humanFirePredictionMapper(): days_to_map is ", days_to_map)

        # Loop through all of the days that we need to map.
        for date in days_to_map:

            # print("humanFirePredictionMapper(): Now preparing maps for %s ..." % str(date))
            
            # If we are to display historical arrivals, then load up a new view (in the database sense) for this new date.
            if display_historical_fires_on_maps:

                #print("humanFirePredictionMapper(): actual_fires_df['CURRENT_SIZE'] is ", actual_fires_df['CURRENT_SIZE'])

                actual_reported_date_fires_df_view = actual_fires_df.loc[((actual_fires_df['REPORTED_DATE']).dt.year == date.year) &
                                                                         ((actual_fires_df['REPORTED_DATE']).dt.month == date.month) &
                                                                         ((actual_fires_df['REPORTED_DATE']).dt.day == date.day) &
                                                                         ((actual_fires_df['CURRENT_SIZE']) >= 0.1)]
                # print(actual_reported_date_fires_df_view)

                actual_reported_date_fires_gdf = gpd.GeoDataFrame(actual_reported_date_fires_df_view,
                                                                  crs={'init': 'EPSG:4269'},  # Initialize the coordinate system based on NAD83.
                                                                  geometry=gpd.points_from_xy(actual_reported_date_fires_df_view['FIRE_LOCATION_LONGITUDE'],
                                                                                              actual_reported_date_fires_df_view['FIRE_LOCATION_LATITUDE']))
                
                # Convert the data to the appropriate projection.
                actual_reported_date_fires_gdf = actual_reported_date_fires_gdf.to_crs(crs=alberta_map.crs, epsg=3400)
                
                """actual_start_date_fires_df_view = actual_fires_df.loc[((actual_fires_df['FIRE_START_DATE']).dt.year == date.year) &
                                                                        ((actual_fires_df['FIRE_START_DATE']).dt.month == date.month) &
                                                                        ((actual_fires_df['FIRE_START_DATE']).dt.day == date.day)]
                print(actual_start_date_fires_df_view)

                actual_start_date_fires_gdf = gpd.GeoDataFrame(actual_start_date_fires_df_view,
                                                               crs={'init': alberta_map.crs},
                                                               geometry=gpd.points_from_xy(actual_start_date_fires_df_view['FIRE_LOCATION_LONGITUDE'],
                                                                                           actual_start_date_fires_df_view['FIRE_LOCATION_LATITUDE']))"""
            
            # Load up a new view for this new date.
            gridded_predictions_df_view = gridded_predictions_df.loc[(gridded_predictions_df['date'].dt.year == date.year) &
                                                                     (gridded_predictions_df['date'].dt.month == date.month) &
                                                                     (gridded_predictions_df['date'].dt.day == date.day)]
                
            confidence_intervals_df_view = confidence_intervals_df.loc[(confidence_intervals_df['year'] == date.year) &
                                                                        (confidence_intervals_df['month'] == date.month) &
                                                                        (confidence_intervals_df['day'] == date.day)]

            geo_df_gridded_predictions = gpd.GeoDataFrame(gridded_predictions_df_view,
                                                          crs={'init': 'EPSG:4269'},  # Initialize the coordinate system based on NAD83 lat/long.
                                                          geometry=gpd.points_from_xy(gridded_predictions_df_view['longitude'],
                                                                                      gridded_predictions_df_view['latitude']))
            
            # Colour the fishnet polygons based on the probabilities of this day's predictions.
            # colour_fishnet_polygons(gridded_predictions_df_view)
            
            # Convert the data to the appropriate projection.
            geo_df_gridded_predictions = geo_df_gridded_predictions.to_crs(crs=alberta_map.crs, epsg=3400)
            
            # Now that are views are updated, generate the maps that we need to for the new day.
            if map_type == 'probability' or map_type == 'all':

                # print("humanFirePredictionMapper(): Processing probability map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(15, 12)  # Use these size values for now; the map's whitespace will be cropped further down in the code.
                alberta_map.plot(ax=ax, alpha=0.2, color='grey')
                alberta_forest_area.plot(ax=ax, alpha=0.1, color='black')

                # Display, or don't display, the probability ranges on the map labels depending on the value of FOPConstantsAndFunctions.SHOW_PROBABILITY_ARRIVAL_HOLDOVER_RANGES.
                if FOPConstantsAndFunctions.SHOW_PROBABILITY_ARRIVAL_HOLDOVER_RANGES_IN_LEGEND:
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] > 0.1)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme (> 0.10)')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] > 0.03) & (geo_df_gridded_predictions['probability'] <= 0.1)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High (> 0.03 to 0.10)')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] > 0.01) & (geo_df_gridded_predictions['probability'] <= 0.03)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High (> 0.01 to 0.03)')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] > 0.003) & (geo_df_gridded_predictions['probability'] <= 0.01)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate (> 0.003 to 0.01)')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] >= 0.0) & (geo_df_gridded_predictions['probability'] <= 0.003)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low (≥ 0.0 to 0.003)')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] < 0)].plot(ax=ax, markersize=9, color='black', marker='o', label='No data')
                else:
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] > 0.1)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] > 0.03) & (geo_df_gridded_predictions['probability'] <= 0.1)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] > 0.01) & (geo_df_gridded_predictions['probability'] <= 0.03)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] > 0.003) & (geo_df_gridded_predictions['probability'] <= 0.01)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] >= 0.0) & (geo_df_gridded_predictions['probability'] <= 0.003)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low')
                    geo_df_gridded_predictions[(geo_df_gridded_predictions['probability'] < 0)].plot(ax=ax, markersize=9, color='black', marker='o', label='No data')

                
                # Add information related to confidence intervals here (with some logic to display either a whole number or float, as appropriate):
                ci_string = '\n'.join((r'Predictions with %s%% confidence' % (str(int(hmn_fire_confidence_interval) if hmn_fire_confidence_interval.is_integer() else hmn_fire_confidence_interval)),
                                        r'Alberta: %d to %d fires' % (confidence_intervals_df_view['totarrPROV_ci_low'],
                                                                      confidence_intervals_df_view['totarrPROV_ci_high']),
                                        r'Western Boreal: %d to %d fires' % (confidence_intervals_df_view['totarrWESTBOREAL_ci_low'],
                                                                             confidence_intervals_df_view['totarrWESTBOREAL_ci_high']),
                                        r'Eastern Boreal: %d to %d fires' % (confidence_intervals_df_view['totarrEASTBOREAL_ci_low'],
                                                                             confidence_intervals_df_view['totarrEASTBOREAL_ci_high']),
                                        r'Eastern Slopes: %d to %d fires' % (confidence_intervals_df_view['totarrSLOPES_ci_low'],
                                                                             confidence_intervals_df_view['totarrSLOPES_ci_high'])))
                
                # Hacky way of getting the confidence interval string to appear in the legend.
                plt.plot([], [], ' ', label=ci_string)

                # Display actual lightning fires on our map, if desired.
                if display_historical_fires_on_maps and len(actual_reported_date_fires_gdf.index) > 0:
                    actual_reported_date_fires_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Reported human-caused fire', edgecolor='black', linewidth=0.5)

                    # Hacky way of getting the total number of historical arrivals to appear in the legend.
                    arrivals_string = (r'Reported human-caused fires (≥ 0.1 ha): %d' % len(actual_reported_date_fires_gdf.index))
                    plt.plot([], [], ' ', label=arrivals_string)
                
                # Add a title to the plot.
                plt.title("Alberta Human-Caused Fire Arrival Probabilities for " + date.strftime('%Y-%m-%d'))
                
                # Determine if the legend to be plotted will be empty. If there are no handles nor labels, do not add the legend to the plot.
                handles, labels = ax.get_legend_handles_labels()                
                if handles and labels:
                    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

                # Hide the x- and y-axis ticks and labels.
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)

                # Output the generated map to a PNG image; crop the map's whitespace, leaving a 0.25 inch padding.
                plt.savefig(fname=(self.hmn_output_maps_folder + "/hmn_probability_" + date.strftime('%Y-%m-%d') + ".png"), format='png', dpi=200,
                            bbox_inches='tight', pad_inches=0.25)
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')
            
            if map_type == 'ffmc' or map_type == 'all':

                # print("humanFirePredictionMapper(): Processing FFMC map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(15, 12)
                alberta_map.plot(ax=ax, alpha=0.2, color='grey')
                alberta_forest_area.plot(ax=ax, alpha=0.1, color='black')

                geo_df_gridded_predictions[(geo_df_gridded_predictions['ffmc_interpolated'] > 91)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme (92+)')
                geo_df_gridded_predictions[(geo_df_gridded_predictions['ffmc_interpolated'] > 88) & (geo_df_gridded_predictions['ffmc_interpolated'] <= 91)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High (89 to 91)')
                geo_df_gridded_predictions[(geo_df_gridded_predictions['ffmc_interpolated'] > 84) & (geo_df_gridded_predictions['ffmc_interpolated'] <= 88)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High (85 to 88)')
                geo_df_gridded_predictions[(geo_df_gridded_predictions['ffmc_interpolated'] > 76) & (geo_df_gridded_predictions['ffmc_interpolated'] <= 84)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate (77 to 84)')
                geo_df_gridded_predictions[(geo_df_gridded_predictions['ffmc_interpolated'] >= 0) & (geo_df_gridded_predictions['ffmc_interpolated'] <= 76)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low (0 to 76)')
                geo_df_gridded_predictions[(geo_df_gridded_predictions['ffmc_interpolated'] < 0)].plot(ax=ax, markersize=9, color='black', marker='o', label='No data')

                # Add a title to the plot.
                plt.title("FFMC for " + date.strftime('%Y-%m-%d'))
                
                # Determine if the legend to be plotted will be empty. If there are no handles nor labels, do not add the legend to the plot.
                handles, labels = ax.get_legend_handles_labels()                
                if handles and labels:
                    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

                # Hide the x- and y-axis ticks and labels.
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)

                # Output the generated map to a PNG image.
                plt.savefig(fname=(self.hmn_output_maps_folder + "/hmn_ffmc_" + date.strftime('%Y-%m-%d') + ".png"), format='png', dpi=200,
                            bbox_inches='tight', pad_inches=0.25)
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')

        # End for loop
    
    def humanConfidenceIntervalGraphGenerator(self, days_to_plot, hmn_fire_confidence_interval):
        """ This method creates graphs of daily confidence intervals against actual historical
            arrivals (reported fires) and holdovers (fire starts). """
        
        # Load the historical lightning fires file.
        # Use encoding='cp1252' to deal with the Windows "smart quotes" in the historical fires file, 0x92.
        actual_fires_df = pd.read_csv(self.hmn_actual_fire_arrivals_file, sep=',', encoding='cp1252', parse_dates=['reported_date', 'fire_start_date'])
        # print("humanConfidenceIntervalGraphGenerator(): Dropping all duplicate fires / identical rows...")
        actual_fires_df.drop_duplicates(keep='first', inplace=True)
        actual_fires_df.columns = map(str.upper, actual_fires_df.columns)
        # We want to select all fires (including "Unknown" fires) which are not Lightning fires.
        actual_fires_df = actual_fires_df[(actual_fires_df['GENERAL_CAUSE_DESC'].str.contains("Lightning") == False)]
        
        # print("humanConfidenceIntervalGraphGenerator(): Loaded actual fire arrivals file.")
        
        # Load up the confidence intervals file and add column headers.
        confidence_intervals_df = pd.read_csv(self.hmn_confidence_intervals_output_path, delim_whitespace=True, header=None)
        confidence_intervals_df.columns = FOPConstantsAndFunctions.HMN_CONFIDENCE_INTERVAL_PREDICTIONS_HEADERS
        
        # print("humanConfidenceIntervalGraphGenerator(): Loaded confidence intervals predictions.")
         
        # Loop through the date range provided and grab the fire arrivals
        # (reported fires) and holdovers (fire starts) for each of the days we need.
        reported_fires_dict = {}
        
        for date in days_to_plot:

            actual_reported_date_fires_df_view = actual_fires_df.loc[((actual_fires_df['REPORTED_DATE']).dt.year == date.year) &
                                                                     ((actual_fires_df['REPORTED_DATE']).dt.month == date.month) &
                                                                     ((actual_fires_df['REPORTED_DATE']).dt.day == date.day) &
                                                                     ((actual_fires_df['CURRENT_SIZE']) >= 0.1)]            
            reported_fires_dict[date.strftime("%Y-%m-%d")] = len(actual_reported_date_fires_df_view.index)

        # Created a sorted-by-date list of tuples out of the dictionary.
        historical_list = sorted(reported_fires_dict.items())
        x, y = zip(*historical_list)

        # Determine how many days occur where the actual reported fires fall outside of the confidence interval range.
        num_days_arrivals_out_of_range = 0
        for index in range(0, len(x)):
            
            if (y[index] < confidence_intervals_df['totarrPROV_ci_low'][index]) or (y[index] > confidence_intervals_df['totarrPROV_ci_high'][index]):
                num_days_arrivals_out_of_range += 1
        
        # Fire arrivals.
        plt.clf()
        fig, ax = plt.subplots(sharex=True)
        fig.set_size_inches((6 + 0.45 * len(days_to_plot)), 12)  # Variably-widthed plot depending on number of dates we are plotting.
        plt.xlabel("Date")        
        plt.ylabel("Number of reported human-caused fires")     
        #string_dates = [date.strftime("%m-%d") for date in days_to_plot]
        #print("confidenceIntervalGraphGenerator(): string_dates is ", string_dates)
        #plt.xticks(range(len(days_to_plot)))
        #plt.xticks([range(len(days_to_plot))])
        #ax.set_xticklabels(days_to_plot, rotation='vertical')

        # Helper function to determine Saturdays and Sundays out of a given list.
        def find_saturdays_and_sundays(dates):
            saturdays_sundays = []
            for i in range(len(dates)):

                # Monday = 0 ... Sunday = 6
                if dates[i].weekday() >= 5:  # Saturday and Sunday.
                    saturdays_sundays.append(dates[i])
            return saturdays_sundays
        
        ax.xaxis.set_major_locator(mdates.DayLocator())
        #ax.xaxis.set_minor_locator(mdates.DayLocator())
        #month_fmt = mdates.DateFormatter('%B')
        day_fmt = mdates.DateFormatter('%b %d')
        #ax.xaxis_date()
        ax.xaxis.set_major_formatter(day_fmt)
        #weekend_fmt = mdates.DateFormatter('%b %d')
        #ax.xaxis.set_minor_formatter(weekend_fmt)
        #weekday_locator = mdates.WeekdayLocator(byweekday=(SA, SU))
        #ax.xaxis.set_minor_locator(weekday_locator)
        #ax.xaxis.grid(False, 'major')
        #ax.xaxis.grid(True, 'minor')
        #ax.yaxis.grid(False, 'major')
        #ax.yaxis.grid(False, 'minor')
        #ax.minorticks_on()
        #ax.grid(True, which='minor')
        #ax.xaxis.set_tick_params(which='major', pad=13)
        
        
        # [date.strftime("%m%d") for date in days_to_plot]
        # plt.xticks(range(len(days_to_plot)), rotation=90)
        #plt.yticks(rotation=90)

        #print("confidenceIntervalGraphGenerator(): days_to_plot is ", days_to_plot)
        #print("confidenceIntervalGraphGenerator(): confidence_intervals_df['totarrPROV_ci_low'] is ", confidence_intervals_df['totarrPROV_ci_low'])

        plt.plot(days_to_plot, confidence_intervals_df['totarrPROV_ci_high'], color='red', marker='o', markersize=3, label="Human fire arrivals confidence interval,\nhigh bound")
        plt.plot(days_to_plot, confidence_intervals_df['totarrPROV_ci_low'], color='green', marker='o', markersize=3, label="Human fire arrivals confidence interval,\nlow bound")
        
        plt.plot(days_to_plot, y, color='purple', marker='o', markersize=3, label="Daily reported fires")

        ax.set_xlim([min(days_to_plot), max(days_to_plot)])

        saturdays_sundays = find_saturdays_and_sundays(days_to_plot)
        #ax.xaxis.set_minor_locator(saturdays_sundays)
        ax.set_xticks(saturdays_sundays, minor=True)
        #ax.minorticks_on()
        ax.grid(which='minor', linestyle=':', alpha=0.5)

        ax.set_ylim(ymin=0)
        fig.autofmt_xdate()

        hmn_fire_confidence_interval_string = ('Confidence interval used for simulation: %.1f%%' % hmn_fire_confidence_interval)
        plt.plot([], [], ' ', label=hmn_fire_confidence_interval_string)
        
        num_days_arrivals_out_of_range_string = ('Number of days where daily reported\nfires amount was outside confidence\ninterval range: %d' % num_days_arrivals_out_of_range)
        plt.plot([], [], ' ', label=num_days_arrivals_out_of_range_string)

        percentage_days_arrivals_out_of_range_string = ('Percentage of days where daily reported\nfires amount was within confidence\ninterval range: %2.1f%%' % (100 - ((num_days_arrivals_out_of_range / float(len(days_to_plot))) * 100)))
        plt.plot([], [], ' ', label=percentage_days_arrivals_out_of_range_string)

        # Add a title and a legend to the plot.
        plt.title("Predicted Human Fire Confidence Interval Ranges and Historical Reported Fires for " + str(days_to_plot[0].year))
        legend = plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

        plt.savefig(fname=(self.hmn_output_maps_folder + "/hmn_cidiagnostic_arrivals_" + str(days_to_plot[0].year) + ".png"), format='png', dpi=150, bbox_extra_artists=(legend,), bbox_inches='tight')
            
        # Reset and close the plot and figures.
        plt.cla()
        plt.clf()
        plt.close('all')
    
    def humanFOPDateRangeMapperPredictor(self, start_day, end_day, hmn_fire_confidence_interval, display_historical_fires_on_maps):
        """ This method is used to simulate and produce Human FOP maps for a date range that exists in the FOP system state
            DB already.

            Unlike for the Lightning FOP Date Range Mapper, this method simply calls the Human FOP Controller and lets
            the controller decide which dats to predict for vs. which days to map straight away.

            We do it this way for Human FOP because we only need one day's worth of information to make a prediction
            for that day. Whereas for Lightning FOP, we need a precise sequence of days existing due to the nature
            of "bookkeeping" for lightning holdovers and the nature of the tools used to produce lightning fire
            predictions.
        """

        # Call the C Simulator wrapper using the provided start_date and end_date.
        # print("HumanFOPDateRangeMapper(): Determining which days we can map immediately, and which ones we need to predict for first. . .")
        # Call humanFOPController, which will take care of determining which days need predicting, vs. which days we can simply map
        # straight away.
        for date in FOPConstantsAndFunctions.daterange(start_day, end_day + datetime.timedelta(days=1)):
            # print("HumanFOPDateRangeMapper(): Calling humanFOPController() for %s. . .", date.strftime("%Y-%m-%d"))
            self.humanFOPController(date, hmn_fire_confidence_interval, display_historical_fires_on_maps)
        
        # print("HumanFOPDateRangeMapper(): Date range mapping and prediction operation complete.")
    
    def humanFOPCIGraphGenerator(self, dates_to_graph, float_hmn_fire_confidence_interval):
        """ This method is used to produce a fresh simulation run for a date range (usually all days predicted for thus far in a year), from
            which a confidence interval plot of the predicted arrivals along with the actual number of reported fires on each day.

            This is intended to be a diagnostic tool for observing human fire prediction model performance. """
        
        # print("humanFOPCIGraphGenerator(): Calling humanSimulationConfidenceIntervalGenerator() on dates which have had Human FOP performed previously. . .")

        # Get a fresh set of simulations for the days which have had Human FOP performed previously.
        self.humanSimulationConfidenceIntervalGeneratorV2(dates_to_graph, float_hmn_fire_confidence_interval)

        # Call the CI graph generator using the provided list of dates to graph; the major difference between the Human and Lighting CI Graph
        # generator is that .
        self.humanConfidenceIntervalGraphGenerator(dates_to_graph, float_hmn_fire_confidence_interval)

        # We're done!
        # print("humanFOPCIGraphGenerator(): CI graph generation operation completed.")
        return

    def humanFOPController(self, date_to_predict_for, hmn_fire_confidence_interval, display_historical_fires_on_maps):
        """ This method is provided input parameters from the GUI which will determine how the Human FOP model runs.
            
            This method contains the logic behind determining if the master data set needs to be updated or not.
            If it does, load the updated raw weather data and run it through the processing flow.

            This method also contains a lot of error-checking to ensure that the integrity of the data is
            maintained.
            
            The date_to_predict_for is a datetime datatype."""
        
        # Load in the FOP system state data set, and the raw weather data.        
        # Sanity check: Ensure that the system state data set exists.
        try:
            # print("humanFOPController(): Starting by reading in the system state DB...")
            self.fop_system_state_db_df = pd.read_csv(self.fop_system_state_db_path, sep=',', header=0,
                                                      names=FOPConstantsAndFunctions.FOP_SYSTEM_STATE_DB_HEADERS, parse_dates=['DATE'])

            # If the database is empty, then populate all of the dates which can be predicted for both human- and lightning-caused
            # fires (March 01 through October 31).
            if len(self.fop_system_state_db_df.index) == 0:
                # print("humanFOPController(): Initializing empty FOP system state DB. . .:")

                for new_date in FOPConstantsAndFunctions.daterange(pd.Timestamp(date_to_predict_for.year, 3, 1),
                                                                   pd.Timestamp(date_to_predict_for.year, 10, 31) + datetime.timedelta(days=1)
                                                                  ):
                    row_data = {'DATE':[new_date], 'LIGHTNING_FOP_COMPLETED':['N'], 'HUMAN_FOP_COMPLETED':['N'], 'FORECASTED_OR_OBSERVED':['O']}
                    row_data_df = pd.DataFrame.from_dict(row_data)
                    self.fop_system_state_db_df = self.fop_system_state_db_df.append(row_data_df)
        
            # After the column header check (and potentially adding new rows), set the DATE column as the index of the FOP system state DB.
            self.fop_system_state_db_df.set_index('DATE', inplace=True)

            # print("humanFOPController(): self.fop_system_state_db_df before starting Human FOP run:")
            # print(self.fop_system_state_db_df)
            
        except IOError as e:
            # print("humanFOPController(): Exception IOError thrown while reading the FOP system state DB. Exception details follow below. Aborting...")
            # print(e)
            return

        # See if we have already produced predictions for this day.
        if self.fop_system_state_db_df.at[pd.to_datetime(date_to_predict_for), 'HUMAN_FOP_COMPLETED'] == 'Y':
            # print("humanFOPController(): The provided date, %s, exists already in the system. Producing maps for it." % str(date_to_predict_for))

            # The day we want to predict for exists already.
            # Determine the day of year (Julian) so that we can pull the prediction for this day.
            day_of_year = date_to_predict_for.timetuple().tm_yday
            # print("humanFOPController(): day_of_year is ", day_of_year)

            # Determine the confidence intervals for this day by calling the simulation method.
            self.humanSimulationConfidenceIntervalGeneratorV2([date_to_predict_for], hmn_fire_confidence_interval)

            # Valid map strings: 'probability', 'ffmc', ... all case sensitive.
            # Use 'all' to output all maps.
            self.humanFirePredictionMapper('all', [date_to_predict_for], display_historical_fires_on_maps, hmn_fire_confidence_interval)
        
        else:
            # This day does not exist in the system. We need to execute the Human FOP flow for the desired day.            
            # print("humanFOPController(): date_to_predict_for is ", date_to_predict_for)

            # Parse the weather_date column as a datetime to allow for easy access to year, month, day and hour.
            # Here, we use the infer_datetime_format=True flag because the datetime in the file is NOT zero-padded, and
            # the default datetime placeholders do not allow for that by default.
            
            # Next, we need to select only the raw weather data for the day that we need to produce a human-caused
            # prediction for.
            raw_weather_data_df = pd.read_csv(self.hmn_input_raw_weather_data_file, sep=',')

             # Perform a header check to determine the well-formed nature of the CSV.
            if list(raw_weather_data_df.columns) == FOPConstantsAndFunctions.RAW_WEATHER_CSV_HEADERS:

                # Raw weather headers type 1.
                # print("humanFOPController(): Raw weather data column check OK, headers type 1.")
                raw_weather_data_df['weather_date'] = pd.to_datetime(raw_weather_data_df['weather_date'], format='%m/%d/%y %H:%M', infer_datetime_format=True)

            elif list(raw_weather_data_df.columns) == FOPConstantsAndFunctions.RAW_WEATHER_CSV_HEADERS_2:
                
                # Raw weather headers type 2.
                # print("humanFOPController(): Raw weather data column check OK, headers type 2.")
                # print("humanFOPController(): Making headers lower-case...")
                
                # Make all of the weather column headers to be lowercase.
                raw_weather_data_df.columns = map(str.lower, raw_weather_data_df.columns)
                raw_weather_data_df['weather_date'] = pd.to_datetime(raw_weather_data_df['weather_date'], format='%Y-%m-%d %H:%M:%S', infer_datetime_format=True)

            else:
                # print("humanFOPController(): Raw weather data columns do not match what is expected. ERROR")
                raise ValueError

            # Sort the raw weather dataframe by the column: "weather_date".
            raw_weather_data_df = raw_weather_data_df.sort_values(by='weather_date')
        
            # Convert date_to_predict_for using pd.to_datetime().
            date_to_predict_for = pd.to_datetime(date_to_predict_for)

            date_mask_weather = ((raw_weather_data_df['weather_date'].dt.year == date_to_predict_for.year) &
                                 (raw_weather_data_df['weather_date'].dt.month == date_to_predict_for.month) &
                                 (raw_weather_data_df['weather_date'].dt.day == date_to_predict_for.day))

            # Perform the date selection for this dataframe; selection is inclusive.
            raw_weather_data_df = raw_weather_data_df.loc[date_mask_weather]

            # print("humanFOPController(): Raw weather date selection is:")
            # print(raw_weather_data_df)

            # Ensure that we actually have grabbed data for the date we want to predict for.
            if raw_weather_data_df.empty:
                # print("humanFOPController(): The provided date, %s, does not exist in the raw weather dataset. \r\n" \
                    # "Please provide a more up-to-date raw weather data file or adjust the prediction date and try again." % str(date_to_predict_for))
                raise Exception
                return
            
            
            # We are good to go on the raw weather data side. Let's start the Human FOP flow.

            # 1. Call the raw weather data massager method on the prepared raw weather dataframe.
            FOPConstantsAndFunctions.rawWeatherDataMassager(raw_weather_data_df,
                                                            self.hmn_weather_massaged_output_path,
                                                            self.hmn_weather_station_locations_path)
            
            # 2. Call the weather interpolation and binning executable through the following method.
            self.weatherInterpolationBinnerWrapper()

            # 3. Calculate the expected values and probabilities for human-caused fires.
            self.humanFOPProbabilitiesCalculator(date_to_predict_for)

            # 4. Determine the confidence intervals for this day by calling the simulation method.
            self.humanSimulationConfidenceIntervalGeneratorV2([date_to_predict_for], hmn_fire_confidence_interval)

            # 5. Update the FOP system state DB with the newly-processed dates.
            # print("humanFOPController(): Updating FOP system state DB and writing changes to disk...")

            # print("humanFOPController(): FOP system state DB prior to update is: ")
            # print(self.fop_system_state_db_df)

            # Convert date_to_predict_for to a datetime64 for FOP system state DB indexing purposes.
            date_to_predict_for = pd.to_datetime(date_to_predict_for)
            
            # Update the row index at date_to_predict_for in the FOP system state DB as being predicted for.
            self.fop_system_state_db_df.at[date_to_predict_for, 'HUMAN_FOP_COMPLETED'] = 'Y'
            
            # print("humanFOPController(): FOP system state DB after update is:")
            # print(self.fop_system_state_db_df)           

            # Write the new information to the DB on disk.
            self.fop_system_state_db_df.to_csv(self.fop_system_state_db_path, sep=',', index=True)

            # 5. Call the mapping method which will produce maps for the desired date.
            self.humanFirePredictionMapper('all', [date_to_predict_for], display_historical_fires_on_maps, hmn_fire_confidence_interval)

        # We are done!
        print("humanFOPController(): Run successfully completed.")
        return
        
