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
    return settings

def run_remote_etx(hostname=None):
    import paramiko
    import time
    from concurrent.futures import ThreadPoolExecutor

    settings = load_settings()
    
    # Hostname mapping - you can customize this based on your actual setup
    # For now, we'll use the base IP with the hostname for display purposes
    # In a real setup, you might have different IPs or use actual hostnames
    REMOTE_BASE_HOST = settings["REMOTE_HOST"]
    
    if hostname:
        # Use the selected hostname directly if your system supports it
        # Otherwise, you can map specific hostnames to IPs here
        REMOTE_HOST = hostname
        print(f"Using selected hostname: {hostname}")
        
        # Example of hostname mapping (uncomment and customize as needed):
        # hostname_mapping = {
        #     'login01': '202.20.185.101',
        #     'login02': '202.20.185.102',
        #     'login03': '202.20.185.103',
        #     'login04': '202.20.185.104',
        #     'login05': '202.20.185.105',
        #     'login06': '202.20.185.106',
        #     'login07': '202.20.185.107',
        #     'login08': '202.20.185.108',
        #     'login09': '202.20.185.109',
        #     'login10': '202.20.185.110',
        # }
        # REMOTE_HOST = hostname_mapping.get(hostname, REMOTE_BASE_HOST)
        
    else:
        REMOTE_HOST = REMOTE_BASE_HOST
        print(f"Using default hostname: {REMOTE_HOST}")
    
    REMOTE_PORT = settings["REMOTE_PORT"]
    REMOTE_USER = settings["REMOTE_USER"]
    REMOTE_PASSWORD = settings["REMOTE_PASS"]
    commands = settings["REMOTE_COMMANDS"]
    
    print(f"Connecting to: {REMOTE_HOST}:{REMOTE_PORT}")  # Debug info

    # Detect if there are two or more consecutive blank lines (multi-threaded job)
    blocks = []
    current = []
    blank_count = 0
    for cmd in commands:
        if cmd.strip() == '':
            blank_count += 1
            if blank_count >= 2 and current:
                blocks.append(current)
                current = []
        else:
            if blank_count >= 2 and current:
                blocks.append(current)
                current = []
            blank_count = 0
            current.append(cmd)
    if current:
        blocks.append(current)

    def run_ssh_commands(commands, host, port, user, password, session_id=None):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=user, password=password)
        command_str = " && ".join(commands)
        print(f"\n[Session {session_id}] Running: {command_str}\n")
        stdin, stdout, stderr = ssh.exec_command(command_str)
        for line in stdout:
            print(f"[Session {session_id}] {line}", end="")
        for line in stderr:
            print(f"[Session {session_id}][stderr] {line}", end="")
        ssh.close()
        print(f"[Session {session_id}] Finished.\n")

    if len(blocks) > 1:
        # Multi-threaded
        with ThreadPoolExecutor() as executor:
            futures = []
            for idx, group in enumerate(blocks, 1):
                futures.append(executor.submit(run_ssh_commands, group, REMOTE_HOST, REMOTE_PORT, REMOTE_USER, REMOTE_PASSWORD, idx))
            for future in futures:
                future.result()
    else:
        # Single-threaded
        run_ssh_commands(commands, REMOTE_HOST, REMOTE_PORT, REMOTE_USER, REMOTE_PASSWORD, 1)

    print("\nAll SSH sessions completed. The window will close in 5 seconds.")
    time.sleep(5)

if __name__ == "__main__":
    run_remote_etx()