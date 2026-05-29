import os
import zipfile

def get_all_files(exclude_dirs, exclude_exts):
    all_files = []
    for root, dirs, files in os.walk('.'):
        # Exclude specified directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            # Exclude zip files, the python script itself, and specific extensions
            if file.endswith('.zip') or file == 'zip_project.py' or file.endswith(exclude_exts):
                continue
            filepath = os.path.join(root, file)
            all_files.append(filepath)
    return all_files

exclude_directories = ['venv', '.git', '__pycache__']
exclude_extensions = ('.mp4', '.avi', '.mov', '.mkv')  # exclude videos

files_to_zip = get_all_files(exclude_directories, exclude_extensions)

zip_name = "lms_ready_to_upload.zip"
print(f"Creating {zip_name}...")

with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for filepath in files_to_zip:
        arcname = os.path.relpath(filepath, '.')
        zipf.write(filepath, arcname)

size_mb = os.path.getsize(zip_name) / (1024 * 1024)
print(f"Success! Final size: {size_mb:.2f} MB")
