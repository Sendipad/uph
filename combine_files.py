#!/usr/bin/env python3
import glob
import os


def combine_files():
	# Find all .py, .js, and .json files excluding dist folder
	all_files = []
	for ext in ["*.py", "*.js", "*.json"]:
		files = glob.glob(f"/home/erpnext/frappe-bench/apps/uph/**/{ext}", recursive=True)
		# Filter out files in dist folder
		files = [f for f in files if "/dist/" not in f]
		all_files.extend(files)

	# Separate test files (those that start with 'test' or contain 'test')
	test_files = []
	non_test_files = []

	for file in all_files:
		filename = os.path.basename(file)
		if filename.startswith("test") or "test" in file.lower():
			test_files.append(file)
		else:
			non_test_files.append(file)

	# Sort files to ensure consistent ordering
	non_test_files.sort()
	test_files.sort()

	# Combine all files into one
	with open("/home/erpnext/Desktop/combined_files.txt", "w", encoding="utf-8") as outfile:  # nosemgrep
		# Write non-test files first
		for file_path in non_test_files:
			outfile.write(f"\n{'=' * 50}\n")
			outfile.write(f"FILE: {file_path}\n")
			outfile.write(f"{'=' * 50}\n")

			try:
				with open(file_path, encoding="utf-8") as infile:  # nosemgrep
					content = infile.read()
					outfile.write(content)
					outfile.write("\n")
			except Exception as e:
				outfile.write(f"ERROR READING FILE {file_path}: {e!s}\n")

		# Write test files at the end
		for file_path in test_files:
			outfile.write(f"\n{'=' * 50}\n")
			outfile.write(f"TEST FILE: {file_path}\n")
			outfile.write(f"{'=' * 50}\n")

			try:
				with open(file_path, encoding="utf-8") as infile:  # nosemgrep
					content = infile.read()
					outfile.write(content)
					outfile.write("\n")
			except Exception as e:
				outfile.write(f"ERROR READING TEST FILE {file_path}: {e!s}\n")


if __name__ == "__main__":
	combine_files()
	print("Files combined successfully!")
