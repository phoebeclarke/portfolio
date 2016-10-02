//----------------------------------------------------------------------------------------------------
// Scriptname:  fiatscript.js
//----------------------------------------------------------------------------------------------------
//
// Description:
// Provides all Javascript functions for the FIAT.html website, for handling user input.
//
// Current Owner:  Mark Worsfold (MW)
//
// History:
// Date       Ticket Comment
// ---------- ------ -------
// 
// ---------- ------ End History
//
// End of header -------------------------------------------------------------------------------------

// START General scripting container
var windowLoaded = function() {
    DrawTabs();
    DrawFcstBtns();
    DrawHourSelectBtns();
    DrawSliderButton();
    DrawModelRunDropdown();
    PopulateDateSelect();
    init();
};

$(document).ready(windowLoaded);
$(document).on('page:load', windowLoaded); // Classic Turbolinks
$(document).on('page:change', windowLoaded);

//START UKV PLOT INSERTION SECTION

 var PlotPrecipUKV = 1;

//END UKV PLOT INSERTION SECTION

var FIATBaseURL = 'FIATPlots';
var UFOBaseURL = 'http://www-nwp/~meso/UFO_VT';
var iconFolder = "/assets/fiat/icons/";
var imageFolder = "/assets/fiat/";

var MAXFORECASTVAL = 120; // How many forecast hour buttons will be drawn (the max t+Xh)
var FcstInfo;

var selectedTab;
var tab;
var paneContainer;

var chosenModel = "Euro4"; // This sets the default chosen model to display when the website loads
var SliderEnabled = 0; // By default the slider is disabled
var cloudObsType = "Cloud/EHEA11";

var allFcstBtns;
var UKVBtn;
var Euro4Btn;
var sliderButton;

var dateDropdown;
var modelRunDropdown;
var selectedDateIndex;
var selectedModelRunIndex;

var selectedDate;
var Year;
var Month;
var Day;
var monthInText;
var dayInText;
var ModelRunStr = "";
var ModelRun;
var hourOffsetIdStr = "";
var hourOffsetId;
var paddedhourOffsetIdStr = "";
var forecastDate;
var obsDate;
var Time;

var DateModelRun = {};
var DateStr = "";

//START DATE STRING INSERTION SECTION

 DateModelRun={'20160823':'00Z,06Z,12Z,18Z','20160824':'00Z,06Z,12Z,18Z','20160825':'00Z,06Z,12Z,18Z','20160826':'00Z,06Z',}

//END DATE STRING INSERTION SECTION

/*
Below is a dictionary of dictionaries containing all information about each individual tab.
In terms of HTML, each tab is a <div> with the class "tab". These are all placed
inside a parent div with the id "tabs". Each tab has an id that denotes the contents
of the tab. I.e. the cloud tab will have id="Cloud". The id is displayed as text inside
the tab, so the user knows what they're selecting. The id is set in DrawTabs().
The 'imgIds' arrays contain the html ids of all of the images; the number of image elements
create for the tab pane is decided based on the length of these arrays (see DrawPaneContent()).
Each image element is then assigned an id from the array and added to the webpage. So displaying
the plotted images is as simple as setting the src urls in the UpdateImgURLs() function.
The 'imgTitles' contain the text to be displayed underneath each plotted image. If a title isn't set
for an image, the text will read "undefined".
The iconSrc is optional; it can either be set to empty an string (""), or omitted entirely 
(whereby trying to reference it would return undefined).
The iconSrc is the url pointing to the icon image to be displayed in the tab bar, for that tab.
This image will be autosized to 41 x 30 px with inline css. 

The colour bars are created and displayed in the CreatePaneContent() function

To reference an entire dictionary you'd use Tabs[DictionaryName]. To reference an attribute of the
dictionary, you'd use Tabs[DictionaryName][AttributeName] 
(i.e. Tabs['Precipitation']['imgIds'][0] would return 'precipStationImg').
You can reference all dictionaries using:
    for (Dictionary in Tabs) {
        // access information here
    }
*/

var Tabs={
    'Precipitation':
        precip={
            imgIds : ['precipitationModImg', 'precipitationFcstImg', 'precipitationRadarObs', 'precipitationStationObs'],
            imgTitles : ['Modified Forecast', 'Euro4 Forecast', '', 'Radar/Station Observations (Rain Gauge)'], // Due to the slider, the title for the radarObs img is covered
            iconSrc : iconFolder + "precip.png",
            modelFcstFilename : "PmslZRnSnCl",
            slider : "enabled" // If you wish to put a slider on the tab, the image to be displayed on top must be before the image to be revealed with the slider
                                // In this case, radar observation is placed on top of station observation      
        },
    'Temperature':
        temp={
            imgIds : ['temperatureModImg', 'temperatureFcstImg', 'temperatureStationObs'],
            imgTitles : ['Modified Forecast', 'Euro4 Forecast', 'Station Observations'],
            iconSrc : iconFolder + "temp.png",
            modelFcstFilename : "T_surf",
            slider : "disabled"
        },
     'Cloud':
        cloud={
            imgIds : ['cloudModImg', 'cloudFcstImg', 'cloudObsImg'],
            imgTitles : ['Modified Forecast', 'Euro4 Forecast', 'Satellite Image Type'],
            iconSrc : iconFolder + "cloud.png",
            modelFcstFilename : "cloud",
            slider : "disabled"
        }
};
/* To add a new plot to the website, simply set the id of the image and give it a title.
    Then set the URL of the image in UpdateImgURLs() */

