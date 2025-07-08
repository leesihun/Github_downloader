# Enhanced SSH Implementation Guide

## 🚀 **Problem Solved: SSH Compatibility with Job Schedulers**

### **What was wrong with the original approach?**

The original `ssh.exec_command()` approach had **fundamental compatibility issues** with job schedulers:

1. **Session Isolation**: Each command ran in a separate session
2. **No Environment Persistence**: Environment variables weren't preserved between commands
3. **Non-interactive Mode**: Job schedulers expect interactive shell sessions
4. **Short Timeouts**: Insufficient time for job submission processing

### **✅ Enhanced SSH Implementation**

The new implementation uses `ssh.invoke_shell()` for **persistent shell sessions**:

```python
# OLD (broken with job schedulers):
stdin, stdout, stderr = ssh.exec_command(command)

# NEW (compatible with job schedulers):
shell = ssh.invoke_shell()
shell.send(command + '\n')
# Process output in real-time...
```

## 🏗️ **HPC Connection Architecture**

### **How Your System Works:**

```
Your Computer → [Internet] → 202.20.185.100 (HPC Gateway)
                                    ↓
                            Internal Load Balancer
                                    ↓
                    login01  login02  login03  login04  (CPU nodes)
                    login05  login06  login07  login08  (GPU nodes)
                    login09  login10                    (GPU nodes)
```

### **Key Points:**

- **Single IP Address**: All connections go to `202.20.185.100`
- **Internal Assignment**: The server decides which login node you get
- **Hostname Selection**: For user preference/organization only
- **Load Balancing**: Automatic distribution to available nodes
- **Prompt Shows Assignment**: You see `[s.hun.lee@login04 ~]` after connection

## 🔧 **Configuration**

### **Connection Settings (settings.txt):**
```
REMOTE_HOST=202.20.185.100  # Single gateway IP
REMOTE_PORT=22
REMOTE_USER=s.hun.lee
REMOTE_PASS=atleast12!
```

### **Hostname Selection Logic:**
- **CPU Mode**: Requests assignment to login01-04
- **GPU Mode**: Requests assignment to login05-10
- **All connect to same IP**: `202.20.185.100`
- **Server handles assignment**: Internal load balancing

## 📊 **Enhanced Features**

### **1. Real-time Output Display**
```python
# Continuous output processing
while True:
    if shell.recv_ready():
        output = shell.recv(1024).decode('utf-8')
        print(output, end='')
        full_output += output
    
    if shell.exit_status_ready():
        break
```

### **2. Persistent Shell Sessions**
- Environment variables preserved
- Working directory maintained
- Interactive commands supported
- Job scheduler compatibility

### **3. Intelligent Error Handling**
- Connection timeouts (60 seconds)
- Authentication failures
- Network connectivity issues
- Job scheduler error detection

### **4. CPU/GPU Toggle Interface**
- Dynamic hostname selection
- Visual mode indicators
- Automatic node targeting
- User preference storage

## 🎯 **Job Scheduler Compatibility**

### **Why Enhanced SSH Works:**

1. **Persistent Sessions**: Commands run in the same shell environment
2. **Environment Variables**: `source ML_env/bin/activate` persists
3. **Working Directory**: `cd` commands affect subsequent commands
4. **Interactive Mode**: Job schedulers can interact with the shell
5. **Extended Timeouts**: Enough time for job submission processing

### **Example Job Submission:**
```bash
# All of these run in the same persistent shell session:
source ML_env/bin/activate
cd ML_env/SimulGen-VAE/v3/PCB_slit/484_dataset/1
phd run -ng 1 -p shr_gpu -GR H100 -l %J.log python SimulGen-VAE.py --preset=1
```

## 🔍 **Troubleshooting**

### **Connection Issues:**
- **Check IP**: Verify `202.20.185.100` is accessible
- **Check Credentials**: Ensure username/password are correct
- **Check Network**: VPN might be required for external access
- **Check Firewall**: Port 22 must be open

### **Job Scheduler Issues:**
- **Environment**: Ensure `source ML_env/bin/activate` runs first
- **Paths**: Use absolute paths or navigate to correct directory
- **Permissions**: Check file and directory permissions
- **Resources**: Verify requested GPU/CPU resources are available

### **Output Issues:**
- **Encoding**: UTF-8 encoding is used for all output
- **Buffering**: Real-time output might lag slightly
- **Timeout**: Extend timeout for long-running jobs

## 📈 **Performance Improvements**

### **Before (exec_command)**:
- ❌ New session per command
- ❌ Environment reset each time
- ❌ No job scheduler compatibility
- ❌ Limited timeout
- ❌ No real-time output

### **After (invoke_shell)**:
- ✅ Persistent shell session
- ✅ Environment preserved
- ✅ Job scheduler compatible
- ✅ Extended timeout (60s)
- ✅ Real-time output display

## 🎉 **Result**

Your ETX Dashboard now has **full compatibility** with:
- ✅ **MobaXterm-like behavior**
- ✅ **Job scheduler commands (phd run)**
- ✅ **Persistent shell sessions**
- ✅ **Real-time output display**
- ✅ **CPU/GPU hostname selection**
- ✅ **Enhanced error handling**

The system now works exactly like MobaXterm with the added benefit of a web-based interface and automated job management! 