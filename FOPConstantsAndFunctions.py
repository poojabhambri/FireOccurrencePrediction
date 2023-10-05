""" This file provides helper functions used in multiple places in the FOP application and model.
"""

import datetime
import random
import pandas as pd
from math import isnan

######################################### CONSTANTS #########################################

# Numericals.
MAX_INT = 32767

# Feature and function toggles that are hands-off to the user.
SHOW_PROBABILITY_ARRIVAL_HOLDOVER_RANGES_IN_LEGEND = False

# Header for the FOP system state DB.
FOP_SYSTEM_STATE_DB_HEADERS = ['DATE','LIGHTNING_FOP_COMPLETED','HUMAN_FOP_COMPLETED','FORECASTED_OR_OBSERVED']

# Raw lightning strike data column headers used to ensure input lightning data is structured correctly.
LTG_STRIKE_SHAPEFILE_HEADERS = ['OBJECTID','ID','CREATE_TIMESTAMP','CREATE_USERID','DATETIME','LATITUDE',
                                'LONGITUDE','STRENGTH','MULTIPLICITY','UPDATE_TIMESTAMP','UPDATE_USERID','LOCAL_STRIKETIME']
                                
LTG_STRIKE_CSV_HEADERS = ['date_group','local_striketime','gmt_striketime','mst_striketime','latitude','longitude','strength',
                          'multiplicity']

LTG_STRIKE_CSV_HEADERS_2 = ['LOCAL_STRIKETIME', 'LATITUDE', 'LONGITUDE', 'STRENGTH', 'MULTIPLICITY', 'year']

# Raw weather data column headers used to ensure input weather data is structured correctly.
RAW_WEATHER_CSV_HEADERS = ['id', 'ws_id', 'c_sky_cndt_id', 'c_wthr_typ_id', 'c_wnd_drct_id', 'weather_date',
                               'dry_bulb_temperature', 'wet_bulb_temperature', 'minimum_temperature', 'maximum_temperature',
                               'relative_humidity', 'visibility_km', 'wind_speed_kmh', 'wind_gust_kmh', 'rain_mm', 'snow_cm',
                               'hail_mm', 'dew_point', 'high_cloud_amt', 'middle_cloud_amt', 'low_cloud_amt', 'cu_cloud_amt',
                               'cuplus_cloud_amt', 'cb_cloud_amt', 'grand_total', 'fine_fuel_moisture_code',
                               'initial_spread_index', 'duff_moisture_code', 'build_up_index', 'drought_code',
                               'daily_severity_rating', 'fire_weather_index', 'present_weather', 'weather_remarks',
                               'station_id', 'c_wnd_drct_type', 'c_sky_cndt_type', 'name']
