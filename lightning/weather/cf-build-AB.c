/* 2018....earl season too.....changed

this is now set up to read thru the ALBERTA wx dataset
 and develop CF files

** interpolates from APRIL onward

** the inter smoothing cooefficents (smooth[]) should be adjusted some day to
match whats best for the province (no study has been done yet)

jan 05
*/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

// MATT: Used for determining the correct CWD to output the coefficient files.
#include <unistd.h>

typedef double alldata[600][3];
typedef double square[600][600];
typedef double column[600];

  alldata interp;
  column cf;

  square a,b;
  column c,y;


void multiply(square a,int arow,int acol,column b,int brow,int bcol,column c,
  int *crow,int *ccol);
void invert(square a,int row,square b);
void regress(alldata stuff,column coeff,int row,int col,float mult);

void distance(double *x, double *y, float cent_lat, float cent_long,
              float lat, float lon);

void interpolate(alldata info,int num,column a,float mult);


int main(int argc, char *argv[])
{
  // MATT:
  // argv[1] is the input path to (and including) Alberta_PM_Weather_2018_MASSAGED.csv
  // argv[2] is the path to place the output interpolated weather coefficient files in.
  //
  // Sample command line usage for Lab PC:
  // cf-build-AB.exe "C:\\Users\\Ansell\\Desktop\\Mike\'s large LOP datasets\\alberta_data\\Alberta_PM_Weather_2018_MASSAGED.csv" "C:\Users\Ansell\Desktop\Mike\'s large LOP datasets\\weather_interpolation\\"
  //
  // Sample gcc compile command:
  // 'C:\mingw-w64\x86_64-8.1.0-posix-seh-rt_v6-rev0\mingw64\bin\gcc.exe' -g 'c:\Users\Ansell\Dropbox\University of Alberta\Software Development\FireOccurrencePrediction\lightning\weather\cf-build-AB.c' -o 'c:\Users\Ansell\Dropbox\University of Alberta\Software Development\FireOccurrencePrediction\lightning\weather\cf-build-AB.exe'

  if (argc != 3)
  {
    printf("Invalid number of command line arguments provided.\r\n");
    printf("Usage: cf-build-AB.exe [...\\Alberta_PM_Weather_2018_MASSAGED.csv] [...DIRECTORY_TO_STORE_INTERMEDIATE_FILES_IN]\r\n");
    return 1;
  }

  // MATT: Change the current working directory to the output path of the coefficient files.
  chdir(argv[2]);

  FILE  *data,  *out[10];

  int err, err2, err3, N, z, i, j, k, rec,  b;
  int yr, mon, day;
  int oldyr,oldmon,oldday, id,NSTANS[11],NUM;

  double x, y;

  float lat, lon;
  float location[416][2];
  float max, min, latmax,latmin,longmin,longmax;
  float wx[416][12], latlong[416][10][2];
  float smooth[10]={0.001, 0.001, 0.001, 0.01, 0.001, 0.001, 0.001, 0.001,
                    0.001, 0.001};
  
  // MATT: Add declarations for these missing float variables.
  float temp, rh, ws, rain, ffmc, dmc, dc, isi, bui, fwi;

  char dum;

  for (i=0; i<2; i++) {
    for (N=0; N<=415; N++) {
      location[N][i]=0.0;
    }
  }
  printf("here .......declaration\n");

  // MATT: Removed the "8316" from the coefficient file names to make the file name more understandable.
  out[0] = fopen("CF-temp.ab", "w");
  out[1] = fopen("CF-rh.ab", "w");
  out[2] = fopen("CF-ws.ab", "w");
  out[3] = fopen("CF-rain.ab", "w");
  out[4] = fopen("CF-ffmc.ab", "w");
  out[5] = fopen("CF-dmc.ab", "w");
  out[6] = fopen("CF-dc.ab", "w");
  out[7] = fopen("CF-isi.ab", "w");
  out[8] = fopen("CF-bui.ab", "w");
  out[9] = fopen("CF-fwi.ab", "w");

/*
   all set up is done now  ...read in first lines from WX and extraRAIN files
   the implicit assumption here is that there are entries for EACH day April thru sept
   for each year in each of the files.
*/

 // data = fopen("C:/BMW/work/alberta/interp/wx1975-2012.txt", "r");
 // argv[0] is the path to the massaged weather data.
  data = fopen(argv[1], "r");
  if(data==NULL)exit(1);
  printf("here fopen\n");

  err2=fscanf(data, "%d%f%f%d%d%d%f%f%f%f%f%f%f%f%f%f", &id, &lat,&lon, &yr, &mon,
                  &day, &temp, &rh, &ws, &rain, &ffmc, &dmc, &dc, &isi, &bui, &fwi);
  for(i=0,dum=fgetc(data);i<80 && dum!='\n';i++,dum=fgetc(data) );
printf("after read   lat=%f mon=%d\n",lat,mon);
  oldyr=yr;
  oldmon=mon;
  oldday=day;

  printf("starting into the loop\n");
  while (err2>=0 ) {

    /* ERASE all old entries*/
    for (k=0; k<=415; k++)for (i=0; i<10; i++) wx[k][i]=-999.99;
    latmax=-999.999;latmin=999.999;
    longmin=999.999; longmax=-999.999;

    /* LOAD up on the wx values for one day  */
    printf("reading in weather for %4d %3d %3d\n", oldyr,oldmon,oldday);
    for(k=0;k<11;k++)NSTANS[k]=0;
    while (yr==oldyr && mon==oldmon && day==oldday && err2>=0) {
      if(temp>-90){wx[NSTANS[0]][0]=temp;latlong[NSTANS[0]][0][0]=lat;latlong[NSTANS[0]][0][1]=lon;NSTANS[0]++;}
      if(rh>-90){wx[NSTANS[1]][1]=(float)(rh);latlong[NSTANS[1]][1][0]=lat;latlong[NSTANS[1]][1][1]=lon;NSTANS[1]++;}
      if(ws>-90){wx[NSTANS[2]][2]=(float)(ws);latlong[NSTANS[2]][2][0]=lat;latlong[NSTANS[2]][2][1]=lon;NSTANS[2]++;}
      if(rain>-90){wx[NSTANS[3]][3]=rain;latlong[NSTANS[3]][3][0]=lat;latlong[NSTANS[3]][3][1]=lon;NSTANS[3]++;}
      if(ffmc>-90){wx[NSTANS[4]][4]=ffmc;latlong[NSTANS[4]][4][0]=lat;latlong[NSTANS[4]][4][1]=lon;NSTANS[4]++;}
      if(dmc>-90){wx[NSTANS[5]][5]=(float)(dmc);latlong[NSTANS[5]][5][0]=lat;latlong[NSTANS[5]][5][1]=lon;NSTANS[5]++;} 
      if(dc>-90){wx[NSTANS[6]][6]=(float)(dc);latlong[NSTANS[6]][6][0]=lat;latlong[NSTANS[6]][6][1]=lon;NSTANS[6]++;}
      if(isi>-90){wx[NSTANS[7]][7]=isi;latlong[NSTANS[7]][7][0]=lat;latlong[NSTANS[7]][7][1]=lon;NSTANS[7]++;}
      if(bui>-90){wx[NSTANS[8]][8]=bui;latlong[NSTANS[8]][8][0]=lat;latlong[NSTANS[8]][8][1]=lon;NSTANS[8]++;}
      if(fwi>-90){wx[NSTANS[9]][9]=fwi;latlong[NSTANS[9]][9][0]=lat;latlong[NSTANS[9]][9][1]=lon;NSTANS[9]++;}
      if(lat>-90){
           wx[NSTANS[10]][10]=lat;
           wx[NSTANS[10]][11]=lon;
           NSTANS[10]++;
           if(lat>latmax)latmax=lat;
           if(lat<latmin)latmin=lat;
           if(lon>longmax)longmax=lon;
           if(lon<longmin)longmin=lon;
      }

      err2=fscanf(data, "%d%f%f%d%d%d%f%f%f%f%f%f%f%f%f%f",&id, &lat, &lon,&yr, &mon,
                  &day, &temp, &rh, &ws, &rain, &ffmc, &dmc, &dc,
                  &isi, &bui, &fwi);

      for(i=0,dum=fgetc(data);i<80 && dum!='\n';i++,dum=fgetc(data) );
    } /* end while (yr==oldyr mon=omon d=od) */
   if(oldyr>1900){
    printf("and now.......interpolating...N=%d \n",NSTANS[10]);

    for(i=0;i<10;i++){
      printf("%d ",i);   /* go thru each index */
      for(k=0;k<600;k++){
        for(j=0;j<3;j++)interp[k][j]=0.00;
        cf[k]=0.00000;
      }
      if(NSTANS[i]>1 && oldmon>0 && oldmon<13){   /* only is we have some reasonable number of stations  and month is april*/
       max=-999.99;min=999.99;
       NUM=NSTANS[i];
       for(j=0;j<NUM;j++){
            interp[j][0]=latlong[j][i][0];
            interp[j][1]=latlong[j][i][1];
            interp[j][2]=wx[j][i];
            if(max<wx[j][i])max=wx[j][i];
            if(min>wx[j][i])min=wx[j][i];
       }
       interpolate(interp, NUM, cf, smooth[i]);

      } /* end the if more than 10 stations */
      else NUM=0;  /* as a key in the output so we know its a no good day */

      /*OUTPUT */
      if (oldmon<11){
         fprintf(out[i],"%04d%02d%02d%03d%06.1f%06.1f%07.2f%07.2f%07.2f%07.2f",
              oldyr,oldmon,oldday,NUM,min,max,latmin-1.5,latmax+1.5,longmin-3.0,longmax+3.0);

           /* note the allowable lat/long box is a bit bigger than the real range...
          interpolation becomes extrapolation for a small bit at the edge*/

         for(j=0;j<600;j++)fprintf(out[i],"%08.3f%08.3f%014.6f",
              interp[j][0],interp[j][1],cf[j]);
         fprintf(out[i],"\n");
      /* keep in mind here that this outputs the final extra 3 intercept coeffients after
         the NUM place is reached*/
      }   /* end the iff err*/

    }  /* end the for thru the 10 indexs*/
     printf("\n");
   }  /* end the IF yr>1983 loop added in for ltg  */
    /* now reset the old values to the new day....wx/rain has already been read in*/
    oldyr=yr;
    oldmon=mon;
    oldday=day;

  } /* end big while loop...end while(there is still data) */

  for(i=0;i<10;i++)fclose(out[i]);
  fclose(data);
}