function init(){
    // The below code selects the intial options when the webpage loads
    sliderButton = document.getElementById("sliderButton");
    //dateDropdown = document.getElementById("dateDropdown");
    //dateDropdown.value = dateDropdown.options[0];
    $("#dateDropdown")[0].selectedIndex = 0;
    PopulateModelRunDropdown();
    //modelRunDropdown = document.getElementById("ModelRunDropdown");
    //modelRunDropdown.value = modelRunDropdown.options[0];
     $("#ModelRunDropdown")[0].selectedIndex = 0;
    UpdateFcstButtonText();
    FcstInfo = document.getElementById("FcstInfo");
    SelectTab(document.getElementsByClassName("tab")[0]); // Selects the first tab in the list and displays its contents
    SetActiveFcstBtn(document.getElementById("FcstSel0")); // Populates the website on load by selecting the 00 hour button
}

// Checks whether the URL for the image id exists, and if not loads "ObsUnavailable" instead
function ImageCheck(id, url) {
  $('#'+ id).attr('src', url).error(function() {
      $(this).attr("src", imageFolder+"DataUnavailable.png");
  });
}
// END General scripting container


// START Tabs scripting container
// Controls the creation, animation [expand/collapse], and event handling [onclick, onmouseover/onmouseleave] of the tabs
function DrawTabs() {
    var tabContainer = document.getElementById("tabs");
    
    for (tabName in Tabs) {
        tab = document.createElement("DIV");
        tab.id = tabName;
        tab.setAttribute("class", "tab");
        
        setTabIcon(tab);

        /*START Container for tab animation*/
        // Remove the code in the animation containers to stop the expansion/collapse of the tabs
        tab.onmouseover = function() { 
            if (!$(this).hasClass("chosen")) {
                ExpandTab(this);
            }
        };
        tab.onmouseleave = function() { 
            if (!$(this).hasClass("chosen")) {
                CollapseTab(this, 10); 
            }
        };
        /*END container for tab animation*/
        
        tab.onclick = function() { SelectTab(this) };
        tabContainer.appendChild(tab);
    }
}

// Adds an icon to the tab if an image exists and the url has been set. 
// Otherwise labels the tab with the first letter of the tab name. (I.e. C for Cloud)
function setTabIcon(tab) {
    var iconSrc = Tabs[tab.id]['iconSrc'];
    
    if (iconSrc == "" || iconSrc == undefined) { // If the icon url hasn't been set
        // Set the text inside the tab as the first letter of the tab name
        tab.innerHTML = tab.id.slice(0, 1);
    } else {
        // If an icon has been made and the source has been set in the dictionary,
        // this creates the tab icon image element and places it inside the tab
        tab.innerHTML = "<img id='" + tab.id + "Icon' src='" + iconSrc + "' style='width: 41px; height: 30px'/>";
    }
}

/*START Container for tab animation functions*/
function ExpandTab(tab) {
    // offsetWidth is the width of the element including the padding and border, but not the margin, in pixels
    var currentWidth = tab.offsetWidth;
    var maxWidth = 150; // The width the tab will expand to (in pixels)
    
    var increaseWidth = function() {
        if (currentWidth < maxWidth) {
            currentWidth += 8; // The amount to expand the tab by each loop
            tab.style.width = currentWidth + 'px'; // Currently set in pixels
        }
    }

    var interval = setInterval(function() {
        if (tab.clientWidth >= maxWidth) {
            tab.innerHTML = tab.id; // Removes the tab icon and replaces it with text
            clearInterval(interval); // This stops (finishes) the animation
        }
        else {
            increaseWidth(); // Whilst the tab is smaller than maxWidth, keep calling the function to expand
        }
    }, 12); // How often the increaseWidth() function should be called in ms
            // Essentially the speed of the animation
}

function CollapseTab(tab, speed) {
    // offsetWidth is the width of the element including the padding and border, but not the margin, in pixels
    var currentWidth = tab.offsetWidth;
    var minWidth = 55; // The width the tab will shrink to (in pixels)
    
    setTabIcon(tab); // Remove the text from inside the tab and display the icon
    
    var decreaseWidth = function() {
        if (currentWidth > minWidth) {
            currentWidth -= 8; // The amount to shrink the tab by each loop
            tab.style.width = currentWidth + 'px'; // Currently set in pixels
        }
    }

    var interval = setInterval(function() {
        if (tab.clientWidth <= minWidth) {
            clearInterval(interval); // This stops (finishes) the animation
        } else {
            decreaseWidth(); // Whilst the tab is bigger than minWidth, keep calling the function to shrink
        }
    }, speed); // How often the decreaseWidth() function should be called in ms
               // Essentially the speed of the animation
}
/*END Container for tab animation functions*/

function SelectTab(chosenTab){
    $(".chosen").each(function() {
        $(this).removeClass("chosen");
    });
    $(chosenTab).addClass("chosen");
    
    /*START Tab animation container*/
    $(".tab:not('.chosen')").each(function() {
        CollapseTab(this, 9); // Makes sure all other tabs are collapsed
    });
    /*END Tab animation container*/
    
    chosenTab.innerHTML = chosenTab.id; // Sets the text inside the tab
    ClearPaneContent();
    selectedTab = chosenTab.id;
    DrawPaneContent();
    SetActiveFcstBtn(document.getElementsByClassName("active")[0]); // 'Remembers' the clicked hour button when switching tabs
}
// END Tabs scripting container


// START Pane content scripting container
function ClearPaneContent() {
    // Removes all images/image text/colour bar from inside the pane
    document.getElementById("InnerContainer").innerHTML = "";
}

