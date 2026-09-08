import pandas as pd
import glob
import os

# Folder containing all Flipkart CSV files
folder = r"dataset\flipkart data"

# Find all CSV files
csv_files = glob.glob(os.path.join(folder, "*.csv"))

print("===================================")
print("Flipkart Dataset Combiner")
print("===================================")
print()

if len(csv_files) == 0:
    print("❌ No CSV files found!")
    print("Check the folder path:", folder)
    exit()

print("Files Found:")
for f in csv_files:
    print("-", os.path.basename(f))

print()

dataframes = []

for file in csv_files:

    print("Reading:", os.path.basename(file))

    # Try different encodings
    try:
        df = pd.read_csv(file, encoding="utf-8")

    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file, encoding="latin1")

        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file, encoding="ISO-8859-1")

            except:
                df = pd.read_csv(
                    file,
                    encoding="latin1",
                    engine="python",
                    on_bad_lines="skip"
                )

    # Add Category column
    category = os.path.basename(file)

    category = category.replace("flipkart_", "")

    category = category.replace(".csv", "")

    df["Category"] = category

    dataframes.append(df)

# Combine all datasets
combined = pd.concat(dataframes, ignore_index=True)

# Remove duplicate products if any
combined = combined.drop_duplicates()

# Save combined dataset
output_path = r"dataset\flipkart.csv"

combined.to_csv(output_path, index=False, encoding="utf-8-sig")

print()
print("===================================")
print("✅ Combined Successfully!")
print("===================================")
print("Total Files:", len(csv_files))
print("Total Products:", len(combined))
print("Saved As:", output_path)
print("===================================")