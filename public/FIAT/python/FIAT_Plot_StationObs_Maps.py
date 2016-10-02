#!/usr/bin/env python

#-------------------------------------------------------------------------------
# Scriptname:  UFO_VT_StationObs_Maps.py
#-------------------------------------------------------------------------------
#
# Description:
# Generates hourly visibility, temperature, windspeed and raingauge observations maps
# Reads filenames in destination folder to determine most current data file
# Then extracts data from MetDB from this time onwards and places the data in a dictionary
# This is done to lighten the load on MetDB
#
# Then the code loops through the data contained in each data dictionary to produce a 
# map of the hourly observations for that variable
#
# Called by:
# UFO_VT_Retrieve_Images.sh
# 
# Inputs:
# datelist         - List of dates to generate plots
# screentempobsdir - Directory in which screen temperature data is plotted
# windobsdir       - Directory in which windspeed  data is plotted
# visobsdir        - Directory in which visibility data is plotted
# precipobsdir     - Directory in which precipitation data is plotted
#
# Current Owner:  Mark Worsfold
#
# History:
# Date       Ticket Comment
# ---------- ------ -------
# 16/07/2015        Original script
# ---------- ------ End History
#
# End of header ----------------------------------------------------------------

import os
import shutil
import glob
import re
import argparse
from datetime import datetime, timedelta
import numpy as np
import metdb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

import cartopy.crs as ccrs
import iris.analysis.cartography

import PIL
from PIL import Image


parser = argparse.ArgumentParser() # Read arguments from command line
     
parser.add_argument("datelist", type=str, help="List of dates to generate plots")
parser.add_argument("screentempobsdir", type=str, help="Directory in which screen temperature data is plotted")
#parser.add_argument("windobsdir", type=str, help="Directory in which windspeed  data is plotted")
#parser.add_argument("visobsdir", type=str, help="Directory in which visibility data is plotted")
parser.add_argument("precipobsdir", type=str, help="Directory in which precipitation data is plotted")
args = parser.parse_args()

DateList=str(args.datelist) # Datelist format: YYYYMMDD
DateList = DateList.split(' ')

TempObsDir=str(args.screentempobsdir)
#WindObsDir=str(args.windobsdir)
#VisObsDir=str(args.visobsdir)
PrecipObsDir=str(args.precipobsdir)

if not os.path.exists(TempObsDir): os.makedirs(TempObsDir)
#if not os.path.exists(WindObsDir): os.makedirs(WindObsDir)
#if not os.path.exists(VisObsDir): os.makedirs(VisObsDir)
if not os.path.exists(PrecipObsDir): os.makedirs(PrecipObsDir)

