import csv
import json

def parse_float(val):
    """ Convert numeric strings with a comma (e.g., '28,80') to float (28.80). """
    if not val:
        return 0.0
    try:
        return float(val.replace(',', '.'))
    except ValueError:
        return 0.0

def parse_int(val):
    """ Safely convert strings to integers. """
    if not val:
        return 0
    try:
        return int(val)
    except ValueError:
        return 0

def convert_csv_to_json(csv_filename, json_filename):
    records = []

    # Open the CSV file specifying the semicolon delimiter ';'
    with open(csv_filename, mode='r', encoding='utf-8', errors='ignore') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';')

        for row in reader:
            item = {}
            for key, val in row.items():
                if not key:
                    continue

                # Normalize keys to lowercase and strip whitespace
                clean_key = key.strip().lower()
                clean_val = val.strip() if val else ""

                # Convert numeric fields accordingly
                if clean_key in ['quantity', 'tax']:
                    item[clean_key] = parse_int(clean_val)
                elif clean_key in ['price', 'discount', 'total']:
                    item[clean_key] = parse_float(clean_val)
                else:
                    item[clean_key] = clean_val

            records.append(item)

    # Save the result into a structured, readable JSON file
    with open(json_filename, mode='w', encoding='utf-8') as json_file:
        json.dump(records, json_file, ensure_ascii=False, indent=2)

    print(f"Process completed! Successfully converted {len(records)} records to {json_filename}")

if __name__ == '__main__':
    # Make sure your CSV file is named 'catalog.csv' or change the filename here
    convert_csv_to_json('src/data.csv', 'data.json')
