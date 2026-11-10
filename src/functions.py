## Import
import csv
import json
from datetime import datetime

# Read the file as raw bytes
def read_raw_bytes(path):
    ## Read CSV file in binary mode
    with open(path, 'rb') as f:
        data = f.read()
    return data

# Find the encoding that decodes the bytes without errors
def detect_encoding(data):
    # Detect the encoding by trial and error
    # Order matters: latin-1 goes last because it never fails
    encodings_list = ['utf-8-sig', 'cp1252', 'latin-1']

    for encoding in encodings_list:
        try:
            # Raises an error if the bytes are not valid for this encoding
            data.decode(encoding)
            # Decoding worked: keep the encoding name (not the decoded text)
            encoding_result = encoding
            # Stop at the first encoding that works
            break
        except ValueError:
            # Decoding failed: try the next encoding in the list
            continue
    return encoding_result

# Find the delimiter by counting candidates in the header
def detect_delimiter(data, encoding_result):
    # Decode the bytes into text using the detected encoding
    text = data.decode(encoding_result)
    # The first line is the header
    header = text.splitlines()[0]

    # Delimiters we consider possible
    candidate_delimiters = [';', ',', '\t', '|']

    # Highest count found so far
    max_count = 0
    # Stays None if no candidate appears in the header
    delimiter_result = None
    for delimiter in candidate_delimiters:
        # How many times this delimiter appears in the header
        delimiter_count = header.count(delimiter)
        # Keep the delimiter with the highest count
        if delimiter_count > max_count:
            max_count = delimiter_count
            delimiter_result = delimiter
    return delimiter_result

# Load the CSV into a list of rows using the detected encoding and delimiter
def read_rows(path, encoding_result, delimiter_result):
    # Open in text mode with the detected encoding; newline='' lets csv handle line breaks
    with open(path, 'r', encoding=encoding_result, newline='') as f:
        csv_reader = csv.reader(f, delimiter=delimiter_result)
        # Load all rows into memory before the file closes
        rows = list(csv_reader)
    return rows


# Split rows into accepted and rejected, with counts
def validate_rows(rows):
    rejected_count = 0
    accepted_count = 0
    accepted_rows = []
    rejected_rows = []
    # First row is the header; used as reference for the expected number of columns
    header = rows[0]

    # Skip the header and validate each data row
    for row in rows[1:]:
        field_count = len(row)

        # Reject rows with a different number of columns than the header
        if len(header) != field_count:
            rejected_count += 1
            rejected_rows.append(row)
            continue

        # Reject invalid dates (wrong format or impossible date)
        try:
            datetime.strptime(row[0], "%Y-%m-%d")
        except ValueError:
            rejected_count += 1
            rejected_rows.append(row)
            continue

        # Reject empty store or SKU (strip catches whitespace-only values)
        if row[1].strip() == "" or row[2].strip() == "":
            rejected_count += 1
            rejected_rows.append(row)
            continue

        # Reject quantity that is not an integer
        try:
            quantity = int(row[3])
        except ValueError:
            rejected_count += 1
            rejected_rows.append(row)
            continue
        # Reject quantity that is zero or negative
        if quantity <= 0:
            rejected_count += 1
            rejected_rows.append(row)
            continue

        # Reject price that is not numeric (comma decimal converted for float)
        try:
            price = float(row[4].replace(',', '.'))
        except ValueError:
            rejected_count += 1
            rejected_rows.append(row)
            continue
        # Reject price that is zero or negative
        if price <= 0:
            rejected_count += 1
            rejected_rows.append(row)
            continue

        # Valid price: store it with a dot as decimal separator
        row[4] = row[4].replace(',', '.')

        # Row passed every validation
        accepted_count += 1
        accepted_rows.append(row)

    return rejected_count, accepted_count, accepted_rows, rejected_rows

# Sum the value column of the accepted rows
def sum_accepted_values(accepted_rows):
    total_value = 0
    for row in accepted_rows:
        # row[4] is the line total (already quantity x unit price)
        total_value += float(row[4])
        total_value = round(total_value, 2)
    return total_value

# Build the summary dictionary (counts, total, encoding and delimiter)
def build_summary(rows, rejected_count, accepted_count, total_value, encoding_result, delimiter_result):
    summary = {
        # Data rows only (header excluded)
        "rows_read": len(rows) - 1,
        "rows_rejected": rejected_count,
        "rows_accepted": accepted_count,
        "total_value": total_value,
        "encoding": encoding_result,
        "delimiter": delimiter_result,
    }
    return summary

# Print the summary in an executive format
def print_summary(summary):
    print("=" * 40)
    print("   SALES EXTRACTION REPORT")
    print("=" * 40)
    print(f"Rows read      : {summary['rows_read']}")
    print(f"Rows accepted  : {summary['rows_accepted']}")
    print(f"Rows rejected  : {summary['rows_rejected']}")
    print("-" * 40)
    print(f"Total value    : {summary['total_value']:.2f}")
    print("-" * 40)
    print(f"Encoding       : {summary['encoding']}")
    print(f"Delimiter      : {summary['delimiter']}")
    print("=" * 40)

# Write the summary dictionary to a JSON file
def export_summary(summary):
    # "w" creates the file or overwrites it; utf-8 is the standard encoding for JSON
    with open("data/output/sales_summary.json", "w", encoding="utf-8") as f:
        # indent=4 makes the file readable; ensure_ascii=False keeps accented characters as they are
        json.dump(summary, f, indent=4, ensure_ascii=False)

# Write the header and accepted rows to the clean CSV
def export_csv(rows, encoding_result, delimiter_result, accepted_rows):
    # The header is the first row of the original data
    header = rows[0]
    # "w" creates the file or overwrites it; newline="" avoids blank lines between rows
    with open("data/output/sales_report_final.csv", "w", encoding = encoding_result, newline = "") as f:
        # Writer uses the same delimiter detected in the original file
        writer = csv.writer(f, delimiter = delimiter_result)
        # Write the header as a single row
        writer.writerow(header)
        # Write all accepted rows at once (one row per item in the list)
        writer.writerows(accepted_rows)
        # Confirm the export finished without errors
        print("Report exported successfully")