/* Using the 'Tabs' dictionary of dictionaries this will get all necessary information and create the tab pane. */
function DrawPaneContent() {
    paneContainer = document.getElementById("InnerContainer");

    tab = Tabs[selectedTab]; // The id (text inside) of the selected tab is the key for the dictionary

    for (var i = 0; i < tab.imgIds.length; i++){
        var imgContainer = document.createElement("DIV");
        imgContainer.setAttribute("class", "ImgContainer");
        
        var img = document.createElement("IMG");
        img.id = tab.imgIds[i]; // The image ids are predefined in the Tabs dictionary
        
        if (img.id == "precipitationRadarObs") { // The id of the image to act as the slider
            // We want to apply a slider to the radar and station observation plots in the precip tab
            imgCover = document.createElement("IMG");
            imgCover.id = "cover";
			   imgCover.style.height="585px";
            imgCover.style.position = "absolute";
            imgCover.style.overflow = "hidden";
            imgCover.style.textAlign = "initial";
            imgCover.appendChild(img);
            
            imgContainer.style.position = "absolute";
            imgContainer.style.textAlign = "initial";
            imgContainer.appendChild(imgCover);
        } else {
            imgContainer.appendChild(img);
        }
        
		  var imgTextContainer = document.createElement("DIV");
        imgTextContainer.setAttribute("class", "ImgText");
        var imgTitle = document.createElement("H4");
        imgTitle.innerHTML = tab.imgTitles[i]; // Gets the text underneath the images from the dictionary
        
        imgTextContainer.appendChild(imgTitle);
        imgContainer.appendChild(imgTextContainer);
        paneContainer.appendChild(imgContainer);
    }
    
    if (selectedTab == "Precipitation" || selectedTab == "Cloud" || selectedTab == "Temperature") {
        DrawModelSelectBtns(selectedTab); // Creates the UKV/Euro4 model select buttons
    }
    
    if (selectedTab == "Precipitation") { 
        // Attach the slider handler
        $("#InnerContainer").mousemove(function(event) {
            slider(event);
        });
        // Create ad display the various precip colour bars
        precipModColourBar = document.createElement("IMG");
        precipModColourBar.setAttribute("class", "colourBar");
        precipModColourBar.src = imageFolder+"PrecipColourBar_mod.png";
        insertAfter(document.getElementById("precipitationModImg"), precipModColourBar);
        
        precipRadarColourBar = document.createElement("IMG");
        precipRadarColourBar.setAttribute("class", "colourBar");
        precipRadarColourBar.src = imageFolder+"PrecipColourBar_mod.png";
        insertAfter(document.getElementById("precipitationStationObs"), precipRadarColourBar);
        
        precipUKVEURO4ColourBar = document.createElement("IMG");
        precipUKVEURO4ColourBar.setAttribute("class", "colourBar");
        precipUKVEURO4ColourBar.src = imageFolder+"PrecipColourBar_ukveuro4.png";
        insertAfter(document.getElementById("precipitationFcstImg"), precipUKVEURO4ColourBar);
        
    } else if (selectedTab == "Temperature") {
        // Create and display the temperature colour bar
        tempColourBar = document.createElement("IMG");
        tempColourBar.setAttribute("class", "colourBar");
        tempColourBar.src = imageFolder+"TempColourBar.png";
        insertAfter(document.getElementById("temperatureModImg"), tempColourBar);
        
    } else if (selectedTab == "Cloud") {
        // Create and display the cloud colour bar
        cloudColourBar = document.createElement("IMG");
        cloudColourBar.setAttribute("class", "colourBar");
        cloudColourBar.src = imageFolder+"CloudColourBar.png";
        document.getElementById("InnerContainer").appendChild(cloudColourBar);
        
        DrawCloudObsButtons();
    }
}
// END Pane content scripting container


// START Hour Select buttons scripting container
// Allows hour change to be controlled with the arrow keys (down/right increases the hour, up/left decreases the hour)
$(document).on("keydown", function (e) {
    if (e.keyCode == 37 || e.keyCode == 38) {
        e.preventDefault();
        changeHour("minusHour");
    } else if (e.keyCode == 39 || e.keyCode == 40) {
        e.preventDefault();
        changeHour("plusHour");
    }
});

function DrawHourSelectBtns() {
    var hourSelectDiv = document.getElementById("hourSelectBtns");

    var leftArrow = document.createElement("BUTTON");
    leftArrow.setAttribute("id", "minusHour");
    leftArrow.innerHTML = "-1 hour";
    leftArrow.onclick = function() { changeHour("minusHour") };
    
    hourSelectDiv.appendChild(leftArrow);
    
    var rightArrow = document.createElement("BUTTON");
    rightArrow.setAttribute("id", "plusHour");
    rightArrow.innerHTML = "+1 hour";
    rightArrow.onclick = function() { changeHour("plusHour") };
    
    hourSelectDiv.appendChild(rightArrow);
}

function changeHour(hourBtnClicked) {
    var currentClickedFcstBtn = $(".active");
    allFcstBtns = $(".FcstBtn");
    
    for (var i = 0; i < $(allFcstBtns).length; i ++) {
        var button = $(allFcstBtns[i]);
        
        if ($(currentClickedFcstBtn).attr('id') == $(button).attr('id')) {
        
            if (hourBtnClicked == "plusHour" && (i+1) != $(allFcstBtns).length) {
                $(allFcstBtns[i + 1])[0].click(); // Selects the next hour button (if it exists)
                
            } else if (hourBtnClicked == "minusHour" && i != 0) { // If the currently clicked hour button isn't the first
            
                if ($(currentClickedFcstBtn).parent().attr('class') == "section") {
                    // If moving upwards from one section to another, this causes the next (above) section to expand
                    // and closes the previous (below) section
                    ToggleAccordion($(currentClickedFcstBtn).parent().prev().children()[0]); // Essentially emulates a header button being clicked
                }
                // When moving upwards onto a header button, we don't want the section to collapse
                SetActiveFcstBtn($(allFcstBtns[i - 1])[0]);
            }
            break;
        }
    }
}
// END Hour Select buttons scripting container


// START Slider scripting container
function DrawSliderButton() {
    sliderButton = document.createElement("BUTTON");
    sliderButton.id = "sliderButton";
    sliderButton.innerHTML = "Slider [Disabled]";
    sliderButton.onclick = function() {
        SliderActivation();        
    };
    document.getElementById("HourSelect").appendChild(sliderButton);
}
// END Slider scripting container


