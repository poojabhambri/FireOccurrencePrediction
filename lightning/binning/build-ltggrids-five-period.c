/* this sums up ltg strikes around each wx stn

three spots to change the year
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

float distance(float *x, float *y, float lat,float lon, float cent_lat,float cent_long)
{
  double alat ;
  alat=(3.1415926/180.0)*(cent_lat+lat)/2.0;

  *x=(111.413*cos(alat)-0.094*cos(3*alat) )*(cent_long-lon);
  *y=(111.113-0.559*cos(2*alat)) * (lat-cent_lat);
  return (float)(sqrt(*x * *x + *y * *y));
}

int julian(int mon, int day)
{
  int month[13]={0,31,59,90,120,151,181,212,242,273,304,334};
  return month[mon-1]+day;
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

int main(int argc, char *argv[]){
  // MATT:
  // argv[1] is the input path to (and including) Gridlocations.prn
  // argv[2] is the input path to (and including) ABltg_space.out
  // argv[3] is the output path to (and including) ltg2010-20by20-five-period.dat
  //
  // Sample command line usage for Home PC:
  // build-ltggrids-five-period.exe "Y:\\University of Alberta\\Software Development\\FireOccurrencePrediction\\lightning\\binning\\Gridlocations.prn" "Z:\\LightningFireOccurrencePredictionInputs\\ABltg_space_MATT.out" "Z:\\LightningFireOccurrencePredictionInputs\\ltg2010-20by20-five-period.dat"
  printf("Number of command line args is %d", argc);

  // MATT: Rudimentary command line argument check.
  if (argc != 4)
  {
    printf("Invalid number of command line arguments provided.\r\n");
    printf("Usage: build-ltggrids-five-period.exe [...\\Gridlocations.prn] [...\\ABltg_space.out] [...\\ltg2010-20by20-five-period.dat]\r\n");
    return 1;
  }

  FILE *inp, *out;
  float dist, stans[10010][2],lat,lon,stren;
  int junk,yrid,i,j,id,index,err,year,oyear,omon,oday,hour,mon,day,jd,oldjd,mult;
  float x,y;
  int neg[10010][5],pos[10010][5], stnid[10010], PER=5;
  char a,dum;

  // MATT:
  //inp=fopen("C:\\Users\\Ansell\\Desktop\\Mike's large LOP datasets\\ltg_binning\\Gridlocations.prn","r");  
  inp=fopen(argv[1], "r");
  err=fscanf(inp,"%d%f%f",&id,&lat,&lon);
  index=0;
  while(err>=0){
       stans[index][0]=lat;
       stans[index][1]=lon;
       stnid[index]=id;
       index++;
       err=fscanf(inp,"%d%f%f",&id,&lat,&lon);
  }
  fclose(inp);


  // MATT:
  // inp=fopen("C:\\Users\\Ansell\\Desktop\\Mike's large LOP datasets\\ltg_binning\\ABltg_space.out","r");
  // out=fopen("C:\\Users\\Ansell\\Desktop\\Mike's large LOP datasets\\ltg_binning\\ltg2010-20by20-five-period.dat","w");
  inp=fopen(argv[2],"r");
  out=fopen(argv[3],"w");

  for(i=0;i<10010;i++)for(j=0;j<PER;j++){neg[i][j]=0;pos[i][j]=0;}
  for(i=0,dum=fgetc(inp);i<80 && dum!='\n';i++,dum=fgetc(inp) );     /* read byu header */
  err=fscanf(inp,"%f%f%f%d%d%d%d%d",&lat,&lon,&stren,&mult,&year,&mon,&day,&hour);
  jd=julian(mon,day);

  oldjd=jd;oyear=year;
  while(err>=0){
   while(jd==oldjd && year==oyear && err>=0){
    for(i=0;i<index;i++){
       dist=distance(&x,&y,lat,lon,stans[i][0],stans[i][1]);
       x=fabs(x); y=fabs(y);  /* 5 km on either side  */
       if(x<5.000 && y<5.000 )break;
    } /* end the for loop*/
    if(i<index){
      if(stren>0){
          if(hour<6) pos[i][0]++;   /* overnite */
          else if (hour<12) pos[i][1]++;   /* 1 is during early aft */
          else if (hour<18) pos[i][2]++;   /* 2 is late day */
          else if (hour<21) pos[i][3]++;   /* 3 is late day */
          else pos[i][4]++;   /* 4 is evening */

      }
      else {
          if(hour<6) neg[i][0]++;   /* overnite */
          else if (hour<12) neg[i][1]++;   /* 1 is during early aft */
          else if (hour<18) neg[i][2]++;   /* 2 is late day */
          else if (hour<21) neg[i][3]++;   /* 3 is late day */
          else neg[i][4]++;   /* 4 is evening */
      }
    }
   err=fscanf(inp,"%f%f%f%d%d%d%d%d",&lat,&lon,&stren,&mult,&year,&mon,&day,&hour);
    jd=julian(mon,day);

   }  /* end WHILE (jd=oldjd)  its a new jd  ..just after 1300..OR much later??*/
   nailuj(&omon,&oday,(oldjd),0);  /* ASSOCIAte with current day*/

   for(i=0;i<index;i++)for(j=0;j<PER;j++)if(neg[i][j]>0 || pos[i][j]>0) fprintf(out,
       "%5d %7.3f %7.3f %4d %2d %2d %1d %5d %5d\n",
       stnid[i],stans[i][0],stans[i][1],oyear,omon,oday, j , neg[i][j],pos[i][j]);

   for(i=0;i<10010;i++)for(j=0;j<PER;j++){neg[i][j]=0;pos[i][j]=0;}
   oldjd=jd;oyear=year;
  }  /* thru the main while loop*/

  fclose(out);
  fclose(inp);
}
