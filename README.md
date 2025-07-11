# ETX Automation Dashboard

A comprehensive automation system for managing GitHub to HPC workflows with an interactive web dashboard and terminal interface.

## 🚀 Features

### **📊 Web Dashboard**
- **Visual job management** with real-time status updates
- **Side-by-side job log & terminal view** for simultaneous monitoring
- **Interactive terminal** with real SSH command execution
- **Settings editor** for easy configuration management
- **Job history tracking** with downloadable logs
- **Live log streaming** during job execution

### **🎮 Interactive Terminal Modes**
- **🤖 Automated Mode** - Run all predefined commands automatically
- **🎮 Interactive Mode** - Type commands in real-time with auto-typing simulation
- **🔧 Step-by-Step Mode** - Review and modify each command before execution
- **🚀 Run All Command** - Execute all ETX commands combined with && (run 1 && 2 && ... && end)

### **🔄 Workflow Automation**
- **GitHub → Local** - Download repositories automatically
- **Local → ETX** - Upload files to HPC systems via SFTP
- **Command Execution** - Run complex command sequences on remote systems
- **Pipeline Mode** - Execute complete workflow end-to-end

## 📁 Project Structure

```
Github_to_etx/
├── README.md                     # This file
├── settings.txt                  # Configuration file
├── 
├── # Main Scripts
├── Github_to_Local_to_ETX.py     # Primary workflow pipeline
├── run_ETX.py                    # Interactive SSH command execution
├── app.py                        # Web dashboard backend (Flask)
├── run_dashboard.py              # Dashboard launcher
├── 
├── # Web Interface
├── templates/
│   └── index.html                # Dashboard HTML interface
├── static/
│   ├── style.css                 # Dashboard styling
│   └── app.js                    # Dashboard JavaScript
├── 
├── # Logs and Data
├── job_logs/                     # Execution logs directory
├── run_etx.log                   # ETX command execution logs
└── 
```

## 🛠️ Installation

### Prerequisites
- **Python 3.7+**
- **Required packages:**
  ```bash
  pip install paramiko flask requests
  ```

### Quick Start
1. **Clone or download** this repository
2. **Configure settings** in `settings.txt`
3. **Start the dashboard:**
   ```bash
   python run_dashboard.py
   ```
4. **Open browser** to `http://localhost:5000`

## ⚙️ Configuration

Edit `settings.txt` to configure your system:

```ini
# ===== Github to Local =====
PROJECT_URL=https://github.com/username/repository
ZIP_PATH=C:/Downloads/project.zip
LOCAL_TARGET_DIR=D:/Projects/MyProject

# ===== Local to ETX =====
REMOTE_HOST=202.20.185.100
REMOTE_PORT=22
REMOTE_USER=your.username
REMOTE_PASS=your_password
REMOTE_TARGET_DIRS=
/home/username/project/dir1
/home/username/project/dir2

# ===== Remote Commands =====
REMOTE_COMMANDS=
echo "Starting workflow"
hostname
cd /home/username/project
ls -la
# Add your commands here...
```

## 🎯 Usage Guide

### **Option 1: Web Dashboard (Recommended)**

1. **Start the dashboard:**
   ```bash
   python run_dashboard.py
   ```

2. **Access the interface:**
   - Open `http://localhost:5000` in your browser

3. **Use the features:**
   - **Job Controls** - Execute individual workflow steps
   - **Interactive Terminal** - Real-time command execution
   - **Settings Editor** - Modify configuration
   - **Job History** - Track execution history

### **Option 2: Command Line Interface**

#### **Interactive Command Execution:**
```bash
python run_ETX.py
```
**Choose from:**
- 🤖 **Automated Mode** - Silent execution
- 🎮 **Interactive Mode** - Watch commands being typed + manual input
- 🔧 **Step-by-Step Mode** - Review each command

#### **Complete Workflow:**
```bash
python Github_to_Local_to_ETX.py
```

### **Option 3: Individual Scripts**

**Download from GitHub:**
```python
from Github_to_Local_to_ETX import download_github_to_local
download_github_to_local()
```

