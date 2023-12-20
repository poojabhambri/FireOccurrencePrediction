import numpy as np
import csv
import os
alldata = np.zeros((600, 3), dtype=float)

# Equivalent to typedef double square[600][600];
square = np.zeros((600, 600), dtype=float)

# Equivalent to typedef double column[600];
column = np.zeros(600, dtype=float)
interp = np.zeros((600, 3), dtype=float)

# Equivalent to typedef double column[600];
cf = np.zeros(600, dtype=float)

# Equivalent to typedef double square[600][600];
a = np.zeros((600, 600), dtype=float)
b = np.zeros((600, 600), dtype=float)

# Equivalent to typedef double column[600];
c = np.zeros(600, dtype=float)
y = np.zeros(600, dtype=float)

def multiply(a, arow, acol, b, brow, bcol, c):
    """
    Multiply matrices in order A * B.
    """
    if bcol != arow:
        print("The matrices are the wrong size for multiplication")
        return

    crow, ccol = arow, bcol

    for i in range(crow):
        c[i] = 0

    for i in range(arow):
        for k in range(brow):
            c[i] += a[i][k] * b[k]

    return crow, ccol

def invert(a, row):
    """
    Invert a square matrix using Gaussian elimination.
    """
    b = np.zeros((row, row), dtype=float)

    for i in range(row):
        for j in range(row):
            if i == j:
                b[i][j] = 1
            else:
                b[i][j] = 0

    for i in range(row):
        div = a[i][i]

        if div == 0.0:
            for k in range(i + 1, row):
                div = a[k][i]

                if div != 0:
                    for l in range(row):
                        tmp = a[i][l]
                        a[i][l] = a[k][l]
                        a[k][l] = tmp

                        tmp = b[i][l]
                        b[i][l] = b[k][l]
                        b[k][l] = tmp

                    k = row + 2

                if k == row:
                    print("Problem in the inversion routine")
                    exit(1)

                div = a[i][i]

        if div != 0:
            for j in range(row):
                a[i][j] /= div
                b[i][j] /= div

            for j in range(row):
                div = -1.0 * a[j][i]

                if div != 0.0:
                    if j > i:
                        for k in range(row):
                            b[j][k] = b[j][k] / div + b[i][k]
                            a[j][k] = a[j][k] / div + a[i][k]
                    elif j < i:
                        for k in range(row):
                            b[j][k] = b[i][k] * div + b[j][k]
                            a[j][k] = a[i][k] * div + a[j][k]

    return b


def regress(stuff, coeff, row, col, mult):
    stations = row + 3

    a = np.zeros((stations, stations), dtype=float)
    y = np.zeros(stations, dtype=float)

    for j in range(row):
        for i in range(col):
            a[j][i] = 0.0
            if i != j:
                xl, yl = stuff[j][1], stuff[j][0]
                xk, yk = stuff[i][1], stuff[i][0]
                ds = np.sqrt((xk - xl) ** 2 + (yk - yl) ** 2)
                if ds == 0:
                    a[j][i] = 0.0
                else:
                    a[j][i] = ds ** 2 * np.log(ds)
            else:
                a[j][i] = row * mult

    for j in range(row):
        a[j][row] = 1.0
        a[row][j] = 1.0
        a[j][row + 1] = float(stuff[j][1])
        a[row + 1][j] = float(stuff[j][1])
        a[j][row + 2] = float(stuff[j][0])
        a[row + 2][j] = float(stuff[j][0])

    for j in range(row, stations):
        for i in range(row, stations):
            a[j][i] = 0.0

    for j in range(row):
        y[j] = float(stuff[j][2])

    for j in range(row, row + 3):
        y[j] = 0.0

    # Invert the matrix using np.linalg.inv
    b = np.linalg.inv(a)

    # Multiply matrices using np.dot
    c = np.dot(b, y)

    # Copy the result to the coeff array
    for i in range(len(c)):
        coeff[i] = c[i]

