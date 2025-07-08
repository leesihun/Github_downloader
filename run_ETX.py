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

def run_remote_etx():
    import paramiko
    import time
    from concurrent.futures import ThreadPoolExecutor

    settings = load_settings()
    
    # HPC Gateway Connection
    REMOTE_HOST = settings["REMOTE_HOST"]
    print(f"Connecting to HPC gateway: {REMOTE_HOST}")
    
    REMOTE_PORT = settings["REMOTE_PORT"]
    REMOTE_USER = settings["REMOTE_USER"]
    REMOTE_PASSWORD = settings["REMOTE_PASS"]
    commands = settings["REMOTE_COMMANDS"]
    
    print(f"Connecting to: {REMOTE_HOST}:{REMOTE_PORT}")  # Debug info
    
    # SSH execution mode configuration
    # Enhanced mode: Uses persistent shell sessions like MobaXterm (recommended for job schedulers)
    # Legacy mode: Uses exec_command for simple command execution (original behavior)
    USE_ENHANCED_SSH = True  # Change to False to use legacy mode
    
    print(f"Using {'Enhanced' if USE_ENHANCED_SSH else 'Legacy'} SSH mode")
    if USE_ENHANCED_SSH:
        print("Enhanced mode: Persistent shell sessions for job scheduler compatibility")

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
        """
        MobaXterm-compatible SSH command execution
        Simulates typing commands directly into a terminal like MobaXterm
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            print(f"[Session {session_id}] Attempting to connect to {host}:{port}")
            # Connect with additional options for better compatibility
            ssh.connect(
                host, 
                port=port, 
                username=user, 
                password=password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            print(f"[Session {session_id}] Successfully connected to {host}:{port}")
            
            # Create interactive shell session exactly like MobaXterm
            # Using larger terminal size and proper terminal type
            shell = ssh.invoke_shell(term='vt100', width=132, height=40)
            
            # Wait longer for login shell to fully initialize (like MobaXterm)
            print(f"[Session {session_id}] Waiting for shell initialization...")
            time.sleep(5)
            
            # Capture and display initial login output
            initial_output = ""
            start_time = time.time()
            while time.time() - start_time < 10:  # Wait up to 10 seconds for login
                if shell.recv_ready():
                    chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                    initial_output += chunk
                    print(chunk, end='')
                else:
                    time.sleep(0.1)
                    
                # Check if we have a proper prompt (login complete)
                if any(pattern in initial_output[-50:] for pattern in ['$ ', '> ', '# ', '] ', ') ', '~]$ ']):
                    break
            
            print(f"[Session {session_id}] Shell ready - starting command execution")
            
            # Force load user environment like MobaXterm does
            setup_commands = [
                "source ~/.bashrc",
                "source ~/.bash_profile", 
                "source ~/.profile"
            ]
            
            print(f"[Session {session_id}] Loading user environment...")
            for setup_cmd in setup_commands:
                shell.send(setup_cmd + '\n')
                time.sleep(1)
                # Clear any output from setup commands
                if shell.recv_ready():
                    setup_output = shell.recv(4096).decode('utf-8', errors='ignore')
                    # Only print if there are actual errors
                    if 'error' in setup_output.lower() or 'no such file' in setup_output.lower():
                        print(f"[Session {session_id}] Setup: {setup_output.strip()}")
            
            print(f"[Session {session_id}] Environment loaded - executing user commands")
            
            # Execute user commands one by one, exactly like typing in MobaXterm
            for i, command in enumerate(commands):
                if not command.strip():
                    continue
                    
                print(f"[Session {session_id}] Typing command {i+1}: {command}")
                
                # Send command character by character to simulate typing (like MobaXterm)
                for char in command:
                    shell.send(char)
                    time.sleep(0.01)  # Small delay between characters
                
                # Send Enter key
                shell.send('\n')
                
                # Collect output with real-time display
                output = ""
                start_time = time.time()
                max_wait = 120  # Extended timeout for complex commands like ansys_sub
                
                print(f"[Session {session_id}] Output:")
                while time.time() - start_time < max_wait:
                    if shell.recv_ready():
                        chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                        output += chunk
                        print(chunk, end='')  # Real-time output exactly like MobaXterm
                    else:
                        time.sleep(0.1)
                        
                    # More comprehensive prompt detection
                    if output and any(pattern in output[-100:] for pattern in [
                        '$ ', '> ', '# ', '] ', ') ', '~]$ ', '~]# ', 
                        'login0', 'login1', '~]', '$HOME', 'Complete', 'Done'
                    ]):
                        # Wait a bit more to ensure all output is captured
                        time.sleep(0.5)
                        if shell.recv_ready():
                            final_chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                            output += final_chunk
                            print(final_chunk, end='')
                        break
                
                if time.time() - start_time >= max_wait:
                    print(f"[Session {session_id}] Command timed out after {max_wait}s")
                
                # Longer delay between commands for stability
                time.sleep(2)
            
            print(f"[Session {session_id}] All commands completed")
            
            # Graceful logout
            shell.send('exit\n')
            time.sleep(2)
            shell.close()
            
        except Exception as e:
            error_msg = str(e)
            if "getaddrinfo failed" in error_msg:
                print(f"[Session {session_id}] DNS Resolution Error: Cannot resolve hostname '{host}'")
                print(f"[Session {session_id}] This usually means the hostname doesn't exist or isn't reachable")
                print(f"[Session {session_id}] Check your network connection and hostname configuration")
            elif "Connection refused" in error_msg:
                print(f"[Session {session_id}] Connection Refused: {host}:{port} is not accepting connections")
                print(f"[Session {session_id}] Check if SSH service is running on the target server")
            elif "Authentication failed" in error_msg:
                print(f"[Session {session_id}] Authentication Failed: Invalid username or password")
                print(f"[Session {session_id}] Check your credentials in settings")
            elif "timeout" in error_msg.lower():
                print(f"[Session {session_id}] Connection Timeout: {host}:{port} is not responding")
                print(f"[Session {session_id}] Check network connectivity and firewall settings")
            else:
                print(f"[Session {session_id}] Connection Error: {e}")
            
            print(f"[Session {session_id}] Failed to establish SSH connection")
            import traceback
            traceback.print_exc()
        finally:
            ssh.close()
            print(f"[Session {session_id}] Session completed")

    def run_ssh_commands_legacy(commands, host, port, user, password, session_id=None):
        """
        Legacy implementation using exec_command (original behavior)
        Kept for fallback compatibility
        """
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

    # Choose SSH function based on configuration
    ssh_function = run_ssh_commands if USE_ENHANCED_SSH else run_ssh_commands_legacy
    
    # Create session identifier
    session_prefix = "etx"
    
    if len(blocks) > 1:
        # Multi-threaded
        with ThreadPoolExecutor() as executor:
            futures = []
            for idx, group in enumerate(blocks, 1):
                session_id = f"{session_prefix}-{idx}"
                futures.append(executor.submit(ssh_function, group, REMOTE_HOST, REMOTE_PORT, REMOTE_USER, REMOTE_PASSWORD, session_id))
            for future in futures:
                future.result()
    else:
        # Single-threaded
        session_id = f"{session_prefix}-1"
        ssh_function(commands, REMOTE_HOST, REMOTE_PORT, REMOTE_USER, REMOTE_PASSWORD, session_id)

    print("\nAll SSH sessions completed. The window will close in 5 seconds.")
    time.sleep(5)

if __name__ == "__main__":
    run_remote_etx()