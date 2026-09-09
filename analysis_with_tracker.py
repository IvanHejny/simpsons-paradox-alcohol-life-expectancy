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
n_raw = len(df_country_code)

df_country_code = df_country_code[['Three_Letter_Country_Code', 'Country_Name', 'Continent_Name']]
df_country_code.columns = ['ISO_Code', 'Country_Name', 'Continent']

# Rows with no ISO code at all are disputed territories / neutral zones with
# no real country behind them -- drop before doing anything else with this
# table, since a missing key can't be usefully deduplicated or joined on.
df_country_code = df_country_code.dropna(subset=['ISO_Code'])
n_after_dropna = len(df_country_code)

# A handful of codes legitimately appear twice, because the country (or its
# outlying territories) spans two continents. Rather than an arbitrary
# keep='first', resolve each one explicitly by which continent holds the
# larger share of the country's land area. This is a real judgment call --
# population-weighted or political/EU classification would give different
# answers for several of these (Cyprus and Turkey especially) -- but
# landmass is the rule applied consistently here.
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

is_duplicated = df_country_code['ISO_Code'].duplicated(keep=False) # df with true for all rows that have a duplicate ISO_Code somewhere in the table
n_duplicate_codes = df_country_code.loc[is_duplicated, 'ISO_Code'].nunique() # number of unique ISO codes that appear more than once in the table

unambiguous = df_country_code[~is_duplicated]
resolved = df_country_code[
    is_duplicated & (df_country_code['ISO_Code'].map(manual_continent) == df_country_code['Continent'])
]
df_country_code = pd.concat([unambiguous, resolved]).sort_values('ISO_Code').reset_index(drop=True)

# Safety net: fail loudly if the source data ever introduces a duplicate
# this table doesn't already account for, instead of silently keep='first'-ing it.
still_duplicated = df_country_code[df_country_code['ISO_Code'].duplicated(keep=False)]
assert len(still_duplicated) == 0, f"Unresolved duplicate ISO codes -- extend manual_continent:\n{still_duplicated}"

print(f"df_country_code: {n_raw} raw rows -> {n_after_dropna} after dropping missing ISO_Code "
      f"-> {len(df_country_code)} unique ISO codes after resolving {n_duplicate_codes} duplicated codes")

# Sanity check: alcohol/life/gdp should never have a missing ISO_Code -- only
# the reference table does (disputed territories, neutral zones), already
# handled above. Fail loudly if that assumption ever breaks, rather than
# silently dropping rows somewhere downstream.
assert df_alcohol['ISO_Code'].notna().all(), "df_alcohol has rows with missing ISO_Code"
assert df_life['ISO_Code'].notna().all(), "df_life has rows with missing ISO_Code"
assert df_gdp['ISO_Code'].notna().all(), "df_gdp has rows with missing ISO_Code"
print("Checked: df_alcohol, df_life, df_gdp all have complete ISO_Code coverage (no missing keys).")

# df_country_code is now exactly one row per ISO_Code, with Country_Name and
# Continent both resolved -- every merge and lookup below can just use it
# directly, with no separate "_clean" copy needed.

# Remove aggregate ISO that are not for single countries such as WB_, OWID_, WHO_,
valid_iso = set(df_country_code['ISO_Code'])
df_alcohol = df_alcohol[df_alcohol['ISO_Code'].isin(valid_iso)].copy()
df_life    = df_life[df_life['ISO_Code'].isin(valid_iso)].copy()
df_gdp     = df_gdp[df_gdp['ISO_Code'].isin(valid_iso)].copy()

# ===========================================================
# 2. FILTER FOR THE TARGET YEAR
# ===========================================================
df_alcohol_year = df_alcohol[df_alcohol['Year'] == TARGET_YEAR]
df_life_year = df_life[df_life['Year'] == TARGET_YEAR]
df_gdp_year = df_gdp[df_gdp['Year'] == TARGET_YEAR]

print(f"\n--- After removing aggregate ISOs that do not appear in df_country_code such as WB_, OWID_, WHO_ we get for ({TARGET_YEAR}) ---")
print(f"df_alcohol_year: {len(df_alcohol_year)} rows")
print(f"df_life_year:    {len(df_life_year)} rows")
print(f"df_gdp_year:     {len(df_gdp_year)} rows")

# ===========================================================
# 3. MERGE
# ===========================================================
# Each step is an inner join, so a country survives only if it is present in
# every table joined so far. Names track what has been added, not "step N":
#   alc_life       -- alcohol + life expectancy
#   alc_life_cont  -- + continent
#   analytic_df    -- + GDP; this is the analysis sample (later filtered in place)