RGBVals={
    # Temperature colourbar RGB data recovered from IDL colour file '/home/h06/meso/bin/op_charts/linux/idl/colours/myT2_glob.clr'
    'Temp': 
        " 0 255   8  12  17  21  25  29  34  38  42  46  51  55  59  63  68  72  76  80  85  89  93  97 102 106 110 114 119 123 127 131 136 140 144 148 153 157 \
         161 165 170 174 178 182 187 191 195 199 204 208 212 216 221 225 229 233 238 242 246 251 249 248 247 246 244 243 241 240 238 237 235 233 231 229 227 225 \
         223 221 218 216 213 211 208 205 202 199 195 192 188 185 181 177 173 168 164 159 154 149 144 138 132 126 120 113 107 100  92  85  77  68  60  51  41  31 \
          21  11   0  10  20  31  41  52  62  73 109 145 182 218 255 236 218 200 182 163 145 127 109  91  72  54  36  18   0   1   3   4   6   8   9  11  13  14 \
          16  18  19  21  23  23  23  23  23  23  23  23  23  52  81 110 139 168 197 226 255 254 254 254 253 253 252 252 251 251 250 249 248 247 246 244 243 241 \
         239 235 232 229 226 223 219 216 213 210 207 204 200 194 188 182 176 170 164 158 152 147 112 104  96  89  81  74  66  59  51  43  36  28  21  13   6  35 \
        58  77  93 107 119 130 140 150 158 166 173 180 187 193 199 204 209 214 219 224 228 232 236 240 244 248 251 255 \
           0 255   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0 \
           0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0 \
           0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0 \
           0   0   0  22  44  66  88 110 132 155 175 195 215 235 255 255 255 255 255 255 255 255 255 255 255 255 255 255 255 244 234 223 213 202 192 181 171 160 \
         150 139 129 118 108 121 135 148 162 175 189 202 216 220 225 230 235 240 245 250 255 251 246 241 236 229 222 213 204 193 181 167 151 133 113  90  63  34 \
           0  12  24  37  49  61  74  86  98 111 123 136 133 127 122 117 111 106 101  95  90  85  57  53  49  46  42  38  35  31  27  24  20  16  13   9   6  35 \
         58  77  93 107 119 130 140 150 158 166 173 180 187 193 199 204 209 214 219 224 228 232 236 240 244 248 251 255 \
        0 255   8  12  17  21  25  29  34  38  42  46  51  55  59  63  68  72  76  80  85  89  93  97 102 106 110 114 119 123 127 131 136 140 144 148 153 157 \
         161 165 170 174 178 182 187 191 195 199 204 208 212 216 221 225 229 233 238 242 246 251 250 250 250 250 249 249 249 249 248 248 248 247 247 247 246 246 \
         245 245 245 244 244 243 243 242 242 241 240 240 239 238 238 237 236 235 235 234 233 232 231 230 229 228 227 225 224 223 221 220 219 217 216 214 212 210 \
         208 207 205 209 213 218 222 227 231 236 239 243 247 251 255 236 218 200 182 163 145 127 109  91  72  54  36  18   0   0   0   0   0   0   0   0   0   0 \
           0   0   0   0   0  17  35  53  71  89 107 125 143 125 107  89  71  53  35  17   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0 \
           0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   1   1   1   1   2   2   2   2   2   3   3   3   4   4   4   4   5   5   5   6  35 \
          58  77  93 107 119 130 140 150 158 166 173 180 187 193 199 204 209 214 219 224 228 232 236 240 244 248 251 255",

    # Wind colourbar RGB data recovered from IDL colour file '/home/h06/meso/bin/op_charts/linux/idl/colours/wind2.clr'
    'Wind':
        " 0 250 248 246 244 241 239 236 233 230 227 223 219 215 210 205 200 194 188 181 174 166 157 148 138 127 116 103  90  75  59  43  40  37  34  32  29  26  24  21  18  16 \
          13  10   8   5   2   0  15  30  45  60  75  91 106 121 136 151 167 182 197 212 227 243 243 243 243 243 243 243 243 243 243 243 243 243 243 243 243 243 243 243 243 243 \
         243 243 243 243 243 243 243 243 243 243 243 243 243 243 244 244 244 245 245 246 246 246 247 247 247 248 248 249 249 249 250 250 250 251 251 252 252 252 253 253 253 254 \
         254 255 249 244 239 233 228 223 217 212 207 201 196 191 185 180 175 170 164 159 154 148 143 138 132 127 122 116 111 106 100  95  90  85  79  74  69  63  58  53  47  42 \
          37  31  26  21  15  10   5   0   3   6   9  12  15  19  22  25  28  31  35  38  41  44  47  51  54  57  60  63  66  70  73  76  79  82  86  89  92  95  98 102 105 108 \
         111 114 117 121 124 127 130 133 137 140 143 146 149 153 156 159 162 165 168 172 175 178 181 184 188 191 194 197 200 204 207 210 213 216 219 223 226 229 232 235 239 242 \
         245 248 251 255 \
           0 251 249 248 246 244 243 241 239 236 234 231 228 225 222 218 214 210 205 200 195 189 183 176 169 161 153 144 134 123 112 100 105 111 116 122 127 133 138 144 150 155 \
         161 166 172 177 183 189 193 197 201 205 209 213 217 222 226 230 234 238 242 246 250 255 248 242 236 230 224 218 212 206 200 194 188 182 176 170 164 158 152 146 140 134 \
         128 122 116 110 104  98  92  86  80  74  68  62  62  62  63  63  63  64  64  64  65  65  65  66  66  66  67  67  67  68  68  68  69  69  69  70  70  70  71  71  71  72 \
          72  73  71  69  68  66  65  63  62  60  59  57  56  54  53  51  50  48  47  45  44  42  41  39  38  36  34  33  31  30  28  27  25  24  22  21  19  18  16  15  13  12 \
          10   9   7   6   4   3   1   0   3   6   9  12  15  19  22  25  28  31  35  38  41  44  47  51  54  57  60  63  66  70  73  76  79  82  86  89  92  95  98 102 105 108 \
         111 114 117 121 124 127 130 133 137 140 143 146 149 153 156 159 162 165 168 172 175 178 181 184 188 191 194 197 200 204 207 210 213 216 219 223 226 229 232 235 239 242 \
         245 248 251 255 \
           0 253 252 251 251 250 249 248 247 246 245 244 242 241 240 238 236 234 232 230 228 225 222 219 216 212 209 204 200 195 190 185 173 161 150 138 127 115 104  92  80  69 \
          57  46  34  23  11   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   0   1   1   2   2   3   3   4   4   5   5   6   6   7   7   8   8   8   9   9 \
          10  10  11  11  11  12  12  13  13  14  14  15  22  30  37  45  52  60  67  75  82  90  97 105 112 120 127 135 142 150 157 165 172 180 187 195 202 210 217 225 232 240 \
         247 255 249 244 239 233 228 223 217 212 207 201 196 191 185 180 175 170 164 159 154 148 143 138 132 127 122 116 111 106 100  95  90  85  79  74  69  63  58  53  47  42 \
          37  31  26  21  15  10   5   0   3   6   9  12  15  19  22  25  28  31  35  38  41  44  47  51  54  57  60  63  66  70  73  76  79  82  86  89  92  95  98 102 105 108 \
         111 114 117 121 124 127 130 133 137 140 143 146 149 153 156 159 162 165 168 172 175 178 181 184 188 191 194 197 200 204 207 210 213 216 219 223 226 229 232 235 239 242 \
         245 248 251 255",

    # Visibility colourbar RGB data recovered from IDL colour file '/home/h06/meso/bin/op_charts/linux/idl/colours/myvisib.clr'
    'Vis':
        " 201  232 255 255  54 143 197 255 170 108  13 \
        0    0  151 240 166 220 255 255 232 155  13  \
        255   0   0  97  73  100 197 255 255 205 143 ",
    
    # Precipitation colourbar RGB data recovered from IDL colour file '/home/h06/meso/bin/op_charts/linux/idl/colours/overplot_ppncloud.clr'
    # but with white and aqua added to bottom to reflect extra rainfall information from raingauges
    'Precip':
        "255  51 121  81  40  31 255 255 236 255 220 \
        255 255 178 147 104 201 240 155  50  93 220\
        255 255 233 212 189  27  58   0  27 251 220"
    }
    
