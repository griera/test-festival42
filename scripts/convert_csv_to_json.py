import csv
import json
import argparse

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
    """ Reads a semicolon-delimited CSV file and converts it into a structured JSON file. """
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

    print(f"Process completed! Successfully converted {len(records)} records from {csv_filename} to {json_filename}")

if __name__ == '__main__':
    # Set up argument parser with detailed usage and execution examples
    parser = argparse.ArgumentParser(
        description="Convert a semicolon-delimited festival CSV file into a structured JSON payload for the web app.",
        epilog="Examples of execution:\n"
               "  1. Convert default catalog CSV:\n"
               "     python3 scripts/convert_csv_to_json.py\n\n"
               "  2. Convert a custom CSV input file:\n"
               "     python3 scripts/convert_csv_to_json.py --input data/catalog_large.csv\n\n"
               "  3. Custom input and output files:\n"
               "     python3 scripts/convert_csv_to_json.py -i data/catalog_large.csv -o data.json\n\n"
               "  4. Display help menu:\n"
               "     python3 scripts/convert_csv_to_json.py --help",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "-i", "--input",
        type=str,
        default="data/data.csv",
        help="Path to the input CSV file to convert (default: data/data.csv)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="data.json",
        help="Path to the output JSON file (default: data.json)"
    )

    args = parser.parse_args()

    # Execute conversion function with parsed parameters
    convert_csv_to_json(args.input, args.output)
