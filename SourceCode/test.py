import os
import requests
import zipfile
import subprocess
import shutil

def download_file(url, destination):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(destination, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def build_sumatra_pdf(source_dir):
    # Note: This part assumes you have Visual Studio's command line tools available
    # The script should run this command in the Visual Studio command prompt
    # Adjust the path to the VC environment if necessary
    build_command = f'cd {source_dir} && msbuild SumatraPDF.sln /p:Configuration=Release'
    subprocess.run(build_command, shell=True, check=True)

def find_mupdf_dll(build_dir):
    # Search for the libmupdf.dll file in the Release folder
    for root, dirs, files in os.walk(build_dir):
        if 'libmupdf.dll' in files:
            return os.path.join(root, 'libmupdf.dll')
    return None

def main():
    # URLs and paths
    zip_url = 'https://github.com/sumatrapdfreader/sumatrapdf/archive/refs/heads/master.zip'
    zip_path = 'sumatrapdf-master.zip'
    extract_dir = 'sumatrapdf-master'
    build_dir = os.path.join(extract_dir, 'Release')  # Adjust if necessary

    # Step 1: Download the SumatraPDF source code
    print('Downloading SumatraPDF source code...')
    download_file(zip_url, zip_path)

    # Step 2: Extract the downloaded zip file
    print('Extracting source code...')
    extract_zip(zip_path, extract_dir)

    # Step 3: Build the project using Visual Studio
    print('Building the project...')
    build_sumatra_pdf(extract_dir)

    # Step 4: Find the libmupdf.dll file
    print('Searching for libmupdf.dll...')
    dll_path = find_mupdf_dll(build_dir)
    if dll_path:
        print(f'Found libmupdf.dll at: {dll_path}')
    else:
        print('libmupdf.dll not found.')

    # Clean up
    os.remove(zip_path)
    shutil.rmtree(extract_dir)

if __name__ == '__main__':
    main()