# 3a. Alcohol + Life Expectancy
alc_life = pd.merge(
    df_alcohol_year, df_life_year,
    on=['ISO_Code', 'Country_Name', 'Year'], how='inner'
)
print('size of alc_life after first merge (alc + life):', alc_life.shape)

# 3b. Add Continent
alc_life_cont = pd.merge(
    alc_life, df_country_code[['ISO_Code', 'Continent']],
    on='ISO_Code', how='inner'
)
print('size of alc_life_cont after second merge (+ continent):', alc_life_cont.shape)

# 3c. Add GDP
analytic_df = pd.merge(
    alc_life_cont, df_gdp_year[['ISO_Code', 'GDP_per_Capita']],
    on='ISO_Code', how='inner'
)
print('size of analytic_df after third merge (+ gdp):', analytic_df.shape)

total_countries = len(analytic_df)
if EXCLUDE_LOW_ALCOHOL:
    analytic_df = analytic_df[analytic_df['Alcohol_Consumption'] >= alcohol_threshold].copy()
total_countries_after_filter = len(analytic_df)
print(f"\nTotal Countries in final dataframe {TARGET_YEAR}: {total_countries}")
print(f"Countries with >= {alcohol_threshold} litre of alcohol consumption: {total_countries_after_filter}")

# 4. Create GDP Categories (Quartiles)
gdp_labels = ['Low Income', 'Lower-Middle', 'Upper-Middle', 'High Income']
analytic_df['GDP_Category'] = pd.qcut(analytic_df['GDP_per_Capita'], q=4, labels=gdp_labels)

# ---------------------------------------------------------
# CORRELATION ANALYSIS (3x3 Matrix)
# ---------------------------------------------------------
print(f"\n--- CORRELATION MATRIX ({TARGET_YEAR}) ---")
corr_matrix = analytic_df[['Alcohol_Consumption', 'Life_Expectancy', 'GDP_per_Capita']].corr()
print(corr_matrix.round(3))
print("----------------------------------------\n")

print("\n1. BY CONTINENT:")
for continent, group in analytic_df.groupby('Continent'):
    if len(group) > 1:
        corr = group['Alcohol_Consumption'].corr(group['Life_Expectancy'])
        print(f"  - {continent}: r = {corr:.3f} (n={len(group)})")
    else:
        print(f"  - {continent}: Not enough data")

print("\n2. BY ECONOMIC STATUS (GDP Category):")
for category, group in analytic_df.groupby('GDP_Category', observed=False):
    if len(group) > 1:
        corr = group['Alcohol_Consumption'].corr(group['Life_Expectancy'])
        print(f"  - {category}: r = {corr:.3f} (n={len(group)})")
    else:
        print(f"  - {category}: Not enough data")
print("----------------------------------------\n")

# ---------------------------------------------------------
# SCATTER HELPER
# All five plots below are the same figure -- 10x6, alpha 0.7, black
# edges, dashed grid -- differing only in columns, log scaling, and
# whether points are split by a grouping column. Build them from one place.
# ---------------------------------------------------------
def scatter_plot(x, y, xlabel, ylabel, title, logx=False, group_col=None, **scatter_kw):
    plt.figure(figsize=(10, 6))
    if group_col is None:
        plt.scatter(analytic_df[x], analytic_df[y], alpha=0.7, edgecolors='k', **scatter_kw)
    else:
        for name, group in analytic_df.groupby(group_col, observed=False):
            plt.scatter(group[x], group[y], label=name, alpha=0.7, edgecolors='k', s=50)
        plt.legend(title=group_col.replace('_', ' '), bbox_to_anchor=(1.05, 1), loc='upper left')
    if logx:
        plt.xscale('log')
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()


ALCOHOL_LABEL = 'Alcohol Consumption (Litres of Pure Alcohol per Capita)'
LIFE_LABEL = 'Life Expectancy at Birth (Years)'
GDP_LABEL = 'GDP per Capita (Log Scale)'

# PLOT 1: alcohol vs life expectancy, all countries together
scatter_plot(
    'Alcohol_Consumption', 'Life_Expectancy', ALCOHOL_LABEL, LIFE_LABEL,
    f'Alcohol Consumption vs Life Expectancy ({TARGET_YEAR})',
)

# PLOT 2: same, split by continent
scatter_plot(
    'Alcohol_Consumption', 'Life_Expectancy', ALCOHOL_LABEL, LIFE_LABEL,
    f'Alcohol Consumption vs Life Expectancy by Continent ({TARGET_YEAR})',
    group_col='Continent',
)

# PLOT 3: life expectancy vs GDP (log scale)
scatter_plot(
    'GDP_per_Capita', 'Life_Expectancy', GDP_LABEL, LIFE_LABEL,
    f'Life Expectancy vs GDP per Capita ({TARGET_YEAR})',
    logx=True, color='mediumseagreen',
)

