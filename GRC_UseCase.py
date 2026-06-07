try:
	import pandas as pd
except Exception:
	pd = None

# Load the Country Data Protection Policies dataset
csv_path = 'country_plus_policies.csv'
if pd is not None:
	data_protection = pd.read_csv(csv_path)
	print("Sample Data:\n", data_protection.head())
	print("\nData Protection Policies by Country Count:", data_protection.Subject.value_counts())
else:
	# Fallback when pandas is not available: use the csv module
	import csv
	with open(csv_path, newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		rows = [row for _, row in zip(range(5), reader)]
	print("Sample Data (fallback, first rows):\n", rows)
	