// START Date select scripting container
// Generates array of dates from DateModelRun string
function PopulateDateSelect() {
    var dateSelectDiv = document.getElementById("DateSelect");

    dateDropdown = document.createElement("SELECT");
    dateDropdown.id = "dateDropdown";
    dateDropdown.addEventListener("change", function() {
        PopulateModelRunDropdown();
        UpdateFcstButtonText();
    });
    
    minusDateBtn = document.createElement("BUTTON");
    minusDateBtn.id = "minusDate";
    minusDateBtn.innerHTML = "<";
    minusDateBtn.addEventListener("click", function() { changeDate('minusDate') });
    
    plusDateBtn = document.createElement("BUTTON");
    plusDateBtn.id = "plusDate";
    plusDateBtn.innerHTML = ">";
    plusDateBtn.addEventListener("click", function() { changeDate('plusDate') });
    
    dateSelectDiv.appendChild(minusDateBtn);
    dateSelectDiv.appendChild(dateDropdown);
    dateSelectDiv.appendChild(plusDateBtn);
    
    var i = 0;

    for (var key in DateModelRun) {
        if (DateModelRun.hasOwnProperty(key)) {
            i=i+1;
            var date = document.createElement("OPTION");
            var parsedDate = (key.slice(0,4) + "-" + key.slice(4,6) + "-" + key.slice(6,8));
            dateDropdown.options[dateDropdown.options.length] = new Option(parsedDate, key); // The option appears in YYYY-MM-DD format, but its value is YYYYMMDD
        }
    }
}

function changeDate(dateChange) {
    var dateDropdown = document.getElementById("dateDropdown");
    var selectedDateIndex = dateDropdown.selectedIndex;

    if (dateChange == "plusDate" && selectedDateIndex < dateDropdown.options.length - 1) {
        // If the '>' button has been clicked, and the user hasn't already selected the newest available date
        dateDropdown.value = dateDropdown.options[selectedDateIndex + 1].value; // Selects the next date
    } else if (dateChange == "minusDate" && selectedDateIndex > 0) {
        // If the '<' button has been clicked, and the user hasn't already selected the oldest available date
        dateDropdown.value = dateDropdown.options[selectedDateIndex - 1].value; // Selects the previous date
    }
    PopulateModelRunDropdown();
    UpdateFcstButtonText();
}
// END Date select scripting container


// START ModelRun dropdown scripting container
function DrawModelRunDropdown() {
    modelRunDropdown = document.createElement("SELECT");
    modelRunDropdown.id = "ModelRunDropdown";
    modelRunDropdown.onchange = UpdateFcstButtonText;
    document.getElementById("ModelRunSelect").appendChild(modelRunDropdown);
}

function PopulateModelRunDropdown(){
    var selectedDateValue = $("#dateDropdown").val();

    for (date in DateModelRun){
        if (date == selectedDateValue){
            RetrieveModelRuns(date);
            break;
        }
    }
}

function RetrieveModelRuns(date) {
    DateStr = date;
    var ModelRunList
    var ModelRunListSplit
    var RegexCheck = /\d{2}./;
    var parsedModelRun;
    modelRunDropdown = document.getElementById("ModelRunDropdown");
    $("#ModelRunDropdown").empty(); // Removes current options
    
    ModelRunList = DateModelRun[DateStr];
    ModelRunListSplit = ModelRunList.split(",");
    
    // Creates array with model runs
    for (var j=0; j < ModelRunListSplit.length; j++ ) {
        if ( RegexCheck.exec(ModelRunListSplit[j]) ) { // Check string contains 2 digits and a character
            parsedModelRun = ModelRunListSplit[j].slice(0,2);
            modelRunDropdown.options[modelRunDropdown.options.length] = new Option(parsedModelRun, parsedModelRun);
        }
    }
}
// END ModelRun dropdown scripting container


// START Forecast buttons scripting container
// Handles displaying/hiding the forecast hour buttons as the user selects/navigates them
function ToggleAccordion(clickedBtn) {
    var innerFcstBtns = document.getElementsByClassName("innerBtn");
    
    if (clickedBtn.nextSibling.firstElementChild != null && !(clickedBtn.nextSibling.firstElementChild.style.display === "block")) {
    // if the clicked hour button is a header button with a section of inner buttons, and the inner buttons aren't currently shown    
        for (var i = 0; i < innerFcstBtns.length; i ++){
            // hides all inner buttons of the previous section
            innerFcstBtns[i].style.display = "none";
        }
        
        var sectionBtns = clickedBtn.nextSibling.childNodes; // references the inner buttons of the NEXT section
        
        for (var j = 0; j < sectionBtns.length; j ++){
            // displays the buttons for the next section (opens the next section)
            sectionBtns[j].style.display = "block";
        }
        
    } else {
        // If the clicked hour button doesn't have any inner buttons (i.e. the last button in the list)
        for (var i = 0; i < innerFcstBtns.length; i ++){
            // hides all inner buttons of the previous section
            innerFcstBtns[i].style.display = "none";
        }
    }
}

function SetActiveFcstBtn(clickedBtn){
    if (clickedBtn == undefined) {
        // If no button has been clicked, select the first.
        clickedBtn = document.getElementById("FcstSel0");
    }

    if (clickedBtn.style.display == "none") {
        // If the clicked hour button is somehow hidden, emulates clicking the header button to show the inner buttons
        $(clickedBtn).parent().prev()[0].click();
    }
    $(".active").removeClass("active");
    $(clickedBtn).addClass("active");

    // Extracts date, model run, and forecast time data    
    selectedDateIndex = dateDropdown.selectedIndex;
    selectedModelRunIndex = modelRunDropdown.selectedIndex;
    
    CalculateFcstInformation(selectedDateIndex, selectedModelRunIndex, clickedBtn);
}

