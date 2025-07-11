import os
import shutil
import zipfile
import paramiko
import requests
import time

# ========== CONFIGURABLE VARIABLES ==========
def load_settings(settings_path="settings.txt"):
    settings = {}
    with open(settings_path, "r") as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        if line.startswith("REMOTE_COMMANDS=") or line.startswith("REMOTE_TARGET_DIRS="):
            key = line.split("=", 1)[0].strip().upper()
            values = []
            val = line[len(key)+1:].strip()
            if val:
                values.append(val)
            i += 1
            while i < len(lines):
                cmd_line = lines[i].strip()
                if not cmd_line or cmd_line.startswith('#'):
                    i += 1
                    continue
                if '=' in cmd_line and not cmd_line.startswith(' '):
                    break
                values.append(cmd_line)
                i += 1
            settings[key] = values
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            settings[key.strip().upper()] = value.strip()
        i += 1
    # Type conversions
    if "REMOTE_PORT" in settings:
        settings["REMOTE_PORT"] = int(settings["REMOTE_PORT"])
    if "DELETE_FILES" in settings:
        settings["DELETE_FILES"] = settings["DELETE_FILES"].lower() in ("true", "1", "yes")
    return settings

def download_github_zip(url, dest_path):
    print(f"Downloading {url} ...")
    proxies = {
        "http": "http://168.219.61.252:",
        "https": "http://168.219.61.252:8080"
    }
    try:
        response = requests.get(url, proxies=proxies)
    except requests.exceptions.SSLError as e:
        print(f"SSL error: {e}")
        print("Retrying without certificate verification (NOT SECURE).")
        response = requests.get(url, verify=False, proxies=proxies)
    if response.status_code == 200:
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded to {dest_path}")
    else:
        print(f"Failed to download: {response.status_code}")

def unzip_file(zip_path, extract_to):
    if os.path.exists(extract_to):
        shutil.rmtree(extract_to)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(os.path.dirname(extract_to))
    # The zip will extract to a folder, so we rename/move it to extract_to
    extracted_folder = os.path.join(os.path.dirname(extract_to), os.path.basename(zip_path).replace('.zip', ''))
    if os.path.exists(extracted_folder) and extracted_folder != extract_to:
        shutil.move(extracted_folder, extract_to)

def copy_all(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def sftp_upload_dir(sftp, local_dir, remote_dir):
    # Recursively upload a directory to the remote server, overwriting files
    total_files = 0
    success_files = 0
    failed_files = 0
    for root, dirs, files in os.walk(local_dir):
        rel_path = os.path.relpath(root, local_dir)
        remote_path = os.path.join(remote_dir, rel_path).replace('\\', '/')
        try:
            sftp.stat(remote_path)
        except FileNotFoundError:
            sftp.mkdir(remote_path)
        for file in files:
            total_files += 1
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_path, file).replace('\\', '/')
            try:
                sftp.put(local_file, remote_file)
                # Verify file size
                local_size = os.path.getsize(local_file)
                remote_size = sftp.stat(remote_file).st_size
                if local_size == remote_size:
                    print(f"Uploaded and verified: {remote_file}")
                    success_files += 1
                else:
                    print(f"WARNING: Size mismatch for {remote_file} (local: {local_size}, remote: {remote_size})")
                    failed_files += 1
            except Exception as e:
                print(f"Failed to upload {local_file} to {remote_file}: {e}")
                failed_files += 1
    print(f"Upload summary: {success_files}/{total_files} files succeeded, {failed_files} failed.")

def github_zip_url_from_project_url(project_url):
    # e.g. https://github.com/leesihun/SimulGen-VAE -> https://github.com/leesihun/SimulGen-VAE/archive/refs/heads/main.zip
    return project_url.rstrip('/') + '/archive/refs/heads/main.zip'

