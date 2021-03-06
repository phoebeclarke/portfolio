#!/bin/bash

#----------------------------------------------------------------------------------------------------
# Scriptname:  FIAT_Control.sh
#----------------------------------------------------------------------------------------------------
#
# Description: 
# There's three main components to the script:
# SECTION 1: Scans the meso folders for the dates to plot images.
#            (Produces a list of X previous dates, where X is specified with NumDays)
# SECTION 2: Creates a date string and a PlotPrecipUKV string and writes them both
#            to the Javascript webpage file (as specified by $WebPage)
# SECTION 3: Calls the image retrieval script and supplies it with conditional variables
#
#
# Script calls:
# FIAT_Retrieve_Images.sh - Produces images required for the website
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

Exec_Folder=${HOME}/public_html/FIAT

Script_Folder=${Exec_Folder}/scripts
Python_Folder=${Exec_Folder}/python

### NOTE: When running this code on standalone PC - the html folder and Plot_Folder need 
### to BOTH be in public_html BUT when running code on a server - we can just use 
### symbolic links from the public_html directory to Web_Folder and Plot_Folder
Web_Folder=${Exec_Folder}/html
Plot_Folder=${Exec_Folder}/FIATPlots

WebPage=${Web_Folder}/js/fiatscript.js
ImageRetrievalCode=${Script_Folder}/FIAT_Retrieve_Images.sh
ScanDir=/project/meso_charts/ukv_charts # Looks in this folder for date/modelrun info

NumDays=4
PlotPrecipUKV=1

DateModelRun_Str=""
DateList=""

echo "Running FIAT_Control.sh at time: " `date`

# Function: Uses list of dates to create date/model run string for insertion into web page
CreateDateModelRunString () {
    eval DateList="$1"
    # The Euro4 and Modified plots are only avialable for certain model runs
    ModelRuns=(00Z 06Z 12Z 18Z)
    
    NumDays=$(echo "${DateList}" | wc -w) #Finds number of elements in DateList

    DateModelRun_Str="DateModelRun={"

    i=0
    for Date in ${DateList}; do
        ModelRunList=()
        DateModelRun_Str+="'"${Date}"':"

        Year=${Date:0:4}
        Month=${Date:4:2}
        Day=${Date:6:2}

        for MR in ${ModelRuns[@]}; do
            if [ -e ${ScanDir}/${Day}${Month}${Year}/$MR ]; then
                ModelRunList+=$MR' '
            fi
        done        
        
        #ModelRunList=$(ls ${ScanDir}/${Day}${Month}${Year} ) #Searches within date folder for available model runs
        ModelRunList=$(echo $ModelRunList | sed -r 's/ /,/g') #Fill out whitespaces with commas

        DateModelRun_Str+="'"${ModelRunList}"'"

        if [ "$i" -ne  "${NumDays}" ]; then DateModelRun_Str+=","; fi # Appends comma unless last element in array
        
        i=$((i + 1))
    done

    DateModelRun_Str+="}"

}


# Function: Inserts the given string into a webpage between the two "STRING INSERTION SECTION" lines
# NOTE: This function assumes that the two string insertion section lines in the WEBPAGE have 
# the javascript comment character - "//" prepended to them
InsertStringIntoWebpage () {
    eval Web_Page="$1"
    InsertionLine_Start=$2
    InsertionLine_End=$3
    eval Insert_String="$4"

    StartStringExist=$(grep -Fx "//${InsertionLine_Start}" ${Web_Page})  #Checks that these lines exist in webpage
    EndStringExist=$(grep -Fx "//${InsertionLine_End}" ${Web_Page})

    if [[ "$StartStringExist" && "$EndStringExist" ]];
    then
        sed -i "/\/\/${InsertionLine_Start}/,/\/\/${InsertionLine_End}/"'{//!d}' ${Web_Page} #Deletes lines in between insertion lines

        sed -i "s/\/\/${InsertionLine_Start}/&\n/g" ${Web_Page} #Inserts newline character

        sed -i "/\/\/${InsertionLine_Start}/a\ ${Insert_String}" ${Web_Page} # Inserts string into insertion section

        sed -i "s/\/\/${InsertionLine_Start}/&\n/g" ${Web_Page}
    else
        echo "Cannot insert string - insertion section lines not found in webpage"  
        return 1
    fi
}

