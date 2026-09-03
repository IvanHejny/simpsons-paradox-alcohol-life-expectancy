# Life expectancy - Data package

This data package contains the data that powers the chart ["Life expectancy"](https://ourworldindata.org/grapher/life-expectancy-at-birth-who-gho?v=1&csvType=full&useColumnShortNames=false) on the Our World in Data website. It was downloaded on July 29, 2026.

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


## Life expectancy at birth (years) - Sex: both sexes
Last updated: May 22, 2026  
Next update: May 2027  
Date range: 2000–2021  
Unit: Years  


### How to cite this data

#### In-line citation
If you have limited space (e.g. in data visualizations), you can use this abbreviated in-line citation:  
World Health Organization - Global Health Observatory (2026) – with minor processing by Our World in Data

#### Full citation
World Health Organization - Global Health Observatory (2026) – with minor processing by Our World in Data. “Life expectancy at birth (years) - Sex: both sexes – WHO” [dataset]. World Health Organization, “Global Health Observatory” [original data].
Source: World Health Organization - Global Health Observatory (2026) – with minor processing by Our World In Data

### How is this data described by its producer - World Health Organization - Global Health Observatory (2026)?
#### Rationale
Life expectancy reflects the overall mortality level of a population. It summarizes the mortality pattern that prevails at the time in the remaining years of life at a certain age.

#### Definition
The average number of years that a person could expect to live, if he or she were to pass through the remaining years of life exposed to the sex- and age-specific death rates prevailing at the time, for a specific year, in a given country, territory, or geographic area.
At birth: taking into account years lived throughout the entire life course.
At age 60: taking into account years lived at age 60 years and above.

#### Method of measurement
Life expectancy at a specific age is derived from life tables and is based on sex- and age-specific death rates.

#### Method of estimation
Final estimates of age-sex-specific mortality rates for years 1990-2021 were used to compute abridged life tables for 183 WHO Member States with population of 90,000 or greater in 2021. Life expectancies at birth are reported in World Health Statistics 2024 and full life tables are available in the WHO Global Health Observatory WHO applies standard methods to the analysis of Member State data to ensure comparability of estimates across countries. This will inevitably result in differences for some Member States with official estimates for quantities such as life expectancy, where a variety of different projection methods and other methods are used. These WHO estimates of mortality and life expectancies should not be regarded as the nationally endorsed statistics of Member States, which may have been derived using alternative methodologies and assumptions.

### Source

#### World Health Organization – Global Health Observatory
Retrieved on: 2026-05-22  
Retrieved from: https://www.who.int/data/gho  


    