datadicts={
    'Temp': {
        'plotType': 'screen temperature',
        'directory': TempObsDir,
        'StartTime': '0000', # 0000Z is used as the default start time
        'obsDataType': 'LANDSYN', 
        'label': 'Temp ($^\circ$C)', 
        'titlesize': 6, 
        'dpi': 162, 
        'min': -45, 
        'max': 45, # min/max = Upper and lower bounds of dataset
        'NumColors': 256, 
        'RGB_Values': RGBVals['Temp'], 
        'ticks': [-45,-40,-35,-30,-25,-20,-15,-10,-5,0,5,10,15,20,25,30,35,40,45],
        'extend': 'both', 
        'labelfontsize': 5 
        },
#    
#    'Wind': {
#        'plotType': 'wind speed',
#        'directory': WindObsDir,
#        'StartTime': '0000', # 0000Z is used as the default start time
#        'obsDataType': 'LANDSYN', 
#        'label': 'Windspeed (knots)', 
#        'titlesize': 5.5, 
#        'dpi': 170, 
#        'min': 0, 
#        'max': 80, # min/max = Upper and lower bounds of dataset
#        'NumColors': 256, 
#        'RGB_Values': RGBVals['Wind'], 
#        'ticks': np.arange(0, 80+1, 10), # 0 and 80 refer to datadicts['Wind']['min'] and datadicts['Wind']['max'] respectively
#        'extend': 'max' 
#        },
#    
#    'Vis': {
#        'plotType': 'visibility',
#        'directory': VisObsDir,
#        'StartTime': '0000', # 0000Z is used as the default start time
#        'obsDataType': 'LANDSYN', 
#        'label': 'Visibility (m)', 
#        'titlesize': 5.5, 
#        'dpi': 170, 
#        'bounds': [0,50,100,200,1000,5000,10000,20000,30000,50000,70000,75001],
#        'NumColors': 11, 
#        'RGB_Values': RGBVals['Vis'], 
#        'ticks': np.arange(0,1,0.0909), 
#        'extend': 'neither',
#        'ticklabels': ['','50m','100m','200m', '1km', '5km', '10km', '20km', '30km', '50km', '70km',''], 
#        'labelfontsize': 5 
#        },
    
    'Precip': {
        'plotType': 'precipitation',
        'directory': PrecipObsDir,
        'StartTime': '0000', # 0000Z is used as the default start time
        'obsDataType': 'SREW', 
        'label': 'Hourly Precip (mm)', 
        'titlesize': 5.5, 
        'dpi': 170, 
        'bounds': [0,0.0001,0.1,0.25,0.5,1,2,4,8,16,32,100],
        'NumColors': 11, 
        'RGB_Values': RGBVals['Precip'], 
        'ticks': np.arange(0,1,0.0906), 
        'extend': 'neither',
        'ticklabels': ['0','>0','0.1-0.25','0.25-0.5','0.5-1', '1-2', '2-4', '4-8', '8-16', '16-32', '32+'], 
        'labelfontsize': 4, 
        'labelrotation': 50 
        }
            
    } # Dictionary of dictionaries containing all relevant info for each type of plot