# RAW_WEATHER_CSV_HEADERS = ['id','ws_id','c_wnd_drct_id','weather_date','dry_bulb_temperature','minimum_temperature','maximum_temperature','relative_humidity','wind_speed_kmh','wind_gust_kmh','rain_mm','dew_point','precipitation','station_id','c_wnd_drct_type','name','wind_degrees','rh_max_h','rh_min_h','t_max_h','t_min_h','maximum_18h_rh','minimum_18h_rh']
# RAW_WEATHER_CSV_HEADERS = ['id','ws_id','c_sky_cndt_id','c_wthr_typ_id','c_wnd_drct_id','weather_date','dry_bulb_temperature','wet_bulb_temperature','minimum_temperature','maximum_temperature','relative_humidity','visibility_km','wind_speed_kmh','wind_gust_kmh','rain_mm','snow_cm','hail_mm','dew_point','high_cloud_amt','middle_cloud_amt','low_cloud_amt','cu_cloud_amt','cuplus_cloud_amt','cb_cloud_amt','grand_total','fine_fuel_moisture_code','initial_spread_index','duff_moisture_code','build_up_index','drought_code','daily_severity_rating','fire_weather_index','present_weather','weather_remarks','station_id','c_wnd_drct_type','c_sky_cndt_type','name','precipitation']
# RAW_WEATHER_CSV_HEADERS_2 = ['WEATHER_DATE', 'STATION_ID', 'LATITUDE', 'LONGITUDE', 'STATION_TYPE', 'FORECAST_REGION',
#                                  'DRY_BULB_TEMPERATURE', 'RELATIVE_HUMIDITY', 'WIND_SPEED_KMH', 'WIND_DIRECTION', 'PRECIPITATION',
#                                  'FINE_FUEL_MOISTURE_CODE', 'DUFF_MOISTURE_CODE', 'DROUGHT_CODE', 'BUILD_UP_INDEX', 'INITIAL_SPREAD_INDEX',
#                                  'FIRE_WEATHER_INDEX', 'DAILY_SEVERITY_RATING', 'ACTIVE']
RAW_WEATHER_CSV_HEADERS_2 = ['STATION_ID', 'WEATHER_DATE','DRY_BULB_TEMPERATURE', 'RELATIVE_HUMIDITY','rain_mm','snow_cm','hail_mm','precipitation_mm','WIND_SPEED_KMH', 'WIND_DIRECTION', 'FINE_FUEL_MOISTURE_CODE', 'DUFF_MOISTURE_CODE', 'DROUGHT_CODE', 'INITIAL_SPREAD_INDEX','BUILD_UP_INDEX', 'FIRE_WEATHER_INDEX', 'DAILY_SEVERITY_RATING']

# Interpolated and binned weather data column headers.
INTERPOLATED_BINNED_WEATHER_DATA_HEADERS = ['grid', 'year', 'month', 'day', 'temp', 'rh', 'ws', 'rain',
                                            'ffmc', 'dmc', 'dc', 'isi', 'bui', 'fwi']

# Column headers for the confidence interval C simulation predictions output file, 'AB-predictions.out'.
LTG_CONFIDENCE_INTERVAL_PREDICTIONS_HEADERS = ['year', 'today', 'month', 'day', 'avgnign', 'totfire', 'ltgsum',
                                               'totholdPROV_ci_low', 'totholdPROV_ci_high', 'totarrPROV_ci_low', 'totarrPROV_ci_high',
                                               'totholdSLOPES_ci_low', 'totholdSLOPES_ci_high', 'totarrSLOPES_ci_low', 'totarrSLOPES_ci_high',
                                               'totholdWESTBOREAL_ci_low', 'totholdWESTBOREAL_ci_high', 'totarrWESTBOREAL_ci_low', 'totarrWESTBOREAL_ci_high',
                                               'totholdEASTBOREAL_ci_low', 'totholdEASTBOREAL_ci_high', 'totarrEASTBOREAL_ci_low', 'totarrEASTBOREAL_ci_high',
                                               'unused1', 'unused2', 'unused3']

LTG_GRIDDED_PREDICTIONS_HEADERS = ['grid', 'year', 'month', 'day', 'lat', 'lon', 'narrtoday', 'nholdtoday', 'nigntoday']

# Column headers for the probability of arrivals and holdovers predictions file.
LTG_PROBABILITY_ARRIVALS_HOLDOVERS_HEADERS = ['grid', 'lat', 'lon', 'year', 'jd', 'probign', 'probarr0', 'probarr1', 'totltg',
                                              'numfire', 'region', 'nltg0', 'nltg1', 'nltg2', 'nltg3', 'nltg4', 'dmc', 'dc']

# Column headers for the Human FOP gridded expected value and probabilities file.
HMN_PROBABILITIES_EXPECTED_VALUES_HEADERS = ['fishnet_id', 'date', 'day_of_year', 'latitude', 'longitude',
                                             'forest_area', 'region_ci', 'nsr_numerical_code', 'ffmc_interpolated', 'logit', 'probability']

