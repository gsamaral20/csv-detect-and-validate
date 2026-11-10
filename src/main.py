## Import
from functions import (
    read_raw_bytes,
    detect_encoding,
    detect_delimiter,
    read_rows,
    validate_rows,
    sum_accepted_values,
    build_summary,
    print_summary,
    export_summary,
    export_csv,
)

# Path of the input file
path = 'data/input/vendas_cafe.csv'

# Step 1: read the file as raw bytes
data = read_raw_bytes(path)

# Step 2: detect the encoding by trial and error
encoding_result = detect_encoding(data)

# Step 3: detect the delimiter by counting candidates in the header
delimiter_result = detect_delimiter(data, encoding_result)

# Step 4: load the CSV into a list of rows (first row is the header)
rows = read_rows(path, encoding_result, delimiter_result)

# Step 5: validate each row and split into accepted and rejected
rejected_count, accepted_count, accepted_rows, rejected_rows = validate_rows(rows)

# Step 6: sum the value column of the accepted rows
total_value = sum_accepted_values(accepted_rows)

# Step 7: build the summary dictionary
summary = build_summary(rows, rejected_count, accepted_count, total_value, encoding_result, delimiter_result)

# Step 8: export the clean CSV (header + accepted rows)
export_csv(rows, encoding_result, delimiter_result, accepted_rows)

# Step 9: export the summary to a JSON file
export_summary(summary)

# Step 10: print the summary in an executive format
print_summary(summary)