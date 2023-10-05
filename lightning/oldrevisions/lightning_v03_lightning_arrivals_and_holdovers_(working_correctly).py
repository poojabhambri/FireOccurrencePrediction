""" This is a Python translation of the SAS portion of Dr. Mike Wotton's Lightning Occurrence Prediction model.

    This code is written for the UAlberta Fire Occurrence Prediction project, in collaboration with the Government of Alberta
    and the Canadian Forest Service.

    Author: Matthew Ansell
    2019
"""

import csv  # Used for input / output data processing.
import math  # Used for model calculations.``
import timeit  # Used for measuring code execution time.
from decimal import Decimal  # Used to round probabilities to an exact decimal as opposed to float.
import datetime  # Used to determine the day of year.


class LightningOccurrencePrediction(object):
    """ This class contains the logic for the Lightning Occurrence Prediction model itself. """

    def __init__(self, ltg_arrivals_input_path, ltg_arrivals_output_path):
        self.ltg_arrivals_input_path = ltg_arrivals_input_path
        self.ltg_arrivals_output_path = ltg_arrivals_output_path

        # Assign the arrival probabilities as 0 by default.
        self.prob_arr0 = []  # Probabilities that a fire arrives on the day it is ignited.
        self.prob_arr1 = []  # Probabilities that a fire arrives any day after ignition.

    def processLightningArrivalsIgnitions(self):
        """ For each line of input, this method will append two columns containing probability
            values:

            probarr0 = The probability that a fire arrives on the day it is ignited by lightning;
            probarr1 = The probability that a fire arrives the day after ignition. """

        start_time = timeit.default_timer()
        print ("Calculating fire arrivals probabilities...")
        print ("Time elapsed: ", timeit.default_timer() - start_time)
        
        input_file_handle = open(self.ltg_arrivals_input_path, 'rb')
        input_csv_file = csv.reader(input_file_handle, quotechar='|')

        output_file_handle = open(self.ltg_arrivals_output_path, 'wb')
        output_csv_file = csv.writer(output_file_handle, quotechar='|')

        # Retain the first line of the file, which is the header.
        input_csv_header = next(input_csv_file)

        # The output CSV header has two more columns, one for each of the computed
        # probabilities.
        # We want a new list, not a list reference, which is why we use [:] here.
        output_csv_header = input_csv_header[:]
        
        # Delete irrelevent columns from the output header list.
        output_csv_header = filter(lambda a: a not in ['neg', 'rh', 'ws', 'rain', 'isi',
                                                   'pos', 'timing', 'ZONE_CODE', 'NSRNAME'], output_csv_header)

        output_csv_header.extend(['probarr0', 'probarr1', 'probign', 'jds'])
        output_csv_file.writerow(output_csv_header)

        i = 0
        processed = 0
        for next_row in input_csv_file:
            assert(len(input_csv_header) == len(next_row))

            i = i + 1
            processed = processed + 1
            if i % 10000 == 0:           
                print("Currently on row #", i, ".")
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
            
            # Mike: This is just a quick fix to addressing the roll over flaw in the
            # GLM linearity ... SIMPLE for now
            
            jds = datetime.date(int(working_dict['year']), \
                                int(working_dict['mon']), \
                                int(working_dict['day'])).timetuple().tm_yday
            
            # Append the probign and jds columns to the end of the dataset.
            working_dict['probign'] = ('{0:.10f}'.format(probign)).rstrip('0')  # 10 decimal places
            working_dict['jds'] = jds
            
            # Now that we have all of the probabilities, let's append these columns to the data set.
            new_row = []
            
            # Ensure that we output the columns in the same order as they were during the input
            # stage.
            for column_name in output_csv_header:

                # Omit the following columns from the data set.
                if column_name == 'neg':
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
                    continue
                
                new_row.append(working_dict[column_name])
            
            # Append to the output file.
            output_csv_file.writerow(new_row)
        
        # End of fire arrivals for loop.
        print("Completed calculating lightning fire probabilities.")
        print("Time elapsed: ", timeit.default_timer() - start_time)
        print("Overall total rows analyzed: ", i)
        print("Rows processed: ", processed)


def mainMethod():
    """ This is the main method called by the application entrypoint. """

    # Will likely switch these paths to command-line parameters, or a config.ini file, later.
    # Use strings for now.
    # 
    # HOME PC:
    # input_path = 'Z:\LightningFireOccurrencePredictionInputs\AB-processing-forMATT-datasetALL.csv'
    # output_path = 'Z:\LightningFireOccurrencePredictionInputs\ltg_output.csv' 
    # 
    # LAB PC:
    input_path = 'C:\Users\Ansell\Desktop\Mike\'s LOP dataset\AB-processing-forMATT-datasetALL_FIRST_500000_ROWS_PLUS_HEADER.csv'
    output_path = 'C:\Users\Ansell\Desktop\Mike\'s LOP dataset\ltg_output.csv'

    obj = LightningOccurrencePrediction(input_path, output_path)
    obj.processLightningArrivalsIgnitions()


# Entrypoint for application execution.
if __name__ == "__main__":

    # Call the main method.
    mainMethod()

