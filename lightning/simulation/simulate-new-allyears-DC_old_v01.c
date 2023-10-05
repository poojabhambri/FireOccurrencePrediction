/*

This things does a simulation of fire occurence at each cell on each day in the fire season
....that is it uses the probabilitys of ignition and arrival and draws random outcomes
from lightning activity and then from pools of holdover fires.
For each day and grid cell it runs through 200 simulations.....and then uses
these 200 simulations to come up with a prediction and a95% confidence band rfor a prediction for
each zone for a particualr day


THIS NOW DOES THE EXPECTED NUMBER OF FIRES GOING BACKwards in time a number of DAYS,
a number dependant on the DC (higher the DC longer we look back in time
at lightning, holdovers and arrivals.

bmw/2007

NOTE---this is a quite set of prediciton for 2010...DOES not READ in FIRES.!!!!!


*/


#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

long ignbin(long n,float pp);  /* binomial function pasted in from the RANBIN library */

int nailuj(int *mon, int *day, int jd, int leap);

  // MATT: Needed to increase the matrix dimensions since the grid variable goes all the way
  // up to ~8000.
  //  int grid,jd,totltg,totpltg,region,nltg0,nltg1,nltg2,nltg3,nltg4, mon,day,mm,dd,today,leap,numfire,totfire;
  //  int err,j,i,h,SEED,ltg[5000][154],ltgp[5000][154][5],eco[5000][154],
  //    totarr[500],tothold[500],nigns[500],dmcgrid[5000][154],dcgrid[5000][154],firegrid[5000][154];
  //  int nign, nhold,narr1,narr2,sim,temp,fire,ltgsum,numfires[25][183],n;
  //  float probarr0, probarr1,probign,pign[5000][154],parr0[5000][154],parr1[5000][154];
  //  float pa,rand1,rand2,longi[5000],lati[5000],lat,lon, narrtoday[5000], nholdtoday[5000], nigntoday[5000],avgnign;
  int grid,jd,totltg,totpltg,region,nltg0,nltg1,nltg2,nltg3,nltg4, mon,day,mm,dd,today,leap,numfire,totfire;
  int err,j,i,h,SEED,ltg[10000][154],ltgp[10000][154][5],eco[10000][154],
    totarr[500],tothold[500],nigns[500],dmcgrid[10000][154],dcgrid[10000][154],firegrid[10000][154];
  int nign, nhold,narr1,narr2,sim,temp,fire,ltgsum,numfires[25][183],n;
  float probarr0, probarr1,probign,pign[10000][154],parr0[10000][154],parr1[10000][154];
  float pa,rand1,rand2,longi[10000],lati[10000],lat,lon, narrtoday[10000], nholdtoday[10000], nigntoday[10000],avgnign;


#define ABS(x) ((x) >= 0 ? (x) : -(x))
//   #define min(a,b) ((a) <= (b) ? (a) : (b))
// #define max(a,b) ((a) >= (b) ? (a) : (b))