def download_github_to_local():
    settings = load_settings()
    PROJECT_URL = settings["PROJECT_URL"]
    ZIP_PATH = settings["ZIP_PATH"]
    UNZIP_DIR = settings["UNZIP_DIR"]
    LOCAL_TARGET_DIR = settings["LOCAL_TARGET_DIR"]
    ZIP_URL = github_zip_url_from_project_url(PROJECT_URL)
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Attempt {attempt}] Downloading {ZIP_URL} to {ZIP_PATH}...")
            download_github_zip(ZIP_URL, ZIP_PATH)
            print(f"[Attempt {attempt}] Unzipping {ZIP_PATH} to {UNZIP_DIR}...")
            unzip_file(ZIP_PATH, UNZIP_DIR)
            print(f"[Attempt {attempt}] Copying files from {UNZIP_DIR} to {LOCAL_TARGET_DIR}...")
            copy_all(UNZIP_DIR, LOCAL_TARGET_DIR)
            print("Github to Local complete.")
            break
        except Exception as e:
            print(f"[Attempt {attempt}] Error: {e}")
            if attempt < max_retries:
                print("Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print("All attempts failed. Giving up.")

def upload_local_to_etx():
    settings = load_settings()
    LOCAL_SOURCE_DIR = settings["LOCAL_SOURCE_DIR"]
    REMOTE_HOST = settings["REMOTE_HOST"]
    REMOTE_PORT = settings["REMOTE_PORT"]
    REMOTE_USER = settings["REMOTE_USER"]
    REMOTE_PASS = settings["REMOTE_PASS"]
    REMOTE_TARGET_DIRS = settings["REMOTE_TARGET_DIRS"] if isinstance(settings["REMOTE_TARGET_DIRS"], list) else [settings["REMOTE_TARGET_DIRS"]]
    print(f"Uploading {LOCAL_SOURCE_DIR} to remote targets:")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(REMOTE_HOST, port=REMOTE_PORT, username=REMOTE_USER, password=REMOTE_PASS, timeout=10)
        print("SSH connection established.")
    except paramiko.AuthenticationException:
        print("Authentication failed, please verify your credentials.")
        return
    except paramiko.SSHException as sshException:
        print(f"Unable to establish SSH connection: {sshException}")
        return
    except Exception as e:
        print(f"Exception in connecting to the server: {e}")
        return
    try:
        sftp = ssh.open_sftp()
        print("SFTP session established.")
    except Exception as e:
        print(f"Failed to open SFTP session: {e}")
        ssh.close()
        return
    for REMOTE_TARGET_DIR in REMOTE_TARGET_DIRS:
        print(f"Uploading to {REMOTE_TARGET_DIR}...")
        # Ensure remote target dir exists
        try:
            sftp.stat(REMOTE_TARGET_DIR)
        except FileNotFoundError:
            # Recursively create directories
            dirs = REMOTE_TARGET_DIR.strip('/').split('/')
            path = ''
            for d in dirs:
                path += '/' + d
                try:
                    sftp.stat(path)
                except FileNotFoundError:
                    try:
                        sftp.mkdir(path)
                        print(f"Created remote directory: {path}")
                    except Exception as e:
                        print(f"Failed to create remote directory {path}: {e}")
                        continue
        try:
            sftp_upload_dir(sftp, LOCAL_SOURCE_DIR, REMOTE_TARGET_DIR)
            print(f"Upload to {REMOTE_TARGET_DIR} completed.")
        except Exception as e:
            print(f"Error during file upload to {REMOTE_TARGET_DIR}: {e}")
            continue
        # Verification: List remote files
        try:
            print(f"Remote directory contents after upload to {REMOTE_TARGET_DIR}:")
            for entry in sftp.listdir_attr(REMOTE_TARGET_DIR):
                print(f"  {entry.filename}")
        except Exception as e:
            print(f"Could not list remote directory {REMOTE_TARGET_DIR}: {e}")
    sftp.close()
    ssh.close()

def delete_local_folders():
    settings = load_settings()
    ZIP_PATH = settings["ZIP_PATH"]
    UNZIP_DIR = settings["UNZIP_DIR"]
    LOCAL_TARGET_DIR = settings["LOCAL_TARGET_DIR"]
    LOCAL_SOURCE_DIR = settings.get("LOCAL_SOURCE_DIR", None)
    print("Deleting local folders and files...")
    for path in [ZIP_PATH, UNZIP_DIR, LOCAL_TARGET_DIR, LOCAL_SOURCE_DIR]:
        if not path:
            continue
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"Deleted folder: {path}")
            elif os.path.isfile(path):
                os.remove(path)
                print(f"Deleted file: {path}")
        except Exception as e:
            print(f"Could not delete {path}: {e}")
    print("Done.")

def run_github_to_local_to_etx():
    download_github_to_local()
    upload_local_to_etx()

if __name__ == "__main__":
    run_github_to_local_to_etx()
