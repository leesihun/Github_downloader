# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

# Get the current directory
current_dir = os.getcwd()

# Define data files to include
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('settings.txt', '.'),
    ('README.md', '.'),
]

# Try to include job_logs directory if it exists
job_logs_dir = os.path.join(current_dir, 'job_logs')
if os.path.exists(job_logs_dir):
    datas.append(('job_logs', 'job_logs'))

# Hidden imports for Flask and other dependencies
hiddenimports = [
    'flask',
    'paramiko',
    'requests',
    'threading',
    'queue',
    'uuid',
    'json',
    'datetime',
    'werkzeug',
    'werkzeug.utils',
    'concurrent.futures',
    'urllib3',
    'cryptography',
    'bcrypt',
    'nacl',
    'six',
    'cffi',
    'pycparser',
]

# Analysis
a = Analysis(
    ['run_dashboard.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ETX_Dashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='supercom_auto_icon.ico',
) 