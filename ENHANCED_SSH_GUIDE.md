# Enhanced SSH Mode for Job Scheduler Compatibility

## 🎯 Problem Solved

**Question:** Is the current SSH implementation the same as MobaXterm?

**Answer:** **NOW IT IS!** The enhanced SSH mode has been implemented to provide MobaXterm-equivalent functionality.

## 🔍 Key Differences: Before vs After

### ❌ **Original Implementation (Legacy Mode)**
- Used `ssh.exec_command()` - creates new session per command
- Commands chained with `&&` - environment may not persist
- Limited job scheduler compatibility
- No persistent shell sessions

### ✅ **Enhanced Implementation (New Default)**
- Uses `ssh.invoke_shell()` - persistent shell sessions
- Commands executed sequentially in same shell
- **Job scheduler compatible** (phd run, SLURM, PBS, etc.)
- Real-time output display
- Environment variables persist between commands

## 🚀 MobaXterm Equivalent Features

| Feature | MobaXterm | Enhanced SSH | Legacy SSH |
|---------|-----------|--------------|------------|
| Persistent Shell Session | ✅ | ✅ | ❌ |
| Environment Inheritance | ✅ | ✅ | ❌ |
| Job Scheduler Support | ✅ | ✅ | ❌ |
| Real-time Output | ✅ | ✅ | ❌ |
| Interactive Commands | ✅ | ✅ | ❌ |
| Terminal Allocation | ✅ | ✅ | ❌ |

## 💡 How to Use Enhanced SSH Mode

### 1. **Default Configuration**
Enhanced SSH is **enabled by default** in `run_ETX.py`:
```python
USE_ENHANCED_SSH = True  # MobaXterm-like behavior
```

### 2. **Job Scheduler Commands**
Now you can uncomment your job scheduler commands in `settings.txt`:
```bash
# Job scheduler commands (uncomment to use with enhanced SSH mode):
phd run -ng 1 -p shr_gpu -GR H100 -l %J.log python SimulGen-VAE.py --preset=1 --plot=2 --train_pinn_only=0 --size=small --load_all=1
```

### 3. **Hostname Selection**
- **CPU Mode:** login01-04 (default: login04)
- **GPU Mode:** login05-10 (default: login10)
- Toggle in the dashboard or modify `hostname_mapping` in `run_ETX.py`

## 🔧 Technical Implementation Details

### Enhanced SSH Session Management
```python
# Create persistent shell session (like MobaXterm)
shell = ssh.invoke_shell(term='xterm', width=120, height=30)

# Execute commands sequentially in same shell
for command in commands:
    shell.send(command + '\n')
    # Real-time output collection with timeout
    # Proper prompt detection
    # Environment state preservation
```

### Job Scheduler Compatibility
- **Increased timeout:** 60 seconds for job submissions
- **Persistent environment:** `source ML_env/bin/activate` works across commands
- **Interactive support:** Handles job scheduler prompts and responses
- **Terminal allocation:** Proper terminal settings for job schedulers

## 📊 Testing Your Setup

Run the test script to verify functionality:
```bash
python test_enhanced_ssh.py
```

## 🛠️ Troubleshooting

### If You Get DNS Resolution Errors:

The system now tries to connect directly to hostnames like `login04`. If you get "getaddrinfo failed" errors:

1. **Configure Hostname Mapping:**
   ```python
   # In run_ETX.py, uncomment and configure Method 2:
   hostname_mapping = {
       'login01': '202.20.185.101',
       'login02': '202.20.185.102',
       'login03': '202.20.185.103',
       'login04': '202.20.185.104',
       'login05': '202.20.185.105',
       'login06': '202.20.185.106',
       'login07': '202.20.185.107',
       'login08': '202.20.185.108',
       'login09': '202.20.185.109',
       'login10': '202.20.185.110',
   }
   ```

2. **Or Use Fully Qualified Domain Names:**
   ```python
   # If your system uses domains, uncomment Method 3:
   REMOTE_HOST = f"{hostname}.hpc.university.edu"
   ```

### If Job Submissions Still Don't Work:

1. **Verify Job Scheduler Commands:**
   - Test commands manually in MobaXterm first
   - Ensure proper syntax for your scheduler (`phd run`, `sbatch`, etc.)
   - Check queue and resource availability

2. **Network Connectivity:**
   - Ensure selected hostnames (login01-10) are accessible
   - Verify credentials and permissions
   - Check firewall and network policies

3. **Check SSH Connection:**
   - Verify you can connect to the selected hostname manually
   - Ensure SSH service is running on the target nodes
   - Check if the hostnames resolve in your network

## 🎉 Benefits Over Original Implementation

1. **✅ Job Scheduler Support:** `phd run`, `sbatch`, `qsub` commands now work
2. **✅ Environment Persistence:** Virtual environments and modules stay active
3. **✅ Real-time Feedback:** See command output as it happens
4. **✅ Better Error Handling:** Proper timeout and error detection
5. **✅ MobaXterm Compatibility:** Nearly identical behavior to MobaXterm SSH

## 🔄 Fallback Option

If you need the original behavior:
```python
# In run_ETX.py, change:
USE_ENHANCED_SSH = False  # Use legacy mode
```

## 📝 Configuration Examples

### Example 1: Basic Job Submission
```bash
source ML_env/bin/activate
cd /path/to/your/project
phd run -ng 1 -p shr_gpu -GR H100 -l job.log python your_script.py
```

### Example 2: Multiple Jobs with Different Hosts
```bash
# Commands will run on selected hostname (login04 or login10)
source ML_env/bin/activate
cd /path/to/project1
phd run -ng 1 -p shr_gpu -GR H100 -l job1.log python script1.py

cd /path/to/project2
phd run -ng 1 -p shr_gpu -GR H100 -l job2.log python script2.py
```

---

**🚀 The enhanced SSH mode now provides MobaXterm-equivalent functionality for job scheduler compatibility!** 