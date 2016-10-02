#!/usr/bin/env python

#-------------------------------------------------------------------------------
# Scriptname:  FIAT_Plot_Modified_Fields.py
#-------------------------------------------------------------------------------
#
# Description:
# Generates hourly precipitation (rain rate) and temperature modified forecast maps
# Scans data directory for data files to be plotted
# Then creates the colour map for that specific plot type and reads data cubes in from the files
# The cube data is then converted depending on the data type, and plotted to a map
# This plotted image is saved in a directory specified by the user on the command line
#
# The model to plot by can be specified in the dictionary for each data type.
# The values for this model must then be specified in the ModelVals dictionary.
#
# Called by:
# FIAT_Retrieve_Images.sh
# 
# Inputs:
# datadir  - Directory containing GRIB data files to plot
# plotdir  - Plot images into this folder
# filetype - Type of GRIB file to plot
# date     - Date to plot
# modelrun - Model run to plot
#
# Current Owner:  Mark Worsfold
#
# History:
# Date       Ticket Comment
# ---------- ------ -------
# 10/08/2016        Original script - Phoebe Clarke and Mark Worsfold
# ---------- ------ End History
#
# End of header ----------------------------------------------------------------


from matplotlib.colors import LinearSegmentedColormap
import matplotlib
matplotlib.use('Agg') # Allows images to be generated without having a window appear;
                      # prevents runtime errors when running the script through a crontab
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import iris
import iris.plot as iplt

import numpy as np

import glob
import argparse

import trui
from trui.meanplot.ext_matplotlib import HEX_DGREY, segment2list, lsm2list, ColourbarFormatter
from trui.trui_regrid_file import template_cube_from_predefined_grids, guess_bounds_for_regrid

trui.loadct_all()

from pylab import *
from numpy import *


class nlcmap(LinearSegmentedColormap):
    """Used to create a nonlinear colormap"""
    
    name = 'nlcmap'
    
    def __init__(self, cmap, levels):
        self.cmap = cmap
        self.N = cmap.N
        self.monochrome = self.cmap.monochrome
        self.levels = asarray(levels, dtype='float64')
        self._x = self.levels / self.levels.max()
        self._y = linspace(0.0, 1.0, len(self.levels))
    
    def __call__(self, xi, alpha=1.0, **kw):
        yi = interp(xi, self._x, self._y)
        return self.cmap(yi, alpha)


parser = argparse.ArgumentParser() #Read arguments from command line
parser.add_argument("datadir", type=str, help="Directory containing GRIB data files to plot")
parser.add_argument("plotdir", type=str, help="Plot images into this folder")
parser.add_argument("filetype", type=str, help="Type of GRIB file to plot")
parser.add_argument("date", type=str, help="Date to plot")
parser.add_argument("modelrun", type=str, help="Model run to plot")
args = parser.parse_args()

DataDir=str(args.datadir)
PlotDir=str(args.plotdir)
FileType=str(args.filetype) # File name type: "Dynamic_Rain_Rate"
Date=str(args.date)         # Format: YYYYMMDD format
ModelRun=str(args.modelrun) # Format: number with leading zeros eg. "00" or "18" etc.

#print "Recieved arguments: DataDir="+DataDir+" PlotDir="+PlotDir+" FileType="+FileType+" Date="+Date+" ModelRun="+ModelRun+"" # For testing

# Converts the RGB string into a matplotlib colourmap
def Convert_RGB_To_Colourmap(RGB_values,NumColors):   
    a_list = []
    
    for item in RGB_values.split(' '):
        if item != '':
            a_list.append(int(item)/255.)
    
    RGB_array = np.asarray(a_list).reshape(3, NumColors).T
    
    ColourMap=mcolors.ListedColormap(RGB_array)
    
    return ColourMap


# Converts the data units depending on the plot type
def ConvertData(plotType, data):
    if plotType == "Rain_Rate":
        # The rainfall data is kg/m2 per second. So need to multiply by 3600 to get kg/m2 per hour.
        return data*3600
        
    elif plotType == "Temperature_1p5m":
        # Converts temperature from Kelvin to Degrees
        return data-273.15


# The red, green, blue values for creating colour maps
RGBVals = {
    # Temperature colourbar RGB data recovered from IDL colour file '/home/h06/meso/bin/op_charts/linux/idl/colours/myT2_glob.clr'
    'Temperature_1p5m':
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
          58  77  93 107 119 130 140 150 158 166 173 180 187 193 199 204 209 214 219 224 228 232 236 240 244 248 251 255"
}