landsyn_obs_dict={} # Dictionary to store the landsyn data for each day. The keys are dates.
srew_obs_dict={} # Dictionary to store the srew data for each day. The keys are dates.

# Converts the RGB string into a matplotlib colourmap
def Convert_RGB_To_Colourmap(RGB_values,NumColors):   
    a_list = []
    
    for item in RGB_values.split(' '):
        if item != '':
            a_list.append(int(item)/255.)
    
    RGB_array = np.asarray(a_list).reshape(3, NumColors).T
    
    ColourMap=mcolors.ListedColormap(RGB_array)
    
    return ColourMap


def rotate_coords(lat, lon):
    '''takes lat and lon and returns the rotated coordinates with respect to 
    the rotated model grid
    default settings UKV rotated pole'''
          
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    rlon,rlat = iris.analysis.cartography.rotate_pole(lon,lat,Rot_pole_lon,Rot_pole_lat)
     
    return rlat,rlon

# Finds the earliest start time of the different plot types
def getEarliestStartTime():
    startTimeList = []
    
    for Plot in datadicts:
        startTimeList.append(datadicts[Plot]['StartTime'])
        startTimeList.sort()
        
    return startTimeList[0]

# Map projection variables
Rot_pole_lat=37.5
Rot_pole_lon=177.5
 
