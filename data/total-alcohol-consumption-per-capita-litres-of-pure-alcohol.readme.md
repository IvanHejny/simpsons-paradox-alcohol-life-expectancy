# Alcohol consumption per person - Data package

This data package contains the data that powers the chart ["Alcohol consumption per person"](https://ourworldindata.org/grapher/total-alcohol-consumption-per-capita-litres-of-pure-alcohol?v=1&csvType=full&useColumnShortNames=false) on the Our World in Data website. It was downloaded on July 29, 2026.

### Active Filters

A filtered subset of the full data was downloaded. The following filters were applied:

## CSV Structure

The high level structure of the CSV file is that each row is an observation for an entity (usually a country or region) and a timepoint (usually a year).

The first two columns in the CSV file are "Entity" and "Code". "Entity" is the name of the entity (e.g. "United States"). "Code" is the OWID internal entity code that we use if the entity is a country or region. For most countries, this is the same as the [iso alpha-3](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3) code of the entity (e.g. "USA") - for non-standard countries like historical countries these are custom codes.

The third column is either "Year" or "Day". If the data is annual, this is "Year" and contains only the year as an integer. If the column is "Day", the column contains a date string in the form "YYYY-MM-DD".

The final column is the data column, which is the time series that powers the chart. If the CSV data is downloaded using the "full data" option, then the column corresponds to the time series below. If the CSV data is downloaded using the "only selected data visible in the chart" option then the data column is transformed depending on the chart type and thus the association with the time series might not be as straightforward.


## Metadata.json structure

The .metadata.json file contains metadata about the data package. The "charts" key contains information to recreate the chart, like the title, subtitle etc.. The "columns" key contains information about each of the columns in the csv, like the unit, timespan covered, citation for the data etc..

## About the data

Our World in Data is almost never the original producer of the data - almost all of the data we use has been compiled by others. If you want to re-use data, it is your responsibility to ensure that you adhere to the sources' license and to credit them correctly. Please note that a single time series may have more than one source - e.g. when we stich together data from different time periods by different producers or when we calculate per capita metrics using population data from a second source.

## Detailed information about the data


## Total alcohol consumption per capita – In liters of pure alcohol, projected estimates, 15+ years of age
Last updated: July 14, 2026  
Next update: January 2027  
Date range: 2000–2020  
Unit: liters of pure alcohol, projected estimates, 15+ years of age  


### How to cite this data

#### In-line citation
If you have limited space (e.g. in data visualizations), you can use this abbreviated in-line citation:  
Global Health Observatory Data Repository - World Health Organization (WHO), via World Bank (2026) – processed by Our World in Data

#### Full citation
Global Health Observatory Data Repository - World Health Organization (WHO), via World Bank (2026) – processed by Our World in Data. “Total alcohol consumption per capita – In liters of pure alcohol, projected estimates, 15+ years of age” [dataset]. Global Health Observatory Data Repository - World Health Organization (WHO), via World Bank, “World Development Indicators 129” [original data].
Source: Global Health Observatory Data Repository - World Health Organization (WHO), via World Bank (2026) – processed by Our World In Data

### How is this data described by its producer - Global Health Observatory Data Repository - World Health Organization (WHO), via World Bank (2026)?
Total alcohol per capita consumption is defined as the total (sum of recorded and unrecorded alcohol) amount of alcohol consumed per person (15 years of age or older) over a calendar year, in litres of pure alcohol, adjusted for tourist consumption.

### Aggregation method:
Weighted average

### Statistical concept and methodology:
Methodology: The estimates for the total alcohol consumption are produced by summing up the 3-year average per capita (15+) recorded alcohol consumption and an estimate of per capita (15+) unrecorded alcohol consumption for a calendar year. Tourist consumption takes into account tourists visiting the country and inhabitants visiting other countries.

### Development relevance:
According to the World Health Organization, alcohol consumption is a causal factor in more than 200 disease and injury conditions. In the world, an estimated 3 million deaths are from harmful use of alcohols every year. Drinking alcohol is associated with a risk of developing health problems such as mental and behavioural disorders, including alcohol dependence, major noncommunicable diseases such as liver cirrhosis, some cancers and cardiovascular diseases, as well as injuries resulting from violence and road clashes and collisions.

### Other notes:
This is the Sustainable Development Goal indicator 3.5.2[https://unstats.un.org/sdgs/metadata/].

### Source

#### Global Health Observatory Data Repository - World Health Organization (WHO), via World Bank – World Development Indicators
Retrieved on: 2026-07-14  
Retrieved from: https://data.worldbank.org/indicator/SH.ALC.PCAP.LI  


    