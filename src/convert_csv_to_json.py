import csv
import json

csv_file_path = 'src/data.csv'
json_file_path = 'data.json'

data_list = []

# Read CSV and append rows as dictionaries
with open(csv_file_path, mode='r', encoding='utf-8') as csv_file:
  csv_reader = csv.DictReader(csv_file)
  for row in csv_reader:
    data_list.append(row)

# Write out to JSON file with clean formatting
with open(json_file_path, mode='w', encoding='utf-8') as json_file:
  json.dump(data_list, json_file, ensure_ascii=False, indent=2)

print(
    f'Successfully converted {len(data_list)} records from {csv_file_path} to'
    f' {json_file_path}'
)
