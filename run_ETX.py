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
        if line.startswith("REMOTE_COMMANDS="):
            # Multi-line value
            commands = []
            cmd = line[len("REMOTE_COMMANDS="):].strip()
            if cmd:
                commands.append(cmd)
            i += 1
            while i < len(lines):
                cmd_line = lines[i].strip()
                if not cmd_line or cmd_line.startswith('#'):
                    i += 1
                    continue
                if '=' in cmd_line and not cmd_line.startswith(' '):
                    break
                commands.append(cmd_line)
                i += 1
            settings["REMOTE_COMMANDS"] = commands
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            settings[key.strip().upper()] = value.strip()
        i += 1
    # Type conversions
    if "REMOTE_PORT" in settings:
        settings["REMOTE_PORT"] = int(settings["REMOTE_PORT"])
    return settings

def run_remote_etx():
    import paramiko
    from concurrent.futures import ThreadPoolExecutor

    settings = load_settings()
    REMOTE_HOST = settings["REMOTE_HOST"]
    REMOTE_PORT = settings["REMOTE_PORT"]
    REMOTE_USER = settings["REMOTE_USER"]
    REMOTE_PASSWORD = settings["REMOTE_PASS"]
    commands = settings["REMOTE_COMMANDS"]

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

    command_groups = []
    group = []
    for cmd in commands:
        if cmd.strip() == '':
            if group:
                command_groups.append(group)
                group = []
        else:
            group.append(cmd)
    if group:
        command_groups.append(group)

    with ThreadPoolExecutor() as executor:
        futures = []
        for idx, group in enumerate(command_groups, 1):
            futures.append(executor.submit(run_ssh_commands, group, REMOTE_HOST, REMOTE_PORT, REMOTE_USER, REMOTE_PASSWORD, idx))
        for future in futures:
            future.result()

    print("\nAll SSH sessions completed. The connection will remain open until you press Enter.")
    input("Press Enter to close the connection...")

if __name__ == "__main__":
    run_remote_etx()