#####################################################################################################################################
### SECTION 1: Scan directories and finds list of most recent dates to process                                                    ###
#####################################################################################################################################
# Creates list of folders in directory "ScanDir" and uses this to generate "DateFolderList" then sorts through 
# DateFolderList to find the most recent folder dates (can't just take last values from "DateFolderList" - not reliable method)

echo "Compiling date list for previous ${NumDays} days by scanning forecast data directories"

DateFolderList=$(ls -d ${ScanDir}/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9])

MostRecentDate=$(date --date "20000101" +%s) #Initialises most recent date

for DateFolder in ${DateFolderList}; do

    DateFolder=${DateFolder##*/} #This slice command returns all characters from the last '/' character

    # The dates used for the forecast folder names are in the format DDMMYYYY not YYYYMMDD
    Year=${DateFolder:4:4}
    Month=${DateFolder:2:2}
    Day=${DateFolder:0:2}

    FileDate=$(date --date $Year$Month$Day +%s)

    if [ "$FileDate" -ge "$MostRecentDate" ]; then MostRecentDate=$FileDate; fi

done


# Rewinds from present date to $NumDays days ago - the dates must be in reverse order for the website
# Saves the most recent $NumDays into $DateList
for ((i=$((NumDays-1)); i>=0; i-=1)); do

    if [ "$i" -lt "${NumDays}" ]; 
    then
        DateList+=$(date -d @$((MostRecentDate-(86400*$i))) +%Y%m%d)" ";
    fi
    
done

#############################################################################################################################
### SECTION 2: Creates and writes various strings to the webpage                                                          ###
#############################################################################################################################
echo "Creating date/model run string for insertion into javascript file"

if [[ -e ${WebPage} ]];
then
    CreateDateModelRunString "\${DateList}"

    InsertStringIntoWebpage "\${WebPage}" "START DATE STRING INSERTION SECTION" "END DATE STRING INSERTION SECTION" "\${DateModelRun_Str}"
else
    echo "Web page ${WebPage} not found - cannot insert datestring"
fi

# Whilst UFO_VT is operational we can simply use the UKV forecasts already stored on the meso server.
# However at some point we may wish to plot our own UKV images, in which case the directory will be changed
# The "PlotPrecipUKV" conditional is used to set the directory path for the forecast image sources
# The conditional is set above and used in the FIAT_Retrieve_Images script, and the fiatscript JavaScript file

echo "Writing UKV plotting conditional to webpage"

PlotPrecipUKV_Str="var PlotPrecipUKV = "${PlotPrecipUKV}";"

if [[ -e ${WebPage} ]]; then
    InsertStringIntoWebpage "\${WebPage}" "START UKV PLOT INSERTION SECTION" "END UKV PLOT INSERTION SECTION" "\${PlotPrecipUKV_Str}"
else
    echo "Web page ${WebPage} not found - cannot insert datestring"
fi    

####################################################################################################################
### SECTION 3: Calls/sends information to image retrieval code                                                   ###
####################################################################################################################
# We want to produce forecast and obs plots for past $NumDays days ago 
# HOWEVER - this is unnecessary if we are running the code hourly - therefore 
# we have an "ExtractAll" conditional in the "FIAT_Retrieve_Images.sh" code. 
# When ExtractAll=1 we extract data for all dates, when ExtractAll=0 (default) we only extract data for the last day
# We also have a PlotPrecipUKV conditonal that states whether to plot UKV precip forecasts or use existing

ExtractAll=0

echo "Sending information to image retrieval script"
. ${ImageRetrievalCode} ${Plot_Folder} ${Python_Folder} "${DateList}" ${ExtractAll} ${PlotPrecipUKV}


echo "FIAT_Control.sh completed at time: " `date`
