/* this is set up for alberta now



jan 05
*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// MATT: Used for determining the correct CWD to output the coefficient files.
#include <unistd.h>

typedef double alldata[600][3];
  float codes[10010][10];
  float ERlocation[10010][2];


void distance(double *x, double *y, float cent_lat, float cent_long,
              float lat, float lon);
float calculate(alldata cf, int NUM, float lat,float lon, float min,float max);

int main(int argc, char *argv[])
{
  // MATT:
  // argv[1] is the output path to (and including) FWIgrid10-AB.dat, the interpolated weather data.
  // argv[2] is the output path to (and including) Gridlocations_plus.prn.
  // argv[3] is the path to load the input interpolated weather coefficient files from.
  //
  // Sample command line usage for Lab PC:
  // use_cf2.exe "C:\\Users\\Ansell\\Desktop\\Mike\'s large LOP datasets\\alberta_data\\FWIgrid10-AB.dat" "C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\weather_interpolation\\"
  //
  // Sample gcc compile command for Lab PC:
  // 'C:\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin\gcc.exe' -g 'c:\Users\Ansell\Dropbox\University of Alberta\Software Development\FireOccurrencePrediction\lightning\weather\use_cf2.c' -o 'c:\Users\Ansell\Dropbox\University of Alberta\Software Development\FireOccurrencePrediction\lightning\weather\use_cf2.exe'
  //
  // Sample gcc compile command for Home PC:
  // 'C:\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin\gcc.exe' -g 'Y:\University of Alberta\Software Development\FireOccurrencePrediction\lightning\weather\use_cf2.c' -o 'Y:\University of Alberta\Software Development\FireOccurrencePrediction\lightning\weather\use_cf2.exe'
  printf("HEEEERREEEEE 1!!!!");
  if (argc != 4)
  {
    printf("HEEEERREEEEE 3!!!!");
    printf("Invalid number of command line arguments provided.\r\n");
    printf("Usage: use_cf2.exe [...\\FWIgrid10-AB.dat] [...\\Gridlocations_plus.prn] [...DIRECTORY_TO_STORE_INTERMEDIATE_FILES_IN]\r\n");
    return 1;
  }
  printf("HEEEERREEEEE 2!!!!");
  // MATT: Change the current working directory to the input path of the coefficient files.
  chdir(argv[3]);

  FILE  *inp[10], *out,*points;

  alldata interp;
  int yr,mon,day,i,j,k,err, NUM,ecoregion[10010],REGIONS;
  float lat, lon;
  float max, min, latmax,latmin,longmin,longmax;

   inp[0] = fopen("CF-temp.ab", "r");
   inp[1] = fopen("CF-rh.ab", "r");
   inp[2] = fopen("CF-ws.ab", "r");
   inp[3] = fopen("CF-rain.ab", "r");
   inp[4] = fopen("CF-ffmc.ab", "r");
   inp[5] = fopen("CF-dmc.ab", "r");
   inp[6] = fopen("CF-dc.ab", "r");
   inp[7] = fopen("CF-isi.ab", "r");
   inp[8] = fopen("CF-bui.ab", "r");
   inp[9] = fopen("CF-fwi.ab", "r");

   out=fopen(argv[1],"w");  // FWIgrid10-AB.dat
   points=fopen(argv[2],"r");   
   if(points==NULL)printf("Points file not found\n");

   err=fscanf(points,"%d%f%f",&ecoregion[0],&ERlocation[0][0],&ERlocation[0][1]);
   REGIONS=0;
   while(err>=0){
    printf("HEEEERREEEEE 4!!!!");
      //  printf("%5d == lat= %0.2f  lon= %0.2f\n",
          //  REGIONS,ERlocation[REGIONS][0],ERlocation[REGIONS][1]);
       REGIONS++;
       err=fscanf(points,"%d%f%f",&ecoregion[REGIONS],
              &ERlocation[REGIONS][0],&ERlocation[REGIONS][1]);
   }
   fclose(points);

   printf("done --%d grids\n",REGIONS);

   err=1;
  //  printf("HEEEERREEEEE 5!!!!");
   while(err>=0){   /* go thru one day at a time */
    // printf("HEEEERREEEEE 6!!!!");
      for(i=0;i<10;i++)for(j=0;j<10010;j++)codes[j][i]=-999.9;
      for(i=0;i<10;i++){   /* go thru each index */
        err=fscanf(inp[i],"%4d%2d%2d%3d%6f%6f%7f%7f%7f%7f",
              &yr,&mon,&day,&NUM,&min,&max,&latmin,&latmax,&longmin,&longmax);
              // printf("NUM = %d",NUM);
              // printf("Year = %d",yr);
        for(k=0;k<600;k++)err=fscanf(inp[i],"%8lf%8lf%14lf",
                &interp[k][0],&interp[k][1],&interp[k][2]);
       /* now go thru all points and fill in matrix*/
        // printf("I DO get over HERE!");
        // printf("Regions: %d ", REGIONS);
        if(yr>1900)for(j=0;j<REGIONS;j++){  /* ************* YEAR exclusion */
          lat=ERlocation[j][0];
          lon=ERlocation[j][1];
          if(NUM>0)
               codes[j][i]=calculate(interp,NUM,lat,lon,min,max);
        }  /* then the loop thur the ER locations  */
      } /* end the i=1->10 loop */
      if (err > 0)
      {
        printf("%d  %d %d\n",yr,mon,day);
      }
      for(j=0;j<REGIONS;j++){
          if(codes[j][1]>-900.0 && err>0){   /* its not a missing value ****  YEAR exclusion*/
//comma seperated
             fprintf(out,"%d,%d,%d,%d",ecoregion[j],yr,mon,day);
             for(i=0;i<10;i++)fprintf(out,",%0.1f",codes[j][i]);
             fprintf(out,"\n");
// space seperated
/*
             fprintf(out,"%6d %4d %2d %2d ",ecoregion[j],yr,mon,day);
             for(i=0;i<10;i++)fprintf(out,"%5.1f ",codes[j][i]);
             fprintf(out,"%6.2f\n",0.0272*pow(codes[j][9],1.77) );
*/
          }
      } /* printed out all regions now */

   } /* end the while....get the next day*/
   for(i=0;i<10;i++)fclose(inp[i]);
   fclose(out);
}

/* functions julian & nailuj taken from /disk15/mwotton/progs/nailuj.c  */



float calculate(alldata cf, int NUM, float lat,float lon, float min,float max)
{
  int i;
  double ds,x,y;
  double calc;

  calc=cf[NUM][2]+ lon*cf[NUM+1][2]+lat*cf[NUM+2][2];
  for(i=0;i<NUM;i++){
    ds=sqrt( (lat-cf[i][0])*(lat-cf[i][0])+(lon-cf[i][1])*(lon-cf[i][1]) );
    if (ds>0.00001 )calc+=cf[i][2]*ds*ds*log(ds);
  }

 if(calc>max) calc=max;
 if(calc<min) calc=min;
 return (float)(calc);
}