int main(int argc ,char *argv[]){
  // MATT:
  // argv[1] is a random number seed
  // argv[2] is the input path to (and including) ltg_output.csv
  // argv[3] is the input path to (and including) AB-predictions.out
  // argv[4] is the output path to (and including) AB-grids.out
  //
  // Sample command line usage for Home PC:
  // simulate-new-allyears-DC.exe 12345 "Z:\\LightningFireOccurrencePredictionInputs\\ltg_output.csv" "Z:\\LightningFireOccurrencePredictionInputs\\AB-predictions.out" "Z:\\LightningFireOccurrencePredictionInputs\\AB-grids.out"
  //
  // Sample gcc compile command for Home PC:
  // 'C:\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin\gcc.exe' -g 'Y:\University of Alberta\Software Development\FireOccurrencePrediction\lightning\simulation\simulate-new-allyears-DC.c' -lm -o 'Y:\University of Alberta\Software Development\FireOccurrencePrediction\lightning\simulation\simulate-new-allyears-DC.exe'

  printf("Number of command line args is %d", argc);

  // MATT: Rudimentary command line argument check.
  if (argc != 5)
  {
    printf("Invalid number of command line arguments provided.\r\n");
    printf("Usage: simulate-new-allyears.exe [RANDOM_NUMBER_SEED] [...\\ltg_output.csv] [...\\AB-predictions.out] [...\\AB-grids.out]\r\n");
    return 1;
  }

  FILE *inp,*out,*out2;
  int cells=9999, sims=200,baseyear=1990;
  int holdover,year,oldyear,zone,dc,dmc,ltgsum2;

  // MATT: I've modified this part to zero out the numfires matrix.
  //
  //inp=fopen("fires_arrivals1990-2014.dat","r");
  //  err=fscanf(inp,"%d%d%d",&year,&jd,&numfire);
  //  while(err>=0){
  //    numfires[year-baseyear][jd-121]=numfire;
  //    err=fscanf(inp,"%d%d%d",&year,&jd,&numfire);
  //  }
  //fclose(inp);
  for(int i = 0; i < 25; i++)
  {
    for(int j = 0; j < 183; j++)
    {
      numfires[i][j] = 0;
    }
  }

  inp=fopen(argv[2],"r");
/* this input file has Probability of Ignition, Probability arrival,lightning summarized
for each day in periods within the day, DMc and DC and a little other info  */

  out=fopen(argv[3],"w");
  out2=fopen(argv[4],"w");

  //if(argc!=2){printf("enter a seed as well..a new seed\n");exit(1);}
  SEED=atoi(argv[1]);
  srand(SEED);   /* IMPORTANT : reseed with a new  number  */

  /* load up the matrizes with data*/

  //for(i=0;i<183;i++)for(j=0;j<20;j++){numfires[j][i][0]=0;numfires[j][i][1]=0;}

   printf(" before first read of inp\n");
   if (inp==NULL) printf(" hey INP is NULL \n");
   err=fscanf(inp,"%d%f%f%d%d%f%f%f%d%d%d%d%d%d%d%d%d%d",
               &grid,&lat,&lon,&year,&jd,&probign,&probarr0,&probarr1,&totltg,&numfire,
               &region,&nltg0,&nltg1,&nltg2,&nltg3,&nltg4,&dmc,&dc);

             printf(" AFTER first read of inp: grid=%d  dmc=%d dc=%d year=%d\n",grid,dmc, dc, year);
  oldyear=year;
  while(err>=0){  /* scans thru each yerar*/

   printf("YEAR=%d  grid=%d jd=%d pig=%f pa=%f totltg=%d  reg=%d\n",year, grid,jd,probign,probarr0,totltg,region);

   for(i=0;i<cells;i++)for(j=0;j<154;j++){   /* zero out the matrixes*/
     eco[i][j]=0;
     pign[i][j]=0.0;    /* probability of ignition */
     parr0[i][j]=0.0;       /* probability of arrival on day 0*/
     parr1[i][j]=0.0;       /* probability of arrival after day 0*/
     dmcgrid[i][j]=0;
     dcgrid[i][j]=0;
     lati[i]=0.0;           /* lat and long of the gridcell--for output purposes */
     longi[i]=0.0;
     ltg[i][j]=0;         /* total ltg  */
     ltgp[i][j][0]=0;   /* ltg in period 1    0000-0600   */
     ltgp[i][j][1]=0;    /* ltg in period 2    0600-1200   */
     ltgp[i][j][2]=0;    /* ltg in period 3    1200-1800   */
     ltgp[i][j][3]=0;    /* ltg in period 4    1800-2100   */
     ltgp[i][j][4]=0;    /* ltg in period 5    2100-2359   */
   }
   if (year%4==0 )leap=1;  /* leap=0 means not a leap year  why do we care????*/
   else leap=0;
   ltgsum2=0;
   
   while(err>=0 && oldyear==year){  /* load up a years worth!!!!!!  */
     if(jd>120 && jd<274){
      eco[grid][jd-121]=region;
      pign[grid][jd-121]=probign;
      parr0[grid][jd-121]=probarr0;
      parr1[grid][jd-121]=probarr1;
      dmcgrid[grid][jd-121]=dmc;
      dcgrid[grid][jd-121]=dc;
      lati[grid]=lat;
      longi[grid]=lon;
      ltg[grid][jd-121]=totltg;
      firegrid[grid][jd-121]=numfire;
      ltgsum2+=totltg;
      ltgp[grid][jd-121][0]=nltg0;ltgp[grid][jd-121][1]=nltg1;
      ltgp[grid][jd-121][2]=nltg2;ltgp[grid][jd-121][3]=nltg3;
      ltgp[grid][jd-121][4]=nltg4;
     }
     err=fscanf(inp,"%d%f%f%d%d%f%f%f%d%d%d%d%d%d%d%d%d%d",
               &grid,&lat,&lon,&year,&jd,&probign,&probarr0,&probarr1,&totltg,&numfire,
               &region,&nltg0,&nltg1,&nltg2,&nltg3,&nltg4,&dmc,&dc);
     
     // printf("grid=%d  year=%d jd=%d ltg=%d dmc=%d dc=%d pign=%f parr0=%f\n",grid,year,jd, totltg,dmc,dc,probign,probarr0);
   }  /* the look per year   */
   printf("*************************done first main read of 1990*****************88   ltgtot=%d   year=%d\n", ltgsum2,oldyear);
   ltgsum2=0;
   // MATT: Changing today to be < 274
   // for(today=130;today<243;today++){
    for(today=130;today<274;today++){
    ltgsum=0;
    totfire=0;
    for(i=0;i<cells;i++){narrtoday[i]=0.0;nholdtoday[i]=0.0;nigntoday[i]=0.0;}

    for(sim=0;sim<sims;sim++){   /*go thru 200 times  */
      totarr[sim]=0;
      tothold[sim]=0;
      nigns[sim]=0;
      for(i=1;i<=cells;i++){
        nhold=0;

        /* deciding how long to look backwards in time for holdovers*/
        if(dcgrid[i][today-121]<200)holdover=(int)(dcgrid[i][today-121]*3.0/200.0+4.0+0.5);
        else holdover=(int)( (dcgrid[i][today-121]-200.0)*14.0/300.0+7.0+0.5);
        //holdover=min(holdover, today-121);  /* can't go back prior to May 1 (121) */
        // MATT: Change the min function so that the code compiles properly.
        holdover=fmin(holdover, today-121);
 // if(sim==1 && ltg[i][today-121]>0 )printf("jd=%d daltg=%d\n",today,ltg[i][today-121]);
        for(day=today-holdover;day<=today;day++){

   //       if(nhold>0)printf("hold....cell=%d day=%d  hold=%d\n",i,day,nhold);

          if( day>(today-holdover) ){
          /*  narr1=ignbin( (long)(nhold), parr1[i][day-121]);*/
           /* narr1 is arrivals from the files holding over from the previous days */

              for(h=0,narr1=0;h<nhold;h++){
                           rand2=(float)(rand())/(float)(RAND_MAX);
                           if(rand2<parr1[i][day-121])narr1++;
                }
             }  /* this was an alternate to get the binomial draw done*/
          else narr1=0;

       /*HEREERERER   elimiate ignbin
          nign=ignbin( (long)(ltg[i][day-121]), pign[i][day-121]);   new ignitions today*/
          for(h=0,nign=0; h<ltg[i][day-121];h++){
             rand2=(float)(rand())/(float)(RAND_MAX);
             if(rand2<pign[i][day-121]) nign++;
          }
          narr2=0;  /* look at arrivals from todays ingniotns  */

          for(j=0,totpltg=0;j<5;j++) totpltg += ltgp[i][day-121][j];
     /*          if (totpltg!=ltg[i][day-121])printf("totltg mismatch  tltg=%d  pltg=%d\n",
                                                  ltg[i][day-121],totpltg); */

          for(fire=0;fire<nign;fire++){ /*(for each fire,  test arrival)*/
                    /*(here we decide on which period the fire was in
                      Based on weighting the lightning strikes in each period))*/
            rand1=(float)(rand())/(float)(RAND_MAX)*(float)(totpltg); /*RAND1=random integer number between 0 and TLTG[I]*/

            if(rand1<ltgp[i][day-121][0]) pa=parr0[i][day-121];  /* before 0600*/
            else if(rand1<(ltgp[i][day-121][1]+ltgp[i][day-121][0])) pa=parr0[i][day-121];  /* before 1200*/
            else if(rand1<(ltgp[i][day-121][2]+ltgp[i][day-121][1]+ltgp[i][day-121][0])) pa=1.0*parr0[i][day-121];   /*before 1800*/
            else if(rand1<(ltgp[i][day-121][3]+ltgp[i][day-121][2]+ltgp[i][day-121][1]+ltgp[i][day-121][0])) pa=0.8*parr0[i][day-121];  /* before 2100*/
            else pa=0.20*parr0[i][day-121];

            rand2=(float)(rand())/(float)(RAND_MAX);
            if(rand2<pa)narr2=narr2+1;

          }/* END( close the for loop)*/

          nhold=nhold - narr1 + nign - narr2;
        }  /*END  (close the day loop)*/

        narrtoday[i]+=(float)(narr1+narr2)/(float)(sims);

        nholdtoday[i]+=(float)(nhold+narr1+narr2)/(float)(sims);

        nigntoday[i]+=(float)(nign)/(float)(sims);

        if(sim==1){
           ltgsum+=ltg[i][today-121];
           totfire+=firegrid[i][today-121];
        }
        nigns[sim]+=nign;  /* ignitons on the last day*/
        totarr[sim]=totarr[sim] + narr1 + narr2;
        tothold[sim]=tothold[sim] + (nhold+narr1+narr2);
        /*(these are the sum over all CELLS of the arrivals and holdovers for today..
        this is the point to figure out alternate sums for each of the ZONEs essentailly*/

      } /*  i (close the tru the CELLs loop)*/
    }/*  sim   close the simloop)*/
       ltgsum2+=ltgsum;

    /* sorting so we can figure out 2.5th and 97.5th percentiles*/
    for(i=0;i<sims;i++) for(j=i;j<sims;j++){
         if(totarr[j]<totarr[i]){ temp=totarr[i];totarr[i]=totarr[j];totarr[j]=temp;}
         if(tothold[j]<tothold[i]){ temp=tothold[i];tothold[i]=tothold[j];tothold[j]=temp;}
         if(nigns[j]<nigns[i]){ temp=nigns[i];nigns[i]=nigns[j];nigns[j]=temp;}
    }
    nailuj(&mon,&day,today,leap);  /* 0 means not a leap year*/
    for(i=0,avgnign=0.0;i<sims;i++) avgnign+=(float)(nigns[i])/(float)(sims);

    // MATT: Always use 0 for obs_arr since we don't care about numfires.
    //fprintf(out,"%4d %3d %2d %2d %6.4f  %3d %7d    %3d %3d    %3d %3d      %3d\n", oldyear,today,mon,day,avgnign,totfire,ltgsum,tothold[5-1],tothold[195-1],totarr[5-1],totarr[195-1],numfires[oldyear-baseyear][today-121]);
    //printf("%4d %3d %2d %2d NIGNs=%6.3f obsNign=%3d ltg=%7d HOLD=(%3d,%3d) arrs=(%3d,%3d) obs_arr=%3d\n", oldyear,today, mon,day,avgnign,totfire,ltgsum,tothold[5-1],tothold[195-1],totarr[5-1],totarr[195-1],numfires[oldyear-baseyear][today-121]);
    fprintf(out,"%4d %3d %2d %2d %6.4f  %3d %7d    %3d %3d    %3d %3d      %3d\n", oldyear,today,mon,day,avgnign,totfire,ltgsum,tothold[5-1],tothold[195-1],totarr[5-1],totarr[195-1],0);
    printf("%4d %3d %2d %2d NIGNs=%6.3f obsNign=%3d ltg=%7d HOLD=(%3d,%3d) arrs=(%3d,%3d) obs_arr=%3d\n", oldyear,today, mon,day,avgnign,totfire,ltgsum,tothold[5-1],tothold[195-1],totarr[5-1],totarr[195-1],0);

    for(i=0;i<cells;i++){
     if(lati[i]>0){
          fprintf(out2,"%5d %4d %2d %2d %9.3f %9.3f %7.5f %7.5f %7.5f\n",
              i,oldyear,mon,day,lati[i],longi[i],narrtoday[i],nholdtoday[i],nigntoday[i]);
     } /* end if*/
    }/* end for*/

   }   /* end today loop */
   printf("year=%d, ltgsum2=%d\n", oldyear, ltgsum2);
  oldyear=year;

  } /*  the big loop thru the years*/

  fclose(inp);

  fclose(out);
  fclose(out2);
}




int nailuj(int *mon, int *day, int jd, int leap)
{
  int month[13]={0,31,59,90,120,151,181,212,243,273,304,334};
  int monthl[13]={0,31,60,91,121,152,182,213,244,274,305,335};
  *mon=1;
  if(leap==0){
    while(jd>month[*mon])(*mon)++;
    *day=jd-month[*mon-1];
  }
  else{
    while(jd>monthl[*mon])(*mon)++;
    *day=jd-monthl[*mon-1];
  }
}