function CalculateFcstInformation(selectedDateIndex, selectedModelRunIndex, clickedBtn) {
    // Uses the supplied arguments to calculate the information needed to set the url of each plot type

    selectedDate = dateDropdown.options[selectedDateIndex].value;
    ModelRunStr = modelRunDropdown.options[selectedModelRunIndex].value;
    ModelRun = parseInt(ModelRunStr);
    hourOffsetIdStr = clickedBtn.id.replace(/\D+/g, ''); // Removes all non-numeric characters
    hourOffsetId = parseInt(hourOffsetIdStr);
    
    // zuluTime is used in the URL for the UKV/Euro4 plots
    zuluTime = parseInt(ModelRunStr) + parseInt(hourOffsetIdStr);
    
    if (zuluTime >= 24) {
        zuluTime = zuluTime%24;
    }
    zuluTime = ("0" + zuluTime).slice(-2);
    
    if (hourOffsetId < 10) {
        paddedhourOffsetIdStr = "0" + hourOffsetIdStr; // If the hour is a single digit it needs to be prepadded with a zero
    } else {
        paddedhourOffsetIdStr = hourOffsetIdStr;
    }
    dateOffset = Math.floor((ModelRun + hourOffsetId)/24); // Returns the number of days given the starting hour and the chosen hour (i.e. 06Z and t+90h = 96, which is 4 days)
    
    try {
        forecastDate = dateDropdown.options[selectedDateIndex + dateOffset].value; // The date accounting for the forecast hour (t+X hrs) and the model run (i.e. starting at 2100Z)
        obsDate = forecastDate;
    } catch (TypeError) {
        forecastDate = calculateDate(); // If trying to use a date not in the dropdown
        obsDate = undefined; // The date will be in the future, so there are not observations
    }
    Time = clickedBtn.innerHTML.slice(-4);
    
    Year = forecastDate.slice(0, 4);
    Month = forecastDate.slice(4, 6);
    Day = forecastDate.slice(6, 8);
    yearInt = parseInt(Year);
    monthInt = parseInt(Month);
    dayInt = parseInt(Day);
    dateObj = new Date(yearInt, (monthInt-1), dayInt);
    monthInText = getMonthInText(dateObj.getMonth()); // Not currently used
    dayInText = getDayInText(dateObj.getDay());
                   
    ForecastTextDate = Day + "/" + Month + "/" + Year;            
    FcstInfo.textContent = dayInText + " " + Time + "Z" + " " + ForecastTextDate + " " + "(t+" + hourOffsetId + "h)"; // The text that appears above all of the plots
    
    UpdateImgURLs();
}

/* WORK IN PROGRESS 
How I was considering implementing the URL feature;
each time a user clicks an hour button, the selected date and model run are fetched.
This info is then appended to the current URL (along with the hour selected).
Each piece of info should be separated with the same character, so the string can be
split and the info can be retrieved. Here I've used pipe ("|") but none alphabetical/numerical
character could be used.
There should also be some indication to show the end of the base URL (http://www-nwp/~pclarke/FIAT/html/FIAT.html)
and the start of the information string. Here I've used "?", but again, any non letter/number can be used.

This way the URL can be split on "?", then the second part containing the information can be split again (on "|").
If the URL wasn't split twice, if trying to access the first piece of info (URL.[0]) you'd get the entire base URL and the info.

This string can then be appended to the webpage however you want (here I've gone for a text node, which is just text. No P or H1 etc).

The next stage was to set the URL itself. This can be done with window.location.href, but doing so will cause the webpage to follow the url
unless you use some method to stop it doing so (I hadn't looked into this).

The trickiest part is when to read the URL. This could theoretically be done each time the page loads (onload), but I get the feeling it
won't be that straightforward.
Once the URL is read, it can be split and the information can be retrieved. This then needs to be set as the chosen options; that's
straightforward, but a bit fiddly. With the current setup the index values of the chosen options are stored/read from the URL;
the selected option in the Date and Model Run dropdowns can then be set using these integers by calling CalculateFcstInformation()
and supplying the arguments.
Theoretically things should propogate from there; using the index values the chosen option strings are fetched, then these are converted
into all of the various urls, which are set for the plots (using UpdateImgURLs()).
The code here mostly handles the writing/reading, I just hadn't worked out -when- to read. (Writing can be done by setting another
onclick handler to the forecast buttons, which I've done and commented out in DrawFcstBtns() [the GenerateURL() function]).
ReadURL() would need to initially be called in either the init() function, or the window.onload function (at the very top of the document).
It would also need to be called if the user clicked on the displayed link? I'm unsure. Clicking on the link would cause the page to refresh
and I'm assuming window.onload and init() would be called anyway, but I haven't checked this.

*/
//function GenerateURL() {
//    clickedBtn = document.getElementsByClassName("active")[0];
//    console.log("Generated using: " + clickedBtn);
//    
//    URL = 
//        window.location.href.split("?")[0] // This gets the base URL and reappends the information
//        + "?" 
//        + clickedBtn.id
//        + "|"
//        + dateDropdown.selectedIndex
//        + "|"
//        + modelRunDropdown.selectedIndex;
//        
//    URLText = document.createTextNode(URL);
//    document.getElementById("InnerContainer").appendChild(URLText);
//}

//function ReadURL() {
//    var URL = window.location.href;
//    
//    if (URL.indexOf("?") != -1) {
//        AllURLInfo = URL.split("?")[1];
//        console.log("info in url: " + AllURLInfo);
//        
//        URLInfo = AllURLInfo.split("|");
//        
//        selectedMRIndex = URLInfo[0];
//        selectedDateIndex = URLInfo[1];
//        clickedBtnId = URLInfo[2];
//        
//        CalculateFcstInformation(selectedMRIndex, selectedDateIndex, clickedBtnId);
//        
//    } else {
//        console.log("no info");

//    }
//}

