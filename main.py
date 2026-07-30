import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
# Change this variable to analyze a different year
TARGET_YEAR = 2019
# ---------------------

# Increase printing width to view all columns
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
# We assume the user's gdp file has 5 columns. We will drop the 5th to avoid conflicts.
df_gdp.columns = ['Country', 'Code', 'Year', 'GDP_per_Capita', 'Continent_Name_Drop']

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

# Drop duplicate ISO codes to ensure 1-to-1 matching
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

# 8. Create GDP Categories (Quartiles)
# pd.qcut divides the countries into 4 equally sized groups based on wealth
gdp_labels = ['Low Income', 'Lower-Middle', 'Upper-Middle', 'High Income']
final_df_all['GDP_Category'] = pd.qcut(final_df_all['GDP_per_Capita'], q=4, labels=gdp_labels)


# ---------------------------------------------------------
# CORRELATION ANALYSIS
# ---------------------------------------------------------
print(f"\n--- CORRELATION COEFFICIENTS ({TARGET_YEAR}) ---")

# Global Correlation
global_corr = final_df_all['Alcohol_Consumption'].corr(final_df_all['Life_Expectancy'])

# Regional Correlation
print("\n1. BY CONTINENT:")
print(f"  - Global (All Countries): r = {global_corr:.3f}")
for continent, group in final_df_all.groupby('Continent'):
    if len(group) > 1:
        corr = group['Alcohol_Consumption'].corr(group['Life_Expectancy'])
        print(f"  - {continent}: r = {corr:.3f} (n={len(group)})")
    else:
        print(f"  - {continent}: Not enough data")

# Economic Correlation
print("\n2. BY ECONOMIC STATUS (GDP Category):")
print(f"  - Global (All Countries): r = {global_corr:.3f}")
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
    alpha=0.7, edgecolors='k'
)
plt.title(f'Alcohol Consumption vs Life Expectancy ({TARGET_YEAR})', fontsize=14)
plt.xlabel('Alcohol Consumption (Litres per Capita)', fontsize=12)
plt.ylabel('Life Expectancy (Years)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# PLOT 2: Scatter Plot (Grouped by Continent)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
for continent, group in final_df_all.groupby('Continent'):
    plt.scatter(
        group['Alcohol_Consumption'],
        group['Life_Expectancy'],
        label=continent, alpha=0.7, edgecolors='k', s=50
    )
plt.title(f'Alcohol vs Life Expectancy by Continent ({TARGET_YEAR})', fontsize=14)
plt.xlabel('Alcohol Consumption (Litres per Capita)', fontsize=12)
plt.ylabel('Life Expectancy (Years)', fontsize=12)
plt.legend(title='Continent', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# PLOT 3: Life Expectancy vs GDP per Capita (The Preston Curve)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.scatter(
    final_df_all['GDP_per_Capita'],
    final_df_all['Life_Expectancy'],
    alpha=0.7, edgecolors='k', color='seagreen'
)
plt.title(f'Life Expectancy vs GDP per Capita ({TARGET_YEAR})', fontsize=14)
plt.xlabel('GDP per Capita (USD) - Logarithmic Scale', fontsize=12)
plt.ylabel('Life Expectancy (Years)', fontsize=12)
# Using a log scale for the X-axis is standard for GDP to spread out the data
plt.xscale('log')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# PLOT 4: Alcohol Consumption vs GDP per Capita
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.scatter(
    final_df_all['GDP_per_Capita'],
    final_df_all['Alcohol_Consumption'],
    alpha=0.7, edgecolors='k', color='coral'
)
plt.title(f'Alcohol Consumption vs GDP per Capita ({TARGET_YEAR})', fontsize=14)
plt.xlabel('GDP per Capita (USD) - Logarithmic Scale', fontsize=12)
plt.ylabel('Alcohol Consumption (Litres per Capita)', fontsize=12)
plt.xscale('log')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# PLOT 5: Scatter Plot (Grouped by GDP Category)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
# Loop through the ordered GDP categories we created with qcut
for category in gdp_labels:
    group = final_df_all[final_df_all['GDP_Category'] == category]
    plt.scatter(
        group['Alcohol_Consumption'],
        group['Life_Expectancy'],
        label=category, alpha=0.7, edgecolors='k', s=50
    )
plt.title(f'Alcohol vs Life Expectancy by Economic Status ({TARGET_YEAR})', fontsize=14)
plt.xlabel('Alcohol Consumption (Litres per Capita)', fontsize=12)
plt.ylabel('Life Expectancy (Years)', fontsize=12)
plt.legend(title='GDP Category', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()