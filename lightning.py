""" This file contains a Python harness for Dr. Mike Wotton's Lightning Fire Occurrence Prediction (FOP) model.

    It also contains a Controller method that a GUI can interact with to "drive" the Lightning FOP model.

    This code is written for the UAlberta FOP project, in collaboration with the Government of Alberta
    and the Canadian Forest Service.

    Author: Matthew Ansell
    2019
"""

import csv  # Used for simple sequential input / output data processing.
import os.path  # Used for determining the CWD, and other I/O-related tasks.
import subprocess  # Used for calling Dr. Wotton's compiled exe files.
import pandas as pd  # Used for more complicated (occasionally SQL-like) input / output data processing.
import math  # Used for model calculations.
import operator # Used for CSV sort-by-column.
import timeit  # Used for measuring code execution time.
from decimal import Decimal  # Used to round probabilities to an exact decimal as opposed to float.
import datetime  # Used to determine the day of year (Julian), as well as date-based arithmetic.
import random  # Used to generate a random number seed for the C simulation tool.
import geopandas as gpd  # This and the following imports are used for mapping purposes.
import descartes
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from matplotlib import text
import matplotlib.dates as mdates
import pylab
import FOPConstantsAndFunctions
import pandas.io.common

######################################### CLASSES #########################################

class LightningFireOccurrencePrediction(object):
    """ This class contains the logic for the Lightning Fire Occurrence Prediction model itself. """

    def __init__(self,
                 ltg_input_raw_weather_data_file,
                 ltg_input_raw_lightning_strike_data_file,
                 ltg_intermediate_data_folder,
                 ltg_output_data_folder,
                 ltg_output_maps_folder,
                 ltg_actual_fire_arrivals_file  
                 ):

        # Construct paths to all of the necessary files for the Lightning FOP flow. Numbered in order of usage for the Lightning FOP flow.

        # 1. Raw weather data file (path is already constructed, explicit from the GUI).
        self.ltg_input_raw_weather_data_file = ltg_input_raw_weather_data_file

        # 2. Massaged weather data file (to be put in the intermediate data folder).
        self.ltg_weather_massaged_output_path = ltg_intermediate_data_folder + '/2_Massaged_Weather.csv'

        # 3. Weather interpolation coefficients data file path (to be put in the intermediate data folder)
        self.ltg_weather_interpolation_coefficients_path = ltg_intermediate_data_folder + '/3_weather_interpolation_coefficients'

        # 4. Binned weather data file (to be put in the intermediate data folder).
        self.ltg_weather_binned_output_path = ltg_intermediate_data_folder + '/4_Binned_Weather.csv'

        # (4). Binned weather data file with lat-longs added (to be put in the intermediate data folder).
        self.ltg_weather_binned_output_lat_longs_added_path = ltg_intermediate_data_folder + '/4_Binned_Weather_LatLongs_Added.csv'

        # 5. Raw lightning strike data file (path is already constructed, explicit from the GUI).
        self.ltg_input_raw_lightning_strike_data_file = ltg_input_raw_lightning_strike_data_file

        # 6. Massaged lightning strike file path (to be put in the intermediate data folder).
        self.ltg_strike_raw_massaged_output_path = ltg_intermediate_data_folder + '/6_AB_ltg_space_massaged.out'

        # 7. Binned lightning strike file path (to be put in the intermediate data folder).
        self.ltg_lightning_binned_output_path = ltg_intermediate_data_folder + '/7_ltg-10by10-five-period.dat'

        # 8. Merged binned weather and lightning file path (to be put in the intermediate data folder).
        self.ltg_merged_weather_lightning_data_path = ltg_intermediate_data_folder + '/8_Alberta_Merged_Weather_Lightning.csv'

        # 9. Confidence intervals output file path (to be put in the output data folder)
        self.ltg_confidence_intervals_output_path = ltg_output_data_folder + '/AB-predictions.out'

        # 10. Gridded expected value predictions output file path (to be put in the output data folder)
        self.ltg_gridded_predictions_output_path = ltg_output_data_folder + '/AB-grids.out'

        # DEBUG: Root of the intermediate output folder.
        self.ltg_debugging_weather_station_grid_locations_path = ltg_intermediate_data_folder + "\\Gridlocations-WEATHERSTATIONSDEBUG.prn"

        # Construct paths to the resource files and paths required by the Lightning FOP model:

        # Probability of arrivals and holdovers data file path (to be put in the resources data folder).
        self.ltg_arrivals_holdovers_probabilities_output_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\resource_files\\ltg_fop_probabilities_output.out'))

        # Grid locations file path.
        self.ltg_grid_locations_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\resource_files\\Gridlocations.prn'))
        
        # Weather station locations file path.
        self.hmn_weather_station_locations_path = 'resource_files\\Alberta_Weather_Stations_2019_new.csv'
        
        # Fishnet NSR file path.
        self.ltg_fishnet_nsr_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\resource_files\\alberta_static.csv'))
        
        # Alberta basemap shapefile path.
        self.ltg_alberta_shapefile = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\resource_files\\shapefiles\\asrd_mgmt_area\\BF_ASRD_MGMT_AREA_POLYGON.shp'))
        
        # Alberta fishnet shapefile path.
        self.ltg_alberta_fishnet_shapefile = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\resource_files\\shapefiles\\fishnet\\fishnet.shp'))
        
        # Alberta polygon shapefile path.
        self.ltg_alberta_poly_shapefile = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\resource_files\\shapefiles\\fishnet\\AB_Poly.shp'))

        # Alberta forest area shapefile path.
        self.ltg_alberta_forest_area_shapefile = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\resource_files\\shapefiles\\fishnet\\Forest_Area.shp'))
        
        # FOP system state DB / CSV file path.
        self.fop_system_state_db_path = 'resource_files\\fop_system_state_db.csv'
        
        # Maps output folder path.
        self.ltg_output_maps_folder = ltg_output_maps_folder

        # Actual historical fire arrivals file (for mapping purposes).
        self.ltg_actual_fire_arrivals_file = ltg_actual_fire_arrivals_file

        # Dr. Wotton's C program executable paths.

        # Build the path to the C binning executable.
        self.lightning_wrapper_exe_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\lightning\\binning\\build-ltggrids-five-period.exe'))
        
        # Build the path to the C weather interpolation executable.
        self.weather_interpolation_exe_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\lightning\\weather\\cf-build-AB.exe'))
        
        # Build the path to the C weather binning executable.
        self.weather_binning_exe_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\lightning\\weather\\use_cf2.exe'))

        # Build the path to the C simulation executable.
        self.simulation_exe_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'FireOccurrencePrediction\\lightning\\simulation\\simulate-new-allyears-DC.exe'))
    
    def lightningFirePredictionMapper(self, map_type, days_to_map, display_historical_fires_on_maps, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval):
        """ This method produces a map of lightning fire predictions overlayed on an Alberta
            weather zone map.
        """
        
        # Read in the Alberta shapefile and set up the plot.
        #alberta_map = alberta_map.to_crs(epsg=4326)
        #fig, ax = plt.subplots(figsize=(15,15))
        #lims = plt.axis('tight')
        #alberta_map = gpd.read_file(self.ltg_alberta_shapefile)        
        alberta_map = gpd.read_file(self.ltg_alberta_poly_shapefile)
        alberta_fishnet = gpd.read_file(self.ltg_alberta_fishnet_shapefile)
        alberta_forest_area = gpd.read_file(self.ltg_alberta_forest_area_shapefile)
        print("lightningFirePredictionMapper(): Alberta coordinate system is %s" % str(alberta_map.crs))
        
        # Only load up the data files that we need to pull information from for our maps.
        # Get a new view for the arrivals, if desired.
        if display_historical_fires_on_maps:
            # Use encoding='cp1252' to deal with the Windows "smart quotes" in the historical fires file, 0x92.
            actual_fires_df = pd.read_csv(self.ltg_actual_fire_arrivals_file, sep=',', parse_dates=['reported_date', 'fire_start_date'], encoding='cp1252')
            print("lightningFirePredictionMapper(): Dropping all duplicate lightning strikes / identical rows...")
            actual_fires_df.drop_duplicates(keep='first', inplace=True)
            actual_fires_df.columns = map(str.upper, actual_fires_df.columns)
            actual_fires_df = actual_fires_df[actual_fires_df['GENERAL_CAUSE_DESC'].str.contains("Lightning")]
            print(actual_fires_df['REPORTED_DATE'])
        
        # Load up the necessary files as specified by the method input parameters, and populate dataframes.
        # If map_type == 'all', then we want to open up both data files.
        if map_type in ['arrival', 'holdover', 'all']:

            print("lightningFirePredictionMapper(): Loading gridded prediction file and populating GeoDataFrame...")

            # Load up the grid predictions file and add column headers.
            gridded_predictions_df = pd.read_csv(self.ltg_gridded_predictions_output_path, delim_whitespace=True, header=None)
            gridded_predictions_df.columns = FOPConstantsAndFunctions.LTG_GRIDDED_PREDICTIONS_HEADERS

            # Load up the confidence intervals file and add column headers.
            confidence_intervals_df = pd.read_csv(self.ltg_confidence_intervals_output_path, delim_whitespace=True, header=None)
            confidence_intervals_df.columns = FOPConstantsAndFunctions.LTG_CONFIDENCE_INTERVAL_PREDICTIONS_HEADERS
        
        if map_type in ['probign', 'probarr0', 'DMC', 'DC', 'totltg', 'all']:    

            print("lightningFirePredictionMapper(): Loading FWI / probability file and populating GeoDataFrame...")       

            # Load up the probability file and add column headers.
            probabilities_df = pd.read_csv(self.ltg_arrivals_holdovers_probabilities_output_path, delim_whitespace=True, header=None)
            probabilities_df.columns = FOPConstantsAndFunctions.LTG_PROBABILITY_ARRIVALS_HOLDOVERS_HEADERS
        
        print("lightningFirePredictionMapper(): days_to_map is ", days_to_map)

        # Loop through all of the days that we need to map.
        for date in days_to_map:

            print("lightningFirePredictionMapper(): Now preparing maps for %s ..." % str(date))
            
            # If we are to display historical arrivals, then load up a new view (in the database sense) for this new date.
            if display_historical_fires_on_maps:

                actual_reported_date_fires_df_view = actual_fires_df.loc[((actual_fires_df['REPORTED_DATE']).dt.year == date.year) &
                                                                         ((actual_fires_df['REPORTED_DATE']).dt.month == date.month) &
                                                                         ((actual_fires_df['REPORTED_DATE']).dt.day == date.day)]
                print(actual_reported_date_fires_df_view)

                actual_reported_date_fires_gdf = gpd.GeoDataFrame(actual_reported_date_fires_df_view,
                                                                  crs={'init': 'EPSG:4269'},  # Initialize the coordinate system based on NAD83 lat/long.
                                                                  geometry=gpd.points_from_xy(actual_reported_date_fires_df_view['FIRE_LOCATION_LONGITUDE'],
                                                                                              actual_reported_date_fires_df_view['FIRE_LOCATION_LATITUDE']))
                
                print("actual_reported_date_fires_gdf is ", actual_reported_date_fires_gdf)
                print("YESSSSSS IM IN HEREEEEE!!!!!!!!!")
                # Convert the reported_date fires data to the appropriate projection.
                actual_reported_date_fires_gdf = actual_reported_date_fires_gdf.to_crs(crs=alberta_map.crs, epsg=3400)
                actual_fires_df.dropna(subset=['FIRE_START_DATE'], inplace=True)

                # Convert FIRE_START_DATE to datetime
                actual_fires_df['FIRE_START_DATE'] = pd.to_datetime(actual_fires_df['FIRE_START_DATE'], errors='coerce')

                actual_start_date_fires_df_view = actual_fires_df.loc[((actual_fires_df['FIRE_START_DATE']).dt.year == date.year) &
                                                                      ((actual_fires_df['FIRE_START_DATE']).dt.month == date.month) &
                                                                      ((actual_fires_df['FIRE_START_DATE']).dt.day == date.day)]
                print(actual_start_date_fires_df_view)

                actual_start_date_fires_gdf = gpd.GeoDataFrame(actual_start_date_fires_df_view,
                                                               crs={'init': 'EPSG:4269'},  # Initialize the coordinate system based on NAD83 lat/long.
                                                               geometry=gpd.points_from_xy(actual_start_date_fires_df_view['FIRE_LOCATION_LONGITUDE'],
                                                                                           actual_start_date_fires_df_view['FIRE_LOCATION_LATITUDE']))
                
                # Convert the start_date fires data to the appropriate projection.
                actual_start_date_fires_gdf = actual_start_date_fires_gdf.to_crs(crs=alberta_map.crs, epsg=3400)
            
            # If we are creating a map based on the expected arrivals and holdovers, load up a new view for this new date.
            if map_type in ['arrival', 'holdover', 'all']:

                gridded_predictions_df_view = gridded_predictions_df.loc[(gridded_predictions_df['year'] == date.year) &
                                                                         (gridded_predictions_df['month'] == date.month) &
                                                                         (gridded_predictions_df['day'] == date.day)]
                
                confidence_intervals_df_view = confidence_intervals_df.loc[(confidence_intervals_df['year'] == date.year) &
                                                                           (confidence_intervals_df['month'] == date.month) &
                                                                           (confidence_intervals_df['day'] == date.day)]

                geo_df_arrivals_holdovers = gpd.GeoDataFrame(gridded_predictions_df_view,
                                                             crs={'init': 'EPSG:4269'},  # Initialize the coordinate system based on NAD83 lat/long.
                                                             geometry=gpd.points_from_xy(gridded_predictions_df_view['lon'],
                                                                                         gridded_predictions_df_view['lat']))
                
                # Convert the predictions data to the appropriate projection.
                geo_df_arrivals_holdovers = geo_df_arrivals_holdovers.to_crs(crs=alberta_map.crs, epsg=3400)

            # If we are creating a map based on FWI, raw probabilities, or total lightning, load up a new view for this new date.
            if map_type in ['probign', 'probarr0', 'DMC', 'DC', 'totltg', 'all']:
                
                probabilities_df_view = probabilities_df.loc[(probabilities_df['jd'] == int(date.strftime('%j'))) &
                                                             (probabilities_df['year'] == date.year)]

                geo_df_fwi_probabilities = gpd.GeoDataFrame(probabilities_df_view,
                                                            crs={'init': 'EPSG:4269'},  # Initialize the coordinate system based on NAD83 lat/long.
                                                            geometry=gpd.points_from_xy(probabilities_df_view['lon'],
                                                                                        probabilities_df_view['lat']))
                
                # Convert the FWI data to the appropriate projection.
                geo_df_fwi_probabilities = geo_df_fwi_probabilities.to_crs(crs=alberta_map.crs, epsg=3400)
            
            # Now that are views are updated, generate the maps that we need to for the new day.
            if map_type == 'arrival' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing arrival map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(15, 12)
                alberta_map.plot(ax=ax, alpha=0.2, color='grey')
                alberta_forest_area.plot(ax=ax, alpha=0.1, color='black')
                
                # Display, or don't display, the probability ranges on the map labels depending on the value of FOPConstantsAndFunctions.SHOW_PROBABILITY_ARRIVAL_HOLDOVER_RANGES.
                if FOPConstantsAndFunctions.SHOW_PROBABILITY_ARRIVAL_HOLDOVER_RANGES_IN_LEGEND:
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.1)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme (> 0.10)')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.03) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.1)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High (> 0.03 to 0.10)')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.01) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.03)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High (> 0.01 to 0.03)')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.003) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.01)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate (> 0.003 to 0.010)')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] >= 0.0) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.003)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low (≥ 0.0 to 0.003)')
                else:
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.1)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.03) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.1)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.01) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.03)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.003) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.01)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] >= 0.0) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.003)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low')
                    
                # Add information related to confidence intervals here (with some logic to display either a whole number or float, as appropriate):
            
                print(confidence_intervals_df_view.head())
                last_row = confidence_intervals_df_view.iloc[-1]
                ci_string = '\n'.join((r'Predictions with %s%% confidence' % (str(int(ltg_fire_confidence_interval) if ltg_fire_confidence_interval.is_integer() else ltg_fire_confidence_interval)),
                                        r'Alberta: %d to %d fires' % (last_row['totarrPROV_ci_low'],
                                                                      last_row['totarrPROV_ci_high']),
                                        r'Western Boreal: %d to %d fires' % (last_row['totarrWESTBOREAL_ci_low'],
                                                                             last_row['totarrWESTBOREAL_ci_high']),
                                        r'Eastern Boreal: %d to %d fires' % (last_row['totarrEASTBOREAL_ci_low'],
                                                                             last_row['totarrEASTBOREAL_ci_high']),
                                        r'Eastern Slopes: %d to %d fires' % (last_row['totarrSLOPES_ci_low'],
                                                                             last_row['totarrSLOPES_ci_high'])))
                
                # Hacky way of getting the confidence interval string to appear in the legend.
                plt.plot([], [], ' ', label=ci_string)
                
                # Display actual lightning fires on our map, if desired.
                if display_historical_fires_on_maps and len(actual_reported_date_fires_gdf.index) > 0:
                    actual_reported_date_fires_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Reported lightning-caused fire', edgecolor='black', linewidth=0.5)
                    
                    # Hacky way of getting the total number of historical arrivals to appear in the legend.
                    arrivals_string = (r'Reported lightning-caused fires: %d' % len(actual_reported_date_fires_gdf.index))
                    plt.plot([], [], ' ', label=arrivals_string)
                
                # Add a title to the plot.
                plt.title("Alberta Expected Lightning-Caused Fire Arrival Predictions for " + date.strftime('%Y-%m-%d'))
                
                # Determine if the legend to be plotted will be empty. If there are no handles nor labels, do not add the legend to the plot.
                handles, labels = ax.get_legend_handles_labels()                
                if handles and labels:
                    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

                # Hide the x- and y-axis ticks and labels.
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)

                # Output the generated map to a PNG image.
                plt.savefig(fname=(self.ltg_output_maps_folder + "/ltg_arrival_" + date.strftime('%Y-%m-%d') + ".png"), format='png', dpi=200,
                            bbox_inches='tight', pad_inches=0.25)
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')

            if map_type == 'holdover' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing holdover map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(15, 12)
                alberta_map.plot(ax=ax, alpha=0.2, color='grey')
                alberta_forest_area.plot(ax=ax, alpha=0.1, color='black')

                # Display, or don't display, the probability ranges on the map labels depending on the value of FOPConstantsAndFunctions.SHOW_PROBABILITY_ARRIVAL_HOLDOVER_RANGES.
                if FOPConstantsAndFunctions.SHOW_PROBABILITY_ARRIVAL_HOLDOVER_RANGES_IN_LEGEND:
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.1)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme (> 0.10)')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.05) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.1)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High (> 0.05 to 0.10)')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.02) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.05)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High (> 0.02 to 0.05)')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.005) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.02)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate (> 0.005 to 0.02)')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] >= 0.0) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.005)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low (≥ 0.0 to 0.005)')
                else:
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.1)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.05) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.1)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.02) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.05)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.005) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.02)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate')
                    geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] >= 0.0) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.005)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low')
                
                # Display actual lightning fires on our map, if desired.
                if display_historical_fires_on_maps and len(actual_start_date_fires_gdf.index) > 0:
                    actual_start_date_fires_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning-caused fire start', edgecolor='black', linewidth=0.5)
                    
                    # Hacky way of getting the total number of historical arrivals to appear in the legend.
                    arrivals_string = (r'Lightning-caused fire starts: %d' % len(actual_start_date_fires_gdf.index))
                    plt.plot([], [], ' ', label=arrivals_string)
                
                if ltg_fire_holdover_lookback_time < 0:
                    hlt_string = (r'Holdover lookback time: DC-dependent')
                else:
                    hlt_string = (r'Holdover lookback time (days): %d' % ltg_fire_holdover_lookback_time)
                    
                # Hacky way of getting the holdover lookback time string to appear in the legend.
                plt.plot([], [], ' ', label=hlt_string)

                # Add a title to the plot.
                plt.title("Alberta Expected Lightning-Caused Fire Holdover Predictions for " + date.strftime('%Y-%m-%d'))
                
                # Determine if the legend to be plotted will be empty. If there are no handles nor labels, do not add the legend to the plot.
                handles, labels = ax.get_legend_handles_labels()                
                if handles and labels:
                    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

                # Hide the x- and y-axis ticks and labels.
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)

                # Output the generated map to a PNG image.
                plt.savefig(fname=(self.ltg_output_maps_folder + "/ltg_holdover_" + date.strftime('%Y-%m-%d') + ".png"), format='png', dpi=200,
                            bbox_inches='tight', pad_inches=0.25)
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')

            if map_type == 'probign' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing probability of ignition map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(15, 12)
                alberta_map.plot(ax=ax, alpha=0.2, color='grey')
                alberta_forest_area.plot(ax=ax, alpha=0.1, color='black')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0.025)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme (> 0.025)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0.015) & (geo_df_fwi_probabilities['probign'] <= 0.025)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High (> 0.015 to 0.025)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0.005) & (geo_df_fwi_probabilities['probign'] <= 0.015)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High (> 0.005 to 0.015)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0.001) & (geo_df_fwi_probabilities['probign'] <= 0.005)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate (> 0.010 to 0.005)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0) & (geo_df_fwi_probabilities['probign'] <= 0.001)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low (> 0.000 to 0.001)')
                
                # Display actual lightning strikes on our map, if desired.
                if display_historical_fires_on_maps and len(actual_start_date_fires_gdf.index) > 0:
                    actual_start_date_fires_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning-caused fire start', edgecolor='black', linewidth=0.5)

                    # Hacky way of getting the total number of historical arrivals to appear in the legend.
                    arrivals_string = (r'Lightning-caused fire starts: %d' % len(actual_start_date_fires_gdf.index))
                    plt.plot([], [], ' ', label=arrivals_string)

                # Add a title to the plot.
                plt.title("Alberta Probability of Lightning Fire Ignitions (\"probign\") for " + date.strftime('%Y-%m-%d'))
                
                # Determine if the legend to be plotted will be empty. If there are no handles nor labels, do not add the legend to the plot.
                handles, labels = ax.get_legend_handles_labels()                
                if handles and labels:
                    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

                # Hide the x- and y-axis ticks and labels.
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)

                # Output the generated map to a PNG image.
                plt.savefig(fname=(self.ltg_output_maps_folder + "/ltg_probign_" + date.strftime('%Y-%m-%d') + ".png"), format='png', dpi=200,
                            bbox_inches='tight', pad_inches=0.25)
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')

            if map_type == 'probarr0' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing probability of arrivals \"0\" map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(15, 12)
                alberta_map.plot(ax=ax, alpha=0.2, color='grey')
                alberta_forest_area.plot(ax=ax, alpha=0.1, color='black')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0.85)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme (> 0.85)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0.75) & (geo_df_fwi_probabilities['probarr0'] <= 0.85)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High (> 0.75 to 0.85)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0.55) & (geo_df_fwi_probabilities['probarr0'] <= 0.75)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High (> 0.55 to 0.75)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0.3) & (geo_df_fwi_probabilities['probarr0'] <= 0.55)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate (> 0.30 to 0.55)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0) & (geo_df_fwi_probabilities['probarr0'] <= 0.3)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low (> 0.00 to 0.30)')
                
                # Display actual lightning fires on our map, if desired.
                if display_historical_fires_on_maps and len(actual_start_date_fires_gdf.index) > 0:
                    actual_start_date_fires_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning-caused fire start', edgecolor='black', linewidth=0.5)

                    # Hacky way of getting the total number of historical arrivals to appear in the legend.
                    arrivals_string = (r'Lightning-caused fire starts: %d' % len(actual_start_date_fires_gdf.index))
                    plt.plot([], [], ' ', label=arrivals_string)

                # Add a title to the plot.
                plt.title("Alberta Probability of Lightning Fire Arrivals (\"probarr0\") for " + date.strftime('%Y-%m-%d'))
                
                # Determine if the legend to be plotted will be empty. If there are no handles nor labels, do not add the legend to the plot.
                handles, labels = ax.get_legend_handles_labels()                
                if handles and labels:
                    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

                # Hide the x- and y-axis ticks and labels.
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)

                # Output the generated map to a PNG image.
                plt.savefig(fname=(self.ltg_output_maps_folder + "/ltg_probarr0_" + date.strftime('%Y-%m-%d') + ".png"), format='png', dpi=200,
                            bbox_inches='tight', pad_inches=0.25)
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')
            
            if map_type == 'DMC' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing DMC map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(15, 12)
                alberta_map.plot(ax=ax, alpha=0.2, color='grey')
                alberta_forest_area.plot(ax=ax, alpha=0.1, color='black')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] > 60)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme (61+)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] > 40) & (geo_df_fwi_probabilities['dmc'] <= 60)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High (41 to 60)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] > 27) & (geo_df_fwi_probabilities['dmc'] <= 40)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High (28 to 40)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] > 21) & (geo_df_fwi_probabilities['dmc'] <= 27)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate (22 to 27)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] >= 0) & (geo_df_fwi_probabilities['dmc'] <= 21)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low (0 to 21)')
                
                # Add a title to the plot.
                plt.title("DMC for " + date.strftime('%Y-%m-%d'))
                
                # Determine if the legend to be plotted will be empty. If there are no handles nor labels, do not add the legend to the plot.
                handles, labels = ax.get_legend_handles_labels()                
                if handles and labels:
                    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

                # Hide the x- and y-axis ticks and labels.
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)

                # Output the generated map to a PNG image.
                plt.savefig(fname=(self.ltg_output_maps_folder + "/ltg_dmc_" + date.strftime('%Y-%m-%d') + ".png"), format='png', dpi=200,
                            bbox_inches='tight', pad_inches=0.25)
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')
            
            if map_type == 'DC' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing DC map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(15, 12)
                alberta_map.plot(ax=ax, alpha=0.2, color='grey')
                alberta_forest_area.plot(ax=ax, alpha=0.1, color='black')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] > 424)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme (425+)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] > 299) & (geo_df_fwi_probabilities['dc'] <= 424)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High (300 to 424)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] > 189) & (geo_df_fwi_probabilities['dc'] <= 299)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High (190 to 299)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] > 79) & (geo_df_fwi_probabilities['dc'] <= 189)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate (80 to 189)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] >= 0) & (geo_df_fwi_probabilities['dc'] <= 79)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low (0 to 79)')
                
                # Add a title to the plot.
                plt.title("DC for " + date.strftime('%Y-%m-%d'))
                
                # Determine if the legend to be plotted will be empty. If there are no handles nor labels, do not add the legend to the plot.
                handles, labels = ax.get_legend_handles_labels()                
                if handles and labels:
                    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

                # Hide the x- and y-axis ticks and labels.
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)

                # Output the generated map to a PNG image.
                plt.savefig(fname=(self.ltg_output_maps_folder + "/ltg_dc_" + date.strftime('%Y-%m-%d') + ".png"), format='png', dpi=200,
                            bbox_inches='tight', pad_inches=0.25)
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')
            
            if map_type == 'totltg' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing totltg map...")
                        
                # Create a new figure and plot the Alberta basemap.
                fig, ax = plt.subplots()
                fig.set_size_inches(15, 12)
                alberta_map.plot(ax=ax, alpha=0.2, color='grey')
                alberta_forest_area.plot(ax=ax, alpha=0.1, color='black')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 12)].plot(ax=ax, markersize=9, color='red', marker='s', label='Extreme (> 12 strikes)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 6) & (geo_df_fwi_probabilities['totltg'] <= 12)].plot(ax=ax, markersize=9, color='orange', marker='s', label='Very High (> 6 to 12 strikes)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 3) & (geo_df_fwi_probabilities['totltg'] <= 6)].plot(ax=ax, markersize=9, color='yellow', marker='s', label='High (> 3 to 6 strikes)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 1) & (geo_df_fwi_probabilities['totltg'] <= 3)].plot(ax=ax, markersize=9, color='green', marker='s', label='Moderate (> 1 to 3 strikes)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 0) & (geo_df_fwi_probabilities['totltg'] <= 1)].plot(ax=ax, markersize=9, color='blue', marker='s', label='Low (> 0 to 1 strike)')
                
                # Display actual lightning fires on our map, if desired.
                if display_historical_fires_on_maps and len(actual_reported_date_fires_gdf.index):
                    actual_reported_date_fires_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Reported lightning-caused fire', edgecolor='black', linewidth=0.5)

                    # Hacky way of getting the total number of historical arrivals to appear in the legend.
                    arrivals_string = (r'Reported lightning-caused fires: %d' % len(actual_reported_date_fires_gdf.index))
                    plt.plot([], [], ' ', label=arrivals_string)

                # Add a title to the plot.
                plt.title("Alberta Total Lightning Strikes (\"totltg\") for " + date.strftime('%Y-%m-%d'))

                # Determine if the legend to be plotted will be empty. If there are no handles nor labels, do not add the legend to the plot.
                handles, labels = ax.get_legend_handles_labels()                
                if handles and labels:
                    plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

                # Hide the x- and y-axis ticks and labels.
                ax.xaxis.set_visible(False)
                ax.yaxis.set_visible(False)

                # Output the generated map to a PNG image.
                plt.savefig(fname=(self.ltg_output_maps_folder + "/ltg_totltg_" + date.strftime('%Y-%m-%d') + ".png"), format='png', dpi=200,
                            bbox_inches='tight', pad_inches=0.25)
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')

        # End for loop
    
    def lightningStrikeDataMassager(self, input_df):
        """ This method massages raw Alberta lightning data into the format required for
            Dr. Wotton's lightning gridder/binner C program.

            Input column headers:
            "LOCAL_STRIKETIME", "LATITUDE", "LONGITUDE", "STRENGTH", "MULTIPLICITY"

            Output format (no header, sorted chronologically - VERY IMPORTANT):
            LATITUDE, LONGITUDE, STRENGTH, MULTIPLICITY, YEAR, MONTH, DAY, HOUR
        """
        
        print("lightningStrikeDataMassager(): Massaging raw lightning data...")

        # Apply column-wide operations.
        print("lightningStrikeDataMassager(): Massaging raw lightning data - LATITUDE / LONGITUDE...")
        input_df['LATITUDE'] = input_df['LATITUDE'].apply(lambda x : round(float(x), 4))
        input_df['LONGITUDE'] = input_df['LONGITUDE'].apply(lambda x : round(float(x), 4))
        
        print("lightningStrikeDataMassager(): Massaging raw lightning data - STRENGTH...")
        input_df['STRENGTH'] = input_df['STRENGTH'].apply(lambda x : round(float(x), 1))
        
        print("lightningStrikeDataMassager(): Massaging raw lightning data - YEAR / MONTH / DAY / HOUR...")
        input_df['YEAR'] = input_df['LOCAL_STRIKETIME'].apply(lambda x : x.year)
        input_df['MONTH'] = input_df['LOCAL_STRIKETIME'].apply(lambda x : x.month)
        input_df['DAY'] = input_df['LOCAL_STRIKETIME'].apply(lambda x : x.day)
        input_df['HOUR'] = input_df['LOCAL_STRIKETIME'].apply(lambda x : x.hour)

        print("lightningStrikeDataMassager(): Massaging raw lightning data - Applying column types...")
        input_df['MULTIPLICITY'] = input_df['MULTIPLICITY'].astype('int32')
        input_df['YEAR'] = input_df['YEAR'].dt.year.astype('int32')
        input_df['MONTH'] = input_df['MONTH'].dt.month.astype('int32')
        input_df['DAY'] = input_df['DAY'].dt.day.astype('int32')
        input_df['HOUR'] = input_df['HOUR'].dt.hour.astype('int32')
        
        print("lightningStrikeDataMassager(): Massaging raw lightning data - Drop LOCAL_STRIKETIME column...")
        input_df = input_df.drop('LOCAL_STRIKETIME', axis=1)

        print(input_df)

        # Write the massaged output to disk. This file will be used as input to Dr. Wotton's lightning binning library.
        # No column headers, no index column, tab-separated.
        # output_csv_df.to_csv(self.ltg_strike_raw_massaged_output_path, sep=' ', header=False, index=False)
        print("lightningStrikeDataMassager(): Outputting massaged lightning data to disk...")
        input_df.to_csv(self.ltg_strike_raw_massaged_output_path, sep=' ', header=False, index=False)

        print("lightningStrikeDataMassager(): Raw lightning strike data massaged successfully.")
    
    def lightningBinnerWrapper(self):
        """ Calls the wrapped lightning binner, feeding it the massaged lightning strike
            data.
            Here, we use subprocess.call as opposed to subprocess.Popen because subprocess.call
            is blocking; we need the external call to finish before we carry on with other stages of
            the processing flow. """
        
        print("lightningBinnerWrapper(): Calling lightning binner exe...")
        # Sample command line arguments call: "Y:\\University of Alberta\\Software Development\\FireOccurrencePrediction\\lightning\\binning\\Gridlocations.prn", "Z:\\LightningFireOccurrencePredictionInputs\\ABltg_space_MATT.out", "Z:\\LightningFireOccurrencePredictionInputs\\ltg2010-20by20-five-period.dat")
        subprocess.call([self.lightning_wrapper_exe_path, self.ltg_grid_locations_path, self.ltg_strike_raw_massaged_output_path, self.ltg_lightning_binned_output_path])
        print("lightningBinnerWrapper(): Lightning binner exe call completed.")
    
    def weatherInterpolationBinnerWrapper(self):
        """ Calls the wrapped weather interpolation and binning tools, feeding it the massaged weather data.
            Here, we use subprocess.call as opposed to subprocess.Popen because subprocess.call
            is blocking; we need the external call to finish before we carry on with other stages of
            the processing flow. """
        
        print("weatherInterpolationBinnerWrapper(): Calling weather interpolation exe...")
        print("weatherInterpolationBinnerWrapper(): self.ltg_weather_interpolation_coefficients_path is %s" % self.ltg_weather_interpolation_coefficients_path)
        # raw_input("Press Enter to continue . . .")

        subprocess.call([self.weather_interpolation_exe_path, self.ltg_weather_massaged_output_path, self.ltg_weather_interpolation_coefficients_path])
        print("weatherInterpolationBinnerWrapper(): Weather interpolation exe call completed.")

        print("weatherInterpolationBinnerWrapper(): Calling weather binner exe...")
        subprocess.call([self.weather_binning_exe_path, self.ltg_weather_binned_output_path, self.ltg_grid_locations_path, self.ltg_weather_interpolation_coefficients_path])
        print("weatherInterpolationBinnerWrapper(): Weather binning exe call completed.")
    
    def simulationWrapper(self, start_day, end_day, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval):
        """ Calls the wrapped simulation tool, feeding it the massaged probability data.
            The simulation tool will produce two output files: one will contain the expected number
            of lightning-caused fires and holdovers on the landscape, and the other will contain
            the confidence interval data.
            
            Here, we use subprocess.call as opposed to subprocess.Popen because subprocess.call
            is blocking; we need the external call to finish before we carry on with other stages of
            the processing flow. """
        
        # Seed the random number generator using the current system time.
        random.seed(datetime.datetime.now())
        
        print("simulationWrapper(): Calling simulation exe for a start day of %s, an end date of %s, a lightning fire holdover lookback time of %d, and a confidence interval of %.1f..." % (str(start_day), str(end_day), ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval))
        # Sample command line arguments call: simulate-new-allyears.exe 12345 "Z:\\LightningFireOccurrencePredictionInputs\\ltg_output.csv" "Z:\\LightningFireOccurrencePredictionInputs\\AB-predictions.out" "Z:\\LightningFireOccurrencePredictionInputs\\AB-grids.out" 121 125
        subprocess.call([self.simulation_exe_path,
                         str(random.randint(1, FOPConstantsAndFunctions.MAX_INT)),
                         self.ltg_arrivals_holdovers_probabilities_output_path,
                         self.ltg_confidence_intervals_output_path,
                         self.ltg_gridded_predictions_output_path,
                         str(start_day),
                         str(end_day),
                         str(ltg_fire_holdover_lookback_time),
                         str(ltg_fire_confidence_interval)])
        print("simulationWrapper(): Simulation exe call completed.")
    
    def createGridLocationsFromWeatherStationLocationsAndTest(self):
        """ This debugging method will take in the weather station locations file and produce another file
            analogous in format to the GridLocations.prn file.

            This file can then be used to test the behaviour of the weather interpolation and binning
            C files."""

        # Load in the weather station locations file.
        input_weather_station_locations_df = pd.read_csv(self.ltg_weather_station_locations_path, sep=',', quotechar='"',
                                                      dtype={'id': int, 'station_name': str})
        
        new_grid_locations_df = input_weather_station_locations_df[['id','latitude','longitude']].sort_values('id')

        
        print("createGridLocationsFromWeatherStationLocations(): new_grid_locations_df is:")
        print(new_grid_locations_df)
        
        new_grid_locations_df.to_csv(self.ltg_debugging_weather_station_grid_locations_path, sep=' ', header=False, index=False)

        print("weatherInterpolationWrapper(): Calling weather interpolation exe...")
        print("weatherInterpolationWrapper(): self.ltg_weather_interpolation_coefficients_path is %s" % self.ltg_weather_interpolation_coefficients_path)
        # raw_input("Press Enter to continue . . .")

        subprocess.call([self.weather_interpolation_exe_path, self.ltg_weather_massaged_output_path, self.ltg_weather_interpolation_coefficients_path])
        print("weatherInterpolationWrapper(): Weather interpolation exe call completed.")

        print("weatherInterpolationWrapper(): Calling weather binner exe...")
        subprocess.call([self.weather_binning_exe_path, self.ltg_weather_binned_output_path, self.ltg_debugging_weather_station_grid_locations_path, self.ltg_weather_interpolation_coefficients_path])
        print("weatherInterpolationWrapper(): Weather binning exe call completed.")
    
    def mergeBinnedWeatherAndLightning(self):
        """ This method will take in the binned weather and lightning data, and combine it into a single
            dataset.

            Once this is completed, the merged dataset can then be used by the
            processLightningArrivalsHoldoversIgnitions() method to compute probabilities of arrivals and
            holdovers. """

        # For the binned lightning CSV, treat multiple consecutive whitespace characters as a
        # single delimeter.
        print("mergeBinnedWeatherAndLightning(): Loading binned weather intermediate data file...")
        input_binned_weather_df = pd.read_csv(self.ltg_weather_binned_output_path, sep=',', header=None)
        input_binned_weather_df.columns = FOPConstantsAndFunctions.INTERPOLATED_BINNED_WEATHER_DATA_HEADERS
                                                 
        print("mergeBinnedWeatherAndLightning(): Loading binned lightning intermediate data file...")
        try:
            print("mergeBinnedWeatherAndLightning(): self.ltg_lightning_binned_output_path is %s" % self.ltg_lightning_binned_output_path)
            input_binned_lightning_df = pd.read_csv(self.ltg_lightning_binned_output_path, header=None, delim_whitespace=True, error_bad_lines=False)
            input_binned_lightning_df.columns = ['grid', 'latitude', 'longitude', 'year', 'month', 'day',
                                                 'period', 'neg', 'pos']
        except pandas.io.common.EmptyDataError as e:
            print("mergeBinnedWeatherAndLightning(): pandas.io.common.EmptyDataError exception thrown, but not critical!")
            print(e)
            print("mergeBinnedWeatherAndLightning(): Setting the binned lightning dataframe to be empty . . .")
            input_binned_lightning_df = pd.DataFrame(columns=['grid', 'latitude', 'longitude', 'year', 'month', 'day',
                                                              'period', 'neg', 'pos'])                       
        
        # Swap the ordering of the neg and pos columns.
        new_columns = ['grid', 'latitude', 'longitude', 'year', 'month', 'day', 'period', 'pos', 'neg']
        input_binned_lightning_df = input_binned_lightning_df.reindex(columns=new_columns)   

        print("mergeBinnedWeatherAndLightning(): Merging tables...")
        merged_lightning_weather_df = pd.merge(input_binned_weather_df, input_binned_lightning_df,
                                                how="outer", on=["grid", "year", "month", "day"])

        print("mergeBinnedWeatherAndLightning(): Table merge completed, massaging data...")

        # Drop the latitude and longitude columns.
        #merged_lightning_weather_df = merged_lightning_weather_df.drop('latitude', axis=1)
        #merged_lightning_weather_df = merged_lightning_weather_df.drop('longitude', axis=1)

        # Add a new column called numfire, place it as the 14th column, and assign it 0 values.
        merged_lightning_weather_df.insert(loc=14, column='numfire', value=0)

        # Add a new column for pos/neg strikes per period, place them as the 16th...nth columns, and assign them 0 values for now.
        merged_lightning_weather_df.insert(loc=16, column='neg4', value=0)
        merged_lightning_weather_df.insert(loc=16, column='pos4', value=0)
        merged_lightning_weather_df.insert(loc=16, column='neg3', value=0)
        merged_lightning_weather_df.insert(loc=16, column='pos3', value=0)
        merged_lightning_weather_df.insert(loc=16, column='neg2', value=0)
        merged_lightning_weather_df.insert(loc=16, column='pos2', value=0)
        merged_lightning_weather_df.insert(loc=16, column='neg1', value=0)
        merged_lightning_weather_df.insert(loc=16, column='pos1', value=0)
        merged_lightning_weather_df.insert(loc=16, column='neg0', value=0)
        merged_lightning_weather_df.insert(loc=16, column='pos0', value=0)

        # Replace all of the nan values in the period, neg and pos columns.
        merged_lightning_weather_df['period'].fillna(0, inplace=True)        
        merged_lightning_weather_df['neg'].fillna(0, inplace=True)
        merged_lightning_weather_df['pos'].fillna(0, inplace=True)

        # Set the appropriate column type for period, neg and pos.
        merged_lightning_weather_df['period'] = merged_lightning_weather_df['period'].astype('int32')
        merged_lightning_weather_df['neg'] = merged_lightning_weather_df['neg'].astype('int32')
        merged_lightning_weather_df['pos'] = merged_lightning_weather_df['pos'].astype('int32')

        # Assign the appropriate values to the new period-based pos and neg columns based on
        # what the value in the period column is.
        # Period 0.
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==0, 'neg0'] = merged_lightning_weather_df['neg']
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==0, 'pos0'] = merged_lightning_weather_df['pos']
        merged_lightning_weather_df['nltg0'] = merged_lightning_weather_df['pos0'] + merged_lightning_weather_df['neg0']
        
        # Period 1.
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==1, 'neg1'] = merged_lightning_weather_df['neg']
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==1, 'pos1'] = merged_lightning_weather_df['pos']
        merged_lightning_weather_df['nltg1'] = merged_lightning_weather_df['pos1'] + merged_lightning_weather_df['neg1']
        
        # Period 2.
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==2, 'neg2'] = merged_lightning_weather_df['neg']
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==2, 'pos2'] = merged_lightning_weather_df['pos']
        merged_lightning_weather_df['nltg2'] = merged_lightning_weather_df['pos2'] + merged_lightning_weather_df['neg2']

        # Period 3.
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==3, 'neg3'] = merged_lightning_weather_df['neg']
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==3, 'pos3'] = merged_lightning_weather_df['pos']
        merged_lightning_weather_df['nltg3'] = merged_lightning_weather_df['pos3'] + merged_lightning_weather_df['neg3']

        # Period 4.
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==4, 'neg4'] = merged_lightning_weather_df['neg']
        merged_lightning_weather_df.loc[merged_lightning_weather_df['period']==4, 'pos4'] = merged_lightning_weather_df['pos']
        merged_lightning_weather_df['nltg4'] = merged_lightning_weather_df['pos4'] + merged_lightning_weather_df['neg4']

        # Drop the period column.
        merged_lightning_weather_df = merged_lightning_weather_df.drop(columns='period')

        # Rename the "month" column to "mon".
        merged_lightning_weather_df = merged_lightning_weather_df.rename(columns={"month": "mon"})

        # Read in the file which will help us tie fishnet grid # to lat/long, zone and NSR name, etc.
        input_fishnet_nsr_dr = pd.read_csv(self.ltg_fishnet_nsr_path, sep=',')
        input_fishnet_nsr_dr = input_fishnet_nsr_dr.rename(columns={"fishnet_AB": "grid"})
        input_fishnet_nsr_dr['grid'] = input_fishnet_nsr_dr['grid'].astype('int32')

        # Merge rows together that have a common grid, year, mon and day, as well as all other features EXCEPT for the period-based
        # lightning strikes.
        # The goal is to 'sum' the pos0, neg0, ..., pos4, neg4 columns after the groupby SQL operation.
        merged_lightning_weather_df = merged_lightning_weather_df.groupby(['year', 'mon', 'day', 'grid', 'temp', 'rh', 'ws', 'rain', 'ffmc', 'dmc', 'dc', 'isi', 'bui', 'fwi']).sum()
        merged_lightning_weather_df = merged_lightning_weather_df.reset_index()

        # Add a new "timing" column that will take the value of "DAY" or "NIGHT" depending on whether more lightning strokes happen
        # during the day periods or night periods (night wins in the event of a tie)
        merged_lightning_weather_df['timing'] = ''
        merged_lightning_weather_df.loc[(merged_lightning_weather_df.pos0 +
                                         merged_lightning_weather_df.neg0 +
                                         merged_lightning_weather_df.pos4 +
                                         merged_lightning_weather_df.neg4) >=
                                        (merged_lightning_weather_df.pos1 +
                                         merged_lightning_weather_df.neg1 +
                                         merged_lightning_weather_df.pos2 +
                                         merged_lightning_weather_df.neg2 +
                                         merged_lightning_weather_df.pos3 +
                                         merged_lightning_weather_df.neg3), 'timing'] = "NIGHT"
        merged_lightning_weather_df.loc[(merged_lightning_weather_df.pos0 +
                                         merged_lightning_weather_df.neg0 +
                                         merged_lightning_weather_df.pos4 +
                                         merged_lightning_weather_df.neg4) <
                                        (merged_lightning_weather_df.pos1 +
                                         merged_lightning_weather_df.neg1 +
                                         merged_lightning_weather_df.pos2 +
                                         merged_lightning_weather_df.neg2 +
                                         merged_lightning_weather_df.pos3 +
                                         merged_lightning_weather_df.neg3), 'timing'] = "DAY"
        
        # Add a new "totltg" column which is the sum of the neg and pos columns.
        merged_lightning_weather_df['totltg'] = merged_lightning_weather_df['pos'] + merged_lightning_weather_df['neg']        

        # Excel formula for double-checking the correctness of the period-based day / night timing:
        # =IF(OR((AND((AD2 + AH2 >= AE2 + AF2 + AG2),(AI2="NIGHT"))),((AND((AD2 + AH2 < AE2 + AF2 + AG2),(AI2="DAY"))))),0,1)

        # Add three columns to the dataset: ZONE_CODE, NSR, and NSRNAME, using this fancy merge function.
        merged_lightning_weather_df['ZONE_CODE'] = merged_lightning_weather_df[['grid']].merge(input_fishnet_nsr_dr, how='left').ZONE_CODE   
        merged_lightning_weather_df['NSR'] = merged_lightning_weather_df[['grid']].merge(input_fishnet_nsr_dr, how='left').NSR

        # NSR is 'region' in the simulation code.
        merged_lightning_weather_df['NSRNAME'] = merged_lightning_weather_df[['grid']].merge(input_fishnet_nsr_dr, how='left').NSRNAME

        # Do the same for latitude and longitude; populate the entire column using gridlocations.prn.
        # Using engine='python' because we want to be able to parse consecutive whitespace as a single separator, and the
        # default C engine in pandas does not support it.
        grid_locations_df = pd.read_csv(self.ltg_grid_locations_path, delim_whitespace=True, header=None)
        grid_locations_df.columns = ['grid', 'latitude', 'longitude']

        merged_lightning_weather_df['latitude'] = merged_lightning_weather_df[['grid']].merge(grid_locations_df, how='left').latitude
        merged_lightning_weather_df['longitude'] = merged_lightning_weather_df[['grid']].merge(grid_locations_df, how='left').longitude

        # Rename the latitude and longitude columns to lat and lon.
        merged_lightning_weather_df = merged_lightning_weather_df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})

        # Rearrange the column headers so that 'grid' is first, followed by 'lat', and then by 'long'.
        column_headers = merged_lightning_weather_df.columns.tolist()
        column_headers.insert(0, column_headers.pop(column_headers.index('grid')))        
        column_headers.insert(1, column_headers.pop(column_headers.index('lat')))
        column_headers.insert(2, column_headers.pop(column_headers.index('lon')))
        merged_lightning_weather_df = merged_lightning_weather_df[column_headers]

        print(merged_lightning_weather_df)
        # raw_input("Press enter to continue...")

        print("mergeBinnedWeatherAndLightning(): Data massaging completed, outputting table to disk...")

        # Output the merged and massaged dataset.
        merged_lightning_weather_df.to_csv(self.ltg_merged_weather_lightning_data_path, sep=',', index=False)

        print("mergeBinnedWeatherAndLightning(): Table has been outputted to disk.")

    def computeArrivalHoldoverIgnitionProbabilities(self):
        """ For each line of input, this method will append two columns containing probability
            values:

            probarr0 = The probability that a fire arrives on the day it is ignited by lightning;
            probarr1 = The probability that a fire arrives the day after ignition. """
            
        print ("computeArrivalHoldoverIgnitionProbabilities(): Calculating fire arrivals probabilities...")
        
        input_file_handle = open(self.ltg_merged_weather_lightning_data_path, 'r')
        input_csv_file = csv.reader(input_file_handle, quotechar='|')

        # We want to append the new dates to the existing probability dataset.        
        # Need to add newline='' parameter so that Python 3 does not add an extra carriage return (\r\r\n) to the output file.       
        output_file_handle = open(self.ltg_arrivals_holdovers_probabilities_output_path, 'a', newline='')
        output_csv_file = csv.writer(output_file_handle, quotechar='|', delimiter=' ')

        # Retain the first line of the file, which is the header.
        input_csv_header = next(input_csv_file)

        # The output CSV header has two more columns, one for each of the computed
        # probabilities.
        # We want a new list, not a list reference, which is why we use [:] here.
        #output_csv_header = input_csv_header[:]
        
        # Delete irrelevent columns from the output header list.
        # output_csv_header = filter(lambda a: a not in ['neg', 'rh', 'ws', 'rain', 'isi',
        #                                                'pos', 'timing', 'ZONE_CODE', 'NSRNAME',
        #                                                'mon', 'day', 'temp', 'ffmc', 'bui',
        #                                                'fwi', 'pos0', 'neg0', 'pos1', 'neg1',
        #                                                'pos2', 'neg2', 'pos3', 'neg3', 'pos4',
        #                                                'neg4'], output_csv_header)

        # output_csv_header.extend(['probarr0', 'probarr1', 'probign', 'jd'])
        
        # Move the jd (Julian date) column to the 5th position.
        # output_csv_header.insert(4, output_csv_header.pop(output_csv_header.index('jd'))) 

        ###################################################################################################### 

        # The columns required by Dr. Wotton's C simulation program.
        output_csv_header = ['grid', 'lat', 'lon', 'year', 'jd', 'probign', 'probarr0', 'probarr1', 'totltg',
                             'numfire', 'region', 'nltg0', 'nltg1', 'nltg2', 'nltg3', 'nltg4', 'dmc', 'dc']
        
        # Output csv header not required.
        # output_csv_file.writerow(output_csv_header)

        i = 0
        processed = 0
        for next_row in input_csv_file:
            assert(len(input_csv_header) == len(next_row))

            i = i + 1
            processed = processed + 1
            if i % 2500 == 0:           
                print("computeArrivalHoldoverIgnitionProbabilities(): Currently on row %d..." % i)

            # if i == 30270:
            #     break  # Break out of the for loop if we get past i.

            # For easy and per-row data manipulation and referencing, use a dictionary
            # data structure. Its keys will be the input CSV header, and their corresponding
            # values will be those of the current row.
            working_dict = dict(zip(input_csv_header, next_row))
            
            # Mike: Just a rough seasonal separation pre-flush/post-flush.

            if int(working_dict['mon']) < 6:
                season = "Spring"
            else:
                season = "Summer"
            
            # Mike: For modelling... not enough lightning fire data outside these dates
            if int(working_dict['mon']) < 5 or int(working_dict['mon']) > 9:
                processed = processed - 1  # Decrement processed because this row will not get processed.
                continue  # Skip the current row and go on to the next one.

            # Note: Commented out in Mike's code?
            # if working_dict['zone_code'] == '':
            #     continue

            if working_dict['NSR'] == '':
                processed = processed - 1  # Decrement i because this row will not get processed.
                continue  # Skip the current row and go on to the next one.
            
            if float(working_dict['ffmc']) < 0:
                working_dict['ffmc'] = ''
            
            if float(working_dict['dmc']) < 0:
                working_dict['dmc'] = ''
            
            if float(working_dict['ws']) < 0:
                working_dict['ws'] = ''
            
            if int(working_dict['ZONE_CODE']) == 10:
                working_dict['ZONE_CODE'] = 9
            
            # Mike: IMPORTANT: RECASTING some small NSRs that had few ltg fires into
            # neighbors.
            if int(working_dict['NSR']) == 15:
                working_dict['NSR'] = 1
            
            if int(working_dict['NSR']) == 18:
                working_dict['NSR'] = 11
            
            if int(working_dict['NSR']) == 14:
                working_dict['NSR'] = 11
            
            if int(working_dict['NSR']) == 5:
                working_dict['NSR'] = 12
            
            if int(working_dict['NSR']) == 7:
                working_dict['NSR'] = 8
            
            int_season = 0  # Mike: Default to summer
            ffmc_season = 0  # Mike: Default to summer

            if season == "Spring":
                int_season = -2.33
                ffmc_season = 0.023
            
            int_first = 2.54
            dmc_first = -0.013
            ws_first = -0.041

            # Mike: The complex set of coefficients here is how they change with NSR...
            # and the interations between NSR and the core predictors... SO that is
            # what this next stuff is about.

            int_nsr = 0.0
            ffmc_nsr = 0.0
            dmc_nsr = 0.0
            dc_nsr = 0.0

            if int(working_dict['NSR']) == 1:
                int_nsr = -0.279
                ffmc_nsr = 0.0011
                dmc_nsr = 0.0033
                dc_nsr = -0.0005
            
            if int(working_dict['NSR']) == 2:
                int_nsr = 0.8539
                ffmc_nsr = -0.014
                dmc_nsr = 0.0064
                dc_nsr = -0.0007
            
            if int(working_dict['NSR']) == 3:
                int_nsr = -0.768
                ffmc_nsr = 0.0099
                dmc_nsr = -0.0043
                dc_nsr = 0.0002
            
            if int(working_dict['NSR']) == 4:
                int_nsr = 0.466
                ffmc_nsr = -0.0056
                dmc_nsr = 0.0232
                dc_nsr = -0.0023
            
            if int(working_dict['NSR']) == 6:
                int_nsr = -0.373
                ffmc_nsr = 0.0105
                dmc_nsr = -0.0057
                dc_nsr = -0.0014
            
            if int(working_dict['NSR']) == 8:
                int_nsr = 1.45
                ffmc_nsr = -0.0221
                dmc_nsr = 0.0098
                dc_nsr = -0.002
            
            if int(working_dict['NSR']) == 9:
                int_nsr = 1.523
                ffmc_nsr = -0.0307
                dmc_nsr = 0.0032
                dc_nsr = 0.0002
            
            if int(working_dict['NSR']) == 10:
                int_nsr = 1.1089
                ffmc_nsr = -0.0150
                dmc_nsr = 0.0225
                dc_nsr = -0.0023
            
            if int(working_dict['NSR']) == 11:
                int_nsr = 1.19
                ffmc_nsr = -0.0164
                dmc_nsr = 0.0217
                dc_nsr = -0.0028
            
            if int(working_dict['NSR']) == 12:
                int_nsr = -1.0345
                ffmc_nsr = 0.0039
                dmc_nsr = -0.0042
                dc_nsr = 0.0019
            
            if int(working_dict['NSR']) == 13:
                int_nsr = -1.47
                ffmc_nsr = -0.0009
                dmc_nsr = 0.0042
                dc_nsr = 0.0022
            
            # Probability calculations.
            pr0 = (-4.223 + int_nsr + int_season + int_first) + \
                  float(working_dict['ffmc']) * (0.0447 + ffmc_nsr + ffmc_season) + \
                  float(working_dict['dmc']) * (0.0186 + dmc_first + dmc_nsr) + \
                  float(working_dict['dc']) * (-0.0026 + dc_nsr) + \
                  float(working_dict['ws']) * (-0.01 + ws_first)
            
            pr1 = (-4.223 + int_nsr + int_season + 0) + \
                  float(working_dict['ffmc']) * (0.0447 + ffmc_nsr + ffmc_season) + \
                  float(working_dict['dmc']) * (0.0186 + 0 + dmc_nsr) + \
                  float(working_dict['dc']) * (-0.0026 + dc_nsr) + \
                  float(working_dict['ws']) * (-0.01 + 0)
            
            # Prob. that a fire arrives on the day it is ignited.
            # prob_arr0 = Decimal(math.exp(pr0) / (1 + math.exp(pr0)))
            # working_dict['probarr0'] = round(prob_arr0, 10)  # 10 decimal places to match Mike
            # self.prob_arr0.append(prob_arr0)

            prob_arr0 = math.exp(pr0) / (1 + math.exp(pr0))
            working_dict['probarr0'] = ('{0:.10f}'.format(prob_arr0)).rstrip('0')  # 10 decimal places            

            # Prob. that a fire arrives any day after ignition.
            # prob_arr1 = Decimal(math.exp(pr1) / (1 + math.exp(pr1)))
            # working_dict['probarr1'] = round(prob_arr1, 10)  # 10 decimal places to match Mike

            prob_arr1 = math.exp(pr1) / (1 + math.exp(pr1))
            working_dict['probarr1'] = ('{0:.10f}'.format(prob_arr1)).rstrip('0')  # 10 decimal places

            #self.prob_arr1.append(prob_arr1)

            # ######## HOLDOVER IGNITION PROBABILITIES ######## #

            # Mike: This is the probability of ignition of a holdover

            if int(working_dict['totltg']) > 0 and int(working_dict['pos']) >= 0:
                perpos = float(working_dict['pos']) / float(working_dict['totltg']) * 100.0
            else:
                perpos = 20
            
            if working_dict['dmc'] == '':
                processed = processed - 1  # Skip over this entry.
                continue
            
            if working_dict['ZONE_CODE'] == '':
                processed = processed - 1  # Skip over this entry.
                continue

            if int(working_dict['ZONE_CODE']) == 10:
                working_dict['ZONE_CODE'] = 9
            
            # Mike: IMPORTANT...RECASTING some small NSRS that had few ltg fires into neighbors

            if working_dict['NSR'] == '':
                processed = processed - 1  # Skip over this entry.
                continue
            
            if int(working_dict['NSR']) == 15:
                working_dict['NSR'] = 1
            
            if int(working_dict['NSR']) == 18:
                working_dict['NSR'] = 11
            
            if int(working_dict['NSR']) == 14:
                working_dict['NSR'] = 11
            
            if int(working_dict['NSR']) == 5:
                working_dict['NSR'] = 12
            
            if int(working_dict['NSR']) == 7:
                working_dict['NSR'] = 8
            
            if working_dict['dmc'] == '':
                processed = processed - 1  # Skip over this entry.
                continue
            
            # dry variable not used.
            # if float(working_dict['rain']) > 0.2:
            #     dry = "WET"
            # else:
            #     dry = "DRY"          
            
            if int(working_dict['mon']) < 6:
                season = "Spring"
                int_season = 0.3201
            else:
                season = "Summer"
                int_season = 0.0
            
            # Mike: Just a categorical classification of density to get at rainfall
            
            if int(working_dict['totltg']) > 17:  # Mike: extreme
                dense = -1.51
            elif int(working_dict['totltg']) > 6:
                dense = -0.48
            elif int(working_dict['totltg']) > 2:
                dense = 0.0
            else:
                dense = 0.2332
            
            # Mike: SEE the definition in the data conditioning part for this
            # IF nighttime ltg total (9pm to 6am) is > daytime lightning total (6am to
            # 9pm) then it's NIGHT, otherwise DAY
            
            if working_dict['timing'] == 'NIGHT':
                int_timing = 0.406
            else:
                int_timing = 0.0
            
            int_nsr = 0.0
            ffmc_nsr = 0.0
            dmc_nsr = 0.0
            
            if int(working_dict['NSR']) == 1:
                int_nsr = 1.43
                ffmc_nsr = -0.0193
                dmc_nsr = 0.0027
            
            if int(working_dict['NSR']) == 2:
                int_nsr = 2.67
                ffmc_nsr = -0.0398
                dmc_nsr = 0.0029
            
            if int(working_dict['NSR']) == 3:
                int_nsr = 1.55
                ffmc_nsr = -0.0139
                dmc_nsr = -0.0093
            
            if int(working_dict['NSR']) == 4:
                int_nsr = -0.6778
                ffmc_nsr = 0.0065
                dmc_nsr = -0.0096
            
            if int(working_dict['NSR']) == 6:
                int_nsr = 0.3966
                ffmc_nsr = -0.0051
                dmc_nsr = 0.0014
            
            if int(working_dict['NSR']) == 8:
                int_nsr = 0.9429
                ffmc_nsr = -0.0188
                dmc_nsr = -0.0030
            
            if int(working_dict['NSR']) == 9:
                int_nsr = 3.388
                ffmc_nsr = -0.0579
                dmc_nsr = 0.0006
            
            if int(working_dict['NSR']) == 10:
                int_nsr = 0.776
                ffmc_nsr = -0.0197
                dmc_nsr = 0.0204
            
            if int(working_dict['NSR']) == 11:
                int_nsr = 1.688
                ffmc_nsr = -0.0292
                dmc_nsr = 0.0190
            
            if int(working_dict['NSR']) == 12:
                int_nsr = 1.566
                ffmc_nsr = -0.028
                dmc_nsr = 0.0025
            
            if int(working_dict['NSR']) == 13:
                int_nsr = 4.80
                ffmc_nsr = -0.062
                dmc_nsr = 0.0018
            
            f = (-11.873 + int_nsr + int_timing + int_season + dense) + \
                float(working_dict['dmc']) * (0.0179 + dmc_nsr) + \
                float(working_dict['dc']) * (0.0020) + \
                float(working_dict['ffmc']) * (0.0709 + ffmc_nsr) - (0.0097 * perpos)

            probign = math.exp(f) / (1.0 + math.exp(f))
            
            if probign > 0.04:
                probign = 0.04 + ((probign - 0.04) * 0.25)
            if probign > 0.05:
                probign = 0.05
            
            # Mike: This is just a quick fix to addressing the roll over flaw in the
            # GLM linearity ... SIMPLE for now
            
            jd = datetime.date(int(working_dict['year']), \
                                int(working_dict['mon']), \
                                int(working_dict['day'])).timetuple().tm_yday
            
            # Append the probign and jds columns to the end of the dataset.
            working_dict['probign'] = ('{0:.10f}'.format(probign)).rstrip('0')  # 10 decimal places
            working_dict['jd'] = jd
            
            # Now that we have all of the probabilities, let's append these columns to the data set.
            new_row = []
            
            # Ensure that we output the columns in the same order as they were during the input
            # stage.
            for column_name in output_csv_header:
                
                # Handle the column name change for NSR / region.
                if column_name == 'region':
                    column_name = 'NSR'

                # Omit the following columns from the data set.
                """if column_name == 'neg':
                    continue
                
                if column_name == 'rh':
                    continue
                
                if column_name == 'ws':
                    continue
                
                if column_name == 'rain':
                    continue
                
                if column_name == 'isi':
                    continue
                
                if column_name == 'pos':
                    continue
                
                if column_name == 'timing':
                    continue
                
                if column_name == 'ZONE_CODE':
                    continue
                
                if column_name == 'NSRNAME':
                    continue"""

                # Perform rounding and casting as per Dr. Wotton's C code requirements.
                working_dict['lat'] = round(float(working_dict['lat']), 4)
                working_dict['lon'] = round(float(working_dict['lon']), 4)
                working_dict['dmc'] = int(float(working_dict['dmc']))
                working_dict['dc'] = int(float(working_dict['dc']))
                
                new_row.append(working_dict[column_name])
            
            #print("process: working_dict is ", working_dict)
            ## raw_input("Press enter to continue...")
            
            # Append to the output file.
            output_csv_file.writerow(new_row)
        
        # End of fire arrivals for loop.
        print("computeArrivalHoldoverIgnitionProbabilities(): Completed calculating lightning fire probabilities.")
        print("computeArrivalHoldoverIgnitionProbabilities(): Overall total rows analyzed: %d" % i)
        print("computeArrivalHoldoverIgnitionProbabilities(): Rows processed: %d" % processed)
    
    def addLatLongsToGriddedFWIWeatherFile(self):
        """ This is a "debugging" method which will add lat/longs as columns to the gridded FWI weather file
            for plotting in Google Earth, as an example.
        """
        
        # Load in the gridded / binned FWI indices file and name the first column "grid".
        input_binned_weather_df = pd.read_csv(self.ltg_weather_binned_output_path, sep=',', header=None)
        columns = list(input_binned_weather_df.columns.values)
        print("addLatLongsToGriddedFWIWeatherFile(): columns is:")
        print(columns)
        columns[0] = "grid"
        input_binned_weather_df.columns = columns

        # Load in the grid locations file and label the columns.
        ltg_grid_locations_df = pd.read_csv(self.ltg_grid_locations_path, delim_whitespace=True, header=None)
        ltg_grid_locations_df.columns = ['grid', 'latitude', 'longitude']

        # Perform a left join on the datasets and merge them.
        input_binned_weather_df_lat_long = pd.merge(input_binned_weather_df, ltg_grid_locations_df,
                                                    how="left", on="grid")
        
        # Reorder columns.
        new_columns = list(input_binned_weather_df_lat_long.columns.values)        
        new_columns.insert(1, new_columns.pop(new_columns.index('latitude')))    
        new_columns.insert(2, new_columns.pop(new_columns.index('longitude'))) 
        input_binned_weather_df_lat_long = input_binned_weather_df_lat_long[new_columns]

        # Round the lat/long to 4 decimal places.
        input_binned_weather_df_lat_long['latitude'] = input_binned_weather_df_lat_long['latitude'].round(4)
        input_binned_weather_df_lat_long['longitude'] = input_binned_weather_df_lat_long['longitude'].round(4)
        
        print("addLatLongsToGriddedFWIWeatherFile(): the new columns are:")
        print(new_columns)
        
        # Output the newly-merged dataset.
        input_binned_weather_df_lat_long.to_csv(self.ltg_weather_binned_output_lat_longs_added_path, sep=',', index=False, header=False)
    
    def lightningConfidenceIntervalGraphGenerator(self, days_to_plot, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval):
        """ This method creates graphs of daily confidence intervals against actual historical
            arrivals (reported fires) and holdovers (fire starts). """
        
        # Load the historical lightning fires file.
        # Use encoding='cp1252' to deal with the Windows "smart quotes" in the historical fires file, 0x92.
        actual_fires_df = pd.read_csv(self.ltg_actual_fire_arrivals_file, sep=',', encoding='cp1252', parse_dates=['reported_date', 'fire_start_date'])
        print("lightningConfidenceIntervalGraphGenerator(): Dropping all duplicate fires / identical rows...")
        actual_fires_df.drop_duplicates(keep='first', inplace=True)
        actual_fires_df.columns = map(str.upper, actual_fires_df.columns)
        actual_fires_df = actual_fires_df[actual_fires_df['GENERAL_CAUSE_DESC'].str.contains("Lightning")]
        
        print("lightningConfidenceIntervalGraphGenerator(): Loaded actual fire arrivals file.")
        
        # Load up the confidence intervals file and add column headers.
        confidence_intervals_df = pd.read_csv(self.ltg_confidence_intervals_output_path, delim_whitespace=True, header=None)
        confidence_intervals_df.columns = FOPConstantsAndFunctions.LTG_CONFIDENCE_INTERVAL_PREDICTIONS_HEADERS
        
        print("lightningConfidenceIntervalGraphGenerator(): Loaded confidence intervals predictions.")
        
        # Loop through the date range provided and grab the fire arrivals
        # (reported fires) and holdovers (fire starts) for each of the days we need.
        reported_fires_dict = {}
        fire_starts_dict = {}
        
        for date in days_to_plot:
            actual_reported_date_fires_df_view = actual_fires_df.loc[((actual_fires_df['REPORTED_DATE']).dt.year == date.year) &
                                                                    ((actual_fires_df['REPORTED_DATE']).dt.month == date.month) &
                                                                    ((actual_fires_df['REPORTED_DATE']).dt.day == date.day)]
            reported_fires_dict[date.strftime("%Y-%m-%d")] = len(actual_reported_date_fires_df_view.index)
            

            actual_start_date_fires_df_view = actual_fires_df.loc[((actual_fires_df['FIRE_START_DATE']).dt.year == date.year) &
                                                                ((actual_fires_df['FIRE_START_DATE']).dt.month == date.month) &
                                                                ((actual_fires_df['FIRE_START_DATE']).dt.day == date.day)]
            fire_starts_dict[date.strftime("%Y-%m-%d")] = len(actual_start_date_fires_df_view.index)

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
        fig, ax = plt.subplots()
        fig.set_size_inches((6 + 0.45 * len(days_to_plot)), 12)  # Variably-widthed plot depending on number of dates we are plotting.
        plt.xlabel("Date")        
        plt.ylabel("Number of reported lightning-caused fires")     
        #string_dates = [date.strftime("%m-%d") for date in days_to_plot]
        #print("confidenceIntervalGraphGenerator(): string_dates is ", string_dates)
        #plt.xticks(range(len(days_to_plot)))
        #plt.xticks([range(len(days_to_plot))])
        #ax.set_xticklabels(days_to_plot, rotation='vertical')
        
        
        #ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_locator(mdates.DayLocator())
        #month_fmt = mdates.DateFormatter('%B')
        day_fmt = mdates.DateFormatter('%b %d')
        #ax.xaxis_date()
        ax.xaxis.set_major_formatter(day_fmt)
        #ax.xaxis.set_minor_formatter(day_fmt)
        #ax.xaxis.set_tick_params(which='major', pad=13)
        

        # [date.strftime("%m%d") for date in days_to_plot]
        # plt.xticks(range(len(days_to_plot)), rotation=90)
        #plt.yticks(rotation=90)

        #print("confidenceIntervalGraphGenerator(): days_to_plot is ", days_to_plot)
        #print("confidenceIntervalGraphGenerator(): confidence_intervals_df['totarrPROV_ci_low'] is ", confidence_intervals_df['totarrPROV_ci_low'])

        plt.plot(days_to_plot, confidence_intervals_df['totarrPROV_ci_high'], color='red', marker='o', markersize=3, label="Lightning fire arrivals confidence interval,\nhigh bound")
        plt.plot(days_to_plot, confidence_intervals_df['totarrPROV_ci_low'], color='green', marker='o', markersize=3, label="Lightning fire arrivals confidence interval,\nlow bound")
        
        plt.plot(days_to_plot, y, color='purple', marker='o', markersize=3, label="Daily reported fires")

        ax.set_xlim([min(days_to_plot), max(days_to_plot)])
        ax.set_ylim(ymin=0)
        fig.autofmt_xdate()

        ltg_fire_confidence_interval_string = ('Confidence interval used for simulation: %.1f%%' % ltg_fire_confidence_interval)
        plt.plot([], [], ' ', label=ltg_fire_confidence_interval_string)
        
        num_days_arrivals_out_of_range_string = ('Number of days where daily reported\nfires amount was outside confidence\ninterval range: %d' % num_days_arrivals_out_of_range)
        plt.plot([], [], ' ', label=num_days_arrivals_out_of_range_string)

        percentage_days_arrivals_out_of_range_string = ('Percentage of days where daily reported\nfires amount was within confidence\ninterval range: %2.1f%%' % (100 - ((num_days_arrivals_out_of_range / float(len(days_to_plot))) * 100)))
        plt.plot([], [], ' ', label=percentage_days_arrivals_out_of_range_string)

        # Add a title and a legend to the plot.
        plt.title("Predicted Lightning Fire Confidence Interval Ranges and Historical Reported Fires for " + str(days_to_plot[0].year))
        legend = plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), borderaxespad=0.)

        plt.savefig(fname=(self.ltg_output_maps_folder + "/ltg_cidiagnostic_arrivals_" + str(days_to_plot[0].year) + ".png"), format='png', dpi=150, bbox_extra_artists=(legend,), bbox_inches='tight')
            
        # Reset and close the plot and figures.
        plt.cla()
        plt.clf()
        plt.close('all')

        print("lightningConfidenceIntervalGraphGenerator(): CI graph has been generated..")

    def lightningFOPDateRangeMapperPredictor(self, start_day, end_day, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval, display_historical_fires_on_maps):
        """ This method is used to predict, simulate and produce Lightning FOP maps for a date range.

            The reason this method exists is because it is time-expensive to simulate and map for a single day at
            a time.

            This method alleviates that by producing predictions for an arbitrary date range, and then mapping for
            that date range - all in one shot - while still minimizing any re-calculating of probabilities.

        """

        # We have two cases. If start_day == end_day, then we just call the Lightning FOP Controller on that single day.
        # The Controller will decide whether a prediction is necessary for this day.
        #
        # In the second case, start_day <= end_day. We call the Lightning FOP Controller on end_day, which will produce
        # probabilities for all days within the mapping range, as well as a map for end_day. We then call the
        # simulation_wrapper() method on the range start_day to (end_day - 1), which will simulate and produce
        # predictions for that range. Finally, we call lightningFirePredictionMapper() on that range.
        # This will leave us with a complete range of probabilities, predictions, and maps.
        print("lightningFOPDateRangeMapperPredictor(): Calling lightningFOPController on %s. . ." % end_day.strftime("%Y-%m-%d"))
        self.lightningFOPController(end_day, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval, display_historical_fires_on_maps)

        if start_day < end_day:

            end_day_minus_one = end_day - datetime.timedelta(days=1)

            # Call the C Simulator wrapper on start_date and (end_date - 1).
            print("lightningFOPDateRangeMapperPredictor(): Calling simulationWrapper() on the date range %s to %s. . ." % (start_day.strftime("%Y-%m-%d"),
                                                                                                                           (end_day_minus_one.strftime("%Y-%m-%d"))))

            # Get the Julian day of the year for the start and end dates.
            start_day_of_year = start_day.timetuple().tm_yday
            end_day_minus_one_day_of_year = end_day_minus_one.timetuple().tm_yday

            self.simulationWrapper(start_day_of_year, end_day_minus_one_day_of_year, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval)

            # Call the Mapping method to produce maps for this date range.

            # For the following range, use the original end_day as opposed to end_day_minus_one since the daterange
            # function is not inclusive on the last parameter and we've already mapped end_day as a part of the original
            # call to lightningFOPController.
            date_range_list = []
            for date in FOPConstantsAndFunctions.daterange(start_day, end_day):
                date_range_list.append(date)
            
            print("lightningFOPDateRangeMapperPredictor(): Calling the lightningFirePredictionMapper() on the date range %s to %s. . ." % (start_day.strftime("%Y-%m-%d"),
                                                                                                                                           (end_day.strftime("%Y-%m-%d"))))
            self.lightningFirePredictionMapper('all', date_range_list, display_historical_fires_on_maps, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval)

        # We're done!
        print("lightningFOPDateRangeMapperPredictor(): Date range mapping and prediction operation completed.")
        return
    
    def lightningFOPCIGraphGenerator(self, start_day, end_day, int_ltg_fire_holdover_lookback_time, float_ltg_fire_confidence_interval):
        """ This method is used to produce a fresh simulation run for a date range (usually all days predicted for thus far in a year), from
            which a confidence interval plot of the predicted arrivals along with the actual number of reported fires on each day.

            This is intended to be a diagnostic tool for observing lightning fire prediction model performance. """
        
        print("lightningFOPCIGraphGenerator(): Calling the simulationWrapper...")

        # Get the Julian day of the year for the start and end dates.
        start_day_of_year = start_day.timetuple().tm_yday
        end_day_of_year = end_day.timetuple().tm_yday

        # Get a fresh set of simulations for the days in the FOP System State DB.
        self.simulationWrapper(start_day_of_year, end_day_of_year, int_ltg_fire_holdover_lookback_time, float_ltg_fire_confidence_interval)

        date_range_list = []
        for date in FOPConstantsAndFunctions.daterange(start_day, end_day + datetime.timedelta(days=1)):
            date_range_list.append(date)

        # Call the CI graph generator.
        self.lightningConfidenceIntervalGraphGenerator(date_range_list, int_ltg_fire_holdover_lookback_time, float_ltg_fire_confidence_interval)

        # We're done!
        print("lightningFOPCIGraphGenerator(): CI graph generation operation completed.")
        return

    def lightningFOPController(self, date_to_predict_for, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval, display_historical_fires_on_maps):
        """ This method is provided input parameters from the GUI which will determine how the Lightning FOP model runs.
            
            This method contains the logic behind determining if the master data set needs to be updated or not.
            If it does, load the updated raw weather and lightning strike data and run it through the
            processing flow.

            This method also contains a lot of error-checking to ensure that the integrity of the data is
            maintained.
            
            The date_to_predict_for is a datetime datatype."""

        # Load in the FOP system state data set, and the raw weather and lightning data.        
        # Sanity check: Ensure that the system state data set exists.
        try:
            print("lightningFOPController(): Starting by reading in the system state DB...")
            self.fop_system_state_db_df = pd.read_csv(self.fop_system_state_db_path, sep=',', header=0,
                                                      names=FOPConstantsAndFunctions.FOP_SYSTEM_STATE_DB_HEADERS, parse_dates=['DATE'])

            # If the database is empty, then populate all of the dates which can be predicted for both human- and lightning-caused
            # fires (March 01 through October 31).
            if len(self.fop_system_state_db_df.index) == 0:
                print("lightningFOPController(): Initializing empty FOP system state DB. . .:")

                for new_date in FOPConstantsAndFunctions.daterange(pd.Timestamp(date_to_predict_for.year, 3, 1),
                                                                   pd.Timestamp(date_to_predict_for.year, 10, 31) + datetime.timedelta(days=1)
                                                                  ):
                    row_data = {'DATE':[new_date], 'LIGHTNING_FOP_COMPLETED':['N'], 'HUMAN_FOP_COMPLETED':['N'], 'FORECASTED_OR_OBSERVED':['O']}
                    row_data_df = pd.DataFrame.from_dict(row_data)
                    self.fop_system_state_db_df = self.fop_system_state_db_df.append(row_data_df)
        
            # After the column header check (and potentially adding new rows), set the DATE column as the index of the FOP system state DB.
            self.fop_system_state_db_df.set_index('DATE', inplace=True)

            print("lightningFOPController(): self.fop_system_state_db_df before starting Lightning FOP run:")
            print(self.fop_system_state_db_df)

        except IOError as e:
            print("lightningFOPController(): Exception IOError thrown while reading the FOP system state DB. Exception details follow below. Aborting...")
            print(e)
            return
        
        # This assertion is a sanity check more than anything else. If this statement isn't true (should be taken care of by GUI input checks),
        # we should throw an exception and stop now.
        assert(pd.Timestamp(date_to_predict_for) in self.fop_system_state_db_df.index)

        # See if we have already produced predictions for this day.
        if self.fop_system_state_db_df.at[pd.to_datetime(date_to_predict_for), 'LIGHTNING_FOP_COMPLETED'] == 'Y':
            print("lightningFOPController(): The provided date, %s, exists already in the system. Producing a prediction for it." % str(date_to_predict_for))

            # The day exists already. 
            # 1. Call the simulation wrapper method for the day we want to predict for.

            # Determine the day of year (Julian) so that we can simulate only for this day.
            day_of_year = date_to_predict_for.timetuple().tm_yday
            print("lightningFOPController(): day_of_year is ", day_of_year)

            self.simulationWrapper(day_of_year, day_of_year, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval)
            
            # 2. Call the mapping method which will produce maps for the desired date.

            # NOTE: Assume that actual historical arrivals will be displayed, and that the maps are to be outputted
            # to disk silently.

            # Valid map strings: 'arrival', 'holdover', 'probign', 'probarr0', 'DMC', 'DC', 'totltg', ... all case sensitive.
            # Use 'all' to output all maps.
            self.lightningFirePredictionMapper('all', [date_to_predict_for], display_historical_fires_on_maps, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval)
        
        else:
            
            # This day does not exist in the system. We need to execute the Lightning FOP flow for all days after
            # and including the desired day.

            # Return the most-recent date in the FOP system state DB for which Lightning FOP has been performed.
            most_recent_date = self.fop_system_state_db_df.loc[self.fop_system_state_db_df['LIGHTNING_FOP_COMPLETED'] == "Y"].index.max()

            # See if most_recent_date is Not a Time (NaT). If it is, then set most_recent_date to be May 01, the start of the lightning fire season.
            if pd.isnull(most_recent_date):
                most_recent_date = pd.Timestamp(date_to_predict_for.year, 5, 1)
            else:
                # NOTE: Increment most_recent_date one more day in order for the date masking below to work correctly.
                # We want the prediction date range to start the day after the day that we have the most-recent prediction for.
                most_recent_date = most_recent_date + datetime.timedelta(days=1)

            print("lightningFOPController(): most_recent_date (the date where this round of predictions must start at) is ", most_recent_date)
            print("lightningFOPController(): date_to_predict_for is ", date_to_predict_for)

            # Parse the weather_date column as a datetime to allow for easy access to year, month, day and hour.
            # Here, we use the infer_datetime_format=True flag because the datetime in the file is NOT zero-padded, and
            # the default datetime placeholders do not allow for that by default.
            
            # Next, we need to select only the raw weather and lightning data for the date range which falls between the first
            # missing day in the FOP system state DB and date_to_predict_for.
            raw_weather_data_df = pd.read_csv(self.ltg_input_raw_weather_data_file, sep=',')

            # Perform a header check to determine the well-formed nature of the CSV.
            if list(raw_weather_data_df.columns) == FOPConstantsAndFunctions.RAW_WEATHER_CSV_HEADERS:

                # Raw weather headers type 1.
                print("lightningFOPController(): Raw weather data column check OK, headers type 1.")
                raw_weather_data_df['weather_date'] = pd.to_datetime(raw_weather_data_df['weather_date'], format='%m/%d/%y %H:%M', infer_datetime_format=True)

            elif list(raw_weather_data_df.columns) == FOPConstantsAndFunctions.RAW_WEATHER_CSV_HEADERS_2:
                
                # Raw weather headers type 2.
                print("lightningFOPController(): Raw weather data column check OK, headers type 2.")
                print("lightningFOPController(): Making headers lower-case...")
                
                # Make all of the weather column headers to be lowercase.
                raw_weather_data_df.columns = map(str.lower, raw_weather_data_df.columns)
                raw_weather_data_df['weather_date'] = pd.to_datetime(raw_weather_data_df['weather_date'], format='%Y-%m-%d %H:%M:%S', infer_datetime_format=True)

            else:
                print("lightningFOPController(): Raw weather data columns do not match what is expected. ERROR")
                raise ValueError            

            # Sort the raw weather dataframe by the column: "weather_date".
            raw_weather_data_df = raw_weather_data_df.sort_values(by='weather_date')

            #day_after_most_recent_day = most_recent_date + datetime.timedelta(days=1)    ###   + datetime.timedelta(days=1)
            date_mask_weather = ((raw_weather_data_df['weather_date'] > pd.Timestamp(most_recent_date)) & (raw_weather_data_df['weather_date'] <= pd.Timestamp(date_to_predict_for + datetime.timedelta(days=1))))

            # Perform the date selection for this dataframe; selection is inclusive.
            # raw_weather_data_df = raw_weather_data_df.loc[raw_weather_data_df['weather_date'][str(day_after_most_recent_day):str(date_to_predict_for)]]
            raw_weather_data_df = raw_weather_data_df.loc[date_mask_weather]

            print("lightningFOPController(): Raw weather date selection is:")
            print(raw_weather_data_df)

            # Ensure that we actually have date_to_predict_for in the range that we grabbed.
            """if datetime.datetime.date(raw_weather_data_df['weather_date'].max()) != date_to_predict_for:
                print("lightningFOPController(): The provided date, %s, does not exist in the raw weather dataset. \r\n" \
                    "Please provide a more up-to-date raw weather data file or adjust the prediction date and try again." % str(date_to_predict_for))
                return"""            
            if not ((raw_weather_data_df['weather_date'].max().year == date_to_predict_for.year) and
                    (raw_weather_data_df['weather_date'].max().month == date_to_predict_for.month) and
                    (raw_weather_data_df['weather_date'].max().day == date_to_predict_for.day)):
                print("lightningFOPController(): The provided prediction date, %s, does not exist in the raw weather dataset. \r\n" \
                    "Please provide a more up-to-date raw weather data file or adjust the prediction date and try again." % str(date_to_predict_for))
                
            
            # We are good to go on the raw weather data side. Let's attempt the same thing for the raw lightning strike data.
            raw_lightning_strike_data_df = pd.read_csv(self.ltg_input_raw_lightning_strike_data_file, sep=',')

            print("lightningFOPController(): Loading lightning strike data and converting LOCAL_STRIKETIME column to datetime format...")
            # Perform a header check to determine the type of lightning strike input CSV.
            if list(raw_lightning_strike_data_df.columns) == FOPConstantsAndFunctions.LTG_STRIKE_SHAPEFILE_HEADERS:
                print("lightningFOPController(): Lightning strike data is from a shapefile.")
                raw_lightning_strike_data_df['LOCAL_STRIKETIME'] = pd.to_datetime(raw_lightning_strike_data_df['LOCAL_STRIKETIME'], format="%m/%d/%y %H:%M:%S", infer_datetime_format=True)

            elif list(raw_lightning_strike_data_df.columns) == FOPConstantsAndFunctions.LTG_STRIKE_CSV_HEADERS:
                print("lightningFOPController(): Lightning strike data is from a CSV export, type 1.")
                # Date format of ltg2017b.csv file:
                raw_lightning_strike_data_df['local_striketime'] = pd.to_datetime(raw_lightning_strike_data_df['local_striketime'], format="%Y-%m-%d %H:%M:%S")

            elif list(raw_lightning_strike_data_df.columns) == FOPConstantsAndFunctions.LTG_STRIKE_CSV_HEADERS_2:
                print("lightningFOPController(): Lightning strike data is from a CSV export, type 2.")
                raw_lightning_strike_data_df['LOCAL_STRIKETIME'] = pd.to_datetime(raw_lightning_strike_data_df['LOCAL_STRIKETIME'], format='%Y-%m-%d %H:%M:%S')

            else:
                print("lightningFOPController(): Unrecognized lightning strike input format.")
                return
            
            # raw_input("Press any key to continue...")

            # Make all of the lightning strike column headers to be uppercase.
            raw_lightning_strike_data_df.columns = map(str.upper, raw_lightning_strike_data_df.columns)
            
            print("lightningFOPController(): Sorting raw lightning strike data chronologically...")

            # Sort the input dataframe by the second column: "local_striketime".
            raw_lightning_strike_data_df = raw_lightning_strike_data_df.sort_values(by='LOCAL_STRIKETIME')

            print("lightningFOPController(): Getting subset of new lightning strike data missing from the FOP system state DB...")    # #####  + datetime.timedelta(days=1)
            date_mask_lightning = ((raw_lightning_strike_data_df['LOCAL_STRIKETIME'] > pd.Timestamp(most_recent_date)) & (raw_lightning_strike_data_df['LOCAL_STRIKETIME'] <= pd.Timestamp(date_to_predict_for + datetime.timedelta(days=1))))

            # Perform the date selection for this dataframe; selection is inclusive.
            # raw_weather_data_df = raw_weather_data_df.loc[raw_weather_data_df['weather_date'][str(day_after_most_recent_day):str(date_to_predict_for)]]
            raw_lightning_strike_data_df = raw_lightning_strike_data_df.loc[date_mask_lightning]

            # Ensure that we actually have date_to_predict_for in the range that we grabbed for the raw lightning strike data.
            if datetime.datetime.date(raw_lightning_strike_data_df['LOCAL_STRIKETIME'].max()) != date_to_predict_for:
                print("lightningFOPController(): Note that the provided date, %s, does not have any lightning strike data." % str(date_to_predict_for))
            
            print("lightningFOPController(): The selected raw lightning strike data is:")
            print(raw_lightning_strike_data_df)

            print("lightningFOPController(): Ready to begin the Lightning FOP processing flow.")
            # 
            # raw_input("Press Enter to continue...")
            
            # We are good to go on the raw lightning strike data side. Let's start the Lightning FOP flow.

            # 1. Call the lightning strike data massager method on the prepared lightning strike dataframe.
            self.lightningStrikeDataMassager(raw_lightning_strike_data_df)

            # 2. Call the lightning strike binner executable through the following method.
            self.lightningBinnerWrapper()

            # 3. Call the raw weather data massager method on the prepared raw weather dataframe.
            FOPConstantsAndFunctions.rawWeatherDataMassager(raw_weather_data_df,
                                                            self.ltg_weather_massaged_output_path,
                                                            self.hmn_weather_station_locations_path)

            # 4. Call the weather interpolation and binning executable through the following method.
            self.weatherInterpolationBinnerWrapper()

            # 5. Call the raw weather data and lightning merger method.
            self.mergeBinnedWeatherAndLightning()

            # 6. Call the Arrival and Holdover Probabilities compute method.
            self.computeArrivalHoldoverIgnitionProbabilities()

            # 7. Call the simulation wrapper method for the desired day.
            # Determine the day of year (Julian) so that we can simulate only for this day.
            day_of_year = date_to_predict_for.timetuple().tm_yday
            print("lightningFOPController(): day_of_year is ", day_of_year)

            self.simulationWrapper(day_of_year, day_of_year, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval)

            # 8. Update the FOP system state DB with the newly-processed dates.
            print("lightningFOPController(): Updating FOP system state DB and writing changes to disk...")

            print("lightningFOPController(): FOP system state DB prior to update is: ")
            print(self.fop_system_state_db_df)
            
            # Update the FOP system state DB with the range of dates we've just produced and saved probabilities for.
            # NOTE: Last date in date range is NOT inclusive in the daterange generator, which is why we add a timedelta of 1 day to date_to_predict_for.
            for new_date in FOPConstantsAndFunctions.daterange(most_recent_date, (date_to_predict_for + datetime.timedelta(days=1))):

                # Cast new_date as a pandas datetime for ease in performing index lookups.
                new_date = pd.to_datetime(new_date)

                # Update new_date in the FOP system state DB as being completed.
                self.fop_system_state_db_df.at[new_date, 'LIGHTNING_FOP_COMPLETED'] = 'Y'

            print("lightningFOPController(): FOP system state DB after update is:")
            print(self.fop_system_state_db_df)

            # Write the new information to the DB on disk.
            self.fop_system_state_db_df.to_csv(self.fop_system_state_db_path, sep=',', index=True)

            # 8. Call the mapping method which will produce maps for the desired date.

            # Valid map strings: 'arrival', 'holdover', 'probign', 'probarr0', 'DMC', 'DC', 'totltg', ... all case sensitive.
            # Use 'all' to output all maps.
            self.lightningFirePredictionMapper('all', [date_to_predict_for], display_historical_fires_on_maps, ltg_fire_holdover_lookback_time, ltg_fire_confidence_interval)

        # We are done!
        print("lightningFOPController(): Run successfully completed.")
        return