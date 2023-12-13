import math

def distance(x, y, lat, lon, cent_lat, cent_long):
    alat = (math.pi / 180.0) * (cent_lat + lat) / 2.0
    x[0] = (111.413 * math.cos(alat) - 0.094 * math.cos(3 * alat)) * (cent_long - lon)
    y[0] = (111.113 - 0.559 * math.cos(2 * alat)) * (lat - cent_lat)
    return math.sqrt(x[0] * x[0] + y[0] * y[0])

def julian(mon, day):
    month = [0, 31, 59, 90, 120, 151, 181, 212, 242, 273, 304, 334]
    return month[mon - 1] + day

def nailuj(mon, day, jd, leap):
    month = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    monthl = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    mon[0] = 1
    if leap == 0:
        while jd > month[mon[0]]:
            mon[0] += 1
        day[0] = jd - month[mon[0] - 1]
    else:
        while jd > monthl[mon[0]]:
            mon[0] += 1
        day[0] = jd - monthl[mon[0] - 1]

def main():
    # MATT:
    # argv[1] is the input path to (and including) Gridlocations.prn =  self.ltg_grid_locations_path =  'FireOccurrencePrediction\\resource_files\\Gridlocations.prn'
    # argv[2] is the input path to (and including) ABltg_space.out = self.ltg_strike_raw_massaged_output_path = 'intermediate_output/6_AB_ltg_space_massaged.out'
    # argv[3] is the output path to (and including) ltg2010-20by20-five-period.dat = self.ltg_lightning_binned_output_path = 'intermediate_output/7_ltg-10by10-five-period.dat'
    #
    # Sample command line usage for Home PC:
    # build-ltggrids-five-period.exe "Y:\\University of Alberta\\Software Development\\FireOccurrencePrediction\\lightning\\binning\\Gridlocations.prn" "Z:\\LightningFireOccurrencePredictionInputs\\ABltg_space_MATT.out" "Z:\\LightningFireOccurrencePredictionInputs\\ltg2010-20by20-five-period.dat"

    # MATT: Rudimentary command line argument check.

    with open("resource_files/Gridlocations.prn", "r") as inp:
        stans = []
        stnid = []
        index = 0
        for line in inp:
            id, lat, lon = map(float, line.strip().split())
            stans.append([lat, lon])
            stnid.append(id)
            index += 1

    with open('intermediate_output/6_AB_ltg_space_massaged.out', "r") as inp, open('intermediate_output/7_ltg-10by10-five-period.dat', "w") as out:
        neg = [[0] * 5 for _ in range(10010)]
        pos = [[0] * 5 for _ in range(10010)]
        PER = 5
        lat, lon, stren, mult, year, mon, day, hour = 0, 0, 0, 0, 0, 0, 0, 0
        jd = 0
        oldjd = jd
        oyear = year
        for line in inp:
            lat, lon, stren, mult, year, mon, day, hour = map(float, line.strip().split())
            jd = julian(int(mon), int(day))
            while jd == oldjd and year == oyear:
                for i in range(index):
                    x, y = [0.0], [0.0]
                    dist = distance(x, y, lat, lon, stans[i][0], stans[i][1])
                    x[0] = abs(x[0])
                    y[0] = abs(y[0])
                    if x[0] < 5.000 and y[0] < 5.000:
                        break
                if i < index:
                    if stren > 0:
                        if hour < 6:
                            pos[i][0] += 1  # overnite
                        elif hour < 12:
                            pos[i][1] += 1  # 1 is during early aft
                        elif hour < 18:
                            pos[i][2] += 1  # 2 is late day
                        elif hour < 21:
                            pos[i][3] += 1  # 3 is late day
                        else:
                            pos[i][4] += 1  # 4 is evening
                    else:
                        if hour < 6:
                            neg[i][0] += 1  # overnite
                        elif hour < 12:
                            neg[i][1] += 1  # 1 is during early aft
                        elif hour < 18:
                            neg[i][2] += 1  # 2 is late day
                        elif hour < 21:
                            neg[i][3] += 1  # 3 is late day
                        else:
                            neg[i][4] += 1  # 4 is evening
                oyear = year
                oldjd = jd
                line = next(inp, None)  # Read the next line from the input file
                if line is None:
                    break  # Exit the loop if there are no more lines
                lat, lon, stren, mult, year, mon, day, hour = map(float, line.strip().split())
                jd = julian(int(mon), int(day))
            nailuj([0], [0], oldjd, 0)  # ASSOCIATE with current day
            for i in range(index):
                for j in range(PER):
                    if neg[i][j] > 0 or pos[i][j] > 0:
                        out.write(
                            f"{stnid[i]:5d} {stans[i][0]:7.3f} {stans[i][1]:7.3f} {oyear:4d} {int(mon):2d} {int(day):2d} {j:1d} {neg[i][j]:5d} {pos[i][j]:5d}\n"
                        )
            neg = [[0] * 5 for _ in range(10010)]
            pos = [[0] * 5 for _ in range(10010)]
            oldjd = jd
            oyear = year

if __name__ == "__main__":
    main()
    print("exiting grids")