rotated_pole = ccrs.RotatedPole(pole_latitude=Rot_pole_lat, pole_longitude=Rot_pole_lon)


#################
### Main code ###
#################

#########################################################################################
### Saves and resizes each image at a particular date/time for a particular plot type ###
#########################################################################################
def saveAndResize(dictionary, dt):
    directory = dictionary['directory']
    DateTime=str(dt)
    
    plt.savefig(directory+"/"+DateTime+".png",bbox_inches='tight', dpi=dictionary['dpi'])
    plt.clf()
    
    # Resizes the image so that it matches up to existing forecast plots on website
    Basewidth=512
            
    img = Image.open(directory+"/"+DateTime+".png")
            
    wpercent = (Basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent))) # Changes the height in proportion to width
            
    img = img.resize((Basewidth, hsize), PIL.Image.ANTIALIAS)
    img.save(directory+"/"+DateTime+".png")



###############################
### Plots observations data ###
###############################
# Calls saveAndResize
def plotObsMaps(Plot):
    dictionary = datadicts[Plot]
        
    print "Plotting", dictionary['plotType'], "station observation maps"
        
    # Set colourmaps used in plotting
    this_cmap=Convert_RGB_To_Colourmap(dictionary['RGB_Values'], dictionary['NumColors'])

    for DateTime in dictionary: # Iterates through all dates in dictionary
        if re.match('[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]', DateTime): # To prevent matching non-date keys
            
            DateStr=str(DateTime[0:8])
            TimeStr=str(DateTime[8:])
            
            Data=dictionary[DateTime]

            ax = plt.axes(projection=rotated_pole)
            ax.set_extent([-9.8, 2.6, 48.59, 59.5]) # Sets left, right, bottom and top of image
            ax.coastlines('10m')

            # Iterates through all values and plots each point onto map
            for line in Data:
                Lat=line[1]
                Lon=line[2]
                Val=line[3] # Val = Temp, Wind, Vis, Precip
                            
                rLat, rLon = rotate_coords(Lat,Lon)
                
                if 'min' in dictionary and 'max' in dictionary:
                    minval = dictionary['min']
                    maxval = dictionary['max']
                    Normalize = True # A flag for including min/max parameters

                    # Normalise the value according to max and min values then convert into RGB tuple
                    Norm=(float(Val)-minval)/(maxval-minval)
                    
                elif 'bounds' in dictionary:
                    bounds = dictionary['bounds']
                    Normalize = False # A flag for -not- including min/max parameters
                    
                    # Normalise the data value - there are 11 colours in the map so the normalised value is quantised into 11 levels
                    for i in range(0,len(bounds)-1):
                        
                        if Val >= bounds[i] and Val < bounds[i+1]:
                            Norm=float(i)/11
                            break

                RGB_tuple=this_cmap(Norm) # Convert normalised value into RGB tuple
                
                ax.plot(rLon, rLat, marker='o',color=RGB_tuple)
                
            plt.title(DateStr+"  "+TimeStr, size=dictionary['titlesize'])
            
            if Normalize:
                sm = plt.cm.ScalarMappable(cmap=this_cmap, norm=plt.Normalize(vmin = dictionary['min'], vmax = dictionary['max'])) # The flagged min/max parameters
            else:
                sm = plt.cm.ScalarMappable(cmap=this_cmap)
                
            sm._A=[] # Fake up the array of the scalar mappable
            
            cbar=plt.colorbar(sm, ticks=dictionary['ticks'], orientation='horizontal', shrink=0.40, aspect=30, pad=0.02, extend=dictionary['extend'])
            cbar.set_label(label=dictionary['label'],size=8)
            
            if 'ticklabels' in dictionary:
                cbar.ax.set_xticklabels(dictionary['ticklabels']) # Sets specialised text labels for the tickmarks
                
            if 'labelfontsize' in dictionary:
                for t in cbar.ax.get_xticklabels(): # Loops through the tick labels and changes their font sizes 
                    t.set_fontsize(dictionary['labelfontsize'])
                    if 'labelrotation' in dictionary: # Rotates the tick labels if a value has been supplied
                        t.set_rotation(dictionary['labelrotation'])

            saveAndResize(dictionary, DateTime)