# PLOT 4: alcohol vs GDP (log scale)
scatter_plot(
    'GDP_per_Capita', 'Alcohol_Consumption', GDP_LABEL, 'Alcohol Consumption (Litres per Capita)',
    f'Alcohol Consumption vs GDP per Capita ({TARGET_YEAR})',
    logx=True, color='coral',
)

# PLOT 5: alcohol vs life expectancy, split by GDP bracket
scatter_plot(
    'Alcohol_Consumption', 'Life_Expectancy', ALCOHOL_LABEL, LIFE_LABEL,
    f'Alcohol Consumption vs Life Expectancy by GDP Bracket ({TARGET_YEAR})',
    group_col='GDP_Category',
)

# ===========================================================
# TRACKER (documentation only)
# ===========================================================
# Nothing above this point depends on anything below it. This section
# exists purely to make the merging pipeline auditable: starting from the
# ISO_Code universe resolved in Section 1, track which countries appear in
# all three data sources, and of those, which pass the alcohol threshold --
# the same two-stage logic the pipeline above applies, just made explicit.
# ---------------------------------------------------------
tracker = df_country_code[['ISO_Code', 'Country_Name']].copy()


def flag_membership(tracker, source_df, id_col='ISO_Code'):
    """Return a 0/1 Series: for each row in tracker, whether its id_col
    value appears anywhere in source_df's id_col column. Always pass an
    ORIGINAL per-source dataframe (df_alcohol_year, df_life_year, ...),
    never an already-merged result -- otherwise a country that dropped out
    at an earlier step gets blamed for a later one too, and you lose the
    ability to tell them apart."""
    return tracker[id_col].isin(source_df[id_col]).astype(int)


tracker['in_alcohol'] = flag_membership(tracker, df_alcohol_year)
tracker['in_life'] = flag_membership(tracker, df_life_year)
tracker['in_gdp'] = flag_membership(tracker, df_gdp_year)
tracker['in_all_three_sources'] = tracker[['in_alcohol', 'in_life', 'in_gdp']].all(axis=1).astype(int)

if EXCLUDE_LOW_ALCOHOL:
    above_thresh_codes = df_alcohol_year.loc[df_alcohol_year['Alcohol_Consumption'] >= alcohol_threshold, ['ISO_Code']]
    tracker['above_thresh'] = flag_membership(tracker, above_thresh_codes)
    tracker['in_final_sample'] = (tracker['in_all_three_sources'] & tracker['above_thresh']).astype(int)
else:
    tracker['in_final_sample'] = tracker['in_all_three_sources']

# --- Pipeline overview: the same waterfall as the main pipeline above,
# just expressed as tracker counts instead of successive merges. ---
n_universe = len(tracker)
n_all_three = tracker['in_all_three_sources'].sum()
n_missing_source = n_universe - n_all_three
n_final = tracker['in_final_sample'].sum()

# The tracker counts are built independently of the merge chain above (set
# membership per source, vs. successive inner joins). They must still agree:
# if this fires, the two have drifted and one of them is wrong.
assert n_all_three == total_countries, (n_all_three, total_countries)
if EXCLUDE_LOW_ALCOHOL:
    assert n_final == total_countries_after_filter, (n_final, total_countries_after_filter)

print(f"\n--- PIPELINE OVERVIEW ---")
print(f"ISO reference universe:                 {n_universe}")
print(f"  missing from either one of alcohol/life/gdp: -{n_missing_source}")
print(f"  present in all three sources:          {n_all_three}")
if EXCLUDE_LOW_ALCOHOL:
    n_dropped_threshold = n_all_three - n_final
    print(f"  below alcohol threshold ({alcohol_threshold} L):     -{n_dropped_threshold}")
print(f"  final analytic sample:                 {n_final}")

# --- Detail: exactly which countries fell out, and at which stage ---
missing_source = tracker[tracker['in_all_three_sources'] == 0]
print(f"\n--- {len(missing_source)} countries missing from at least one source ---")
print(missing_source[['ISO_Code', 'Country_Name', 'in_alcohol', 'in_life', 'in_gdp']].to_string(index=False))

if EXCLUDE_LOW_ALCOHOL:
    below_threshold = tracker[(tracker['in_all_three_sources'] == 1) & (tracker['above_thresh'] == 0)]
    print(f"\n--- {len(below_threshold)} countries in all three sources but below the alcohol threshold ---")
    print(below_threshold[['ISO_Code', 'Country_Name']].to_string(index=False))

Path('outputs').mkdir(parents=True, exist_ok=True)
tracker.to_csv('outputs/country_tracker.csv', index=False)