#!/bin/bash

#----------------------------------------------------------------------------------------------------
# Scriptname:  FIAT_Retrieve_Images.sh
#----------------------------------------------------------------------------------------------------
#
# Description: 
# A script to call various IDL/Python scripts for producing specified data plots
# and store the plots in the supplied directories. These plots will then be
# displayed on the FIAT.html website.
#
#
# Called by:
# FIAT_Control.sh
# 
# Inputs:
# PlotDir       - Directory to store the produced plot images
# Python_Folder - Python code directory
# DateList      - String containing dates in format: "YYYYMMDD YYYYMMDD YYYYMMDD ...."
#                 The code will extract data for these dates
# ExtractAll    - A conditional stating whether to download data/plot images for all supplied dates
#                 or just the most recent date. (0 indicates recent date, 1 indicates all)
# PlotPrecipUKV - A conditional variable stating whether to plot UKV precipitation forecast maps
#                 or to use those that have already been plotted.
#
# Script calls:
# FIAT_make_met_plots_var.pro  - An IDL script that generates UKV and Euro4 precipitation forecasts
# FIAT_Plot_Modified_Fields.py - Generates modified precipitation and temperature forecasts
# FIAT_Plot_StationObs_Maps.py - Generates precipitation and temperature station observation maps
#
#
# Current Owner:  Mark Worsfold (MW)
#
# History:
# Date       Ticket Comment
# ---------- ------ -------
# 
# ---------- ------ End History
#
# End of header -------------------------------------------------------------------------------------

#set -eux

CodeDir=${HOME}/public_html/FIAT/scripts
PythonDir=${HOME}/public_html/FIAT/python
DataDir=/data/local/pclarke/FIATData
#DataDir=/data/nwp1/cfsb/FIAT
mkdir -p ${DataDir}

# Arguments from command line:
PlotDir=$1
Python_Folder=$2
DateList=$3
ExtractAll=$4
PlotPrecipUKV=$5

Obs_Plots=${PlotDir}/Observations
Fcst_Plots=${PlotDir}/Forecasts
ModFcst_Plots=${PlotDir}/ModifiedForecasts

UKV_Fcst_Plots=${Fcst_Plots}/UKV
Euro4_Fcst_Plots=${Fcst_Plots}/Euro4

# Station observation plot directories
Plot_TempStation=${Obs_Plots}/Temp_Station
Plot_PrecipStation=${Obs_Plots}/Precip_Station
mkdir -p ${Plot_TempStation}
mkdir -p ${Plot_PrecipStation}

# Rotated pole forecast directories
Source_Forecasts=/home/h06/dust/public_html/monitoring/Monitoring/project
Plot_UKVPrecipFcst=${UKV_Fcst_Plots}/Precipitation
Plot_Euro4PrecipFcst=${Euro4_Fcst_Plots}/Precipitation
Plot_UKVTempFcst=${UKV_Fcst_Plots}/Temperature
Plot_Euro4TempFcst=${Euro4_Fcst_Plots}/Temperature
Plot_UKVCloudFcst=${UKV_Fcst_Plots}/Cloud
Plot_Euro4CloudFcst=${Euro4_Fcst_Plots}/Cloud
mkdir -p ${Plot_UKVPrecipFcst}
mkdir -p ${Plot_Euro4PrecipFcst}
mkdir -p ${Plot_UKVTempFcst}
mkdir -p ${Plot_Euro4TempFcst}
mkdir -p ${Plot_UKVCloudFcst}
mkdir -p ${Plot_Euro4CloudFcst}


HourNow=$(date +%H) # Finds the hour value
Date=`date +%Y%m%d`

export python=/usr/local/sci/bin/python2.7
export tidl=/usr/local/bin/tidl

# The modified fields are plotted using the TRUI module, so this must be set up beforehand
. ~frtr/trui/vn0.6.2/bin/trui_env.ksh


# Function: Searches and deletes files who's timestamps DON'T match the dates in the DateList
DeleteFiles() {
    eval FileList="$1"

    for File in ${FileList}; do
        Match=0
        for Date in ${DateList}; do
            if [[ ${File} == *${Date}* ]]; then Match=1 ; fi
        done 
        if [ "${Match}" -eq 0 ]; then rm ${File}; fi
    done   
}

