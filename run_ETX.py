#!/usr/bin/env python3
"""
ETX Remote Command Execution Tool
Executes commands on remote HPC systems via SSH with enhanced compatibility
Now supports interactive mode like MobaXterm!
"""

import os
import sys
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Tuple

try:
    import paramiko
except ImportError:
    print("ERROR: paramiko library not found. Install with: pip install paramiko")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('run_etx.log')
    ]
)
logger = logging.getLogger(__name__)

class ETXRemoteExecutor:
    """Enhanced SSH executor for HPC systems with MobaXterm-like functionality"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get('REMOTE_HOST')
        self.port = config.get('REMOTE_PORT', 22)
        self.username = config.get('REMOTE_USER')
        self.password = config.get('REMOTE_PASS')
        self.commands = config.get('REMOTE_COMMANDS', [])
        
        # Connection settings
        self.connection_timeout = 30
        self.command_timeout = 300  # 5 minutes default
        self.job_command_timeout = 600  # 10 minutes for job commands
        self.shell_init_wait = 3
        self.inter_command_delay = 2
        
        # Interactive mode settings
        self.interactive_mode = False
        self.user_input_queue = []
        self.input_thread = None
        self.shell_active = False
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate required configuration parameters"""
        required_fields = ['REMOTE_HOST', 'REMOTE_USER', 'REMOTE_PASS']
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")
        
        if not self.commands:
            logger.warning("No commands specified in REMOTE_COMMANDS")
    
    def _create_ssh_client(self) -> paramiko.SSHClient:
        """Create and configure SSH client"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Enhanced connection parameters for HPC compatibility
        connect_params = {
            'hostname': self.host,
            'port': self.port,
            'username': self.username,
            'password': self.password,
            'timeout': self.connection_timeout,
            'allow_agent': False,
            'look_for_keys': False,
            'banner_timeout': 30,
            'auth_timeout': 30
        }
        
        return client, connect_params
    
    def _is_job_command(self, command: str) -> bool:
        """Check if command is a job submission command"""
        job_keywords = [
            'ansys_sub', 'phd run', 'sbatch', 'qsub', 'bsub', 
            'job', 'submit', 'srun', 'mpirun', 'mpiexec'
        ]
        return any(keyword in command.lower() for keyword in job_keywords)
    
    def _get_command_timeout(self, command: str) -> int:
        """Get appropriate timeout for command"""
        return self.job_command_timeout if self._is_job_command(command) else self.command_timeout
    
    def _setup_shell_environment(self, shell: paramiko.Channel) -> None:
        """Setup shell environment like MobaXterm"""
        logger.info("Setting up shell environment...")
        
        # Wait for shell to initialize
        time.sleep(self.shell_init_wait)
        
        # Clear any initial output
        if shell.recv_ready():
            initial_output = shell.recv(8192).decode('utf-8', errors='ignore')
            if self.interactive_mode:
                print(initial_output, end='')
            logger.debug(f"Initial shell output: {initial_output[:200]}...")
        
        # Load user environment
        env_commands = [
            'source ~/.bashrc 2>/dev/null || true',
            'source ~/.bash_profile 2>/dev/null || true',
            'source ~/.profile 2>/dev/null || true'
        ]
        
        for cmd in env_commands:
            shell.send(f"{cmd}\n")
            time.sleep(0.5)
            
        # Clear environment setup output
        time.sleep(1)
        if shell.recv_ready():
            setup_output = shell.recv(8192).decode('utf-8', errors='ignore')
            if self.interactive_mode:
                print(setup_output, end='')
            logger.debug(f"Environment setup output: {setup_output[:200]}...")
    
    def _start_input_thread(self, shell: paramiko.Channel) -> None:
        """Start thread to handle user input in interactive mode"""
        def input_handler():
            try:
                while self.shell_active:
                    try:
                        user_input = input()
                        if user_input.strip().lower() == 'exit':
                            shell.send('exit\n')
                            break
                        elif user_input.strip().lower() == '!menu':
                            self._show_interactive_menu()
                            continue
                        elif user_input.strip().lower() == '!help':
                            self._show_interactive_help()
                            continue
                        shell.send(user_input + '\n')
                    except EOFError:
                        break
                    except Exception as e:
                        logger.error(f"Input thread error: {e}")
                        break
            except:
                pass
        
        self.input_thread = threading.Thread(target=input_handler, daemon=True)
        self.input_thread.start()
    
    def _show_interactive_menu(self) -> None:
        """Show interactive menu options"""
        print("\n" + "="*50)
        print("🔧 INTERACTIVE MODE MENU")
        print("="*50)
        print("Commands you can use:")
        print("  !help     - Show this help")
        print("  !menu     - Show this menu")
        print("  exit      - Exit the session")
        print("  <command> - Execute any command")
        print("="*50)
    
    def _show_interactive_help(self) -> None:
        """Show interactive help"""
        print("\n" + "="*50)
        print("🚀 INTERACTIVE MODE HELP")
        print("="*50)
        print("You are now connected to: " + self.host)
        print("Phase 1: Automated commands were typed and executed from settings")
        print("Phase 2: You can now type any additional commands manually")
        print("\nExample commands:")
        print("  ls -la")
        print("  pwd")
        print("  cd /home/sr5/s.hun.lee")
        print("  ansys_sub")
        print("  phd run -ng 1 -p shr_gpu -GR H100 python script.py")
        print("\nSpecial commands:")
        print("  !menu - Show menu")
        print("  !help - Show this help")
        print("  exit  - Exit session")
        print("="*50)
    
    def _execute_commands_interactively(self, shell: paramiko.Channel, commands: List[str]) -> bool:
        """Execute commands interactively with automatic typing like MobaXterm"""
        success = True
        
        for i, command in enumerate(commands, 1):
            command = command.strip()
            if not command or command.startswith('#'):
                continue
                
            print(f"\n📝 Command {i}/{len(commands)}: ", end='', flush=True)
            
            # Simulate typing the command character by character
            time.sleep(0.5)  # Pause before typing
            for char in command:
                print(char, end='', flush=True)
                shell.send(char)
                # Variable typing speed - faster for normal chars, slower for special chars
                if char in ' =-|&"\'':
                    time.sleep(0.05)  # Slightly slower for special characters
                else:
                    time.sleep(0.03)  # Normal typing speed
            
            print(" ✓")  # Checkmark after typing command
            time.sleep(0.3)  # Brief pause before pressing Enter
            
            # Send Enter key
            shell.send('\n')
            
            # Show real-time output
            output = ""
            timeout = self._get_command_timeout(command)
            start_time = time.time()
            last_output_time = start_time
            no_output_timeout = 30
            
            print(f"🔄 Executing command {i}/{len(commands)}...")
            
            while time.time() - start_time < timeout:
                if shell.recv_ready():
                    try:
                        chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                        output += chunk
                        print(chunk, end='')  # Real-time output
                        last_output_time = time.time()
                    except Exception as e:
                        print(f"❌ Error reading output: {e}")
                        success = False
                        break
                else:
                    time.sleep(0.1)
                    
                    # Check for no output timeout
                    if time.time() - last_output_time > no_output_timeout:
                        print(f"\n⏱️  No output for {no_output_timeout}s, assuming command completed")
                        break
                
                # Check for command completion
                if self._is_command_complete(output):
                    print(f"\n✅ Command {i} completed")
                    time.sleep(1)  # Wait for any remaining output
                    break
            
            # Handle timeout
            if time.time() - start_time >= timeout:
                print(f"\n⏱️  Command {i} timed out after {timeout}s")
                success = False
            
            # Job command special handling
            if self._is_job_command(command):
                print(f"🔍 Job command detected - checking status...")
                shell.send('echo "Job submission check"\n')
                time.sleep(2)
                
                # Try to check job status
                shell.send('qstat 2>/dev/null || echo "qstat not available"\n')
                time.sleep(3)
                
                # Capture any additional output
                if shell.recv_ready():
                    additional_output = shell.recv(4096).decode('utf-8', errors='ignore')
                    print(additional_output, end='')
            
            # Wait between commands
            print(f"⏳ Waiting {self.inter_command_delay}s before next command...")
            time.sleep(self.inter_command_delay)
        
        return success

    def _execute_command_interactive(self, shell: paramiko.Channel, command: str, 
                                   session_id: str) -> Tuple[str, bool]:
        """Execute single command interactively"""
        logger.info(f"[{session_id}] Executing: {command}")
        
        # Send command
        shell.send(f"{command}\n")
        
        # Collect output
        output = ""
        timeout = self._get_command_timeout(command)
        start_time = time.time()
        last_output_time = start_time
        no_output_timeout = 30  # No output timeout
        
        while time.time() - start_time < timeout:
            if shell.recv_ready():
                try:
                    chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                    output += chunk
                    print(chunk, end='')  # Real-time output
                    last_output_time = time.time()
                except Exception as e:
                    logger.error(f"[{session_id}] Error reading output: {e}")
                    break
            else:
                time.sleep(0.1)
                
                # Check for no output timeout
                if time.time() - last_output_time > no_output_timeout:
                    logger.info(f"[{session_id}] No output for {no_output_timeout}s, assuming command completed")
                    break
            
            # Check for command completion indicators
            if self._is_command_complete(output):
                logger.info(f"[{session_id}] Command completion detected")
                time.sleep(1)  # Wait for any remaining output
                break
        
        # Handle timeout
        if time.time() - start_time >= timeout:
            logger.warning(f"[{session_id}] Command timed out after {timeout}s")
            return output, False
        
        return output, True
    
    def _is_command_complete(self, output: str) -> bool:
        """Check if command has completed based on output patterns"""
        completion_patterns = [
            # Shell prompts
            '$ ', '> ', '# ', '] ', ') ', '~]$ ', '~]# ',
            # Job submission confirmations
            'submitted', 'Submitted', 'SUBMITTED', 'Job ID', 'job id',
            # Completion indicators
            'Complete', 'COMPLETE', 'Done', 'DONE', 'Finished', 'FINISHED',
            # Error indicators (also considered completion)
            'Error', 'ERROR', 'Failed', 'FAILED'
        ]
        
        recent_output = output[-200:] if len(output) > 200 else output
        return any(pattern in recent_output for pattern in completion_patterns)
    
    def _execute_commands_session(self, commands: List[str], session_id: str) -> bool:
        """Execute commands in a single SSH session"""
        logger.info(f"[{session_id}] Starting SSH session to {self.host}:{self.port}")
        
        client, connect_params = self._create_ssh_client()
        
        try:
            # Connect to server
            client.connect(**connect_params)
            logger.info(f"[{session_id}] Connected successfully")
            
            # Create interactive shell
            shell = client.invoke_shell(term='xterm', width=132, height=40)
            self.shell_active = True
            
            # Setup environment
            self._setup_shell_environment(shell)
            
            if self.interactive_mode:
                # Interactive mode: Auto-type commands then allow manual input
                print(f"\n🚀 Connected to {self.host}! Starting automated command execution...")
                print(f"📋 Found {len([c for c in commands if c.strip() and not c.startswith('#')])} commands to execute")
                print("👀 Watch as commands are automatically typed and executed:")
                print("="*60)
                
                # First, execute predefined commands automatically
                success = self._execute_commands_interactively(shell, commands)
                
                # Then allow manual input
                print("\n" + "="*60)
                print("🎮 Automated commands completed! You can now type manual commands.")
                print("Type '!help' for help, '!menu' for menu, or 'exit' to quit.")
                print("="*60)
                
                self._start_input_thread(shell)
                
                # Handle output in real-time for manual commands
                try:
                    while self.shell_active:
                        if shell.recv_ready():
                            chunk = shell.recv(4096).decode('utf-8', errors='ignore')
                            print(chunk, end='')
                        time.sleep(0.1)
                        
                        # Check if shell is still active
                        if shell.closed:
                            break
                            
                except KeyboardInterrupt:
                    print("\n\n🔥 Interrupted by user")
                    shell.send('exit\n')
                
                print("\n👋 Interactive session ended.")
                self.shell_active = False
                
            else:
                # Automated mode: execute predefined commands
                success = True
                for i, command in enumerate(commands, 1):
                    command = command.strip()
                    if not command or command.startswith('#'):
                        continue
                    
                    if self._ask_user_confirmation(command, i, len(commands)):
                        logger.info(f"[{session_id}] Command {i}/{len(commands)}: {command}")
                        output, cmd_success = self._execute_command_interactive(shell, command, session_id)
                        
                        if not cmd_success:
                            logger.error(f"[{session_id}] Command failed or timed out")
                            success = False
                        
                        # Wait between commands
                        time.sleep(self.inter_command_delay)
                    else:
                        print(f"⏭️  Skipping command: {command}")
                
                # Graceful logout
                shell.send('exit\n')
                time.sleep(1)
            
            shell.close()
            logger.info(f"[{session_id}] Session completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"[{session_id}] Session failed: {str(e)}")
            self._log_connection_error(e, session_id)
            return False
        finally:
            self.shell_active = False
            client.close()
    
    def _ask_user_confirmation(self, command: str, current: int, total: int) -> bool:
        """Ask user for confirmation before executing command"""
        print(f"\n📋 Command {current}/{total}: {command}")
        
        while True:
            response = input("Execute? (y/n/q/m): ").lower().strip()
            if response in ['y', 'yes', '']:
                return True
            elif response in ['n', 'no']:
                return False
            elif response in ['q', 'quit']:
                print("🚪 Quitting...")
                sys.exit(0)
            elif response in ['m', 'modify']:
                new_command = input(f"Enter new command (or press Enter to keep '{command}'): ").strip()
                if new_command:
                    command = new_command
                    print(f"📝 Modified command: {command}")
                continue
            else:
                print("Please enter 'y' (yes), 'n' (no), 'q' (quit), or 'm' (modify)")
    
    def _log_connection_error(self, error: Exception, session_id: str) -> None:
        """Log detailed connection error information"""
        error_msg = str(error)
        
        if "getaddrinfo failed" in error_msg:
            logger.error(f"[{session_id}] DNS Resolution Error: Cannot resolve hostname '{self.host}'")
        elif "Connection refused" in error_msg:
            logger.error(f"[{session_id}] Connection Refused: {self.host}:{self.port}")
        elif "Authentication failed" in error_msg:
            logger.error(f"[{session_id}] Authentication Failed: Invalid credentials")
        elif "timeout" in error_msg.lower():
            logger.error(f"[{session_id}] Connection Timeout: {self.host}:{self.port}")
        else:
            logger.error(f"[{session_id}] Connection Error: {error_msg}")
    
    def _split_commands_into_blocks(self, commands: List[str]) -> List[List[str]]:
        """Split commands into execution blocks (for parallel execution)"""
        blocks = []
        current_block = []
        blank_count = 0
        
        for command in commands:
            if command.strip() == '':
                blank_count += 1
                if blank_count >= 2 and current_block:
                    blocks.append(current_block)
                    current_block = []
                    blank_count = 0
            else:
                if blank_count >= 2 and current_block:
                    blocks.append(current_block)
                    current_block = []
                blank_count = 0
                current_block.append(command)
        
        if current_block:
            blocks.append(current_block)
        
        return blocks if blocks else [commands]
    
    def set_interactive_mode(self, interactive: bool) -> None:
        """Enable or disable interactive mode"""
        self.interactive_mode = interactive
    
    def execute_commands(self) -> bool:
        """Execute all commands with appropriate parallelization"""
        if not self.commands and not self.interactive_mode:
            logger.warning("No commands to execute")
            return True
        
        if self.interactive_mode:
            # Interactive mode: single session with predefined commands
            return self._execute_commands_session(self.commands, "etx-interactive")
        
        # Split commands into blocks
        command_blocks = self._split_commands_into_blocks(self.commands)
        
        if len(command_blocks) == 1:
            # Single block execution
            return self._execute_commands_session(command_blocks[0], "etx-main")
        else:
            # Multi-block parallel execution
            logger.info(f"Executing {len(command_blocks)} command blocks in parallel")
            
            success = True
            with ThreadPoolExecutor(max_workers=min(len(command_blocks), 4)) as executor:
                future_to_block = {
                    executor.submit(self._execute_commands_session, block, f"etx-{i}"): i
                    for i, block in enumerate(command_blocks, 1)
                }
                
                for future in as_completed(future_to_block):
                    block_id = future_to_block[future]
                    try:
                        result = future.result()
                        if not result:
                            logger.error(f"Block {block_id} failed")
                            success = False
                        else:
                            logger.info(f"Block {block_id} completed successfully")
                    except Exception as e:
                        logger.error(f"Block {block_id} raised exception: {e}")
                        success = False
            
            return success


def load_settings(settings_path: str = "settings.txt") -> Dict[str, Any]:
    """Load configuration from settings file"""
    if not os.path.exists(settings_path):
        raise FileNotFoundError(f"Settings file not found: {settings_path}")
    
    settings = {}
    
    try:
        with open(settings_path, "r", encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise RuntimeError(f"Failed to read settings file: {e}")
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines and comments
        if not line or line.startswith("#"):
            i += 1
            continue
        
        # Handle multi-line values (REMOTE_COMMANDS, REMOTE_TARGET_DIRS)
        if line.startswith("REMOTE_COMMANDS=") or line.startswith("REMOTE_TARGET_DIRS="):
            key = line.split("=", 1)[0].strip().upper()
            values = []
            
            # Get initial value if present
            val = line[len(key)+1:].strip()
            if val:
                values.append(val)
            
            # Read subsequent lines
            i += 1
            while i < len(lines):
                cmd_line = lines[i].strip()
                if not cmd_line or cmd_line.startswith('#'):
                    i += 1
                    continue
                # Stop if we hit another setting (must be at start of line and uppercase before =)
                if '=' in cmd_line and not cmd_line.startswith(' '):
                    # Check if this looks like a new setting (uppercase key at start)
                    potential_key = cmd_line.split('=')[0].strip()
                    if potential_key.isupper() and '_' in potential_key:
                        break
                values.append(cmd_line)
                i += 1
            
            settings[key] = values
            continue
        
        # Handle single-line settings
        if "=" in line:
            key, value = line.split("=", 1)
            settings[key.strip().upper()] = value.strip()
        
        i += 1
    
    # Type conversions
    if "REMOTE_PORT" in settings:
        try:
            settings["REMOTE_PORT"] = int(settings["REMOTE_PORT"])
        except ValueError:
            logger.warning("Invalid REMOTE_PORT value, using default 22")
            settings["REMOTE_PORT"] = 22
    
    return settings


def show_main_menu() -> str:
    """Show main menu and get user choice"""
    print("\n" + "="*60)
    print("🚀 ETX Remote Command Execution Tool")
    print("="*60)
    print("Choose your execution mode:")
    print("1. 🤖 Automated Mode - Run predefined commands from settings")
    print("2. 🎮 Interactive Mode - Auto-type commands + manual input")
    print("3. 🔧 Step-by-Step Mode - Review each command before execution")
    print("4. ❌ Exit")
    print("="*60)
    
    while True:
        choice = input("Enter your choice (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        print("Please enter 1, 2, 3, or 4")


def main():
    """Main execution function"""
    logger.info("Starting ETX Remote Command Execution")
    
    try:
        # Load configuration
        config = load_settings()
        logger.info(f"Configuration loaded successfully")
        
        # Show menu
        choice = show_main_menu()
        
        if choice == '4':
            print("👋 Goodbye!")
            return 0
        
        # Create executor
        executor = ETXRemoteExecutor(config)
        
        # Set mode based on choice
        if choice == '1':
            print("\n🤖 Running in Automated Mode...")
            success = executor.execute_commands()
        elif choice == '2':
            print("\n🎮 Starting Interactive Mode...")
            executor.set_interactive_mode(True)
            success = executor.execute_commands()
        elif choice == '3':
            print("\n🔧 Running in Step-by-Step Mode...")
            success = executor.execute_commands()
        
        if success:
            logger.info("Execution completed successfully")
            print("\n✅ Execution completed successfully!")
        else:
            logger.error("Execution failed")
            print("\n❌ Execution failed. Check logs for details.")
            
    except KeyboardInterrupt:
        print("\n\n🔥 Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        return 1
    
    return 0


def run_remote_etx():
    """
    Compatibility wrapper for the old run_remote_etx function
    Used by app.py dashboard for backward compatibility
    """
    try:
        # Load configuration
        config = load_settings()
        
        # Create executor in automated mode
        executor = ETXRemoteExecutor(config)
        
        # Execute commands in automated mode
        success = executor.execute_commands()
        
        if success:
            print("✅ All commands executed successfully!")
        else:
            print("❌ Some commands failed. Check logs for details.")
            
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    exit_code = main()
    
    # Keep window open for a moment
    print("\nPress Enter to exit...")
    try:
        input()
    except KeyboardInterrupt:
        pass
    
    sys.exit(exit_code) 