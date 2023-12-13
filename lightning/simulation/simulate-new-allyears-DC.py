import random
import csv
def ignbin(ltg_value, pp):
    count = 0
    n = int(ltg_value)
    for _ in range(n):
        rand = random.random()
        if rand < pp:
            count += 1
    return count

def nailuj(jd, leap):
    month = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    monthl = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    mon = 1
    if leap == 0:
        while jd > month[mon]:
            mon += 1
        day = jd - month[mon-1]
    else:
        while jd > monthl[mon]:
            mon += 1
        day = jd - monthl[mon-1]
    return mon, day

def main():
    grid = 0
    jd = 0
    totltg = 0
    totpltg = 0
    region = 0
    nltg0 = 0
    nltg1 = 0
    nltg2 = 0
    nltg3 = 0
    nltg4 = 0
    mon = 0
    day = 0
    mm = 0
    dd = 0
    today = 0
    leap = 0
    numfire = 0
    totfire = 0
    err = 0
    j = 0
    i = 0
    h = 0
    SEED = 0
    ltg = [[0] * 154 for _ in range(10000)]
    ltgp = [[[0] * 5 for _ in range(154)] for _ in range(10000)]
    eco = [[0] * 154 for _ in range(10000)]
    dmcgrid = [[0] * 154 for _ in range(10000)]
    dcgrid = [[0] * 154 for _ in range(10000)]
    firegrid = [[0] * 154 for _ in range(10000)]
    totarr = [[0] * 1000 for _ in range(5)]
    tothold = [[0] * 1000 for _ in range(5)]
    nigns = [[0] * 1000 for _ in range(5)]
    subreg = [0] * 10000
    totarrPROV = [0] * 1000
    totholdPROV = [0] * 1000
    nignsPROV = [0] * 1000
    nign = 0
    nhold = 0
    narr1 = 0
    narr2 = 0
    sim = 0
    temp = 0
    fire = 0
    ltgsum = 0
    numfires = [[0] * 183 for _ in range(25)]
    n = 0
    probarr0 = 0.0
    probarr1 = 0.0
    probign = 0.0
    pign = [[0.0] * 154 for _ in range(10000)]
    parr0 = [[0.0] * 154 for _ in range(10000)]
    parr1 = [[0.0] * 154 for _ in range(10000)]
    pa = 0.0
    rand1 = 0.0
    rand2 = 0.0
    longi = [0.0] * 10000
    lati = [0.0] * 10000
    lat = 0.0
    lon = 0.0
    narrtoday = [0.0] * 10000
    nholdtoday = [0.0] * 10000
    nigntoday = [0.0] * 10000
    avgnign = 0.0
    with open('intermediate_output\\arguments.csv', 'r', newline='') as csv_file:
        csv_reader = csv.reader(csv_file)
        # Read the first row
        arguments = next(csv_reader)
    # Access individual arguments by index

    argv1, argv2, argv3, argv4, argv5, argv6, argv7, argv8 = arguments
    cells = 9999
    baseyear = 1990
    holdover_time = int(argv7)
    confidence_interval = float(argv8)
    sims = 1000
    ci_low = int(0 + ((1 - (confidence_interval / 100)) / 2) * sims)
    ci_high = int(sims - ((1 - (confidence_interval / 100)) / 2) * sims)
    numfires = [[0] * 183 for _ in range(25)]
    inp = open(argv2, "r")
    out = open(argv3, "w")
    out2 = open(argv4, "w")
    SEED = int(argv1)
    start_date = int(argv5)
    end_date = int(argv6)
    random.seed(SEED)
    grid, lat, lon, year, jd, probign, probarr0, probarr1, totltg, numfire, region, nltg0, nltg1, nltg2, nltg3, nltg4, dmc, dc = map(float, inp.readline().split())
    oldyear = int(year)
    while True:
        for i in range(cells):
            for j in range(154):
                eco[i][j] = 0
                pign[i][j] = 0.0
                parr0[i][j] = 0.0
                parr1[i][j] = 0.0
                dmcgrid[i][j] = 0
                dcgrid[i][j] = 0
                lati[i] = 0.0
                longi[i] = 0.0
                ltg[i][j] = 0
                ltgp[i][j][0] = 0
                ltgp[i][j][1] = 0
                ltgp[i][j][2] = 0
                ltgp[i][j][3] = 0
                ltgp[i][j][4] = 0
        if year % 4 == 0:
            leap = 1
        else:
            leap = 0
        ltgsum2 = 0
        while True:
            if jd > 120 and jd < 274:
                eco[int(grid)][int(jd) - 121] = region
                pign[int(grid)][int(jd) - 121] = probign
                parr0[int(grid)][int(jd) - 121] = probarr0
                parr1[int(grid)][int(jd) - 121] = probarr1
                dmcgrid[int(grid)][int(jd) - 121] = dmc
                dcgrid[int(grid)][int(jd) - 121] = dc
                lati[int(grid)] = lat
                longi[int(grid)] = lon
                ltg[int(grid)][int(jd) - 121] = totltg
                firegrid[int(grid)][int(jd) - 121] = numfire
                ltgsum2 += totltg
                ltgp[int(grid)][int(jd) - 121][0] = nltg0
                ltgp[int(grid)][int(jd) - 121][1] = nltg1
                ltgp[int(grid)][int(jd) - 121][2] = nltg2
                ltgp[int(grid)][int(jd) - 121][3] = nltg3
                ltgp[int(grid)][int(jd) - 121][4] = nltg4
            line = inp.readline()
            if not line:
                break
            grid, lat, lon, year, jd, probign, probarr0, probarr1, totltg, numfire, region, nltg0, nltg1, nltg2, nltg3, nltg4, dmc, dc = map(float, line.split())
        ltgsum2 = 0
        for today in range(start_date, end_date+1):
            ltgsum = 0
            totfire = 0
            narrtoday = [0.0] * cells
            nholdtoday = [0.0] * cells
            nigntoday = [0.0] * cells
            for sim in range(sims):
                totarrPROV[sim] = 0
                totholdPROV[sim] = 0
                nignsPROV[sim] = 0
                nhold= 0
                for i in range(3):
                    totarr[i][sim] = 0
                    tothold[i][sim] = 0
                    nigns[i][sim] = 0
                for i in range(1, cells+1):
                    nhold = 0
                    if eco[i][today-121] >= 7 and eco[i][today-121] <= 11 or eco[i][today-121] == 18 or eco[i][today-121] == 14:
                        subreg[i] = 0
                    else:
                        if longi[i] >= -114:
                            subreg[i] = 2
                        else:
                            subreg[i] = 1
                    if holdover_time < 0:
                        if dcgrid[i][today-121] < 200:
                            holdover = int(dcgrid[i][today-121] * 3.0 / 200.0 + 4.0 + 0.5)
                        else:
                            holdover = int((dcgrid[i][today-121] - 200.0) * 7.0 / 300.0 + 7.0 + 0.5)
                        holdover = min(holdover, 14)
                    else:
                        holdover = holdover_time
                    holdover = min(holdover, today-121)
                    for day in range(today-holdover, today+1):
                        if day > today-holdover:
                            narr1 = ignbin(nhold, parr1[i][day-121])
                        else:
                            narr1 = 0
                        nign = ignbin(ltg[i][day-121], pign[i][day-121])
                        narr2 = 0
                        totpltg = sum(ltgp[i][day-121])
                        for fire in range(nign):
                            rand1 = random.random() * totpltg
                            if rand1 < ltgp[i][day-121][0]:
                                pa = parr0[i][day-121]
                            elif rand1 < ltgp[i][day-121][1] + ltgp[i][day-121][0]:
                                pa = parr0[i][day-121]
                            elif rand1 < ltgp[i][day-121][2] + ltgp[i][day-121][1] + ltgp[i][day-121][0]:
                                pa = 1.0 * parr0[i][day-121]
                            elif rand1 < ltgp[i][day-121][3] + ltgp[i][day-121][2] + ltgp[i][day-121][1] + ltgp[i][day-121][0]:
                                pa = 0.8 * parr0[i][day-121]
                            else:
                                pa = 0.20 * parr0[i][day-121]
                            rand2 = random.random()
                            if rand2 < pa:
                                narr2 += 1
                        nhold = nhold - narr1 + nign - narr2
                    narrtoday[i-1] += (narr1 + narr2) / sims
                    nholdtoday[i-1] += (nhold + narr1 + narr2) / sims
                    nigntoday[i-1] += nign / sims
                    if sim == 1:
                        ltgsum += ltg[i][today-121]
                        totfire += firegrid[i][today-121]
                    nigns[subreg[i]][sim] += nign
                    totarr[subreg[i]][sim] += narr1 + narr2
                    tothold[subreg[i]][sim] += nhold + narr1 + narr2
                nignsPROV[sim] += nign
                totarrPROV[sim] += narr1 + narr2
                totholdPROV[sim] += nhold + narr1 + narr2
            ltgsum2 += ltgsum
            for k in range(3):
                for i in range(sims):
                    for j in range(i, sims):
                        if totarr[k][j] < totarr[k][i]:
                            temp = totarr[k][i]
                            totarr[k][i] = totarr[k][j]
                            totarr[k][j] = temp
                        if tothold[k][j] < tothold[k][i]:
                            temp = tothold[k][i]
                            tothold[k][i] = tothold[k][j]
                            tothold[k][j] = temp
                        if nigns[k][j] < nigns[k][i]:
                            temp = nigns[k][i]
                            nigns[k][i] = nigns[k][j]
                            nigns[k][j] = temp
            for i in range(sims):
                for j in range(i, sims):
                    if totarrPROV[j] < totarrPROV[i]:
                        temp = totarrPROV[i]
                        totarrPROV[i] = totarrPROV[j]
                        totarrPROV[j] = temp
                    if totholdPROV[j] < totholdPROV[i]:
                        temp = totholdPROV[i]
                        totholdPROV[i] = totholdPROV[j]
                        totholdPROV[j] = temp
                    if nignsPROV[j] < nignsPROV[i]:
                        temp = nignsPROV[i]
                        nignsPROV[i] = nignsPROV[j]
                        nignsPROV[j] = temp
            mon, day = nailuj(today, leap)
            avgnign = sum(nignsPROV) / sims
            out.write(f"{oldyear} {today} {mon} {day} {avgnign} {totfire} {ltgsum} {totholdPROV[ci_low-1]} {totholdPROV[ci_high-1]} {totarrPROV[ci_low-1]} {totarrPROV[ci_high-1]} {tothold[0][ci_low-1]} {tothold[0][ci_high-1]} {totarr[0][ci_low-1]} {totarr[0][ci_high-1]} {tothold[1][ci_low-1]} {tothold[1][ci_high-1]} {totarr[1][ci_low-1]} {totarr[1][ci_high-1]} {tothold[2][ci_low-1]} {tothold[2][ci_high-1]} {totarr[2][ci_low-1]} {totarr[2][ci_high-1]} 0 0 0\n")
            for i in range(cells):
                if lati[i] > 0:
                    out2.write(f"{i} {oldyear} {mon} {day} {lati[i]} {longi[i]} {narrtoday[i]} {nholdtoday[i]} {nigntoday[i]}\n")
        oldyear = int(year)
        line = inp.readline()
        if not line:
            break
        grid, lat, lon, year, jd, probign, probarr0, probarr1, totltg, numfire, region, nltg0, nltg1, nltg2, nltg3, nltg4, dmc, dc = map(float, line.split())
    inp.close()
    out.close()
    out2.close()

if __name__ == "__main__":
    main()
