""" This is a Python translation of the SAS portion of Dr. Mike Wotton's Lightning Occurrence Prediction model.

    This code is written for the UAlberta Fire Occurrence Prediction project, in collaboration with the Government of Alberta
    and the Canadian Forest Service.

    Author: Matthew Ansell
    2019
"""

import csv  # Used for simple input / output data processing.
import os.path  # Used for determining the CWD, and other I/O tasks.
import subprocess  # used for calling Dr. Wotton's compiled exe files.
import pandas as pd  # Used for more complicated input / output data processing
import math  # Used for model calculations.
import operator # Used for CSV sort-by-column.
import timeit  # Used for measuring code execution time.
from decimal import Decimal  # Used to round probabilities to an exact decimal as opposed to float.
import datetime  # Used to determine the day of year.
import random  # Used to generate a random number seed for the C simulation tool.
import geopandas as gpd  # This and the following imports are used for mapping purposes.
import descartes
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
import pylab

################# CONSTANTS #################

MAX_INT = 32767

class LightningFireOccurrencePrediction(object):
    """ This class contains the logic for the Lightning Occurrence Prediction model itself. """

    def __init__(self,
                 ltg_arrivals_holdovers_input_path,
                 ltg_arrivals_holdovers_output_path,
                 ltg_strike_raw_input_path,
                 ltg_strike_raw_massaged_output_path,
                 ltg_grid_locations_path,
                 ltg_lightning_binned_output_path,
                 ltg_raw_weather_input_path,
                 ltg_weather_massaged_output_path,
                 ltg_weather_binned_output_path,
                 ltg_weather_binned_output_lat_longs_added_path,
                 ltg_weather_station_locations_path,
                 ltg_fishnet_nsr_path,
                 ltg_merged_weather_lightning_data_path,
                 ltg_weather_interpolation_coefficients_path,
                 ltg_gridded_predictions_output_path,
                 ltg_confidence_intervals_output_path,
                 ltg_alberta_shapefile,
                 ltg_actual_2018_fires,
                 ltg_maps_output_folder,
                 fop_system_state_db_path):

        # Lightning arrivals / holdovers input and output file paths.
        self.ltg_arrivals_holdovers_input_path = ltg_arrivals_holdovers_input_path
        self.ltg_arrivals_holdovers_output_path = ltg_arrivals_holdovers_output_path

        # Ligtning strike / binning input and output file paths.
        self.ltg_strike_raw_input_path = ltg_strike_raw_input_path
        self.ltg_strike_raw_massaged_output_path = ltg_strike_raw_massaged_output_path
        self.ltg_grid_locations_path = ltg_grid_locations_path
        self.ltg_lightning_binned_output_path = ltg_lightning_binned_output_path

        # Raw lightning strike data column headers used to ensure input lightning data is structured correctly.
        self.ltg_strike_shapefile_headers = ['OBJECTID','ID','CREATE_TIMESTAMP','CREATE_USERID','DATETIME','LATITUDE',
                                             'LONGITUDE','STRENGTH','MULTIPLICITY','UPDATE_TIMESTAMP','UPDATE_USERID','LOCAL_STRIKETIME']
        self.ltg_strike_csv_headers = ['date_group','local_striketime','gmt_striketime','mst_striketime','latitude','longitude','strength',
                                       'multiplicity']
        
        # Raw weather data column headers used to ensure input weather data is structured correctly.
        self.ltg_raw_weather_csv_headers = ['id', 'ws_id', 'c_sky_cndt_id', 'c_wthr_typ_id', 'c_wnd_drct_id', 'weather_date',
                                            'dry_bulb_temperature', 'wet_bulb_temperature', 'minimum_temperature', 'maximum_temperature',
                                            'relative_humidity', 'visibility_km', 'wind_speed_kmh', 'wind_gust_kmh', 'rain_mm', 'snow_cm',
                                            'hail_mm', 'dew_point', 'high_cloud_amt', 'middle_cloud_amt', 'low_cloud_amt', 'cu_cloud_amt',
                                            'cuplus_cloud_amt', 'cb_cloud_amt', 'grand_total', 'fine_fuel_moisture_code',
                                            'initial_spread_index', 'duff_moisture_code', 'build_up_index', 'drought_code',
                                            'daily_severity_rating', 'fire_weather_index', 'present_weather', 'weather_remarks',
                                            'station_id', 'c_wnd_drct_type', 'c_sky_cndt_type', 'name']

        # Weather data file paths.
        self.ltg_raw_weather_input_path = ltg_raw_weather_input_path
        self.ltg_weather_massaged_output_path = ltg_weather_massaged_output_path
        self.ltg_weather_binned_output_path = ltg_weather_binned_output_path
        self.ltg_weather_binned_output_lat_longs_added_path = ltg_weather_binned_output_lat_longs_added_path
        self.ltg_weather_station_locations_path = ltg_weather_station_locations_path

        # Build the path to the C binning executable.
        self.lightning_wrapper_exe_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lightning\\binning\\build-ltggrids-five-period.exe'))
        
        # Build the path to the C weather interpolation executable.
        self.weather_interpolation_exe_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lightning\\weather\\cf-build-AB.exe'))
        
        # Build the path to the C weather binning executable.
        self.weather_binning_exe_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lightning\\weather\\use_cf2.exe'))

        # Build the path to the C simulation executable.
        self.simulation_exe_path = \
            os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'lightning\\simulation\\simulate-new-allyears-DC.exe'))
        
        # Path to the CSV which links AB_fishnet to Natural Sub-Regions.
        self.ltg_fishnet_nsr_path = ltg_fishnet_nsr_path

        # Path to the outputted weather and lightning file.
        self.ltg_merged_weather_lightning_data_path = ltg_merged_weather_lightning_data_path

        # Path to the outputted predictions and confidence intervals files.
        self.ltg_gridded_predictions_output_path = ltg_gridded_predictions_output_path
        self.ltg_confidence_intervals_output_path = ltg_confidence_intervals_output_path

        # This is a directory path (NOT a path to a file) where the intermediate weather coefficient output files get placed in.
        self.ltg_weather_interpolation_coefficients_path = ltg_weather_interpolation_coefficients_path

        # Path to the Alberta shapefile.
        self.ltg_alberta_shapefile = ltg_alberta_shapefile

        # Path to the 2018 Alberta actual fires record.
        self.ltg_actual_2018_fires = ltg_actual_2018_fires

        # Path to the **FOLDER** in which to output the maps.
        self.ltg_maps_output_folder = ltg_maps_output_folder

        # Path to the FOP system state DB.
        self.fop_system_state_db_path = fop_system_state_db_path

        # Pandas dataframe of the FOP syatem state DB.
        self.fop_system_state_db_df = None
    
    def lightningFirePredictionMapper(self, map_type, days_to_map, display_actuals, silently_output_maps):
        """ This method produces a map of lightning predictions overlayed on an Alberta
            weather zone map.
        """
        
        # Read in the Alberta shapefile and set up the plot.
        #alberta_map = alberta_map.to_crs(epsg=4326)
        #fig, ax = plt.subplots(figsize=(15,15))
        #lims = plt.axis('tight')
        alberta_map = gpd.read_file(self.ltg_alberta_shapefile)
        print("lightningFirePredictionMapper(): Alberta coordinate system is " + str(alberta_map.crs))
        
        # Only load up the data files that we need to pull information from for our maps.
        # Get a new view for the arrivals, if desired.
        if display_actuals:
            actual_fires_df = pd.read_csv(self.ltg_actual_2018_fires, sep=',')
            actual_fires_df['REP_DATE'] = pd.to_datetime(actual_fires_df['REP_DATE'], format='%m/%d/%y')
        
        # Load up the necessary files as specified by the method input parameters, and populate dataframes.
        # If map_type == 'all', then we want to open up both data files.
        if map_type in ['arrival', 'holdover', 'all']:

            print("lightningFirePredictionMapper(): Loading gridded prediction file and populating GeoDataFrame...")

            # Load up the grid predictions file and add column headers.
            gridded_predictions_df = pd.read_csv(self.ltg_gridded_predictions_output_path, sep=r'\s*', header=None, engine='python')
            gridded_predictions_df.columns = ['grid', 'year', 'month', 'day', 'lat', 'lon', 'narrtoday', 'nholdtoday', 'nigntoday']
        
        if map_type in ['probign', 'probarr0', 'DMC', 'DC', 'totltg', 'all']:    

            print("lightningFirePredictionMapper(): Loading FWI / probability file and populating GeoDataFrame...")       

            # Load up the probability file and add column headers.
            probabilities_df = pd.read_csv(self.ltg_arrivals_holdovers_output_path, sep=r'\s*', header=None, engine='python')
            probabilities_df.columns = ['grid', 'lat', 'lon', 'year', 'jd', 'probign', 'probarr0', 'probarr1', 'totltg',
                                        'numfire', 'region', 'nltg0', 'nltg1', 'nltg2', 'nltg3', 'nltg4', 'dmc', 'dc']

        # Loop through all of the days that we need to map,
        for date in days_to_map:

            print("lightningFirePredictionMapper(): Now preparing maps for " + str(date) + "...")
            
            # If we are to display historical arrivals, then load up a new view (in the database sense) for this new date.
            if display_actuals:

                actual_fires_df_view = actual_fires_df.loc[(actual_fires_df['REP_DATE']) == pd.Timestamp(date)]

                actuals_gdf = gpd.GeoDataFrame(actual_fires_df_view,
                                               crs={'init': alberta_map.crs},
                                               geometry=gpd.points_from_xy(actual_fires_df_view['LONGITUDE'],
                                                                           actual_fires_df_view['LATITUDE']))
            
            # If we are creating a map based on the expected arrivals and holdovers, load up a new view for this new date.
            if map_type in ['arrival', 'holdover', 'all']:

                gridded_predictions_df_view = gridded_predictions_df.loc[(gridded_predictions_df['year'] == date.year) &
                                                                         (gridded_predictions_df['month'] == date.month) &
                                                                         (gridded_predictions_df['day'] == date.day)]

                geo_df_arrivals_holdovers = gpd.GeoDataFrame(gridded_predictions_df_view,
                                                             crs={'init': alberta_map.crs},
                                                             geometry=gpd.points_from_xy(gridded_predictions_df_view['lon'],
                                                                                         gridded_predictions_df_view['lat']))

            # If we are creating a map based on FWI, raw probabilities, or total lightning, load up a new view for this new date.
            if map_type in ['probign', 'probarr0', 'DMC', 'DC', 'totltg', 'all']:
                
                probabilities_df_view = probabilities_df.loc[(probabilities_df['jd'] == int(date.strftime('%j'))) &
                                                             (probabilities_df['year'] == date.year)]            
                geo_df_fwi_probabilities = gpd.GeoDataFrame(probabilities_df_view,
                                                            crs={'init': alberta_map.crs},
                                                            geometry=gpd.points_from_xy(probabilities_df_view['lon'],
                                                                                        probabilities_df_view['lat']))
            
            # Now that are views are updated, generate the maps that we need to for the new day.
            if map_type == 'arrival' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing arrival map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(10, 12)
                plt.xlabel("Longitude (degrees)")
                plt.ylabel("Latitude (degrees)")
                plt.yticks(rotation=90)
                alberta_map.plot(ax=ax, alpha=0.4, color='grey')

                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.003)].plot(ax=ax, markersize=10, color='blue', marker='s', label='Low (> 0.00 to 0.003)')
                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.003) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.01)].plot(ax=ax, markersize=10, color='green', marker='s', label='Moderate (> 0.003 to 0.01)')
                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.01) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.03)].plot(ax=ax, markersize=10, color='yellow', marker='s', label='High (> 0.01 to 0.03)')
                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.03) & (geo_df_arrivals_holdovers['narrtoday'] <= 0.1)].plot(ax=ax, markersize=10, color='orange', marker='s', label='Very High (> 0.03 to 0.10)')
                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['narrtoday'] > 0.1)].plot(ax=ax, markersize=10, color='red', marker='s', label='Extreme (> 0.10)')
                
                # Display actual lightning strikes on our map, if desired.
                if display_actuals:
                    actuals_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning fire arrival', edgecolor='black', linewidth=0.5)

                # Add a title and a legend to the plot.
                plt.title("Expected Lightning Fire Arrival Predictions for " + str(date))
                plt.legend(loc='lower left')

                # Check if we are to silently output the generated maps to a PNG image, or if we are to display them in a viewer.
                if silently_output_maps:
                    plt.savefig(fname=(self.ltg_maps_output_folder + "arrival_" + str(date) + ".png"), format='png', dpi=150)
                else:
                    pylab.show()
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')

            if map_type == 'holdover' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing holdover map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(10, 12)
                plt.xlabel("Longitude (degrees)")
                plt.ylabel("Latitude (degrees)")
                plt.yticks(rotation=90)
                alberta_map.plot(ax=ax, alpha=0.4, color='grey')

                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.005)].plot(ax=ax, markersize=10, color='blue', marker='s', label='Low (> 0.000 to 0.005)')
                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.005) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.02)].plot(ax=ax, markersize=10, color='green', marker='s', label='Moderate (> 0.005 to 0.02)')
                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.02) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.05)].plot(ax=ax, markersize=10, color='yellow', marker='s', label='High (> 0.02 to 0.05)')
                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.05) & (geo_df_arrivals_holdovers['nholdtoday'] <= 0.1)].plot(ax=ax, markersize=10, color='orange', marker='s', label='Very High (> 0.05 to 0.10)')
                geo_df_arrivals_holdovers[(geo_df_arrivals_holdovers['nholdtoday'] > 0.1)].plot(ax=ax, markersize=10, color='red', marker='s', label='Extreme (> 0.10)')
                
                # Display actual lightning strikes on our map, if desired.
                if display_actuals:
                    actuals_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning fire arrival', edgecolor='black', linewidth=0.5)

                # Add a title and a legend to the plot.
                plt.title("Expected Lightning Fire Holdover Predictions for " + str(date))
                plt.legend(loc='lower left')

                # Check if we are to silently output the generated maps to a PNG image, or if we are to display them in a viewer.
                if silently_output_maps:
                    plt.savefig(fname=(self.ltg_maps_output_folder + "holdover_" + str(date) + ".png"), format='png', dpi=150)
                else:
                    pylab.show()
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')

            if map_type == 'probign' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing probability of ignition map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(10, 12)
                plt.xlabel("Longitude (degrees)")
                plt.ylabel("Latitude (degrees)")
                plt.yticks(rotation=90)
                alberta_map.plot(ax=ax, alpha=0.4, color='grey')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0) & (geo_df_fwi_probabilities['probign'] <= 0.001)].plot(ax=ax, markersize=10, color='blue', marker='s', label='Low (> 0.000 to 0.001)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0.001) & (geo_df_fwi_probabilities['probign'] <= 0.005)].plot(ax=ax, markersize=10, color='green', marker='s', label='Moderate (> 0.010 to 0.005)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0.005) & (geo_df_fwi_probabilities['probign'] <= 0.015)].plot(ax=ax, markersize=10, color='yellow', marker='s', label='High (> 0.005 to 0.015)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0.015) & (geo_df_fwi_probabilities['probign'] <= 0.025)].plot(ax=ax, markersize=10, color='orange', marker='s', label='Very High (> 0.015 to 0.025)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probign'] > 0.025)].plot(ax=ax, markersize=10, color='red', marker='s', label='Extreme (> 0.025)')
                
                # Display actual lightning strikes on our map, if desired.
                if display_actuals:
                    actuals_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning fire arrival', edgecolor='black', linewidth=0.5)

                # Add a title and a legend to the plot.
                plt.title("Probability of Ignitions (\"probign\") for " + str(date))
                plt.legend(loc='lower left')

                # Check if we are to silently output the generated maps to a PNG image, or if we are to display them in a viewer.
                if silently_output_maps:
                    plt.savefig(fname=(self.ltg_maps_output_folder + "probign_" + str(date) + ".png"), format='png', dpi=150)
                else:
                    pylab.show()
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')

            if map_type == 'probarr0' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing probability of arrivals \"0\" map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(10, 12)
                plt.xlabel("Longitude (degrees)")
                plt.ylabel("Latitude (degrees)")
                plt.yticks(rotation=90)
                alberta_map.plot(ax=ax, alpha=0.4, color='grey')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0) & (geo_df_fwi_probabilities['probarr0'] <= 0.3)].plot(ax=ax, markersize=10, color='blue', marker='s', label='Low (> 0.00 to 0.30)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0.3) & (geo_df_fwi_probabilities['probarr0'] <= 0.55)].plot(ax=ax, markersize=10, color='green', marker='s', label='Moderate (> 0.30 to 0.55)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0.55) & (geo_df_fwi_probabilities['probarr0'] <= 0.75)].plot(ax=ax, markersize=10, color='yellow', marker='s', label='High (> 0.55 to 0.75)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0.75) & (geo_df_fwi_probabilities['probarr0'] <= 0.85)].plot(ax=ax, markersize=10, color='orange', marker='s', label='Very High (> 0.75 to 0.85)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['probarr0'] > 0.85)].plot(ax=ax, markersize=10, color='red', marker='s', label='Extreme (> 0.85)')
                
                # Display actual lightning strikes on our map, if desired.
                if display_actuals:
                    actuals_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning fire arrival', edgecolor='black', linewidth=0.5)

                # Add a title and a legend to the plot.
                plt.title("Probability of Arrivals (\"probarr0\") for " + str(date))
                plt.legend(loc='lower left')

                # Check if we are to silently output the generated maps to a PNG image, or if we are to display them in a viewer.
                if silently_output_maps:
                    plt.savefig(fname=(self.ltg_maps_output_folder + "probarr0_" + str(date) + ".png"), format='png', dpi=150)
                else:
                    pylab.show()
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')
            
            if map_type == 'DMC' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing DMC map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(10, 12)
                plt.xlabel("Longitude (degrees)")
                plt.ylabel("Latitude (degrees)")
                plt.yticks(rotation=90)
                alberta_map.plot(ax=ax, alpha=0.4, color='grey')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] > 0) & (geo_df_fwi_probabilities['dmc'] <= 21)].plot(ax=ax, markersize=10, color='blue', marker='s', label='Low (> 0 to 21)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] > 21) & (geo_df_fwi_probabilities['dmc'] <= 27)].plot(ax=ax, markersize=10, color='green', marker='s', label='Moderate (> 21 to 27)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] > 27) & (geo_df_fwi_probabilities['dmc'] <= 40)].plot(ax=ax, markersize=10, color='yellow', marker='s', label='High (> 27 to 40)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] > 40) & (geo_df_fwi_probabilities['dmc'] <= 60)].plot(ax=ax, markersize=10, color='orange', marker='s', label='Very High (> 40 to 60)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dmc'] > 60)].plot(ax=ax, markersize=10, color='red', marker='s', label='Extreme (> 60)')
                
                # Display actual lightning strikes on our map, if desired.
                if display_actuals:
                    actuals_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning fire arrival', edgecolor='black', linewidth=0.5)

                # Add a title and a legend to the plot.
                plt.title("DMC (Duff Moisture Code) Measurements for " + str(date))
                plt.legend(loc='lower left')

                # Check if we are to silently output the generated maps to a PNG image, or if we are to display them in a viewer.
                if silently_output_maps:
                    plt.savefig(fname=(self.ltg_maps_output_folder + "dmc_" + str(date) + ".png"), format='png', dpi=150)
                else:
                    pylab.show()
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')
            
            if map_type == 'DC' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing DC map...")
                        
                # Clear the current plot, including its figure and axes, for the current map; and plot the Alberta basemap.
                plt.clf()
                fig, ax = plt.subplots()
                fig.set_size_inches(10, 12)
                plt.xlabel("Longitude (degrees)")
                plt.ylabel("Latitude (degrees)")
                plt.yticks(rotation=90)
                alberta_map.plot(ax=ax, alpha=0.4, color='grey')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] > 0) & (geo_df_fwi_probabilities['dc'] <= 80)].plot(ax=ax, markersize=10, color='blue', marker='s', label='Low (> 0 to 80)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] > 80) & (geo_df_fwi_probabilities['dc'] <= 190)].plot(ax=ax, markersize=10, color='green', marker='s', label='Moderate (> 80 to 190)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] > 190) & (geo_df_fwi_probabilities['dc'] <= 300)].plot(ax=ax, markersize=10, color='yellow', marker='s', label='High (> 190 to 300)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] > 300) & (geo_df_fwi_probabilities['dc'] <= 425)].plot(ax=ax, markersize=10, color='orange', marker='s', label='Very High (> 300 to 425)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['dc'] > 425)].plot(ax=ax, markersize=10, color='red', marker='s', label='Extreme (> 425)')
                
                # Display actual lightning strikes on our map, if desired.
                if display_actuals:
                    actuals_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning fire arrival', edgecolor='black', linewidth=0.5)

                # Add a title and a legend to the plot.
                plt.title("DC (Drought Code) Measurements for " + str(date))
                plt.legend(loc='lower left')

                # Check if we are to silently output the generated maps to a PNG image, or if we are to display them in a viewer.
                if silently_output_maps:
                    plt.savefig(fname=(self.ltg_maps_output_folder + "dc_" + str(date) + ".png"), format='png', dpi=150)
                else:
                    pylab.show()
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')
            
            if map_type == 'totltg' or map_type == 'all':

                print("lightningFirePredictionMapper(): Processing totltg map...")
                        
                # Create a new figure and plot the Alberta basemap.
                fig, ax = plt.subplots()
                fig.set_size_inches(10, 12)
                plt.xlabel("Longitude (degrees)")
                plt.ylabel("Latitude (degrees)")
                plt.yticks(rotation=90)
                alberta_map.plot(ax=ax, alpha=0.4, color='grey')

                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 0) & (geo_df_fwi_probabilities['totltg'] <= 1)].plot(ax=ax, markersize=10, color='blue', marker='s', label='Low (> 0 to 1)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 1) & (geo_df_fwi_probabilities['totltg'] <= 3)].plot(ax=ax, markersize=10, color='green', marker='s', label='Moderate (> 1 to 3)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 3) & (geo_df_fwi_probabilities['totltg'] <= 6)].plot(ax=ax, markersize=10, color='yellow', marker='s', label='High (> 3 to 6)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 6) & (geo_df_fwi_probabilities['totltg'] <= 12)].plot(ax=ax, markersize=10, color='orange', marker='s', label='Very High (> 6 to 12)')
                geo_df_fwi_probabilities[(geo_df_fwi_probabilities['totltg'] > 12)].plot(ax=ax, markersize=10, color='red', marker='s', label='Extreme (> 12)')
                
                # Display actual lightning strikes on our map, if desired.
                if display_actuals:
                    actuals_gdf.plot(ax=ax, markersize=75, marker='*', color='fuchsia', label='Lightning fire arrival', edgecolor='black', linewidth=0.5)

                # Add a title and a legend to the plot.
                plt.title("Total Lightning (\"totltg\") for " + str(date))
                plt.legend(loc='lower left')

                # Check if we are to silently output the generated maps to a PNG image, or if we are to display them in a viewer.
                if silently_output_maps:
                    plt.savefig(fname=(self.ltg_maps_output_folder + "totltg_" + str(date) + ".png"), format='png', dpi=150)
                else:
                    pylab.show()
            
                # Reset and close the plot and figures.
                plt.cla()
                plt.clf()
                plt.close('all')

        # End for loop
    
    def lightningStrikeDataMassager(self):
        """ This method massages raw Alberta lightning data into the format required for
            Dr. Wotton's lightning gridder/binner C program.

            Input column headers:
            date_group, local_striketime, gmt_striketime, mst_striketime, latitude, longitude, strength, multiplicity

            Output format (no header, sorted chronologically - VERY IMPORTANT):
            latitude, longitude, strength, multiplicity, year, month, day, hour
        """

        input_csv_file = pd.read_csv(self.ltg_strike_raw_input_path, sep=',')

        # Perform a header check to determine the type of input CSV.
        if list(input_csv_file.columns) == self.ltg_strike_shapefile_headers:
            print("Lightning strike data is from a shapefile.")
            input_file_type = "Shapefile"
        elif list(input_csv_file.columns) == self.ltg_strike_csv_headers:
            print("Lightning strike data is from a CSV export.")
            input_file_type = "CSV"
        else:
            print("Unrecognized lightning strike input format.")
            raw_input("Press any key to continue...")
            input_file_type = "Unknown"
            return
        
        raw_input("Press any key to continue...")

        start_time = timeit.default_timer()
        print("Massaging raw lightning data...")
        print("Time elapsed: ", timeit.default_timer() - start_time)
        print()
        print("Loading and sorting lightning strike data...")

        # Start the massaging by making all of the column headers to be uppercase.
        input_csv_file.columns = map(str.upper, input_csv_file.columns)

        # Parse the local_striketime column as a datetime to allow for easy access to year, month, day and hour.

        if input_file_type == "CSV":
            # Date format of ltg2017b.csv file:
            input_csv_file['LOCAL_STRIKETIME'] = pd.to_datetime(input_csv_file['LOCAL_STRIKETIME'], format="%d/%m/%y %H:%M")

        elif input_file_type == "Shapefile":
            # Date format of lightning_0301_1031_2018.txt
            input_csv_file['LOCAL_STRIKETIME'] = pd.to_datetime(input_csv_file['LOCAL_STRIKETIME'], format="%m/%d/%y %H:%M:%S", infer_datetime_format=True)

        # Sort the CSV by the second column: "local_striketime".
        input_csv_file = input_csv_file.sort_values(by='LOCAL_STRIKETIME')

        # Prepare the output file dataframe.
        output_csv_df = pd.DataFrame(columns=['LATITUDE', 'LONGITUDE', 'STRENGTH', 'MULTIPLICITY', 'YEAR', 'MONTH', 'DAY', 'HOUR'])

        i = 0
        # Now that the rows are sorted, we need to build the input file for the lightning binner library.
        for index, row in input_csv_file.iterrows():
            
            i = i + 1

            if i % 1000 == 0:
                print("lightningStrikeDataMassager(): Currently on row ", i)

            # Need to build a list with data structured in the following order:
            # latitude, longitude, strength, multiplicity, year, month, day, hour
            new_row = {'LATITUDE': round(float(row['LATITUDE']), 4),
                       'LONGITUDE': round(float(row['LONGITUDE']), 4),
                       'STRENGTH': round(float(row['STRENGTH']), 1),
                       'MULTIPLICITY': row['MULTIPLICITY'],
                       'YEAR': row['LOCAL_STRIKETIME'].year,
                       'MONTH': row['LOCAL_STRIKETIME'].month,
                       'DAY': row['LOCAL_STRIKETIME'].day,
                       'HOUR': row['LOCAL_STRIKETIME'].hour}

            # Append the new row to the output list.
            output_csv_df = output_csv_df.append(new_row, ignore_index=True)
        
        # Recast some integer columns to their appropriate type.
        output_csv_df['MULTIPLICITY'] = output_csv_df['MULTIPLICITY'].astype('int32')
        output_csv_df['YEAR'] = output_csv_df['YEAR'].astype('int32')
        output_csv_df['MONTH'] = output_csv_df['MONTH'].astype('int32')
        output_csv_df['DAY'] = output_csv_df['DAY'].astype('int32') 
        output_csv_df['HOUR'] = output_csv_df['HOUR'].astype('int32')

        print output_csv_df
        raw_input("Press any key to continue...")

        # Write the massaged output to disk. This file will be used as input to Dr. Wotton's lightning binning library.
        # No column headers, no index column, tab-separated.
        output_csv_df.to_csv(self.ltg_strike_raw_massaged_output_path, sep=' ', header=False, index=False)
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
        
        print("weatherInterpolationWrapper(): Calling weather interpolation exe...")
        subprocess.call([self.weather_interpolation_exe_path, self.ltg_weather_massaged_output_path, self.ltg_weather_interpolation_coefficients_path])
        print("weatherInterpolationWrapper(): Weather interpolation exe call completed.")

        print("weatherInterpolationWrapper(): Calling weather binner exe...")
        subprocess.call([self.weather_binning_exe_path, self.ltg_weather_binned_output_path, self.ltg_grid_locations_path, self.ltg_weather_interpolation_coefficients_path])
        print("weatherInterpolationWrapper(): Weather binning exe call completed.")
    
    def simulationWrapper(self):
        """ Calls the wrapped simulation tool, feeding it the massaged probability data.
            The simulation tool will produce two output files: one will contain the expected number
            of lightning-caused fires and holdovers on the landscape, and the other will contain
            the confidence interval data.
            
            Here, we use subprocess.call as opposed to subprocess.Popen because subprocess.call
            is blocking; we need the external call to finish before we carry on with other stages of
            the processing flow. """
        
        # Seed the random number generator using the current system time.
        random.seed(datetime.datetime.now())
        
        print("simulationWrapper(): Calling simulation exe...")
        # Sample command line arguments call: simulate-new-allyears.exe 12345 "Z:\\LightningFireOccurrencePredictionInputs\\ltg_output.csv" "Z:\\LightningFireOccurrencePredictionInputs\\AB-predictions.out" "Z:\\LightningFireOccurrencePredictionInputs\\AB-grids.out"
        subprocess.call([self.simulation_exe_path, str(random.randint(1, MAX_INT)), self.ltg_arrivals_holdovers_output_path, self.ltg_confidence_intervals_output_path, self.ltg_gridded_predictions_output_path])
        print("simulationWrapper(): simulation exe call completed.")    

    def rawWeatherDataMassager(self):
        """ This method massages raw Alberta weather data into the format required for
            Dr. Wotton's weather interpolation and gridding C programs.

            Input column headers:
            id, ws_id, c_sky_cndt_id, c_wthr_typ_id, c_wnd_drct_id, weather_date, dry_bulb_temperature,
            wet_bulb_temperature, minimum_temperature, maximum_temperature, relative_humidity, visibility_km,
            wind_speed_kmh, wind_gust_kmh, rain_mm, snow_cm, hail_mm, dew_point, high_cloud_amt, middle_cloud_amt,
            low_cloud_amt, cu_cloud_amt, cuplus_cloud_amt, cb_cloud_amt, grand_total, fine_fuel_moisture_code,
            initial_spread_index, duff_moisture_code, build_up_index, drought_code, daily_severity_rating,
            fire_weather_index, present_weather, weather_remarks, station_id, c_wnd_drct_type, c_sky_cndt_type, name

            Output format (no header, sorted chronologically - VERY IMPORTANT):
            id???, latitude???, longitude???, year, month, day, dry_bulb_temperature, relative_humidity,
            wind_speed_kmh, rain_mm, fine_fuel_moisture_code, duff_moisture_code, drought_code,
            initial_spread_index, build_up_index, fire_weather_index
        """

        input_csv_file = pd.read_csv(self.ltg_raw_weather_input_path, sep=',')
        input_weather_station_locations = pd.read_csv(self.ltg_weather_station_locations_path, sep=',', quotechar='"',
                                                      dtype={'id': int, 'station_name': str})

        print input_weather_station_locations

        # Perform a header check to determine the type of input CSV.
        if list(input_csv_file.columns) == self.ltg_raw_weather_csv_headers:
            print("Raw weather data column check OK.")
        else:
            print("Raw weather data columns do not match what is expected. ERROR")
            raise ValueError
        
        raw_input("Press any key to continue...")

        start_time = timeit.default_timer()
        print("rawWeatherDataMassager(): Massaging raw weather data...")
        print("Time elapsed: ", timeit.default_timer() - start_time)
        print()
        print("Loading and sorting raw weather data...")

        # Parse the weather_date column as a datetime to allow for easy access to year, month, day and hour.
        # Here, we use the infer_datetime_format=True flag because the datetime in the file is NOT zero-padded, and
        # the default datetime placeholders do not allow for that by default
        input_csv_file['weather_date'] = pd.to_datetime(input_csv_file['weather_date'], format="%m/%d/%y %H:%M", infer_datetime_format=True)

        # Sort the CSV by the column: "weather_date".
        input_csv_file = input_csv_file.sort_values(by='weather_date')

        """Output format (no header, sorted chronologically - VERY IMPORTANT):
            id???, latitude???, longitude???, year, month, day, dry_bulb_temperature, relative_humidity,
            wind_speed_kmh, rain_mm, fine_fuel_moisture_code, duff_moisture_code, drought_code,
            initial_spread_index, build_up_index, fire_weather_index"""

        # Prepare the output file dataframe.
        # TO-DO: NEED TO ADD 'id', 'latitude', 'longitude' COLUMNS!!!!
        output_csv_df = pd.DataFrame(columns=['id', 'latitude', 'longitude', 'year', 'month', 'day', 'dry_bulb_temperature',
                                              'relative_humidity', 'wind_speed_kmh', 'rain_mm', 'fine_fuel_moisture_code',
                                              'duff_moisture_code', 'drought_code', 'initial_spread_index', 'build_up_index',
                                              'fire_weather_index'])
        
        print input_csv_file
        raw_input("Press any key to continue...")
        
        i = 0
        # Now that the rows are sorted, we need to build the input file for the weather interpolation library.
        for index, row in input_csv_file.iterrows():
            
            i = i + 1

            if i % 1000 == 0:
                print("rawWeatherDataMassager(): Currently on row ", i)
            
            # Perform an inner join on the station ID column in the weather station locations file and the raw weather
            # data.
            weather_station_row = input_weather_station_locations.loc[input_weather_station_locations['station_id'] == row['station_id']]

            # There should only be a single unique weather station returned.
            assert(len(weather_station_row) == 1)

            # Need to build a list with data structured in the following order:
            # latitude, longitude, strength, multiplicity, year, month, day, hour
            new_row = {'id': list(weather_station_row['id'])[0],  # This is a weird bit of code to properly extract the numerical station id.
                       'latitude': round(float(weather_station_row['latitude']), 4),
                       'longitude': round(float(weather_station_row['longitude']), 4),
                       'year': row['weather_date'].year,
                       'month': row['weather_date'].month,
                       'day': row['weather_date'].day,
                       'dry_bulb_temperature': round(row['dry_bulb_temperature'], 1),
                       'relative_humidity': round(row['relative_humidity'], 0),
                       'wind_speed_kmh': round(row['wind_speed_kmh'], 0),
                       'rain_mm': round(row['rain_mm'], 2),
                       'fine_fuel_moisture_code': round(row['fine_fuel_moisture_code'], 1),
                       'duff_moisture_code': round(row['duff_moisture_code'], 1),
                       'drought_code': round(row['drought_code'], 1),
                       'initial_spread_index': round(row['initial_spread_index'], 1),
                       'build_up_index': round(row['build_up_index'], 1),
                       'fire_weather_index': round(row['fire_weather_index'], 1)}

            # Since some of the weather and FWI index columns might be NaN, we need to populate them
            # with -999.9 if they are so that Dr. Wotton's weather interpolation program can
            # handle them.
            if math.isnan(row['dry_bulb_temperature']):
                new_row['dry_bulb_temperature'] = -999.9

            if math.isnan(row['relative_humidity']):
                new_row['relative_humidity'] = -999.9

            if math.isnan(row['wind_speed_kmh']):
                new_row['wind_speed_kmh'] = -999.9

            if math.isnan(row['rain_mm']):
                new_row['rain_mm'] = -999.9

            if math.isnan(row['fine_fuel_moisture_code']):
                new_row['fine_fuel_moisture_code'] = -999.9

            if math.isnan(row['duff_moisture_code']):
                new_row['duff_moisture_code'] = -999.9
                
            if math.isnan(row['drought_code']):
                new_row['drought_code'] = -999.9
                
            if math.isnan(row['initial_spread_index']):
                new_row['initial_spread_index'] = -999.9
                
            if math.isnan(row['build_up_index']):
                new_row['build_up_index'] = -999.9
                
            if math.isnan(row['fire_weather_index']):
                new_row['fire_weather_index'] = -999.9          

            # Append the new row to the output list.
            output_csv_df = output_csv_df.append(new_row, ignore_index=True)
                       
        # Recast some integer columns to their appropriate type.
        output_csv_df['id'] = output_csv_df['id'].astype('int32')
        output_csv_df['year'] = output_csv_df['year'].astype('int32')
        output_csv_df['month'] = output_csv_df['month'].astype('int32')
        output_csv_df['day'] = output_csv_df['day'].astype('int32')

        # Write the massaged output to disk. This file will be used as input to Dr. Wotton's weather interpolation library.
        # No column headers, no index column, tab-separated.
        output_csv_df.to_csv(self.ltg_weather_massaged_output_path, sep=' ', header=False, index=False)
        print("rawWeatherDataMassager(): Raw lightning strike data massaged successfully.")
    
    def mergeBinnedWeatherAndLightning(self):
        """ This method will take in the binned weather and lightning data, and combine it into a single
            dataset.

            Once this is completed, the merged dataset can then be used by the
            processLightningArrivalsHoldoversIgnitions() method to compute probabilities of arrivals and
            holdovers. """

        # For the binned lightning CSV, treat multiple consecutive whitespace characters as a
        # single delimeter.
        input_binned_weather_df = pd.read_csv(self.ltg_weather_binned_output_path, sep=',', header=None)
        input_binned_weather_df.columns = ['grid', 'year', 'month', 'day', 'temp', 'rh', 'ws', 'rain',
                                                 'ffmc', 'dmc', 'dc', 'isi', 'bui', 'fwi']
        input_binned_lightning_df = pd.read_csv(self.ltg_lightning_binned_output_path, header=None, delim_whitespace=True)
        input_binned_lightning_df.columns = ['grid', 'latitude', 'longitude', 'year', 'month', 'day',
                                                   'period', 'neg', 'pos']

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
        grid_locations_df = pd.read_csv(self.ltg_grid_locations_path, sep=r'\s*', header=None, engine='python')
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
        raw_input("Press enter to continue...")

        print("mergeBinnedWeatherAndLightning(): Data massaging completed, outputting table to disk...")

        # Output the merged and massaged dataset.
        merged_lightning_weather_df.to_csv(self.ltg_merged_weather_lightning_data_path, sep=',', index=False)

        print("mergeBinnedWeatherAndLightning(): Table has been outputted to disk.")

    def processLightningArrivalsHoldoversIgnitions(self, input_path=None):
        """ For each line of input, this method will append two columns containing probability
            values:

            probarr0 = The probability that a fire arrives on the day it is ignited by lightning;
            probarr1 = The probability that a fire arrives the day after ignition. """
        
        # If a path to the input file is not provided to the method, use the default one.
        if input_path == None:
            input_path = self.ltg_arrivals_holdovers_input_path

        print("processLightningArrivalsHoldoversIgnitions(): input_path is ", input_path)

        start_time = timeit.default_timer()
        print ("Calculating fire arrivals probabilities...")
        print ("Time elapsed: ", timeit.default_timer() - start_time)
        
        input_file_handle = open(input_path, 'rb')
        input_csv_file = csv.reader(input_file_handle, quotechar='|')

        output_file_handle = open(self.ltg_arrivals_holdovers_output_path, 'wb')
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
            if i % 10000 == 0:           
                print("Currently on row #", i)
                print("Time elapsed: ", timeit.default_timer() - start_time)

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
            
            dry = "DRY"
            if float(working_dict['rain']) > 0.2:
                dry = "WET"            
            
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
            #raw_input("Press enter to continue. . .")
            
            # Append to the output file.
            output_csv_file.writerow(new_row)
        
        # End of fire arrivals for loop.
        print("Completed calculating lightning fire probabilities.")
        print("Time elapsed: ", timeit.default_timer() - start_time)
        print("Overall total rows analyzed: ", i)
        print("Rows processed: ", processed)
    
    def addLatLongsToGriddedFWIWeatherFile(self):
        """ This is a "debugging" method which will add lat/longs as columns to the gridded FWI weather file
            for plotting in Google Earth, as an example.
        """
        
        # Load in the gridded / binned FWI indices file and name the first column "grid".
        input_binned_weather_df = pd.read_csv(self.ltg_weather_binned_output_path, sep=',', header=None)
        columns = list(input_binned_weather_df.columns.values)
        print("addLatLongsToGriddedFWIWeatherFile(): columns is ", columns)
        columns[0] = "grid"
        input_binned_weather_df.columns = columns

        # Load in the grid locations file and label the columns.
        ltg_grid_locations_df = pd.read_csv(self.ltg_grid_locations_path, sep=r'\s*', header=None, engine='python')
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

        
        print("addLatLongsToGriddedFWIWeatherFile(): the new columns are ", new_columns)
        
        # Output the newly-merged dataset.
        input_binned_weather_df_lat_long.to_csv(self.ltg_weather_binned_output_lat_longs_added_path, sep=',', index=False, header=False)

def controller(self, date_to_predict_for):
    """ This method contains the logic behind determining if the master data set needs to be updated or not.
        If it does, load the updated raw weather and lightning strike data and run it through the
        processing flow.

        This method also contains a lot of error-checking to ensure that the integrity of the data is
        maintained. """

    # Step #1: Load the post-simulation dataset.

    # Load in the FOP system state data set, and the raw weather and lightning strike data.
    
    # Sanity check: Ensure that the system state data set exists.
    try:
        self.fop_system_state_db_df = pd.read_csv(self.ltg_grid_locations_path, sep=',')
    except:
        print("controller(): Excepted an error reading the FOP system state DB.")
    
    # Determine which days need processing, if any.





    # We first need to check if there are any days missing in the master data set by comparing the most
    # recent date in the data set to the date provided as input to the controller.
    # If there is not, then



def mainMethod():
    """ This is the main method called by the application entrypoint. """

    # Is Matthew working from home today? :)
    working_from_home_today = True

    # Should we use the controller method to automatically update the master dataset, or do we want
    # to just run 

    # Will likely switch these paths to command-line parameters, or a config.ini file, later.
    # Use strings for now.
    if working_from_home_today:
        
        # HOME PC, PHASE #1:
        ltg_arrivals_holdovers_input_path = 'Z:\LightningFireOccurrencePredictionInputs\AB-processing-forMATT-datasetALL-FIRST-136100-ROWS.csv'
        ltg_arrivals_holdovers_output_path = 'Z:\LightningFireOccurrencePredictionInputs\ltg_probabilities_output.out'
        #ltg_strike_raw_input_path = 'Y:\University of Alberta\Software Development\FireOccurrencePrediction\lightning\misc\ltg2017b.csv'
        ltg_strike_raw_input_path = 'Z:\LightningFireOccurrencePredictionInputs\Lightning_0301_1031_2018.txt'
        ltg_strike_raw_massaged_output_path = 'Z:\LightningFireOccurrencePredictionInputs\ABltg_space_MATT.out'
        ltg_grid_locations_path = 'Y:\\University of Alberta\\Software Development\\FireOccurrencePrediction\\lightning\\binning\\Gridlocations.prn'
        ltg_lightning_binned_output_path = 'Z:\\LightningFireOccurrencePredictionInputs\\ltg-10by10-five-period_MATT.dat'
        ltg_raw_weather_input_path = 'Z:\LightningFireOccurrencePredictionInputs\Alberta_PM_Weather_2018.csv'
        ltg_weather_massaged_output_path = 'Z:\LightningFireOccurrencePredictionInputs\Alberta_PM_Weather_2018_MASSAGED.csv'
        ltg_weather_binned_output_path = 'Z:\LightningFireOccurrencePredictionInputs\FWIgrid10-AB.dat'     
        ltg_weather_binned_output_lat_longs_added_path = 'Z:\LightningFireOccurrencePredictionInputs\FWIgrid10-AB-May22-23.dat'       
        ltg_weather_interpolation_coefficients_path = 'Z:\LightningFireOccurrencePredictionInputs\\'
        ltg_weather_station_locations_path = 'Z:\LightningFireOccurrencePredictionInputs\Alberta_Weather_Stations_Active_Inactive_2019_MATT.csv'
        ltg_fishnet_nsr_path = 'Y:\\University of Alberta\\Software Development\\FireOccurrencePrediction\\lightning\\misc\\alberta_static.csv'
        ltg_merged_weather_lightning_data_path = 'Z:\LightningFireOccurrencePredictionInputs\Alberta_Merged_Weather_Lightning_MATT.csv'
        ltg_confidence_intervals_output_path = "Z:\\LightningFireOccurrencePredictionInputs\\AB-predictions.out"
        ltg_gridded_predictions_output_path = "Z:\\LightningFireOccurrencePredictionInputs\\AB-grids.out"
        ltg_alberta_shapefile = 'Y:\\University of Alberta\\Software Development\\FireOccurrencePrediction\\shapefiles\\asrd_mgmt_area\\BF_ASRD_MGMT_AREA_POLYGON.shp'
        ltg_actual_2018_fires = 'Z:\\LightningFireOccurrencePredictionInputs\\ABltgfires-2018.csv'
        ltg_maps_output_folder = 'Z:\\LightningFireOccurrencePredictionInputs\\output_maps\\'

        # HOME PC, PHASE #2:
        """ltg_input_raw_weather_data_path = 'Z:\LightningFireOccurrencePredictionInputs\Alberta_PM_Weather_2018.csv'
        ltg_input_raw_lightning_strike_data_path = ''
        fop_system_state_db_path = 'C:\\Users\\Ansell\\Dropbox\\University of Alberta\\Software Development\\FireOccurrencePrediction\\data\\fop_system_state_db.csv'"""
    else:

        # LAB PC:
        ltg_arrivals_holdovers_input_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\arrival_and_ignition_probabilities\AB-processing-forMATT-datasetALL-FIRST-136100-ROWS.csv'
        ltg_arrivals_holdovers_output_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\arrival_and_ignition_probabilities\ltg_probabilities_output.out'
        #ltg_arrivals_holdovers_output_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\arrival_and_ignition_probabilities\\year2013.ready-new'
        #ltg_strike_raw_input_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\alberta_data\ltg2017b.csv'
        ltg_strike_raw_input_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\alberta_data\Lightning_0301_1031_2018.txt'
        ltg_strike_raw_massaged_output_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\ltg_binning\\ABltg_space_MATT.out'
        ltg_grid_locations_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\ltg_binning\Gridlocations.prn'
        ltg_lightning_binned_output_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\ltg_binning\ltg2010-10by10-five-period_MATT.dat'
        ltg_raw_weather_input_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\alberta_data\Alberta_PM_Weather_2018.csv'
        ltg_weather_massaged_output_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\alberta_data\Alberta_PM_Weather_2018_MASSAGED.csv'
        ltg_weather_binned_output_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\weather_interpolation\FWIgrid10-AB.dat'
        ltg_weather_binned_output_lat_longs_added_path = 'C:\Users\Ansell\Desktop\FOR_MIKE\FWIgrid10-AB-LAT-LONGS-ADDED.dat'
        ltg_weather_interpolation_coefficients_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\weather_interpolation\\'
        ltg_weather_station_locations_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\alberta_data\\Alberta_Weather_Stations_Active_Inactive_2019_MATT.csv'
        ltg_fishnet_nsr_path = 'C:\Users\Ansell\Dropbox\University of Alberta\Software Development\FireOccurrencePrediction\lightning\misc\\alberta_static.csv'
        ltg_merged_weather_lightning_data_path = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\alberta_data\\Alberta_Merged_Weather_Lightning_MATT.csv'
        ltg_confidence_intervals_output_path = "C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\AB-predictions_2018_new_1000_simulations.out"
        ltg_gridded_predictions_output_path = "C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\AB-grids_2018_new.out"
        ltg_alberta_shapefile = 'C:\\Users\\Ansell\\Dropbox\\University of Alberta\\Software Development\\FireOccurrencePrediction\\shapefiles\\asrd_mgmt_area\\BF_ASRD_MGMT_AREA_POLYGON.shp'
        ltg_actual_2018_fires = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\alberta_data\\ABltgfires-2018.csv'
        ltg_maps_output_folder = 'C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\output_maps\\'
        
        fop_system_state_db_path = 'C:\\Users\\Ansell\\Dropbox\\University of Alberta\\Software Development\\FireOccurrencePrediction\\data\\fop_system_state_db.csv'

    obj = LightningFireOccurrencePrediction(ltg_arrivals_holdovers_input_path,
                                            ltg_arrivals_holdovers_output_path,
                                            ltg_strike_raw_input_path,
                                            ltg_strike_raw_massaged_output_path,
                                            ltg_grid_locations_path,
                                            ltg_lightning_binned_output_path,
                                            ltg_raw_weather_input_path,
                                            ltg_weather_massaged_output_path,
                                            ltg_weather_binned_output_path,
                                            ltg_weather_binned_output_lat_longs_added_path,
                                            ltg_weather_station_locations_path,
                                            ltg_fishnet_nsr_path,
                                            ltg_merged_weather_lightning_data_path,
                                            ltg_weather_interpolation_coefficients_path,
                                            ltg_gridded_predictions_output_path,
                                            ltg_confidence_intervals_output_path,
                                            ltg_alberta_shapefile,
                                            ltg_actual_2018_fires,
                                            ltg_maps_output_folder,
                                            fop_system_state_db_path)
    #obj.lightningStrikeDataMassager()
    #obj.lightningBinnerWrapper()
    #obj.rawWeatherDataMassager()
    #obj.weatherInterpolationBinnerWrapper()
    #obj.addLatLongsToGriddedFWIWeatherFile()  # OPTIONAL DEBUGGING STEP!
    #obj.mergeBinnedWeatherAndLightning()
    #obj.processLightningArrivalsHoldoversIgnitions(ltg_merged_weather_lightning_data_path)
    #obj.processLightningArrivalsHoldoversIgnitions()
    #obj.simulationWrapper()

    # Provide a date to the mapper, as well as whether to display actual fires.
    days_to_map = [datetime.date(2018,5,21),
                   datetime.date(2018,5,22),
                   datetime.date(2018,5,23),
                   datetime.date(2018,5,24),
                   datetime.date(2018,5,25),
                   datetime.date(2018,5,26),
                   datetime.date(2018,5,27),
                   datetime.date(2018,6,20),
                   datetime.date(2018,6,21),
                   datetime.date(2018,6,22),
                   datetime.date(2018,6,23),
                   datetime.date(2018,6,24),
                   datetime.date(2018,6,25),
                   datetime.date(2018,6,26),
                   datetime.date(2018,6,27),
                   datetime.date(2018,6,28),
                   datetime.date(2018,7,15),
                   datetime.date(2018,7,16),
                   datetime.date(2018,7,17),
                   datetime.date(2018,7,18),
                   datetime.date(2018,7,19),
                   datetime.date(2018,7,20),
                   datetime.date(2018,7,27),
                   datetime.date(2018,7,28),
                   datetime.date(2018,7,29),
                   datetime.date(2018,7,30),
                   datetime.date(2018,7,31),
                   datetime.date(2018,8,1), 
                   datetime.date(2018,8,2), 
                   datetime.date(2018,8,3), 
                   datetime.date(2018,8,4), 
                   datetime.date(2018,8,5), 
                   datetime.date(2018,8,6), 
                   datetime.date(2018,8,7)
                   ]
    
    """days_to_map = [datetime.date(2018,5,15),
                   datetime.date(2018,5,16),
                   datetime.date(2018,5,17),
                   datetime.date(2018,5,18),
                   datetime.date(2018,5,19),
                   datetime.date(2018,5,20),
                   datetime.date(2018,5,21),
                   datetime.date(2018,5,22),
                   datetime.date(2018,5,23),
                   datetime.date(2018,5,24),
                   datetime.date(2018,5,25),
                   datetime.date(2018,5,26),
                   datetime.date(2018,5,27)
                   ]"""


    display_actual_fires = True
    silently_output_maps = True

    # Valid map strings: 'arrival', 'holdover', 'probign', 'probarr0', 'DMC', 'DC', 'totltg', ... all case sensitive.
    # Use 'all' to output all maps.
    obj.lightningFirePredictionMapper('all', days_to_map, display_actual_fires, silently_output_maps)

# Entrypoint for application execution.
if __name__ == "__main__":

    # Call the main method.
    mainMethod()
