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

# ===========================================================
# 1. LOAD & CLEAN SOURCE TABLES
# ===========================================================
# Column naming convention used throughout this script:
#   ISO_Code      -- ISO 3166-1 alpha-3 country code, the join key everywhere
#   Country_Name  -- human-readable country name
#   Continent     -- the country's continent, resolved once below in
#                     df_country_code and never redefined anywhere else

df_alcohol = pd.read_csv('data/total-alcohol-consumption-per-capita-litres-of-pure-alcohol.csv')
df_alcohol.columns = ['Country_Name', 'ISO_Code', 'Year', 'Alcohol_Consumption']

df_life = pd.read_csv('data/life-expectancy-at-birth-who-gho.csv')
df_life.columns = ['Country_Name', 'ISO_Code', 'Year', 'Life_Expectancy']

df_gdp = pd.read_csv('data/gdp-per-capita-worldbank.csv')
df_gdp.columns = ['Country_Name', 'ISO_Code', 'Year', 'GDP_per_Capita', 'Continent_Name']
df_gdp = df_gdp[['Country_Name', 'ISO_Code', 'Year', 'GDP_per_Capita']]

df_country_code = pd.read_csv('data/country-and-continent-codes-list-csv.csv')
df_country_code = df_country_code[['Three_Letter_Country_Code', 'Country_Name', 'Continent_Name']]
df_country_code.columns = ['ISO_Code', 'Country_Name', 'Continent']

# Rows with no ISO code at all are disputed territories / neutral zones with
# no real country behind them -- drop before doing anything else with this
# table, since a missing key can't be usefully deduplicated or joined on.
df_country_code = df_country_code.dropna(subset=['ISO_Code'])

# A handful of codes legitimately appear twice, because the country (or its
# outlying territories) spans two continents. Rather than an
# arbitrary keep='first', resolve each one explicitly by which continent
# holds the larger share of the country's land area. This is a real
# judgment call -- population-weighted or political/EU classification would
# give different answers for several of these (Cyprus and Turkey
# especially) -- but landmass is the rule applied consistently here.
manual_continent = {
    'ARM': 'Asia',      # Armenia -- entirely in the South Caucasus
    'AZE': 'Asia',      # Azerbaijan -- entirely in the South Caucasus/Caspian basin
    'CYP': 'Asia',      # Cyprus -- the island sits on the Anatolian continental shelf
    'GEO': 'Asia',      # Georgia -- most territory lies south of the Caucasus watershed
    'KAZ': 'Asia',      # Kazakhstan -- only a sliver west of the Ural river is in Europe
    'RUS': 'Asia',      # Russia -- ~77% of land area lies east of the Urals
    'TUR': 'Asia',      # Turkey -- European Thrace is ~3% of total land area
    'UMI': 'Oceania',   # US Minor Outlying Islands -- mostly Pacific atolls; only Navassa Island is Caribbean/North America
}

is_duplicated = df_country_code['ISO_Code'].duplicated(keep=False)
unambiguous = df_country_code[~is_duplicated]
resolved = df_country_code[
    is_duplicated & (df_country_code['ISO_Code'].map(manual_continent) == df_country_code['Continent'])
]
df_country_code = pd.concat([unambiguous, resolved]).sort_values('ISO_Code').reset_index(drop=True)

# Safety net: fail loudly if the source data ever introduces a duplicate
# this table doesn't already account for, instead of silently keep='first'-ing it.
still_duplicated = df_country_code[df_country_code['ISO_Code'].duplicated(keep=False)]
assert len(still_duplicated) == 0, f"Unresolved duplicate ISO codes -- extend manual_continent:\n{still_duplicated}"

# df_country_code is now exactly one row per ISO_Code, with Country_Name and
# Continent both resolved -- every merge and lookup below can just use it
# directly, with no separate "_clean" copy needed.

# ===========================================================
# 2. FILTER FOR THE TARGET YEAR
# ===========================================================
df_alcohol_year = df_alcohol[df_alcohol['Year'] == TARGET_YEAR]
df_life_year = df_life[df_life['Year'] == TARGET_YEAR]
df_gdp_year = df_gdp[df_gdp['Year'] == TARGET_YEAR]

