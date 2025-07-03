def run_remote_etx():
    import paramiko
    from concurrent.futures import ThreadPoolExecutor

    def load_settings(settings_path="settings.txt"):
        settings = {}
        with open(settings_path, "r") as f:
            lines = f.readlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line and not line.startswith("#"):
                if line.startswith("REMOTE_COMMANDS="):
                    # Multi-line value, handled separately
                    i += 1
                    continue
                else:
                    key, value = line.split("=", 1)
                    settings[key.strip()] = value.strip()
            i += 1
        return settings

    def load_command_groups(settings_path="settings.txt"):
        with open(settings_path, "r") as f:
            lines = f.readlines()
        groups = []
        current = []
        in_commands = False
        for line in lines:
            line = line.rstrip('\n')
            if line.strip().startswith("REMOTE_COMMANDS="):
                in_commands = True
                continue
            if not in_commands:
                continue
            if line.strip() == "" and current:
                groups.append(current)
                current = []
            elif line.strip() and not line.strip().startswith("#"):
                current.append(line.strip())
        if current:
            groups.append(current)
        return groups

    def run_ssh_commands(commands, host, user, password, session_id=None):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=user, password=password)
        command_str = " && ".join(commands)
        print(f"\n[Session {session_id}] Running: {command_str}\n")
        stdin, stdout, stderr = ssh.exec_command(command_str)
        for line in stdout:
            print(f"[Session {session_id}] {line}", end="")
        for line in stderr:
            print(f"[Session {session_id}][stderr] {line}", end="")
        ssh.close()
        print(f"[Session {session_id}] Finished.\n")

    settings = load_settings()
    REMOTE_HOST = settings["REMOTE_HOST"]
    REMOTE_USER = settings["REMOTE_USER"]
    REMOTE_PASSWORD = settings["REMOTE_PASSWORD"]

    command_groups = load_command_groups()

    with ThreadPoolExecutor() as executor:
        futures = []
        for idx, group in enumerate(command_groups, 1):
            futures.append(executor.submit(run_ssh_commands, group, REMOTE_HOST, REMOTE_USER, REMOTE_PASSWORD, idx))
        # Wait for all to finish
        for future in futures:
            future.result()

    print("\nAll SSH sessions completed. The connection will remain open until you press Enter.")
    input("Press Enter to close the connection...")

if __name__ == "__main__":
    run_remote_etx()