# Define the interpolate function in terms of the provided regress function
def interpolate(info, num, a, cf, mult):
    regress(info, cf, num, num + 3, mult)

def main():
    input_path = "intermediate_output/2_Massaged_Weather.csv"
    output_dir = "intermediate_output/3_weather_interpolation_coefficients"
    data = None
    out = [None] * 10

    err, err2, err3, N, z, i, j, k, rec, b = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    values = []
    yr, mon, day = 0, 0, 0
    oldyr, oldmon, oldday, id, NSTANS = 0, 0, 0, 0, [0]*11
    NUM = 0

    x, y = 0.0, 0.0

    lat, lon = 0.0, 0.0
    location = [[0.0]*2 for _ in range(416)]
    latmax, latmin, longmin, longmax = 0.0, 0.0, 0.0, 0.0
    wx = [[0.0]*12 for _ in range(416)]
    latlong = [[[0.0]*2 for _ in range(10)] for _ in range(416)]
    smooth = [0.001, 0.001, 0.001, 0.01, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001]

    # MATT: Add declarations for these missing float variables.
    temp, rh, ws, rain, ffmc, dmc, dc, isi, bui, fwi = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    dum = None


    for i in range(2):
        for N in range(416):
            location[N][i] = 0.0
    out[0] = open(os.path.join(output_dir, "CF-temp.ab"), "w")
    out[1] = open(os.path.join(output_dir, "CF-rh.ab"), "w")
    out[2] = open(os.path.join(output_dir, "CF-ws.ab"), "w")
    out[3] = open(os.path.join(output_dir, "CF-rain.ab"), "w")
    out[4] = open(os.path.join(output_dir, "CF-ffmc.ab"), "w")
    out[5] = open(os.path.join(output_dir, "CF-dmc.ab"), "w")
    out[6] = open(os.path.join(output_dir, "CF-dc.ab"), "w")
    out[7] = open(os.path.join(output_dir, "CF-isi.ab"), "w")
    out[8] = open(os.path.join(output_dir, "CF-bui.ab"), "w")
    out[9] = open(os.path.join(output_dir, "CF-fwi.ab"), "w")

    with open(input_path, "r") as data:
    # Check if the file is successfully opened
        if data is None:
            exit(1)

        # Read data from the file
        line = data.readline()
        while line:
            values = list(map(float, line.split()))
            if len(values) == 16:
                id, lat, lon, yr, mon, day, temp, rh, ws, rain, ffmc, dmc, dc, isi, bui, fwi = values[:16]
                oldyr = yr
                oldmon = mon
                oldday = day
                break  # Exit the loop if a line with 16 values is found
            else:
                line = data.readline()
        # Skip the next 80 characters or until a newline character is encountered

        oldyr = yr
        oldmon = mon
        oldday = day
        err2 = len(values)
        while err2 > 0:
            # ERASE all old entries
            for k in range(416):
                for i in range(10):
                    wx[k][i] = -999.99

            latmax = -999.999
            latmin = 999.999
            longmin = 999.999
            longmax = -999.999
            for k in range(11):
                NSTANS[k] = 0
            while yr == oldyr and mon == oldmon and day == oldday and err2 > 0:
                #print(err2)
                if temp > -90:
                    wx[NSTANS[0]][0] = temp
                    latlong[NSTANS[0]][0][0] = lat
                    latlong[NSTANS[0]][0][1] = lon
                    NSTANS[0] += 1

                if rh > -90:
                    wx[NSTANS[1]][1] = float(rh)
                    latlong[NSTANS[1]][1][0] = lat
                    latlong[NSTANS[1]][1][1] = lon
                    NSTANS[1] += 1

                if ws > -90:
                    wx[NSTANS[2]][2] = float(ws)
                    latlong[NSTANS[2]][2][0] = lat
                    latlong[NSTANS[2]][2][1] = lon
                    NSTANS[2] += 1

                if rain > -90:
                    wx[NSTANS[3]][3] = rain
                    latlong[NSTANS[3]][3][0] = lat
                    latlong[NSTANS[3]][3][1] = lon
                    NSTANS[3] += 1

                if ffmc > -90:
                    wx[NSTANS[4]][4] = ffmc
                    latlong[NSTANS[4]][4][0] = lat
                    latlong[NSTANS[4]][4][1] = lon
                    NSTANS[4] += 1

                if dmc > -90:
                    wx[NSTANS[5]][5] = float(dmc)
                    latlong[NSTANS[5]][5][0] = lat
                    latlong[NSTANS[5]][5][1] = lon
                    NSTANS[5] += 1

                if dc > -90:
                    wx[NSTANS[6]][6] = float(dc)
                    latlong[NSTANS[6]][6][0] = lat
                    latlong[NSTANS[6]][6][1] = lon
                    NSTANS[6] += 1

                if isi > -90:
                    wx[NSTANS[7]][7] = isi
                    latlong[NSTANS[7]][7][0] = lat
                    latlong[NSTANS[7]][7][1] = lon
                    NSTANS[7] += 1

                if bui > -90:
                    wx[NSTANS[8]][8] = bui
                    latlong[NSTANS[8]][8][0] = lat
                    latlong[NSTANS[8]][8][1] = lon
                    NSTANS[8] += 1

                if fwi > -90:
                    wx[NSTANS[9]][9] = fwi
                    latlong[NSTANS[9]][9][0] = lat
                    latlong[NSTANS[9]][9][1] = lon
                    NSTANS[9] += 1

                if lat > -90:
                    wx[NSTANS[10]][10] = lat
                    wx[NSTANS[10]][11] = lon
                    NSTANS[10] += 1

                    if lat > latmax:
                        latmax = lat

                    if lat < latmin:
                        latmin = lat

                    if lon > longmax:
                        longmax = lon

                    if lon < longmin:
                        longmin = lon
                oldyr, oldmon, oldday = yr, mon, day
                line = data.readline()
                values = list(map(float, line.split()))
                err2 = len(values)
                if len(values) < 16 and len(values) > 0:
                    continue
                if err2 > 0:
                    id, lat, lon, yr, mon, day, temp, rh, ws, rain, ffmc, dmc, dc, isi, bui, fwi = values
            if oldyr > 1900:
                for i in range(10):
                    for k in range(600):
                        for j in range(3):
                            interp[k][j] = 0.00
                        cf[k] = 0.00000

                    if NSTANS[i] > 1 and 0 < oldmon < 13:
                        max_val = -999.99
                        min_val = 999.99
                        NUM = NSTANS[i]

                        for j in range(NUM):
                            interp[j][0] = latlong[j][i][0]
                            interp[j][1] = latlong[j][i][1]
                            interp[j][2] = wx[j][i]

                            max_val = max(max_val, wx[j][i])
                            min_val = min(min_val, wx[j][i])
                        
                        interpolate(interp, NUM, a, cf, smooth[i])
                 
                    else:
                        NUM = 0  # as a key in the output so we know it's a no-good day

                    # OUTPUT
                    if oldmon < 11:
                        out[i].write(
        
                            f"{oldyr:04.0f}{oldmon:02.0f}{oldday:02.0f}{int(NUM):03d}{min_val:06.1f}{max_val:06.1f}{latmin-1.5:07.2f}{latmax+1.5:07.2f}{longmin-3.0:07.2f}{longmax+3.0:07.2f}"
                        )
                        
                        for j in range(600):
                            out[i].write(f"{interp[j][0]:08.3f}{interp[j][1]:08.3f}{cf[j]:014.6f}")

                        out[i].write("\n")

            # Keep in mind that this outputs the final extra 3 intercept coefficients after the NUM place is reached.
            oldyr, oldmon, oldday = yr, mon, day
    for i in range(10):
        out[i].close()

    data.close()
if __name__ == '__main__':
    main()
