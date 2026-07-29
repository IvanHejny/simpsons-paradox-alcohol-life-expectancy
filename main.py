import pandas as pd
#increase printing width to see all columns
pd.set_option('display.max_columns', None)

# 1. Load the downloaded CSV files
df_alcohol = pd.read_csv('total-alcohol-consumption-per-capita-litres-of-pure-alcohol.csv')
df_life = pd.read_csv('life-expectancy-at-birth-who-gho.csv')

print('df_alcohol columns:\n', df_alcohol.columns)
# make the column names of df_alcohol more readable
df_alcohol.columns = ['Country', 'Code', 'Year', 'Alcohol_Consumption']

print('df_alcohol:\n', df_alcohol.head(25))
print(df_alcohol.shape) # s


print(df_life.columns)
# make the column names of df_life more readable
df_life.columns = ['Country', 'Code', 'Year', 'Life_Expectancy']
# print all columns od df_life

print('df_life:\n', df_life.head(25)) # this only prints the first 25 rows of the dataframe, not all columns
# I want to print all columns in the head

print(df_alcohol.shape) # shape of the dataframe
print(df_life.shape) # print the column names of the dataframe

# filter just year 2019 from both dataframes
df_alcohol_2019 = df_alcohol[df_alcohol['Year'] == 2019]
df_life_2019 = df_life[df_life['Year'] == 2019]

print('df_alcohol_2019:\n', df_alcohol_2019.head(6))
print(df_alcohol_2019.shape) # shape of the dataframe
print('df_life_2019:\n', df_life_2019.head(6))
print(df_life_2019.shape) # shape of the dataframe


# Now I want to merge them on ISO 'Code'. As base take df_alcohol_2019 and merge df_life_2019 on 'Code' column. Use inner join.
final_df = pd.merge(df_alcohol_2019, df_life_2019, on='Code', how='inner')
print('final_df:\n', final_df.head(6))
print(final_df.shape) # shape of the dataframe
#drop the 'Country_y' column and rename 'Country_x' to 'Country'
final_df = final_df.drop(columns=['Country_y', 'Year_y'])
final_df = final_df.rename(columns={'Country_x': 'Country', 'Year_x': 'Year'})
print('final_df:\n', final_df.head(25))


# 2. Filter both to a specific year (e.g., 2019)
#df_alcohol_2019 = df_alcohol[df_alcohol['Year'] == 2019]
#df_life_2019 = df_life[df_life['Year'] == 2019]

# 3. Perform an inner join on the ISO Country Code
#final_df = pd.merge(df_alcohol_2019, df_life_2019, on='Code', how='inner')

# 4. Save the clean dataset for your students
#final_df.to_csv('textbook_dataset.csv', index=False)