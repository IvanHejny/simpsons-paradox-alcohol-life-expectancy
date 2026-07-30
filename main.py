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

# 2. Rename columns for clean merging
df_alcohol.columns = ['Country', 'Code', 'Year', 'Alcohol_Consumption']
df_life.columns = ['Country', 'Code', 'Year', 'Life_Expectancy']

# 3. Filter for the Target Year
df_alcohol_year = df_alcohol[df_alcohol['Year'] == TARGET_YEAR]
df_life_year = df_life[df_life['Year'] == TARGET_YEAR]

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
final_df_with_continent = pd.merge(
    final_df,
    df_country_code_clean,
    on='Code',
    how='inner'
)

# ---------------------------------------------------------
# CORRELATION ANALYSIS
# ---------------------------------------------------------
print(f"\n--- CORRELATION COEFFICIENTS ({TARGET_YEAR}) ---")

# Global Correlation
global_corr = final_df_with_continent['Alcohol_Consumption'].corr(final_df_with_continent['Life_Expectancy'])
print(f"Global (All Countries): r = {global_corr:.3f}")

# Regional Correlation
print("\nBy Continent:")
for continent, group in final_df_with_continent.groupby('Continent'):
    # We need at least 2 data points to compute correlation safely
    if len(group) > 1:
        corr = group['Alcohol_Consumption'].corr(group['Life_Expectancy'])
        print(f"  - {continent}: r = {corr:.3f} (n={len(group)})")
    else:
        print(f"  - {continent}: Not enough data")

print("----------------------------------------\n")

# ---------------------------------------------------------
# PLOT 1: Single Color Scatter Plot (No Continent Grouping)
# ---------------------------------------------------------
plt.figure(figsize=(10, 6))
plt.scatter(
    final_df_with_continent['Alcohol_Consumption'],
    final_df_with_continent['Life_Expectancy'],
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
for continent, group in final_df_with_continent.groupby('Continent'):
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