**Upload to ETX:**
```python
from Github_to_Local_to_ETX import upload_local_to_etx
upload_local_to_etx()
```

**Execute remote commands:**
```python
from run_ETX import run_remote_etx
run_remote_etx()
```

## 🎮 Interactive Terminal Guide

### **Starting a Terminal Session**

1. **In the web dashboard**, scroll to "🎮 Interactive Terminal"
2. **Choose mode:**
   - **🎮 Interactive Mode** - Type commands manually
   - **🤖 Automated Mode** - Run all predefined commands
3. **Or use the "Run ETX Commands" button** - Automatically executes all commands in terminal

### **🚀 Run All Command**

The **"run all"** command is the most powerful feature for executing all your ETX commands:

```bash
run all        # Execute all predefined commands sequentially
```

**Features:**
- **Combined execution** - All commands combined with && operators (cmd1 && cmd2 && ... && end)
- **Single command execution** - Runs as one efficient command chain
- **Real-time output** - See results as they happen
- **Error handling** - Stops execution if any command fails (standard && behavior)
- **Output management** - Long outputs are truncated for readability
- **Interactive afterwards** - Terminal remains active for additional commands

**Example Output:**
```
$ run all
🚀 Running all 5 commands as one combined command:
============================================================
📝 Combined Command: echo "Starting workflow" && hostname && ls -la && cd /project && python script.py
⏳ Executing combined command...
✅ All commands completed successfully
Output:
  Starting workflow
  login01.hpc.example.com
  total 1024
  drwxr-xr-x  8 user group  256 Nov 15 10:30 .
  drwxr-xr-x 15 user group  480 Nov 15 10:29 ..
  -rw-r--r--  1 user group   45 Nov 15 10:30 script.py
  -rw-r--r--  1 user group  1024 Nov 15 10:30 data.txt
  /project
  Script execution completed!

============================================================
🎉 All commands execution completed!

💡 You can now type additional commands or 'exit' to close.
```

### **Available Commands**

```bash
help           # Show available commands
list           # List all predefined commands
run <number>   # Execute predefined command by number
run all        # Execute all predefined commands combined with && (1 && 2 && ... && end)
status         # Show session status
clear          # Clear terminal screen
exit           # Exit session

# Plus any custom shell commands
ls -la
cd /path/to/directory
python script.py
```

### **Interactive Features**
- **Real SSH command execution** - Commands are executed on remote server
- **Real-time output** streaming from remote system
- **Side-by-side job log and terminal** for comprehensive monitoring
- **Run ETX Commands button** - Automatically executes "run all" command in terminal
- **Combined command execution** - Run all commands as one chain with && operators
- **Command history** and suggestions
- **Auto-completion** for predefined commands
- **Session management** with status indicators
- **Error handling** and recovery

## 🔧 Advanced Features

### **Multi-Threading Support**
Commands separated by double blank lines run in parallel:
```ini
REMOTE_COMMANDS=
# Block 1 (runs in parallel with Block 2)
command1
command2

# (double blank line creates new block)

# Block 2 (runs in parallel with Block 1)
command3
command4
```

### **Job Command Detection**
The system automatically detects and handles job submission commands with extended timeouts:
- `ansys_sub`
- `phd run`
- `sbatch`
- `qsub`
- `bsub`
- `srun`

### **Error Recovery**
- **Connection retry logic** with exponential backoff
- **Detailed error logging** for troubleshooting
- **Session recovery** after network interruptions

## 🚨 Troubleshooting

### **Common Issues**

**Connection Errors (WinError 10060):**
```
❌ [WinError 10060] 연결된 구성원으로부터 응답이 없어...
```
**Solutions:**
- Check network connectivity to HPC system
- Verify VPN connection if required
- Confirm SSH service is running on target server
- Validate hostname/IP address in settings

**Authentication Failures:**
```
❌ Authentication Failed: Invalid credentials
```
**Solutions:**
- Verify username and password in `settings.txt`
- Check if account is locked or expired
- Ensure SSH access is enabled for your account

**Terminal 404 Errors:**
```
❌ Connection error: Unexpected token '<'
```
**Solutions:**
- Restart the dashboard: `python run_dashboard.py`
- Clear browser cache and refresh
- Check if Flask app started successfully