# Column headers for the Human FOP confidence intervals file.
HMN_CONFIDENCE_INTERVAL_PREDICTIONS_HEADERS = ['year', 'today', 'month', 'day', 'totarrPROV_ci_low', 'totarrPROV_ci_high',
                                               'totarrSLOPES_ci_low', 'totarrSLOPES_ci_high', 'totarrWESTBOREAL_ci_low', 'totarrWESTBOREAL_ci_high',
                                               'totarrEASTBOREAL_ci_low', 'totarrEASTBOREAL_ci_high']

HMN_INTERMEDIATE_SIM_COLUMNS = ['sim_num', 'fishnet_id', 'region_ci', 'probability', 'random_number', 'fire_alberta', 'fire_slopes', 'fire_west_boreal',
                                'fire_east_boreal']

######################################### FUNCTIONS #########################################

def daterange(start_date, end_date):
    """ This helper function provides a generator which iterates over a date range.
        NOT INCLUSIVE on end_date. """

    # Ensure that we have consistent types.
    if not isinstance(start_date, datetime.datetime):
        start_date = datetime.datetime(start_date.year, start_date.month, start_date.day)
    
    if not isinstance(end_date, datetime.datetime):
        end_date = datetime.datetime(end_date.year, end_date.month, end_date.day)

    for i in range(int((end_date - start_date).days)):
        yield start_date + datetime.timedelta(i)

