import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
# Change this variable to analyze a different year
TARGET_YEAR = 2019
# Set to True to remove countries with < 1 litre of alcohol consumption
EXCLUDE_LOW_ALCOHOL = True
alcohol_threshold = 0.1  # litres of pure alcohol per capita
# ---------------------

# Increase printing width to view all columns in the console
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

# 1. Load CSV files
df_alcohol = pd.read_csv('total-alcohol-consumption-per-capita-litres-of-pure-alcohol.csv')
df_life = pd.read_csv('life-expectancy-at-birth-who-gho.csv')
df_country_code = pd.read_csv('country-and-continent-codes-list-csv.csv')
df_gdp = pd.read_csv('gdp-per-capita-worldbank.csv')

# 2. Rename columns for clean merging
df_alcohol.columns = ['Country', 'Code', 'Year', 'Alcohol_Consumption']
df_life.columns = ['Country', 'Code', 'Year', 'Life_Expectancy']
df_gdp.columns = ['Country', 'Code', 'Year', 'GDP_per_Capita', 'Continent_Name']

# 3. Filter for the Target Year
df_alcohol_year = df_alcohol[df_alcohol['Year'] == TARGET_YEAR]
df_life_year = df_life[df_life['Year'] == TARGET_YEAR]
df_gdp_year = df_gdp[df_gdp['Year'] == TARGET_YEAR]

# 4. First Merge: Alcohol + Life Expectancy
# Merging on ['Code', 'Country', 'Year'] avoids duplicate '_x' and '_y' columns
final_df = pd.merge(
    df_alcohol_year,
    df_life_year,
    on=['Code', 'Country', 'Year'],
    how='inner'
)

# Remove regional total rows that lack an ISO code
final_df = final_df.dropna(subset=['Code'])

# 5. Prepare Continent Data & Deduplicate
df_country_code = df_country_code[['Three_Letter_Country_Code', 'Continent_Name']]
df_country_code.columns = ['Code', 'Continent']

# Drop duplicate ISO codes (e.g., transcontinental nations) to ensure 1-to-1 matching
df_country_code_clean = df_country_code.drop_duplicates(subset=['Code'], keep='first')

# 6. Second Merge: Add Continent Column
final_df_step2 = pd.merge(
    final_df,
    df_country_code_clean,
    on='Code',
    how='inner'
)

# 7. Third Merge: Add GDP Data
# We only merge on 'Code' and bring over the GDP column to keep things clean
final_df_all = pd.merge(
    final_df_step2,
    df_gdp_year[['Code', 'GDP_per_Capita']],
    on='Code',
    how='inner'
)


total_countries = len(final_df_all)
# Optional: Exclude low-consuming countries

if EXCLUDE_LOW_ALCOHOL:
    final_df_all = final_df_all[final_df_all['Alcohol_Consumption'] >= alcohol_threshold]
total_countries_after_filter = len(final_df_all)
# Also, write how many countries remain and what was the total
print(f"\nTotal Countries in {TARGET_YEAR}: {total_countries}")
print(f"Countries with >= {alcohol_threshold} litre of alcohol consumption: {total_countries_after_filter}")


# 8. Create GDP Categories (Quartiles)
# pd.qcut divides the countries into 4 equally sized groups based on wealth
gdp_labels = ['Low Income', 'Lower-Middle', 'Upper-Middle', 'High Income']
final_df_all['GDP_Category'] = pd.qcut(final_df_all['GDP_per_Capita'], q=4, labels=gdp_labels)



# ---------------------------------------------------------
# CORRELATION ANALYSIS (3x3 Matrix)
# ---------------------------------------------------------
print(f"\n--- CORRELATION MATRIX ({TARGET_YEAR}) ---")

# Create a simple 3x3 correlation matrix for the 3 main numeric variables
corr_matrix = final_df_all[['Alcohol_Consumption', 'Life_Expectancy', 'GDP_per_Capita']].corr()
print(corr_matrix.round(3))

print("----------------------------------------\n")


# Regional Correlation
print("\n1. BY CONTINENT:")
for continent, group in final_df_all.groupby('Continent'):
    if len(group) > 1:
        corr = group['Alcohol_Consumption'].corr(group['Life_Expectancy'])
        print(f"  - {continent}: r = {corr:.3f} (n={len(group)})")
    else:
        print(f"  - {continent}: Not enough data")

# Economic Correlation
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
# Loop through each continent group and plot them with a label
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
# We use a log scale here to unbunch the lower-income nations (Preston Curve)
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
# Loop through each wealth quartile and plot them with a label
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