# Function: Deletes all folders where the foldernames are NOT in the DateList
DeleteFolders() {
    eval FolderList="$1"
    
    for Folder in ${FolderList}; do
        Match=0
        for Date in ${DateList}; do
            FolderCheck=$(basename "${Folder}")
            if [[ "${FolderCheck}" -eq ${Date} ]];
            then
                Match=1
            fi
        done
        if [ "${Match}" -eq 0 ]; then rm -r ${Folder}; fi
    done
}

# Function: Calculates the model run/date for 7 hours ago
CalculateModelRun() {
    # The Euro4 data takes approximately six hours to be updated, so we check for the file from 7 hours ago
    # (to be on the safe side)
    # Additionally, the Euro4 and modified data is only available for the 00, 06, 12, and 18 model runs.
    # So we calculate which of these times was most recent 7 hours ago
    # I.e. If running the code at 17:00, the closest model run for the data available is 06
    
    getHour=`date -d"7 hours ago" +%-H`
    
    ModelRun=$((${getHour} - $((${getHour} % 6)) )) # Calculate the nearest model run

    if [ "${ModelRun}" -le 6 ]; then # If downloading data for the 00 or 06 model run we need to pad the value with a 0
        ModelRun="0${ModelRun}"
    fi
    
    Date=`date -d"7 hours ago" +%Y%m%d`
}

################################################
### SECTION 1: Deletes old folders and files ###
################################################

# If we're extracting all data then we must run the delete operation whenever we run the code.
if [ "${ExtractAll}" -eq 1 ];
then
    DeleteOldFiles=1
else
    # If we're running the code automatically we only need to delete the old files once a day (at 6am).        
    if [ "${HourNow}" -eq 9 ];
    then
        echo "Running 9am delete operation"
        DeleteOldFiles=1
    else
        DeleteOldFiles=0
    fi
fi