print(f"df_alcohol_year: {len(df_alcohol_year)} rows")
print(f"df_life_year:    {len(df_life_year)} rows")
print(f"df_gdp_year:     {len(df_gdp_year)} rows")

# ===========================================================
# 3. MERGE
# ===========================================================
# 3a. Alcohol + Life Expectancy
final_df = pd.merge(
    df_alcohol_year, df_life_year,
    on=['ISO_Code', 'Country_Name', 'Year'], how='inner'
)
print('size of final_df after first merge:', final_df.shape)

# Remove regional total rows (e.g. "World", "Africa") that lack an ISO code
final_df = final_df.dropna(subset=['ISO_Code'])
print('size of final_df after dropping rows with missing ISO codes:', final_df.shape)

# 3b. Add Continent
final_df_step2 = pd.merge(
    final_df, df_country_code[['ISO_Code', 'Continent']],
    on='ISO_Code', how='inner'
)

# 3c. Add GDP
final_df_all = pd.merge(
    final_df_step2, df_gdp_year[['ISO_Code', 'GDP_per_Capita']],
    on='ISO_Code', how='inner'
)

total_countries = len(final_df_all)
if EXCLUDE_LOW_ALCOHOL:
    final_df_all = final_df_all[final_df_all['Alcohol_Consumption'] >= alcohol_threshold]
total_countries_after_filter = len(final_df_all)
print(f"\nTotal Countries in {TARGET_YEAR}: {total_countries}")
print(f"Countries with >= {alcohol_threshold} litre of alcohol consumption: {total_countries_after_filter}")

# 4. Create GDP Categories (Quartiles)
gdp_labels = ['Low Income', 'Lower-Middle', 'Upper-Middle', 'High Income']
final_df_all['GDP_Category'] = pd.qcut(final_df_all['GDP_per_Capita'], q=4, labels=gdp_labels)

# ---------------------------------------------------------
# CORRELATION ANALYSIS (3x3 Matrix)
# ---------------------------------------------------------
print(f"\n--- CORRELATION MATRIX ({TARGET_YEAR}) ---")
corr_matrix = final_df_all[['Alcohol_Consumption', 'Life_Expectancy', 'GDP_per_Capita']].corr()
print(corr_matrix.round(3))
print("----------------------------------------\n")

print("\n1. BY CONTINENT:")
for continent, group in final_df_all.groupby('Continent'):
    if len(group) > 1:
        corr = group['Alcohol_Consumption'].corr(group['Life_Expectancy'])
        print(f"  - {continent}: r = {corr:.3f} (n={len(group)})")
    else:
        print(f"  - {continent}: Not enough data")

print("\n2. BY ECONOMIC STATUS (GDP Category):")
for category, group in final_df_all.groupby('GDP_Category', observed=False):
    if len(group) > 1:
        corr = group['Alcohol_Consumption'].corr(group['Life_Expectancy'])
        print(f"  - {category}: r = {corr:.3f} (n={len(group)})")
    else:
        print(f"  - {category}: Not enough data")
print("----------------------------------------\n")

