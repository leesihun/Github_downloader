import paramiko


# ========== REMOTE SERVER CONFIGURABLE VARIABLES ==========
REMOTE_HOST = "202.20.185.100"
REMOTE_PORT = 22
REMOTE_USER = "s.hun.lee"
REMOTE_PASS = "atleast12!"
REMOTE_TARGET_DIR = "/home/sr5/s.hun.lee/ML_env/SimulGen_VAE/v2/PCB_slit/484_dataset/github"
commands = [
    "source ML_env/bin/activate",
    "cd ML_env/SimulGen-VAE/v3/PCB_slit/484_dataset/1",
    "phd run -ng 1 -p shr_gpu -GR H100 -l %J.log python SimulGen-VAE.py --preset=1 --plot=2 --train_pinn_only=0 --size=small --load_all=1",
    "cd ..",
    "cd 2",
    "phd run -ng 1 -p shr_gpu -GR H100 -l %J.log python SimulGen-VAE.py --preset=1 --plot=2 --train_pinn_only=0 --size=small --load_all=1"
]
# ============================================




REMOTE_PASSWORD = REMOTE_PASS
# The commands to run on the remote server

# Connect to the remote server
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(REMOTE_HOST, username=REMOTE_USER, password=REMOTE_PASSWORD)

# Run each command and print output
for cmd in commands:
    print(f"\nRunning: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)
    for line in stdout:
        print(line, end="")
    for line in stderr:
        print(line, end="")

print("\nAll commands executed. The connection will remain open until you press Enter.")
input("Press Enter to close the connection...")

ssh.close()