// Works out the date from the clicked hour, if the date is not in the dropdown
// (I.e. looking at a forecast for a future date)
function calculateDate() {
    lastDate = dateDropdown.options[dateDropdown.options.length-1].value; // The latest date in the list
    
    Year = lastDate.slice(0, 4);
    Month = lastDate.slice(4, 6);
    Day = lastDate.slice(6, 8);
    yearInt = parseInt(Year);
    monthInt = parseInt(Month);
    dayInt = parseInt(Day);
    
    oldDate = new Date(yearInt, monthInt, dayInt);
    newDate = new Date();
    
    newDate.setDate(oldDate.getDate() + dateOffset); // Gets the numerical value of the day and adds the offset.

    var dd = ("0" + newDate.getDate()).slice(-2); // Pads the day value with "0" (if less than 10)
    var mm = ("0" + (newDate.getMonth()+1)).slice(-2); // Pads the month value with "0" (if less than 10)
    var yyyy = newDate.getFullYear();

    var formattedNewDate = yyyy.toString()+mm.toString()+dd.toString(); // Returns the calculated date in the form YYMMDD
    
    return formattedNewDate;    
}

// This is the main function for setting the URLs of the images
// Each URL is checked, and if the image can't be found an 'error image' is shown instead (see ImageCheck function)
function UpdateImgURLs() {
/* The URLs are individually set for each image on each tab. This is done by creating a string containing the URL of the image
then using the URL and the ID of the image (as set in the tab dictionary) as arguments for the ImageCheck(id, url) function.
ImageCheck does not have to be used; the source url of the image can be set manually using: ImageId.src = ImageURL
however if this is done, if the image can't be found nothing will be displayed (whereas using ImageCheck displays an error image) */

    if (selectedTab == "Precipitation") {
        // Create the image URL strings (the URL variable can be called anything; it just has to be sent as an argument to ImageCheck() or set using image.src = url)
        precipStationObsURL = FIATBaseURL + "/Observations/Precip_Station/" + obsDate + Time + ".png";
        precipModImgURL = FIATBaseURL + "/ModifiedForecasts/Modified_Rain_Rate/" + selectedDate + "/" + ModelRunStr + "Z/Rain_Rate_" + paddedhourOffsetIdStr + ".png";
        precipRadarObsURL = UFOBaseURL + "/Obs_Data/Radar/" + obsDate + Time + ".png";
            
        // Check/assign the images using the ImageCheck function and the IDs set in the dictionary
        ImageCheck('precipitationStationObs', precipStationObsURL);
        ImageCheck('precipitationModImg', precipModImgURL);
        ImageCheck('precipitationRadarObs', precipRadarObsURL);
            
    } else if (selectedTab == "Temperature") {
        tempStationObsURL = FIATBaseURL + "/Observations/Temp_Station/" + obsDate + Time + ".png";
        tempModImgURL = FIATBaseURL + "/ModifiedForecasts/Modified_Temperature_1p5m/" + selectedDate + "/" + ModelRunStr + "Z/Temperature_1p5m_" + paddedhourOffsetIdStr + ".png";
        tempErrorMapURL = UFOBaseURL + "/Obs_Data/ScreenTemp_ErrorMap/" + obsDate + "/" + ModelRunStr + "Z/ScreenTemp-" + hourOffsetIdStr + ".png";
            
        ImageCheck('temperatureStationObs', tempStationObsURL);
        ImageCheck('temperatureModImg', tempModImgURL);
        ImageCheck('temperatureErrorMap', tempErrorMapURL);
    
    } else if (selectedTab == "Cloud") {
        cloudModImgURL = FIATBaseURL + "/ModifiedForecasts/Modified_Cloud/" + selectedDate + "/" + ModelRunStr + "Z/Cloud_" + paddedhourOffsetIdStr + ".png";
        
        ImageCheck('cloudModImg', cloudModImgURL);
        
        setCloudObsImg(cloudObsType);
    }
    
    if (Tabs[selectedTab]['modelFcstFilename'] != undefined) { // If the dictionary contains information for a UKV/Euro4 model forecast
        // The UKV forecast only goes up to t+36h for a given day, Euro4 goes up to t+120h.
        // So if the user chooses an hour after t+36h only the Euro4 model will be available.
        // (Both buttons will be disabled, but Euro4 will be selected)
        if (hourOffsetId > 36) {
            UKVBtn.disabled = true;
            UKV.style.backgroundColor = "";
            Euro4Btn.style.backgroundColor = "#63D13E";
            chosenModel = "Euro4";
            
        } else if (chosenModel == "Euro4") {
            // This ensures the UKV model is selectable otherwise
            UKVBtn.disabled = false;
        }
        setForecastImg(Tabs[selectedTab]['modelFcstFilename']);
    }
}

// Returns day of the week represented by the supplied index number
function getDayInText(num) {
    daysOfWeek = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    day = daysOfWeek[num];
    return day;
}
// Returns month of the year represented by the supplied index number
function getMonthInText(num) {
    monthsOfYear = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    month = monthsOfYear[num];
    return month;
}