/* functions julian & nailuj taken from /disk15/mwotton/progs/nailuj.c  */

void interpolate(alldata info,int num,column a,float mult)

/*   NOTE######  all beyond here has been modified to bess less general
and more specific to the thin plate spline methodology.

*/
{

   regress(info,a,num,num+3,mult);

}


void multiply(square a,int arow,int acol,column b,int brow,int bcol,column c,int *crow,int *ccol)
  /*   multiply in order   A * B   */

  {
    int i,j,k;
    if(brow!=acol)
     { printf(" The matrices are the wrong size for multiplication\n");
       return;
     }
    *crow=arow;*ccol=bcol;

    for(i=0;i<(*crow);i++)c[i]=0;
    for(i=0;i<arow;i++)  for(k=0;k<brow;k++)
                        c[i]+=(a[i][k] * b[k]);
  }

 void  invert(square a,int row,square b)


  {
    int i,j,k,l;
    float div,tmp;

    for(i=0;i<row;i++)for(j=0;j<row;j++){
             if(i==j) b[i][j]=1;
             else b[i][j]=0;}

/*
    for(i=row-1;i==1;i--)for(j=0;j<row;j++){
       tmp=a[i-1][j];
       a[i-1][j]=a[i][j];
       a[row][j]=tmp;
    }
*/
    for(i=0;i<row;i++)
     {
       div=(a[i][i]);
       if(div==0.0){
            for(k=i+1;k<row;k++){
              div=a[k][i];
              if(div!=0)
                for(l=0;l<row;l++){
                  tmp=a[i][l];
                  a[i][l]=a[k][l];
                  a[k][l]=tmp;
                  tmp=b[i][l];
                  b[i][l]=b[k][l];
                  b[k][l]=tmp;
                }
              k=row+2;
            }
          if(k==row){printf("Problem in the inversion routine\n");exit(1);}
          div=a[i][i];
       }
       if(div!=0)for(j=0;j<row;j++)  { a[i][j]/=div; b[i][j]/=div; }
       for(j=0;j<row;j++)
        {
          div=-1.0*a[j][i] ;
          if(div!=0.0)  /* this is essentially 0*/
           {
             if(j>i)
                 for(k=0;k<row;k++)
                  {
                    b[j][k]=b[j][k]/div + b[i][k];
                    a[j][k]=a[j][k]/div + a[i][k];
                  }
             else if(j<i)
                 for(k=0;k<row;k++)
                  {
                    b[j][k]=b[i][k]*div +b[j][k];
                    a[j][k]=a[i][k]*div + a[j][k];
                   }
           }        /* end the if */
        }      /* end the for j  */
     }     /*  end the for i  */
  }

 void regress(alldata stuff,column coeff,int row,int col,float mult)