# Precipitation colourbar RBG data recovered from IDL colour file ''/home/h06/meso/bin/op_charts/linux/idl/colours/overplot_ppncloud.clr'
Precip_cdict = {
    'blue': [(0.0, 0.9137254901960784, 0.9137254901960784), (0.14285714285714285, 0.83137254901960778, 0.83137254901960778), (0.2857142857142857, 0.74117647058823533, 0.74117647058823533), (0.42857142857142855, 0.10588235294117647, 0.10588235294117647), (0.5714285714285714, 0.22745098039215686, 0.22745098039215686), (0.71428571428571419, 0.0, 0.0), (0.8571428571428571, 0.10588235294117647, 0.10588235294117647), (1.0, 0.98431372549019602, 0.98431372549019602)],
    'green': [(0.0, 0.69803921568627447, 0.69803921568627447), (0.14285714285714285, 0.57647058823529407, 0.57647058823529407), (0.2857142857142857, 0.40784313725490196, 0.40784313725490196), (0.42857142857142855, 0.78823529411764703, 0.78823529411764703), (0.5714285714285714, 0.94117647058823528, 0.94117647058823528), (0.71428571428571419, 0.60784313725490191, 0.60784313725490191), (0.8571428571428571, 0.19607843137254902, 0.19607843137254902), (1.0, 0.36470588235294116, 0.36470588235294116)],
    'red': [(0.0, 0.47450980392156861, 0.47450980392156861), (0.14285714285714285, 0.31764705882352939, 0.31764705882352939), (0.2857142857142857, 0.15686274509803921, 0.15686274509803921), (0.42857142857142855, 0.12156862745098039, 0.12156862745098039), (0.5714285714285714, 1.0, 1.0), (0.71428571428571419, 1.0, 1.0), (0.8571428571428571, 0.92549019607843142, 0.92549019607843142), (1.0, 1.0, 1.0)]
}


# A dictionary containing all necessary information for each plot type
PlotTypeDict = {
    'Rain_Rate': {
        'Search_File_Type': 'Dynamic_Rain_Rate',
        'Num_Colours': None, # Not needed to create the colour map for this plot type
        'Cube1': None, # This is assigned later
        'Colour_Map': '', # This is assigned later
        'Colour_Levels': [0.1,0.25,0.5,1,2,4,8,16,32],
        'Colourbar' : 'disabled',
        'Tick_Marks': ['0.1-0.25','0.25-0.5', '0.5-1', '1-2', '2-4', '4-8', '8-16', '16-32'],
        'Cbar_Label': 'Rainfall (mm)',
        'bbox_inches': 'tight',
        'dpi': 200,
        'Plot_Model': 'UKV'
    },
    'Temperature_1p5m': {
        'Search_File_Type': 'Temperature_1p5m',
        'Num_Colours': 256,
        'Cube1': None, # This is assigned later
        'Cube2': None,
        'Colour_Map': '', # This is assigned later
        'Colour_Levels': range(-45,46),
        'Colourbar' : 'disabled',
        'Tick_Marks': '', # Not needed to create the colour map for this plot type
        'Cbar_Label': '2 metre surface Temp (C)',
        'bbox_inches': 'tight',
        'dpi': 200,
        'Plot_Model': 'UKV'
    },
    'Cloud': {
        'Search_File_Type': 'Low_Cloud',
        'Cube1': None, # This is assigned later
        'Cube2': None,
        'Cube3': None,
        'levels': np.array([0.05, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]),
        'bbox_inches': 'tight',
        'dpi': 200,
        'Plot_Model': 'UKV'
    }
}


CloudCmapDict = {
    'low_cloud': {'CubeName': 'Cube1',
                  'zorder': 3,
                  'cmap': 'RedAlpha',
                  'cbar label': 'Low Cloud Fraction (Octas)'},
    'mid_cloud': {'CubeName': 'Cube2',
                  'zorder': 4,
                  'cmap': 'GrnAlpha',
                  'cbar label': 'Mid-level Cloud Fraction (Octas)'},
    'high_cloud': {'CubeName': 'Cube3',
                   'zorder': 5,
                   'cmap': 'BluAlpha',
                   'cbar label': 'High Cloud Fraction (Octas)'}
}



# A dictionary to define the model being plotted
ModelVals = {
    'UKV': {
        'Pole_latitude': 37.5,
        'Pole_longitude': 177.5,
        'Image_extent': [-9.8, 2.6, 48.59, 59.5],
        'Coastline_size': '10m'
    }
}