#####################################################################################
### Assigns the required data for each plot type. The data is referenced by date. ###
#####################################################################################
def assignLandsynData(dictionary, date): 
    landsyn_obs = landsyn_obs_dict[date]
    
    # Sorts LANDSYN observations data by datetimes
    for line in landsyn_obs:
        Year=str(line[3])
        Month=("0"+str(line[4]))[-2:] # Pad strings with zeros
        Day=("0"+str(line[5]))[-2:]
        Hour=("0"+str(line[6]))[-2:]
        Minute=("0"+str(line[7]))[-2:]
            
        DateTime=Year+Month+Day+Hour+Minute
        
        # Adds DateTime values to dictionary as key
        if DateTime not in dictionary: dictionary[DateTime] = []

        # Check for masked values before inserting into dictionary
        if line[1] is not np.ma.masked and line[2] is not np.ma.masked:
            if line[8] is not np.ma.masked and dictionary['plotType'] == 'screen temperature': 
                StationData=[int(line[0]), float(line[1]), float(line[2]), float(line[8]-273.15)] # Converts temp from Kelvin to Celsius
                dictionary[DateTime].append(StationData)
            
            if line[9] is not np.ma.masked and dictionary['plotType'] == 'wind speed': 
                StationData=[int(line[0]), float(line[1]), float(line[2]), float(line[9])*1.944] # Converts m/s to knots
                dictionary[DateTime].append(StationData)       
            
            if line[10] is not np.ma.masked and dictionary['plotType'] == 'visibility':
                StationData=[int(line[0]), float(line[1]), float(line[2]), float(line[10])]
                dictionary[DateTime].append(StationData)
          
                    
def assignSrewData(dictionary, date):
    srew_obs = srew_obs_dict[date]
    
    # Sorts SREW observations data by datetimes
    for line in srew_obs:
        Year=str(line[3])
        Month=("0"+str(line[4]))[-2:] #Pad strings with zeros
        Day=("0"+str(line[5]))[-2:]
        Hour=("0"+str(line[6]))[-2:]
        Minute="00"
        
        DateTime=Year+Month+Day+Hour+Minute
        
        # Adds DateTime values to dictionary as key
        if DateTime not in dictionary: dictionary[DateTime] = []
        
        # Check for masked values before inserting into dictionary
        # SREW database also uses values of -1 to indicate trace value and 
        # -9999999 to indicate unmeasurable value or 'NIL' report 
        if line[1] is not np.ma.masked and line[2] is not np.ma.masked:
            if line[7] is not np.ma.masked and float(line[7]) >= 0.0: 
                StationData=[int(line[0]), float(line[1]), float(line[2]), float(line[7])]
                dictionary[DateTime].append(StationData)