{

  int crow,ccol,stations,i,j,k;
  float ds,xk,xl,yk,yl,tmp1,tmp2;
  col=row;
  stations=row+3;

  for(j=0;j< row;j++)
   for(i=0;i< col;i++){
    a[j][i]=0.0;
    if(i!=j){
      xl=stuff[j][1];
      yl=stuff[j][0];
      xk=stuff[i][1];
      yk=stuff[i][0];
      ds=sqrt((xk-xl)*(xk-xl)+(yk-yl)*(yk-yl));
      if(ds==0)a[j][i]=0.0;
      else a[j][i]=ds*ds*log(ds);
    }
    else
     a[j][i]=row*mult;

   }
  for(j=0;j< row;j++){
    a[j][row]=1.0;
    a[row][j]=1.0;
    a[j][row+1]=(float)(stuff[j][1]);  /*set up x*/
    a[row+1][j]=(float)(stuff[j][1]);
    a[j][row+2]=(float)(stuff[j][0]);  /* set up y*/
    a[row+2][j]=(float)(stuff[j][0]);
  }
  for(j=row;j<stations;j++)for(i=row;i<stations;i++)a[j][i]=0.0;
  for(j=0;j<row;j++)y[j]=(float)(stuff[j][2]);
  for(j=row;j< row+3;j++)y[j]=0.0;
  invert(a,stations,b);
  multiply(b,stations,stations,y,stations,1,c,&crow,&ccol);
  for(i=0;i<crow;i++) coeff[i]=(double)(c[i]);
}

