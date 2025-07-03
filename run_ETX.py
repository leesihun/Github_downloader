def load_settings(settings_path="settings.txt"):
    settings = {}
    with open(settings_path, "r") as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line and not line.startswith("#"):
            if line.startswith("REMOTE_COMMANDS="):
                # Multi-line value
                commands = []
                # Get the part after = on the same line, if any
                cmd = line[len("REMOTE_COMMANDS="):].strip()
                if cmd:
                    commands.append(cmd)
                i += 1
                while i < len(lines):
                    cmd_line = lines[i].strip()
                    if cmd_line == '' or cmd_line.startswith('#'):
                        i += 1
                        continue
                    # Stop if we hit another KEY=
                    if '=' in cmd_line and not cmd_line.startswith(' '):
                        break
                    commands.append(cmd_line)
                    i += 1
                settings["REMOTE_COMMANDS"] = commands
                continue
            else:
                key, value = line.split("=", 1)
                settings[key.strip()] = value.strip()
        i += 1
    return settings

settings = load_settings()
REMOTE_HOST = settings["REMOTE_HOST"]
REMOTE_USER = settings["REMOTE_USER"]
REMOTE_PASSWORD = settings["REMOTE_PASSWORD"]
commands = settings["REMOTE_COMMANDS"]

import paramiko

# The commands to run on the remote server

# Connect to the remote server
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(REMOTE_HOST, username=REMOTE_USER, password=REMOTE_PASSWORD)

# Run each command and print output
for cmd in commands:
    if cmd.strip().startswith('#'):
        continue
    print(f"\nRunning: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    for line in stdout:
        print(line, end="")
    for line in stderr:
        print(line, end="")

print("\nAll commands executed. The connection will remain open until you press Enter.")
input("Press Enter to close the connection...")

ssh.close()