# ---------------------------------------------------------
# PLOT 1: Single Color Scatter Plot (No Continent Grouping)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.scatter(
    final_df_all['Alcohol_Consumption'],
    final_df_all['Life_Expectancy'],
    alpha=0.7,
    edgecolors='k'
)
plt.title(f'Alcohol Consumption vs Life Expectancy ({TARGET_YEAR})', fontsize=14)
plt.xlabel('Alcohol Consumption (Litres of Pure Alcohol per Capita)', fontsize=12)
plt.ylabel('Life Expectancy at Birth (Years)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# PLOT 2: Multi-Color Scatter Plot (Grouped by Continent)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
for continent, group in final_df_all.groupby('Continent'):
    plt.scatter(
        group['Alcohol_Consumption'],
        group['Life_Expectancy'],
        label=continent,
        alpha=0.7,
        edgecolors='k',
        s=50
    )
plt.title(f'Alcohol Consumption vs Life Expectancy by Continent ({TARGET_YEAR})', fontsize=14)
plt.xlabel('Alcohol Consumption (Litres of Pure Alcohol per Capita)', fontsize=12)
plt.ylabel('Life Expectancy at Birth (Years)', fontsize=12)
plt.legend(title='Continent', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# PLOT 3: Life Expectancy vs GDP (Log Scale)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.scatter(
    final_df_all['GDP_per_Capita'],
    final_df_all['Life_Expectancy'],
    alpha=0.7,
    edgecolors='k',
    color='mediumseagreen'
)
plt.xscale('log')
plt.title(f'Life Expectancy vs GDP per Capita ({TARGET_YEAR})', fontsize=14)
plt.xlabel('GDP per Capita (Log Scale)', fontsize=12)
plt.ylabel('Life Expectancy at Birth (Years)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# PLOT 4: Alcohol Consumption vs GDP (Log Scale)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.scatter(
    final_df_all['GDP_per_Capita'],
    final_df_all['Alcohol_Consumption'],
    alpha=0.7,
    edgecolors='k',
    color='coral'
)
plt.xscale('log')
plt.title(f'Alcohol Consumption vs GDP per Capita ({TARGET_YEAR})', fontsize=14)
plt.xlabel('GDP per Capita (Log Scale)', fontsize=12)
plt.ylabel('Alcohol Consumption (Litres per Capita)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# PLOT 5: Multi-Color Scatter Plot (Grouped by GDP Category)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
for category, group in final_df_all.groupby('GDP_Category', observed=False):
    plt.scatter(
        group['Alcohol_Consumption'],
        group['Life_Expectancy'],
        label=category,
        alpha=0.7,
        edgecolors='k',
        s=50
    )
plt.title(f'Alcohol Consumption vs Life Expectancy by GDP Bracket ({TARGET_YEAR})', fontsize=14)
plt.xlabel('Alcohol Consumption (Litres of Pure Alcohol per Capita)', fontsize=12)
plt.ylabel('Life Expectancy at Birth (Years)', fontsize=12)
plt.legend(title='GDP Category', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# ===========================================================
# TRACKER (documentation only)
# ===========================================================
# Nothing above this point depends on anything below it. This section
# exists purely to make the data-cleaning/merging process auditable: for
# every ISO code in the reference universe, which source tables it
# appeared in, and whether it made the final analytic sample.
# df_country_code is already one row per ISO_Code with Country_Name
# attached, so building the tracker is now a one-liner.
# ---------------------------------------------------------
tracker = df_country_code[['ISO_Code', 'Country_Name']].copy()


def add_flag(tracker, source_df, flag_name, id_col='ISO_Code'):
    """Add a 0/1 column marking which tracker codes appear in source_df.
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
    above_thresh = df_alcohol_year.loc[df_alcohol_year['Alcohol_Consumption'] >= alcohol_threshold, ['ISO_Code']]
    add_flag(tracker, above_thresh, 'above_thresh')

condition_cols = ['in_alcohol', 'in_life', 'in_gdp']
if EXCLUDE_LOW_ALCOHOL:
    condition_cols.append('above_thresh')

tracker['in_final_sample'] = tracker[condition_cols].all(axis=1).astype(int)

# 'in_any_source' separates a genuine gap (a country that appears in at
# least one real dataset but still failed some condition) from an entry
# that was never a plausible candidate to begin with (e.g. Antarctica,
# Bouvet Island).
tracker['in_any_source'] = tracker[['in_alcohol', 'in_life', 'in_gdp']].any(axis=1).astype(int)

dropped = tracker[tracker['in_final_sample'] == 0]
dropped_relevant = dropped[dropped['in_any_source'] == 1]
dropped_irrelevant = dropped[dropped['in_any_source'] == 0]

print(f"\nISO reference universe: {len(tracker)} codes")
print(f"Codes appearing in >=1 real source table: {tracker['in_any_source'].sum()} / {len(tracker)}")
print(f"Final analytic sample: {tracker['in_final_sample'].sum()} countries")
print(f"\n{len(dropped)} total codes excluded, of which:")
print(f"  {len(dropped_relevant)} are real countries missing from >=1 source -- a genuine gap")
print(f"  {len(dropped_irrelevant)} never appeared in ANY source -- territory/region with no data at all")

print(f"\n--- Genuine gaps (in >=1 source, but not the final sample) ---")
print(dropped_relevant[['ISO_Code', 'Country_Name'] + condition_cols].to_string(index=False))

Path('outputs').mkdir(parents=True, exist_ok=True)
tracker.to_csv('outputs/country_tracker.csv', index=False)