def rawWeatherDataMassager(input_df, output_path, weather_station_locations_path):
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
            id, latitude, longitude, year, month, day, dry_bulb_temperature, relative_humidity,
            wind_speed_kmh, rain_mm, fine_fuel_moisture_code, duff_moisture_code, drought_code,
            initial_spread_index, build_up_index, fire_weather_index
        """

        output_headers = ['id', 'latitude', 'longitude', 'year', 'month', 'day', 'dry_bulb_temperature', 'relative_humidity',
                          'wind_speed_kmh', 'rain_mm', 'fine_fuel_moisture_code', 'duff_moisture_code', 'drought_code',
                          'initial_spread_index', 'build_up_index', 'fire_weather_index']

        # Load in the weather station locations file.
        # input_weather_station_locations = pd.read_csv(self.ltg_weather_station_locations_path, sep=',', quotechar='"',
        #                                               dtype={'id': int, 'station_name': str})
        input_weather_station_locations = pd.read_csv(weather_station_locations_path, sep=',', quotechar='"',
                                                      dtype={'STATION_NAME': str})

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data...")

        # Assign a random number to the 'id' column, Dr. Wotton's binning program doesn't care what the value is.
        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - id...")
        input_df['id'] = random.randint(1, 1001)
        
        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - latitude...")
        # input_df['latitude'] = input_df['station_id'].apply(lambda x : round(float(input_weather_station_locations.loc[input_weather_station_locations['STATION_ID'] == x]['LATITUDE']), 4))
        # Step 1: Filter input_weather_station_locations based on 'station_id'

        print("step 1")

        input_df['filtered_location'] = input_df['station_id'].apply(lambda x: input_weather_station_locations[input_weather_station_locations['STATION_ID'] == x])

 

        # Step 2: Extract latitude from the filtered locations

        print("step 2")

        input_df['latitude'] = input_df['filtered_location'].apply(lambda x: float(x['LATITUDE'].values[0]) if not x.empty else None)

 

        # Step 3: Round latitude to 4 decimal places

        print("step 3")

        input_df['latitude'] = input_df['latitude'].apply(lambda x: round(x, 4) if x is not None else None)

 

        # Step 4: Drop the intermediate column 'filtered_location'

        print("step 4")

        input_df.drop(columns=['filtered_location'], inplace=True)
        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - longitude...")
        # input_df['longitude'] = input_df['station_id'].apply(lambda x : round(float(input_weather_station_locations.loc[input_weather_station_locations['STATION_ID'] == x]['LONGITUDE']), 4))
        input_df['filtered_location'] = input_df['station_id'].apply(lambda x: input_weather_station_locations[input_weather_station_locations['STATION_ID'] == x])

        input_df['longitude'] = input_df['filtered_location'].apply(lambda x: float(x['LONGITUDE'].values[0]) if not x.empty else None)

        input_df['longitude'] = input_df['longitude'].apply(lambda x: round(x, 4) if x is not None else None)

        input_df.drop(columns=['filtered_location'], inplace=True)
        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - year...")
        input_df['year'] = input_df['weather_date'].apply(lambda x : x.year)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - month...")
        input_df['month'] = input_df['weather_date'].apply(lambda x : x.month)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - day...")
        input_df['day'] = input_df['weather_date'].apply(lambda x : x.day)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - dry_bulb_temperature...")
        input_df['dry_bulb_temperature'] = input_df['dry_bulb_temperature'].apply(lambda x : round(x, 1))
        input_df['dry_bulb_temperature'] = input_df['dry_bulb_temperature'].apply(lambda x : '-999.9' if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - relative_humidity...")
        input_df['relative_humidity'] = input_df['relative_humidity'].apply(lambda x : round(x, 1))
        input_df['relative_humidity'] = input_df['relative_humidity'].apply(lambda x : -999.9 if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - wind_speed_kmh...")
        input_df['wind_speed_kmh'] = input_df['wind_speed_kmh'].apply(lambda x : round(x, 1))
        input_df['wind_speed_kmh'] = input_df['wind_speed_kmh'].apply(lambda x : -999.9 if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - rain_mm...")
        input_df['rain_mm'] = input_df['rain_mm'].apply(lambda x : round(x, 2))
        input_df['rain_mm'] = input_df['rain_mm'].apply(lambda x : -999.9 if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - fine_fuel_moisture_code...")
        input_df['fine_fuel_moisture_code'] = input_df['fine_fuel_moisture_code'].apply(lambda x : round(x, 1))
        input_df['fine_fuel_moisture_code'] = input_df['fine_fuel_moisture_code'].apply(lambda x : -999.9 if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - duff_moisture_code...")
        input_df['duff_moisture_code'] = input_df['duff_moisture_code'].apply(lambda x : round(x, 1))
        input_df['duff_moisture_code'] = input_df['duff_moisture_code'].apply(lambda x : -999.9 if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - drought_code...")
        input_df['drought_code'] = input_df['drought_code'].apply(lambda x : round(x, 1))
        input_df['drought_code'] = input_df['drought_code'].apply(lambda x : -999.9 if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - initial_spread_index...")
        input_df['initial_spread_index'] = input_df['initial_spread_index'].apply(lambda x : round(x, 1))
        input_df['initial_spread_index'] = input_df['initial_spread_index'].apply(lambda x : -999.9 if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - build_up_index...")
        input_df['build_up_index'] = input_df['build_up_index'].apply(lambda x : round(x, 1))
        input_df['build_up_index'] = input_df['build_up_index'].apply(lambda x : -999.9 if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - fire_weather_index...")
        input_df['fire_weather_index'] = input_df['fire_weather_index'].apply(lambda x : round(x, 1))
        input_df['fire_weather_index'] = input_df['fire_weather_index'].apply(lambda x : -999.9 if isnan(x) else x)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - Applying column types...")
        input_df['id'] = input_df['id'].astype('int32')
        input_df['year'] = input_df['year'].astype('int32')
        input_df['month'] = input_df['month'].astype('int32')
        input_df['day'] = input_df['day'].astype('int32')

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - Dropping unneeded columns...")
        input_df = input_df[output_headers]
        
        output_headers = ['id', 'latitude', 'longitude', 'year', 'month', 'day', 'dry_bulb_temperature', 'relative_humidity',
                          'wind_speed_kmh', 'rain_mm', 'fine_fuel_moisture_code', 'duff_moisture_code', 'drought_code',
                          'initial_spread_index', 'build_up_index', 'fire_weather_index']

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Massaging raw weather data - Outputting massages weather to disk...")
        input_df.to_csv(output_path, sep=' ', header=False, index=False)
        print(input_df)

        print("FOPConstantsAndFunctions().rawWeatherDataMassager(): Raw weather data massaged successfully.")