if [ "${DeleteOldFiles}" -eq 1 ];
then

    echo "Removing old modified forecast data"
    ModifiedDataList=$(ls -f ${DataDir}/Modified*/*)
    DeleteFiles "\$ModifiedDataList"

    if [ "${PlotPrecipUKV}" -eq 1 ];
    then
        echo "Removing old UKV data"
        DataFolderList=$(ls -d ${DataDir}/UKV_data/*)
        DeleteFolders "\$DataFolderList"
    fi
    
    echo "Removing old Euro4 data"
    DataFolderList=$(ls -d ${DataDir}/Euro4_data/*)
    DeleteFolders "\$DataFolderList"

    echo "Removing old forecast plots"
    ForecastFolderList=$(ls -d ${Fcst_Plots}/*/*/*)
    DeleteFolders "\$ForecastFolderList"
    
    echo "Removing old modified forecast plots"
    ModifiedForecastFolderList=$(ls -d ${ModFcst_Plots}/*/*)
    DeleteFolders "\$ModifiedForecastFolderList"
    
    echo "Removing old observation plots"
    ObservationFileList=$(ls -f ${Obs_Plots}/*/*)
    DeleteFiles "\$ObservationFileList"
    
fi
    
##########################################################
### SECTION 2: Sets up dates for which to extract data ###
##########################################################

# Synchonising or even listing the files in some of the folders takes a very long time
# due to the number of files. Synchonising all dates is unecessary when the code is running 
# hourly so we only need to use the last date. However - if we are running the code afresh, 
# we need to populate the folders for all dates. Hence the "ExtractAll" conditional.

DateListArray=(${DateList}) # Turns DateList into an array for use in VerPy plotting code

if [ "${ExtractAll}" -eq 1 ];
then
    echo "Extract data for all days ${DateList}"
else 
    # Remove the last element from DateList
    LastDateEl=$(echo ${DateList} | rev | cut -d" " -f1 | rev)
    DateList=${LastDateEl}
    
    echo "Extract data for last day only: ${LastDateEl}"
fi


##############################################################################
### SECTION 1: Create modified forecasts for precipitation and temperature ###
##############################################################################

# Function: Creates modified forecasts for the specified data type, date, and model run
CreateModifiedForecasts() {    
    Modified_DataDir=${DataDir}/Modified_${DataType}_data
    mkdir -p ${Modified_DataDir}    
    
    Modified_PlotDir=${ModFcst_Plots}/Modified_${DataType}/${Date}/${ModelRun}Z
    mkdir -p ${Modified_PlotDir}

    ModifiedFiles=`ls -1 ${Modified_DataDir}/U_Live_Euro4kmModified_${Date}${ModelRun}00_*${DataType}_U_*.grb | wc -l`

    if [ "${DataType}" == "Rain_Rate" ] || [ "${DataType}" == "Cloud" ] && [[ "${ModifiedFiles}" -lt 110 ]]; # There are at least 55 dynamic and 55 convective data files
    then
        echo "Downloading ${DataType} data from server for ${Date}${ModelRun}00" # We want to download both Convective_Rain_Rate and Dynamic_Rain_Rate data files
        scp cfsb@exxvmverappop:/data/verify/in/appdata/ModField/U_Live_Euro4kmModified_${Date}${ModelRun}00_*${DataType}_U_??.grb.gz ${Modified_DataDir}/
        gunzip -f ${Modified_DataDir}/*${Date}${ModelRun}00_*.gz
    else
        if [ "${DataType}" != "Rain_Rate" ] && [[ "${ModifiedFiles}" -lt 55 ]]; # If we're missing data files, download them.
        then
            echo "Downloading ${DataType} data from server for ${Date}${ModelRun}00"
            scp cfsb@exxvmverappop:/data/verify/in/appdata/ModField/U_Live_Euro4kmModified_${Date}${ModelRun}00_${DataType}_U_??.grb.gz ${Modified_DataDir}/
            gunzip -f ${Modified_DataDir}/*${Date}${ModelRun}00_${DataType}*.gz
        else
            echo "Already downloaded all ${DataType} data files for ${Date}${ModelRun}00"
        fi
    fi

    NumberOfFiles=`ls -1 "${Modified_PlotDir}" | wc -l`
    
    # The modified forecast is produced up to t+60h (t+54 for the 12Z model run), so there should be 61 (or 55) plotted images for each model run. This also stops Rain Rate being plotted twice.
    if [[ "${NumberOfFiles}" -ne 61 ]] && [[ "${NumberOfFiles}" -ne 55 ]];
    then        
        # DataType, Date and ModelRun are used by the python code to create a regex and the code plots any files in ${Modified_DataDir} found to match this regex
        $python ${PythonDir}/FIAT_Plot_Modified_Fields.py "${Modified_DataDir}" "${Modified_PlotDir}" "${DataType}" "${Date}" "${ModelRun}"
    else
        echo "Already created all plots for ${DataType} ${Date}${ModelRun}00"
    fi
}


Modified_ModelRuns=(00 06 12 18) # Modified data is only available for these model runs
Modified_DataTypes=('Rain_Rate' 'Temperature_1p5m' 'Cloud')

for DataType in "${Modified_DataTypes[@]}";
do
    echo ""
    # If running from scratch we need to create all possible plots
    if [ "${ExtractAll}" -eq 1 ];
    then
        echo "Plotting ${DataType} modified forecasts for all dates and model runs."    

        for Date in ${DateList[@]};
        do
            for ModelRun in "${Modified_ModelRuns[@]}";
            do
                CreateModifiedForecasts
            done
        done
    else
        # If running the control script hourly we only need to create the most recent plots
        
        CalculateModelRun # This returns a date and model run from 7 hours ago (see function comments for explanation)
        echo "Plotting ${DataType} modified forecasts for ${Date}${ModelRun}"
        CreateModifiedForecasts
    fi
done    

#################################################################################
### SECTION 2: Creates temperature and precipitation station observation maps ###
#################################################################################
echo ""
echo "Generating temperature and precipitation station observations maps"

$python ${Python_Folder}/FIAT_Plot_StationObs_Maps.py "${DateList}" "${Plot_TempStation}" "${Plot_PrecipStation}"


#############################################################
### SECTION 3: Extracts UKV/Euro4 rotated pole forecasts  ###
#############################################################
echo ""
echo "Extracting precipitation UKV/Euro4 forecasts"

# Function to crop the 'Snowfall Rate' and 'Cloud Fraction' colour bars from the precipitation plots
CropPrecipitationPlots() {
    eval FileList="$1"
    
    for File in ${FileList[@]};
    do
        ImageWidth=$(identify -format "%w" ${File})
        if [ "${ImageWidth}" -gt 567 ];
        then
            convert $File -crop 797x993-115-288 $File; # removes 115 pixels from the right, 288 from the bottom
            convert $File -crop 797x993+115+0 $File; # removes 115 pixels from the left, 0 from the top
        fi
    done
}

# Function to remove the cloud colour bar (this is added to the webpage manually)
CropCloudPlots() {
    eval FileList="$1"
    
    for File in ${FileList[@]};
    do
        ImageWidth=$(identify -format "%w" ${File})
        if [ "${ImageWidth}" -gt 598 ];
        then
            convert $File -crop 683x1011-0-200 $File; # removes 200 pixels from the bottom
            convert $File -crop 683x1011+85 $File; # removes 85 pixels from the left
        fi
    done  
}

ExtractForecasts() {
    mkdir -p ${Plot_UKVPrecipFcst}/${Date}/${ModelRun}Z
    mkdir -p ${Plot_Euro4PrecipFcst}/${Date}/${ModelRun}Z
    
    # Precipitation (UKV model)
    rsync --quiet --ignore-existing --include="PmslZRnSnCl_oper-ukv_*_UKrot.png" --exclude="*" ${Source_Forecasts}/ukv/${Date}_${ModelRun}Z/* ${Plot_UKVPrecipFcst}/${Date}/${ModelRun}Z
    # Precipitation (Euro4 model)
    rsync --quiet --ignore-existing --include="PmslZRnSnCl_oper-eur_*_UKrot.png" --exclude="*" ${Source_Forecasts}/eur/${Date}_${ModelRun}Z/* ${Plot_Euro4PrecipFcst}/${Date}/${ModelRun}Z
    
    # Crop UKV precipitation plots
    FileList=(`ls ${Plot_UKVPrecipFcst}/${Date}/${ModelRun}Z/*.png`)
    CropPrecipitationPlots "\$FileList"
    
    # Crop Euro4 precipitation plots
    FileList=(`ls ${Plot_Euro4PrecipFcst}/${Date}/${ModelRun}Z/*.png`)
    CropPrecipitationPlots "\$FileList"
    
    mkdir -p ${Plot_UKVTempFcst}/${Date}/${ModelRun}Z    
    mkdir -p ${Plot_Euro4TempFcst}/${Date}/${ModelRun}Z
    
    # Temperature (UKV model)
    rsync --quiet --ignore-existing --include="T_surf_oper-ukv_*_UKrot.png" --exclude="*" ${Source_Forecasts}/ukv/${Date}_${ModelRun}Z/* ${Plot_UKVTempFcst}/${Date}/${ModelRun}Z
    # Temperature (Euro4 model)
    rsync --quiet --ignore-existing --include="T_surf_oper-eur_*_UKrot.png" --exclude="*" ${Source_Forecasts}/eur/${Date}_${ModelRun}Z/* ${Plot_Euro4TempFcst}/${Date}/${ModelRun}Z
    
    mkdir -p ${Plot_UKVCloudFcst}/${Date}/${ModelRun}Z
    mkdir -p ${Plot_Euro4CloudFcst}/${Date}/${ModelRun}Z
    
    # Cloud cover (UKV model)
    rsync --quiet --ignore-existing --include="cloud_oper-ukv_*_UKrot.png" --exclude="*" ${Source_Forecasts}/ukv/${Date}_${ModelRun}Z/* ${Plot_UKVCloudFcst}/${Date}/${ModelRun}Z
    # Cloud cover (Euro4 model)
    rsync --quiet --ignore-existing --include="cloud_oper-eur_*_UKrot.png" --exclude="*" ${Source_Forecasts}/eur/${Date}_${ModelRun}Z/* ${Plot_Euro4CloudFcst}/${Date}/${ModelRun}Z
    
    # Crop UKV cloud plots
    FileList=(`ls ${Plot_UKVCloudFcst}/${Date}/${ModelRun}Z/*.png`)
    CropCloudPlots "\$FileList"
    
    # Crop Euro4 cloud plots
    FileList=(`ls ${Plot_Euro4CloudFcst}/${Date}/${ModelRun}Z/*.png`)
    CropCloudPlots "\$FileList"
}

ModelRuns=(00 06 12 18)

for Date in ${DateList[@]};
do
    if [ "${ExtractAll}" -eq 1 ];
    then
        for ModelRun in ${ModelRuns[@]};
        do
            ExtractForecasts
        done
    else
        CalculateModelRun
        ExtractForecasts
    fi
done

