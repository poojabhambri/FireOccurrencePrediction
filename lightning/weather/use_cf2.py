import math
import os

import numpy as np

interp = np.zeros((600, 3), dtype=float)

def calculate(cf, NUM, lat, lon, minimum, maximum):
    calc = cf[NUM][2] + lon*cf[NUM+1][2]+lat*cf[NUM+2][2]
    for i in range(NUM):
        ds = math.sqrt( (lat-cf[i][0])*(lat-cf[i][0])+(lon-cf[i][1])*(lon-cf[i][1]) )
        if ds>0.00001:
            calc += cf[i][2]*ds*ds*math.log(ds)
    if calc > maximum:
        calc=maximum
    if calc < minimum:
        calc=minimum
    return float(calc)

def main():
    yr = 0.0
    mon = 0.0
    day = 0.0
    NUM = 0.0
    min_val = 0.0
    max_val = 0.0
    latmin = 0.0
    latmax = 0.0
    longmin = 0.0
    longmax = 0.0 
    print("Current Working Directory:", os.getcwd())
    output_path_to_FWIGrid = "intermediate_output/4_Binned_Weather.csv"
    output_path_to_GridLocations =  "resource_files/Gridlocations.prn"
    input_coefficients_directory = 'intermediate_output/3_weather_interpolation_coefficients'
    if not os.path.exists(output_path_to_FWIGrid):
        print(f"File does not exist: {output_path_to_FWIGrid}")
    
    interp = np.zeros((600, 3), dtype=float)

    inp = [open("intermediate_output/3_weather_interpolation_coefficients/CF-temp.ab", "r"),
       open("intermediate_output/3_weather_interpolation_coefficients/CF-rh.ab", "r"),
       open("intermediate_output/3_weather_interpolation_coefficients/CF-ws.ab", "r"),
       open("intermediate_output/3_weather_interpolation_coefficients/CF-rain.ab", "r"),
       open("intermediate_output/3_weather_interpolation_coefficients/CF-ffmc.ab", "r"),
       open("intermediate_output/3_weather_interpolation_coefficients/CF-dmc.ab", "r"),
       open("intermediate_output/3_weather_interpolation_coefficients/CF-dc.ab", "r"),
       open("intermediate_output/3_weather_interpolation_coefficients/CF-isi.ab", "r"),
       open("intermediate_output/3_weather_interpolation_coefficients/CF-bui.ab", "r"),
       open("intermediate_output/3_weather_interpolation_coefficients/CF-fwi.ab", "r")]
    
    ecoregion = [0] * 10011
    ERlocation = [[0.0, 0.0] for _ in range(10010)]



    print("Before opening file...")
    out = open(output_path_to_FWIGrid, "w")
    print("After opening file...")
    try:
        points = open(output_path_to_GridLocations, "r")
    except FileNotFoundError:
        print("Points file not found")


    line = points.readline()

    if line:
        values = [int(val) if i == 0 else float(val) for i, val in enumerate(line.split())]
        err = len(values)
        
        if err >= 1:
            ecoregion[0] = values[0]
        if err >= 2:
            ERlocation[0][0] = values[1]
        if err >= 3:
            ERlocation[0][1] = values[2]
    else:
        err = None

    REGIONS = 0
    while err!= None and err >= 0:
        REGIONS += 1
        anotherline = points.readline()
        if anotherline:
            values = [int(val) if (i == 0 or i == 3) else float(val) for i, val in enumerate(anotherline.split())]
            err = len(values)
            # print(values)
            if err >= 1:
                ecoregion[REGIONS] = values[0]
            if err >= 2:
                ERlocation[REGIONS][0] = values[1]
            if err >= 3:
                ERlocation[REGIONS][1] = values[2]
        else:
            err = None
    points.close()

    err = 1
    # while err and err >= 0:
    #     codes = [[-999.9 for i in range(10)] for j in range(10010)]
    #     for i in range(10):
    #         anotherline = inp[i].readline()
    #         if anotherline:
    #             err = 10
    #             # values = [int(float(val)) if r <=3 else float(val) for r, val in enumerate(anotherline.split())]
    #             # err = len(values)
    #             # print("look here", err)
    #             # if err >= 1:
    #             #     yr = values[0]
    #             # if err >= 2:
    #             #     mon = values[1]
    #             # if err >= 3:
    #             #     day = values[2]
    #             # if err >= 4:
    #             #     print("yup")
    #             #     NUM = values[3]
    #             # if err >= 5:
    #             #     minimum = values[4]
    #             # if err >= 6:
    #             #     maximum = values[5]
    #             # if err >= 7:
    #             #     latmin = values[6]
    #             # if err >= 8:
    #             #     latmax = values[7]
    #             # if err >= 9:
    #             #     longmin = values[8]
    #             # if err >= 10:
    #             #     longmax = values[9]
    #             yr = int(line[0:4])
    #             mon = int(line[4:6])
    #             day = int(line[6:8])
    #             NUM = int(line[8:11])
    #             min_val = float(line[11:17])
    #             max_val = float(line[17:23])
    #             latmin = float(line[23:30])
    #             latmax = float(line[30:37])
    #             longmin = float(line[37:44])
    #             longmax = float(line[44:51])
    #         else:
    #             err = None
    #         for k in range(600):
    #             anotherline = inp[i].readline()
    #             if anotherline:
    #                 values = values = [float(anotherline[0:8]), float(anotherline[8:16]), float(anotherline[16:30])]
    #                 err = len(values)
    #                 if err >= 1:
    #                     interp[k][0] = values[0]
    #                 if err >= 2:
    #                     interp[k][1] = values[1]
    #                 if err >= 3:
    #                     interp[k][2] = values[2]
    #         if yr>1900:
    #             for j in range(REGIONS):
    #               lat=ERlocation[j][0]
    #               lon=ERlocation[j][1]
    #               if(NUM>0):
    #                   #print("do we get here??")
    #                   codes[j][i]=calculate(interp,NUM,lat,lon,minimum,maximum)
    #     if err and err > 0:
    #         #print(yr,mon,day)
    #         for j in range(REGIONS):
    #             if codes[j][1]>-900.0 and err>0:
    #                 out.write(f"{ecoregion[j]},{yr},{mon},{day}")
    #                 for i in range(10):
    #                     out.write(f",{codes[j][i]:0.1f}")
    #                 out.write("\n")
    while err and err >= 0:
        codes = [[-999.9 for i in range(10)] for j in range(10010)]

        for i in range(10):
            anotherline = inp[i].readline()

            if not anotherline:
                err = -1
                # break

            else:
                yr = int(anotherline[0:4])
                mon = int(anotherline[4:6])
                day = int(anotherline[6:8])
                NUM = int(anotherline[8:11])
                min_val = float(anotherline[11:17])
                max_val = float(anotherline[17:23])
                latmin = float(anotherline[23:30])
                latmax = float(anotherline[30:37])
                longmin = float(anotherline[37:44])
                longmax = float(anotherline[44:51])
                err = 10
                # print("values")
                # print(yr, mon, day, NUM, min_val, max_val, latmin, latmax, longmin, longmax)
            file_position = inp[i].tell()
            interp = [[-999.9 for _ in range(3)] for _ in range(600)]  # Initialize interp for each file
            x = 51
            for k in range(600):
                # inp[i].seek(file_position)
                interp_line = anotherline

                if not interp_line:
                    break

                values = [float(interp_line[x:x+8]), float(interp_line[x+8:x+16]), float(interp_line[x+16:x+30])]
                #print("values")
                #print(values)
                err = len(values)

                if err >= 1:
                    interp[k][0] = values[0]
                if err >= 2:
                    interp[k][1] = values[1]
                if err >= 3:
                    interp[k][2] = values[2]
                file_position = inp[i].tell()
                x += 30

            if yr > 1900:
                for j in range(REGIONS):
                    lat = ERlocation[j][0]
                    lon = ERlocation[j][1]
                    if NUM > 0:
                        # print("do we get here??")
                        codes[j][i] = calculate(interp, NUM, lat, lon, min_val, max_val)

        if err and err > 0:
            # print("date")
            # print(yr, mon, day)
            for j in range(REGIONS):
                if codes[j][1] > -900.0 and err > 0:
                    #print(f"{ecoregion[j]},{yr},{mon},{day}")
                    out.write(f"{ecoregion[j]},{yr},{mon},{day}")
                    for i in range(10):
                        # print("codes here")
                        # print(f",{codes[j][i]:0.1f}")
                        out.write(f",{codes[j][i]:0.1f}")
                    out.write("\n")


    for i in range(10):
        inp[i].close()

    out.close()
            

if __name__ == '__main__':
    main()
