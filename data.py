import pandas as pd

# Load the CSV file
df = pd.read_csv("Testing(Updated).csv")

# Remove duplicate rows based on the 'prognosis' column
df_unique = df.drop_duplicates(subset=['prognosis'])

# Save the cleaned data to a new CSV file
df_unique.to_csv("Testing_cleaned.csv", index=False)

print("Duplicates removed based on 'prognosis' column. Cleaned file saved as 'Testing_cleaned.csv'.")
