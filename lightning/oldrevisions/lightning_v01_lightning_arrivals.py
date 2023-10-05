""" This is a Python translation of the SAS portion of Dr. Mike Wotton's Lightning Occurrence Prediction model.

    This code is written for the UAlberta Fire Occurrence Prediction project, in collaboration with the Government of Alberta
    and the Canadian Forest Service.

    Author: Matthew Ansell
    2019
"""

import csv  # Used for input / output data processing.
import math  # Used for model calculations.
import timeit  # Used for measuring code execution time.
from decimal import Decimal  # Used to round probabilities to an exact decimal as opposed to float.


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

        # The arrivals CSV header has two more columns, one for each of the computed
        # probabilities.
        # We want a new list, not a list reference, which is why we use [:] here.
        arrivals_csv_header = input_csv_header[:]
        
        # DELETE THE neg COLUMN FROM THE OUTPUTTED LIST????
        arrivals_csv_header = filter(lambda a: a != 'neg', arrivals_csv_header)

        arrivals_csv_header.extend(['probarr0', 'probarr1'])
        output_csv_file.writerow(arrivals_csv_header)

        i = 0
        for next_row in input_csv_file:
            assert(len(input_csv_header) == len(next_row))

            i = i + 1
            if i % 100000 == 0:           
                print("Currently processing row #", i, ".")
                print("Time elapsed: ", timeit.default_timer() - start_time)

            if i == 3000001:
                break  # Break out of the for loop if we get past i.

            # For easy and per-row data manipulation and referencing, use a dictionary
            # data structure. Its keys will be the input CSV header, and their corresponding
            # values will be those of the current row.
            working_dict = dict(zip(input_csv_header, next_row))
            
            # Mike: Just a rough seasonal separation pre-flush/post-flush.
            season = "Summer"

            if int(working_dict['mon']) < 6:
                season = "Spring"
            
            # Mike: For modelling... not enough lightning fire data outside these dates
            if int(working_dict['mon']) < 5 or int(working_dict['mon']) > 9:
                i = i - 1  # Decrement i because this row will not get processed.
                continue  # Skip the current row and go on to the next one.

            # Note: Commented out in Mike's code?
            # if working_dict['zone_code'] == '':
            #     continue

            if working_dict['NSR'] == '':
                i = i - 1  # Decrement i because this row will not get processed.
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

            int_nsr = 0
            ffmc_nsr = 0
            dmc_nsr = 0
            dc_nsr = 0

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
            prob_arr0 = Decimal(math.exp(pr0) / (1 + math.exp(pr0)))
            working_dict['probarr0'] = round(prob_arr0, 10)  # 10 decimal places to match Mike
            #self.prob_arr0.append(prob_arr0)

            # Prob. that a fire arrives any day after ignition.
            prob_arr1 = Decimal(math.exp(pr1) / (1 + math.exp(pr1)))
            working_dict['probarr1'] = round(prob_arr1, 10)  # 10 decimal places to match Mike
            #self.prob_arr1.append(prob_arr1)

            # Now that we have the arrival probabilities, let's append these columns to the dataset.
            new_row = []

            # Ensure that we output the columns in the same order as they were during the input
            # stage.
            for column_name in arrivals_csv_header:

                # DO NOT APPEND THE neg COLUMN TO THE DATASET?????
                if column_name == 'neg':
                    continue
                
                new_row.append(working_dict[column_name])
            
            # Append to the output file.
            output_csv_file.writerow(new_row)
        
        # End of fire arrivals for loop.
        print ("Completed calculating fire arrivals probabilities.")
        print ("Time elapsed: ", timeit.default_timer() - start_time)


def mainMethod():
    """ This is the main method called by the application entrypoint. """

    # Will likely switch these paths to command-line parameters, or a config.ini file, later.
    # Use strings for now.
    input_path_home_pc = 'Z:\LightningFireOccurrencePredictionInputs\AB-processing-forMATT-datasetALL.csv'
    output_path_home_pc = 'Z:\LightningFireOccurrencePredictionInputs\ltg_arrivals_output.csv'

    obj = LightningOccurrencePrediction(input_path_home_pc, output_path_home_pc)
    obj.processLightningArrivalsIgnitions()


# Entrypoint for application execution.
if __name__ == "__main__":

    # Call the main method.
    mainMethod()

