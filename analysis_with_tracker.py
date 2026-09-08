from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
TARGET_YEAR = 2019
EXCLUDE_LOW_ALCOHOL = True
alcohol_threshold = 0.1  # litres of pure alcohol per capita
# ---------------------

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# 1. Load CSV files
df_alcohol = pd.read_csv('data/total-alcohol-consumption-per-capita-litres-of-pure-alcohol.csv')
df_life = pd.read_csv('data/life-expectancy-at-birth-who-gho.csv')
df_country_code = pd.read_csv('data/country-and-continent-codes-list-csv.csv')
df_gdp = pd.read_csv('data/gdp-per-capita-worldbank.csv')

# 2. Rename columns for clean merging
df_alcohol.columns = ['Country', 'Code', 'Year', 'Alcohol_Consumption']
df_life.columns = ['Country', 'Code', 'Year', 'Life_Expectancy']
df_gdp.columns = ['Country', 'Code', 'Year', 'GDP_per_Capita', 'Continent_Name']

# 3. Filter for the Target Year
df_alcohol_year = df_alcohol[df_alcohol['Year'] == TARGET_YEAR]
df_life_year = df_life[df_life['Year'] == TARGET_YEAR]
df_gdp_year = df_gdp[df_gdp['Year'] == TARGET_YEAR]

print(f"df_alcohol_year: {len(df_alcohol_year)} rows")
print(f"df_life_year:    {len(df_life_year)} rows")
print(f"df_gdp_year:     {len(df_gdp_year)} rows")

# ---------------------------------------------------------
# TRACKER: one row per ISO code, one 0/1 column per condition.
# df_country_code is the universe -- it's the most complete list of valid
# ISO codes, so every code in the other tables should be a subset of it.
# ---------------------------------------------------------
tracker = df_country_code[['Three_Letter_Country_Code']].dropna().drop_duplicates()
tracker.columns = ['Code']
print(f"ISO reference universe: {len(tracker)} codes")

# Attach a readable country name from the reference table itself -- it's the
# only table with full coverage of every code in the universe. (If this
# column name doesn't match your CSV, run print(df_country_code.columns)
# to find the right one -- 'Country_Name' is standard for this particular
# reference file.)
name_lookup = df_country_code[['Three_Letter_Country_Code', 'Country_Name']].dropna(subset=['Three_Letter_Country_Code'])
name_lookup = name_lookup.drop_duplicates(subset='Three_Letter_Country_Code')
name_lookup.columns = ['Code', 'Country']
tracker = tracker.merge(name_lookup, on='Code', how='left')


def add_flag(tracker, source_df, flag_name, id_col='Code'):
    """Add a 0/1 column marking which tracker Codes appear in source_df.
    Always test against an ORIGINAL per-source dataframe (df_alcohol_year,
    df_life_year, ...), never against an already-merged result -- otherwise
    a country that dropped out at an earlier step gets blamed for a later
    one too, and you lose the ability to tell them apart."""
    tracker[flag_name] = tracker[id_col].isin(source_df[id_col]).astype(int)
    return tracker


add_flag(tracker, df_alcohol_year, 'in_alcohol')
add_flag(tracker, df_life_year, 'in_life')
add_flag(tracker, df_gdp_year, 'in_gdp')
if EXCLUDE_LOW_ALCOHOL:
    above_thresh = df_alcohol_year.loc[df_alcohol_year['Alcohol_Consumption'] >= alcohol_threshold, ['Code']]
    add_flag(tracker, above_thresh, 'above_thresh')

# --- everything below is your original pipeline, unchanged ---

# 4. First Merge: Alcohol + Life Expectancy
final_df = pd.merge(
    df_alcohol_year, df_life_year,
    on=['Code', 'Country', 'Year'], how='inner'
)
print('size of final_df after first merge:', final_df.shape)

final_df = final_df.dropna(subset=['Code'])
print('size of final_df after dropping rows with missing ISO codes:', final_df.shape)

# 5. Prepare Continent Data & Deduplicate
df_country_code_clean = df_country_code[['Three_Letter_Country_Code', 'Continent_Name']].copy()
df_country_code_clean.columns = ['Code', 'Continent']
df_country_code_clean = df_country_code_clean.drop_duplicates(subset=['Code'], keep='first')

# 6. Second Merge: Add Continent Column
final_df_step2 = pd.merge(final_df, df_country_code_clean, on='Code', how='inner')

# 7. Third Merge: Add GDP Data
final_df_all = pd.merge(final_df_step2, df_gdp_year[['Code', 'GDP_per_Capita']], on='Code', how='inner')

total_countries = len(final_df_all)
if EXCLUDE_LOW_ALCOHOL:
    final_df_all = final_df_all[final_df_all['Alcohol_Consumption'] >= alcohol_threshold]
total_countries_after_filter = len(final_df_all)
print(f"\nTotal Countries in {TARGET_YEAR}: {total_countries}")
print(f"Countries with >= {alcohol_threshold} litre of alcohol consumption: {total_countries_after_filter}")

# ---------------------------------------------------------
# AUDIT: which countries are missing from the final sample, and why
# ---------------------------------------------------------
condition_cols = ['in_alcohol', 'in_life', 'in_gdp']
if EXCLUDE_LOW_ALCOHOL:
    condition_cols.append('above_thresh')

tracker['in_final_sample'] = tracker[condition_cols].all(axis=1).astype(int)

# 'in_any_source' separates a genuine gap (a country that appears in at
# least one real dataset but still failed some condition) from an entry
# that was never a plausible candidate to begin with (e.g. Antarctica,
# Bouvet Island) -- the ~250-code ISO universe is much broader than what
# any of these three datasets actually covers.
tracker['in_any_source'] = tracker[['in_alcohol', 'in_life', 'in_gdp']].any(axis=1).astype(int)

dropped = tracker[tracker['in_final_sample'] == 0]
dropped_relevant = dropped[dropped['in_any_source'] == 1]
dropped_irrelevant = dropped[dropped['in_any_source'] == 0]

print(f"\nCodes appearing in >=1 real source table: {tracker['in_any_source'].sum()} / {len(tracker)}")
print(f"Final analytic sample: {tracker['in_final_sample'].sum()} countries")
print(f"\n{len(dropped)} total codes excluded, of which:")
print(f"  {len(dropped_relevant)} are real countries missing from >=1 source -- a genuine gap")
print(f"  {len(dropped_irrelevant)} never appeared in ANY source -- territory/region with no data at all")

print(f"\n--- Genuine gaps (in >=1 source, but not the final sample) ---")
print(dropped_relevant[['Code', 'Country'] + condition_cols].to_string(index=False))

Path('outputs').mkdir(parents=True, exist_ok=True)
tracker.to_csv('outputs/country_tracker.csv', index=False)

# 8. Create GDP Categories (Quartiles)
gdp_labels = ['Low Income', 'Lower-Middle', 'Upper-Middle', 'High Income']
final_df_all['GDP_Category'] = pd.qcut(final_df_all['GDP_per_Capita'], q=4, labels=gdp_labels)

# --- rest of your script (correlation analysis, plots) continues unchanged ---