// Function to draw the forecast hour buttons in the sidebar on the right
function DrawFcstBtns() {
    // Initialises variables for the loop
    var headerNumber = -1;
    var currentSectionDiv = null;

    for (var i = 0; i <= MAXFORECASTVAL; i++) { // MAXFORECASTVAL is set at the top of this script

        ForecastStr = i.toString();
        // The 'buttons' are actually <a> elements with heavy css styling
        var fcstBtn = document.createElement("A");
        fcstBtn.setAttribute("id", "FcstSel" + ForecastStr);
        fcstBtn.addEventListener('click', function() { 
            SetActiveFcstBtn(this);
            //GenerateURL(this);
        });
        
        // seperatorVal sets how many buttons there are per collapsible section.
        var seperatorVal = 12;
        headerNumber = Math.floor(i/seperatorVal);

        if (i % seperatorVal == 0) { // For every 'separatorVal'th iteration create a new button section (<div> and header button)
            var outerDiv = document.createElement("DIV"); // Create a new <div> for the section (this will contain all buttons for the section; header and inner)
            outerDiv.setAttribute("class", "section");
            document.getElementById("FcstButtonList").appendChild(outerDiv); // Add it to the overall column of buttons
            
            fcstBtn.setAttribute("class", "FcstBtn headerBtn noselect");// headerBtn denotes a button that collapses/expands a section. It's always displayed. 
                                                                        // 'noselect' class assigns CSS to prevent the text becoming hightlighted when clicking
            fcstBtn.addEventListener('click', function() { ToggleAccordion(this); });
            outerDiv.appendChild(fcstBtn); // Adds the header button to the start (i.e. inside, at the top) of the section <div>

            var innerDiv = document.createElement("DIV"); // Creates another <div> to contain the buttons that can be hidden/shown
            innerDiv.setAttribute("id", "section" + headerNumber);

            insertAfter(fcstBtn, innerDiv); // Appends the inner <div> below the header button (the usual appendChild method doesn't work here)
        
        } else {
            fcstBtn.style.display = "none"; // Initially hides the inner buttons
            fcstBtn.setAttribute("class", "FcstBtn innerBtn noselect"); // The inner buttons are styled very differently to the header buttons to make the section separators clear

            currentSectionDiv = document.getElementById("section" + headerNumber); // Find the newest created section <div> to append the buttons to
            currentSectionDiv.appendChild(fcstBtn);
        }
        document.getElementById("FcstSel"+ForecastStr).innerHTML="+"+ForecastStr+" hrs"; // Writes the hour to the button
    }
}

// Inserts the newNode after the referenceNode
function insertAfter(referenceNode, newNode) {
    referenceNode.parentNode.insertBefore(newNode, referenceNode.nextSibling);
}

// A function to change the hour buttons depending on the model run selected
function UpdateFcstButtonText(){
    var ModelRun = $("#ModelRunDropdown").val(); // Gets the selected model run
    document.activeElement.blur(); // Removes focus from the model run dropdown to prevent the arrow keys changing the chosen model run
    
    for ( var i = 0; i <= MAXFORECASTVAL; i++) {
        
        ForecastStr = i.toString();
        
        var TimeInt = parseInt(ModelRun) + parseInt(ForecastStr); // Calculates the time to be written to the buttons, depending on the model run selected

        if (TimeInt > 23) {
            TimeInt = TimeInt%24;
        }

        // Pad time string with zeros
        var TimeStr = TimeInt.toString();
        TimeStr = ("00"+TimeStr).slice(-2)+"00";

        // Sets the hour text on the forecast hour button
        document.getElementById("FcstSel"+ForecastStr).innerHTML="+"+ForecastStr+" hrs - "+TimeStr;
    }
    // When switching date or model run this will "remember" the previously chosen hour and rechoose it. 
    // Hence the plots are updated each time the user changes their input.
    var activeBtn = document.getElementsByClassName("active")[0];
    if (activeBtn != undefined) {
        SetActiveFcstBtn(activeBtn);
    }
}
// END Forecast buttons scripting container

    
// START Model select buttons scripting container
/* Both functions within this container handle the UKV/Euro4 buttons. */

// Creates the UKV/Euro4 buttons and adds them to the precipitation tab pane
function DrawModelSelectBtns(plotType) {
    var ModelSelectDiv = document.createElement("DIV");
    ModelSelectDiv.id = "ModelSelect";

    UKVBtn = document.createElement("BUTTON");
    UKVBtn.id = "UKV";
    UKVBtn.innerHTML = "UKV";
    
    Euro4Btn = document.createElement("BUTTON");
    Euro4Btn.id = "Euro4";
    Euro4Btn.innerHTML = "Euro4";
    
    UKVBtn.onclick = function() { 
        UKVBtn.blur();
        chosenModel = "UKV";
        Euro4Btn.style.backgroundColor = "";
        UKVBtn.style.backgroundColor = "#63D13E"; // Changes the button background colour to indicate it's been clicked
        setForecastImg(Tabs[plotType]['modelFcstFilename']);
        //changeModelText(plotType);
    };

    Euro4Btn.onclick = function() { 
        Euro4Btn.blur();
        chosenModel = "Euro4";
        UKVBtn.style.backgroundColor = "";
        Euro4Btn.style.backgroundColor = "#63D13E"; // Changes the button background colour to indicate it's been clicked
        setForecastImg(Tabs[plotType]['modelFcstFilename']);
        //changeModelText(plotType);
    };
    
    ModelSelectDiv.appendChild(UKVBtn);
    ModelSelectDiv.appendChild(Euro4Btn);
    
    forecastImgId = plotType.toLowerCase() + "FcstImg";
    var forecastIndex = Tabs[plotType].imgIds.indexOf(forecastImgId); // Find the correct image type [forecast] to put the buttons underneath
    
    document.getElementsByClassName("ImgContainer")[forecastIndex].appendChild(ModelSelectDiv); // Selects the image container containing the forecast image using the array index
    document.getElementsByClassName("ImgText")[forecastIndex].innerHTML = chosenModel + " Forecast"; // Selects the text element containing the forecast information
    //changeModelText(plotType);
    document.getElementById(chosenModel).style.backgroundColor = "#63D13E"; // Ensures the initially chosen/previously chosen model is remembered on tab switching
}

function changeModelText(plotType) {
    ModelSelectDiv = document.getElementById("ModelSelect");
    forecastImgId = plotType.toLowerCase() + "FcstImg";
    var forecastIndex = Tabs[plotType].imgIds.indexOf(forecastImgId); // Find the correct image type [forecast] to put the buttons undernea$
    
    document.getElementsByClassName("ImgContainer")[forecastIndex].appendChild(ModelSelectDiv); // Selects the image container containing t$
    document.getElementsByClassName("ImgText")[forecastIndex].innerHTML = chosenModel + " Forecast"; // Selects the text element containing$
    console.log(forecastIndex);
}    

