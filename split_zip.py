import os
import zipfile
import math

def get_all_files(exclude_dirs):
    all_files = []
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            # Skip the zip files we are creating or the script itself
            if file.endswith('.zip') or file == 'split_zip.py':
                continue
            filepath = os.path.join(root, file)
            all_files.append((filepath, os.path.getsize(filepath)))
    return all_files

exclude = ['venv', '.git', '__pycache__']
files = get_all_files(exclude)

# Sort files by size descending to distribute them evenly
files.sort(key=lambda x: x[1], reverse=True)

parts = [[], [], []]
part_sizes = [0, 0, 0]

for filepath, size in files:
    # Find the part with the smallest current size
    min_idx = part_sizes.index(min(part_sizes))
    parts[min_idx].append(filepath)
    part_sizes[min_idx] += size

print("Splitting into 3 parts:")
for i in range(3):
    zip_name = f"lms_project_part{i+1}.zip"
    print(f"Creating {zip_name} (approx {part_sizes[i] / (1024*1024):.2f} MB)")
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filepath in parts[i]:
            arcname = os.path.relpath(filepath, '.')
            zipf.write(filepath, arcname)
    print(f"Finished {zip_name}")

print("Done!")