### **Debug Mode**

Enable detailed logging by running:
```bash
python run_ETX.py
```
Logs are saved to `run_etx.log` for analysis.

### **Network Configuration**

If behind a proxy, configure in `Github_to_Local_to_ETX.py`:
```python
proxies = {
    "http": "http://proxy.server:port",
    "https": "http://proxy.server:port"
}
```

## 🔐 Security Notes

- **Passwords** are stored in plain text in `settings.txt`
- **Use environment variables** for production:
  ```python
  import os
  REMOTE_PASS = os.getenv('ETX_PASSWORD', 'fallback_password')
  ```
- **Restrict file permissions** on `settings.txt`
- **Use SSH keys** instead of passwords when possible

## 📋 System Requirements

### **Local System:**
- **OS:** Windows 10/11, macOS, Linux
- **Python:** 3.7 or higher
- **Memory:** 512MB+ available
- **Network:** Internet access for GitHub, SSH access to HPC

### **Remote System (HPC):**
- **SSH server** running on port 22 (or configured port)
- **User account** with appropriate permissions
- **Python/Shell** access for command execution

## 🔧 Building Executable

### **Create Standalone .exe File:**

1. **Automatic build (recommended):**
   ```bash
   python build_exe.py
   ```

2. **Manual build:**
   ```bash
   pip install pyinstaller
   pyinstaller ETX_Dashboard.spec --clean
   ```

3. **Output location:**
   - **Executable:** `dist/ETX_Dashboard.exe`
   - **Size:** ~50-70 MB (includes all dependencies)

### **Running the Executable:**
- Double-click `ETX_Dashboard.exe`
- Or run from command line: `.\dist\ETX_Dashboard.exe`
- Dashboard will start automatically at `http://localhost:5000`

### **Executable Features:**
- **Standalone operation** - No Python installation required
- **All functionality included** - Interactive terminal, "run all" commands, job management
- **Portable** - Can be moved to any Windows system
- **Auto-start dashboard** - Opens web interface automatically

## 🆘 Support

### **Logs Location:**
- **ETX commands:** `run_etx.log`
- **Dashboard jobs:** `job_logs/` directory
- **Console output:** Real-time in dashboard

### **Common Commands for Debugging:**
```bash
# Test SSH connection
ssh username@hostname

# Check port accessibility
telnet hostname 22

# View logs
tail -f run_etx.log

# Test individual components
python -c "from run_ETX import load_settings; print(load_settings())"
```

## 🎯 Best Practices

1. **Test connections** manually before automation
2. **Start with small command sets** to verify functionality
3. **Use interactive terminal** for testing commands individually
4. **Monitor logs** during execution in the side-by-side view
5. **Keep backups** of working configurations
6. **Use descriptive job names** for tracking

## 🚀 Getting Started Examples

### **Basic Workflow:**
1. Configure `settings.txt` with your details
2. Test SSH connection manually
3. Start dashboard: `python run_dashboard.py`
4. Run "Local → ETX" to test file transfer
5. Click "Run ETX Commands" to see commands execute in terminal
6. Use interactive terminal to test additional commands
7. Run full pipeline when ready

### **Development Workflow:**
1. Use interactive terminal for command development
2. Test commands individually with `run <number>`
3. Add working commands to `settings.txt`
4. Use "Run ETX Commands" button to execute all commands sequentially
5. Monitor execution in real-time on the terminal side

---

## 📊 Version History

- **v2.4** - Combined command execution with && operators, enhanced "Run All" for single command chain
- **v2.3** - "Run All" command functionality, enhanced ETX Commands button with sequential execution (1 ~ end)
- **v2.2** - ETX Commands in terminal execution, job log & terminal layout swap
- **v2.1** - Real SSH command execution, side-by-side terminal & job log layout
- **v2.0** - Interactive dashboard with real-time terminal
- **v1.5** - Enhanced SSH execution with MobaXterm-like features
- **v1.0** - Basic GitHub to ETX workflow automation

**Built with ❤️ for HPC workflow automation** 