// Sets the forecast image url on tabs containing the UKV/Euro4 buttons
function setForecastImg(filename) {
    FcstImgURL = 
        FIATBaseURL
        + "/Forecasts/"
        + chosenModel 
        + "/" 
        + selectedTab 
        + "/"
        + selectedDate
        + "/"
        + ModelRunStr
        + "Z/"
        + filename 
        + "_oper-"
        + chosenModel.toLowerCase().slice(0,3) // The filename for the Euro4 plots contains "eur"; UKV is ukv
        + "_"
        + forecastDate
        + "_"
        + zuluTime
        + "Z_T"
        + hourOffsetIdStr
        + "_UKrot.png";
        
        ImageCheck(forecastImgId, FcstImgURL);

    // Changes the text underneath the forecast image to state the chosen model
    document.getElementById(forecastImgId).nextSibling.innerHTML = chosenModel +  " Forecast";
}
// END Model select buttons scripting container


// START Cloud obs type buttons scripting container
function DrawCloudObsButtons() {
    CloudTopBtn = document.createElement("BUTTON");
    CloudTopBtn.innerHTML = "Cloud Top";
    CloudTopBtn.onclick = function() { 
        CloudTopBtn.blur();
        cloudObsType = "Cloud/EHEA11";
        VisibleLightBtn.style.backgroundColor = "";
        IRBtn.style.backgroundColor = "";
        CloudTopBtn.style.backgroundColor = "#63D13E"; // Changes the button background colour to indicate it's been clicked
        setCloudObsImg("Cloud/EHEA11");
        //drawCloudTopColourBar(); // Uncomment this to manually add the Cloud Top colour bar to the Cloud tab webpage
    }
    
    VisibleLightBtn = document.createElement("BUTTON");
    VisibleLightBtn.innerHTML = "Visible Light";
    VisibleLightBtn.onclick = function() { 
        VisibleLightBtn.blur();
        cloudObsType = "Vis/EVEB71";
        CloudTopBtn.style.backgroundColor = "";
        IRBtn.style.backgroundColor = "";
        VisibleLightBtn.style.backgroundColor = "#63D13E"; // Changes the button background colour to indicate it's been clicked
        setCloudObsImg("Vis/EVEB71");
        //removeCloudTopColourBar(); // Uncomment this if manually adding the Cloud Top colour bar; this will remove it when you switch tabs
    }
    
    IRBtn = document.createElement("BUTTON");
    IRBtn.innerHTML = "IR";    
    IRBtn.onclick = function() { 
        IRBtn.blur();
        cloudObsType = "IR/EIEA51";
        VisibleLightBtn.style.backgroundColor = "";
        CloudTopBtn.style.backgroundColor = "";
        IRBtn.style.backgroundColor = "#63D13E"; // Changes the button background colour to indicate it's been clicked
        setCloudObsImg("IR/EIEA51");
        //removeCloudTopColourBar(); // Uncomment this if manually adding the Cloud Top colour bar; this will remove it when you switch tabs
    }
    
    CloudObsBtnDiv = document.createElement("DIV");
    CloudObsBtnDiv.id = "CloudObsBtns";
    
    CloudObsBtnDiv.appendChild(CloudTopBtn);
    CloudObsBtnDiv.appendChild(VisibleLightBtn);
    CloudObsBtnDiv.appendChild(IRBtn);
    insertAfter(document.getElementById("cloudObsImg"), CloudObsBtnDiv);
    
    // Cloud Top is selected by default
    CloudTopBtn.style.backgroundColor = "#63D13E";
    VisibleLightBtn.style.backgroundColor = "";
    IRBtn.style.backgroundColor = "";
    setCloudObsImg("Cloud/EHEA11");
    //drawCloudTopColourBar(); // Uncomment this to manually add the Cloud Top colour bar to the Cloud tab webpage
}

function drawCloudTopColourBar() {
    CloudTopColourBar = document.createElement("IMG");
    CloudTopColourBar.src = "imgs/CloudColourBar_obs.png";
    CloudTopColourBar.id = "cloudTopColourBar";
    CloudTopColourBar.setAttribute("class", "colourBar");
    // Adds the cloud top colour bar after the standard cloud colour bar
    document.getElementById("InnerContainer").appendChild(CloudTopColourBar); 
}

function removeCloudTopColourBar() {
    colourBar = document.getElementById("cloudTopColourBar")
    if (colourBar != undefined) {
        document.getElementById("cloudTopColourBar").remove();
    }
}

function setCloudObsImg(chosenCloudObsType) {
    cloudObsImgURL = UFOBaseURL + "/Obs_Data/Sat_" + chosenCloudObsType + "_" + selectedDate + Time + ".png";
    ImageCheck('cloudObsImg', cloudObsImgURL);
}
// END Cloud obs type buttons scripting container


// END Slider scripting container
// This function dynamically changes the width of the top image according to the mouse pointer position
function slider(event) {
    var XOffset;
    
    if (selectedTab == 'Precipitation') {
        if (SliderEnabled == 1) {
            // Uses the offset of the image container
            XOffset = event.pageX - $("#cover").parent().offset().left;
        }
        else if (SliderEnabled == 0) {
            XOffset = "480";
        }
        // Set the width of the radar observation image cover
        $("#cover").width(XOffset);
    }
}

// This switches the slider on and off
function SliderActivation() {
    if (SliderEnabled == 1) {
        sliderButton.innerHTML = "Slider [Disabled]";
    } else {
        sliderButton.innerHTML = "Slider [Enabled]";
    }
    SliderEnabled ^= 1; // Toggles the value of SliderEnabled between 1 and 0
}
// END Slider scripting container