# Plots each cube and saves the image
def PlotCube(dictionary, File):
    print "Plotting data file: ", File

    ForecastHr=File[-6:-4] # Takes forecast hour from filename

    PlotName = PlotDir + "/" + FileType + "_" + ForecastHr + ".png"

    Model = ModelVals[dictionary['Plot_Model']]

    rotated_pole = ccrs.RotatedPole(pole_latitude=Model['Pole_latitude'], pole_longitude=Model['Pole_longitude'])
    ax = plt.axes(projection=rotated_pole)
    ax.set_extent(Model['Image_extent']) # Sets left, right, bottom and top of image to match the ones in the UKV model
    ax.coastlines(Model['Coastline_size'])
  
    # Use TRUI module to plot cloud cover colourbar
    if (FileType == "Cloud"):

        pcms = {}
        cmaps = {}
        norms = {}

        for plot_feature in sorted(CloudCmapDict.keys()):

            cmaps[plot_feature] = segment2list(plt.cm.get_cmap(CloudCmapDict[plot_feature]['cmap']), dictionary['levels'].size, bad_colour=HEX_DGREY)
            
            # make a normalisation:
            norms[plot_feature] = matplotlib.colors.BoundaryNorm(dictionary['levels'], dictionary['levels'].size-1)

            # low_cloud is named "Cube1", medium cloud = Cube2 etc.
            CubeName = CloudCmapDict[plot_feature]['CubeName']

            # Uses Iris to create a matplotlib plot object for each cloud type
            pcms[plot_feature] = iplt.pcolormesh(dictionary[CubeName], \
                                 cmap=cmaps[plot_feature], \
                                 norm=norms[plot_feature], rasterized=True, \
                                 zorder=CloudCmapDict[plot_feature]['zorder'], \
                                 antialiased=True, \
                                 edgecolor=(1.0,1.0,1.0,0.0), linewidth=0.0000001)

            # Prevents the axes being moved about when things are overplotted:    
            plt.autoscale(False)

    else:
        image = iplt.contourf(dictionary['Cube1'], dictionary['Colour_Levels'], cmap = dictionary['Colour_Map'])

        if (dictionary['Colourbar'] == 'enabled'):
            # Sets colourbar and tickmarks (if applicible)
            cbar = plt.colorbar(image)
        
            if dictionary['Tick_Marks'] != '':
                cbar.ax.set_yticklabels(dictionary['Tick_Marks'])

            cbar.set_label(dictionary['Cbar_Label'])

    plt.title(""+Date+" Run "+ModelRun+"Z Forecast "+ForecastHr+"")

    plt.savefig(PlotName, bbox_inches = dictionary['bbox_inches'], dpi = dictionary['dpi'])
    plt.clf() # Clears the previous figure - prevents multiple plots being saved on top of each other.


# Main function to coordinate loading files, assigning relevant information, and plotting the data
def main():
    # Assigns the dictionary according to the file type to be plotted
    dictionary = PlotTypeDict[FileType]
    
    # Creates a list of the available data files to be plotted
    FileNames = glob.glob(DataDir + "/U_Live_Euro4kmModified_" + Date + ModelRun+"00_" + dictionary['Search_File_Type'] + "_U_[0-9][0-9].grb")
    FileNames.sort()

    # If there's no data available the script ends
    if not FileNames:
        print "No filenames found for regex - exiting"
        exit()

    # Creates the colour map for the plot type
    if (FileType == "Rain_Rate"):
        Precip_Levels = [0.1,0.25,0.5,1,2,4,8,16,32]
        Precip_cmap = mpl.colors.LinearSegmentedColormap('my_colormap', Precip_cdict, 256)

        # Precipitation levels are non linear (1,2,4 etc) - so need to create a non-linear colourmap
        dictionary['Colour_Map'] = nlcmap(Precip_cmap, Precip_Levels)
        
    elif (FileType == "Temperature_1p5m"):
        dictionary['Colour_Map'] = Convert_RGB_To_Colourmap(RGBVals[FileType], dictionary['Num_Colours'])
    
    # Loops through the list of available files to be plotted
    for File in FileNames:

        # Assigns the cube from the file and converts the data depending on the type
        dictionary['Cube1'] = iris.load(File)[0]

        ForecastHr=File[-6:-4] # Takes forecast hour from filename

        # If plotting rain rate there are two data files needed to create each plot
        if (FileType == "Rain_Rate"):
            dictionary['Cube1'].data = ConvertData(FileType, dictionary['Cube1'].data)

            # Finds name of convective rainfall data file
            ConvectiveRainFile = DataDir+"/U_Live_Euro4kmModified_"+Date+ModelRun+"00_Convective_Rain_Rate_U_"+ForecastHr+".grb"

            # Loads the convective cube and converts the data
            dictionary['Cube2'] = iris.load(ConvectiveRainFile)[0]
            dictionary['Cube2'].data = ConvertData(FileType, dictionary['Cube2'].data)

            # Adds the convective raindata to the dynamic rainfall data cube
            dictionary['Cube1'].data = dictionary['Cube1'].data + dictionary['Cube2'].data

        elif (FileType == "Temperature_1p5m"):
            dictionary['Cube1'].data = ConvertData(FileType, dictionary['Cube1'].data)
        
        # Cloud Cover has 3 data types which must be saved separately
        elif (FileType == "Cloud"):

            # Finds name of medium and high level cloud data files
            MediumCloudFile = DataDir+"/U_Live_Euro4kmModified_"+Date+ModelRun+"00_Med_Cloud_U_"+ForecastHr+".grb"
            HighCloudFile = DataDir+"/U_Live_Euro4kmModified_"+Date+ModelRun+"00_High_Cloud_U_"+ForecastHr+".grb"

            # Loads the medium and high level cloud cubes
            dictionary['Cube2'] = iris.load(MediumCloudFile)[0]
            dictionary['Cube3'] = iris.load(HighCloudFile)[0]

        # Plots the cube and saves the image
        PlotCube(dictionary, File)
            
main()            