####################################################
### Extracts Landsyn and Srew data for each date ###
####################################################
# Calls getEarliestStartTime, assignLandsynData and assignSrewData
def extractData(Date):

    StartTime = getEarliestStartTime() # Checks the start time of each plot dictionary and gets the earliest. 
                                       # This way we can ensure there aren't any missed plots for that date.

    CurrentHour = str( datetime.now() )[11:13]+"00" # Takes the current hour timestamp

    if StartTime == "2400":
        raise Exception ("Already have all images for date "+Date+"")
        
    elif StartTime == CurrentHour:
        raise Exception("Images already up to date for date "+Date+"")
        
    else:
        contact = 'mark.worsfold@metoffice.gov.uk'
        keywords = ['START TIME '+Date+'/'+StartTime+'Z', 'END TIME '+Date+'/2300Z','PLATFORM 03']

        print "Extracting LANDSYN data from MetDB for datetime: "+Date+StartTime+""
        subtype = 'LNDSYN'
        elements = ['WMO_STTN_NMBR','LTTD','LNGD', 'YEAR', 'MNTH', 'DAY','HOUR','MINT','SRFC_AIR_TMPR','SRFC_WIND_SPED', 'HRZL_VSBLY']
        
        try:
            landsyn_obs = metdb.obs(contact, subtype, keywords, elements)
            landsyn_obs_dict[Date] = landsyn_obs # Puts the extracted data in the landsyn dictionary, setting the date as the key
            
        except Exception as e:
            print "MetDB LANDSYN data extraction failed:"
            print e


        print "Extracting SREW data from MetDB for datetime: "+Date+StartTime+""
        subtype = 'SREW'
        elements = ['WMO_STTN_INDX_NMBR','LTTD','LNGD', 'YEAR', 'MNTH', 'DAY','HOUR','Q1HOUR_PRCTN_AMNT']
        
        try:
            srew_obs = metdb.obs(contact, subtype, keywords, elements)
            srew_obs_dict[Date] = srew_obs # Puts the extracted data in the srew dictionary, setting the date as the key
            
        except Exception as e:
            print "MetDB SREW data extraction failed:"
            print e
                    


#################################################
### Sets the time to start plotting maps from ###
#################################################
def setStartTime(dictionary, Date):    
    # Need to inspect folder and see what files have been generated so far - then generate data from this time onwards
    FileTimes=[]
    FileNames = glob.glob(dictionary['directory'] + '/'+Date+'[0-9][0-9][0-9][0-9].png' ) # Returns list of files which sastify the regex
        
    # Extracts only filename and sorts in order
    for File in FileNames:
        FileName = File.split('/')[-1]
        FileTimes.append(int(FileName[8:12]))
    FileTimes.sort()

    if not FileTimes:
        print "No files in", dictionary['plotType'], "folder for date "+Date+" - use 0000Z for start time"
        dictionary['StartTime'] = '0000'
    else:
        # Takes last element in FileTimes (the latest time) and adds an hour to get the start time for the data extraction
        StartTime=FileTimes[-1]+100
        StartTime=str(StartTime)
        StartTime=("0"+str(StartTime))[-4:] #Pad strings with zeros
        dictionary['StartTime'] = StartTime



#####################
### Main function ###
#####################
'''
The function below can be changed depending on the requirements of the code user.
For instance, it's currently set up to plot maps for each plot type given in the datadicts dictionary,
but if you wanted to plot maps for one specific type, you could simply set the Plot varaible to the type name
i.e. Plot = "Vis". NOTE: If doing this, ensure you specify Plot in the getEarliestStartTime() function as well,
otherwise it will check all supplied StartTimes in the dictionary. (Alt, you could specify StartTime in extractData() )
'''
def main():
    for Date in DateList:
        if not re.match(r'[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]', Date): # Checks Date matches expected pattern
            continue
        for Plot in datadicts:
            dictionary = datadicts[Plot]
            # Assigns each plot dictionary a start time for each date in the list (the default being 0000)
            setStartTime(dictionary, Date)
        
        try:
            # Extracts the landsyn/srew data for each day, starting at a specified time   
            extractData(Date)
            
        except Exception as e:
            print e
            continue
        
        for Plot in datadicts:
            dictionary = datadicts[Plot]
            
            if dictionary['obsDataType'] == "LANDSYN": # Temp, Wind, Vis
                # Assigns the extracted landsyn data to each plot dictionary that requires it
                assignLandsynData(dictionary, Date)
                
            elif dictionary['obsDataType'] == "SREW": # Precip
                # Assigns the extracted srew data to each plot dictionary that requires it
                assignSrewData(dictionary, Date)

    for Plot in datadicts:
        plotObsMaps(Plot)
                            
main()
