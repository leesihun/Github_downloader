# How to Use the ETX Dashboard

1. Make sure all files and folders are in the same directory as run_dashboard.exe (including templates/, static/, settings.txt, etc).

2. Double-click run_dashboard.exe **as Administrator** to start the server in the background (port 80 requires admin privileges).

3. Open your browser and go to:
   http://127.0.0.1

4. Use the dashboard as normal. All settings and job controls are available in the web interface.
   - To change settings, use the Settings form on the right side of the dashboard. Each parameter has its own field.

# Notes
- The .exe is already built and provided for you. No need to install Python or build anything.
- If you want to use a custom local domain (e.g., http://autosupercom), edit your hosts file:
  - Open C:\Windows\System32\drivers\etc\hosts as Administrator
  - Add this line:
    127.0.0.1   autosupercom
  - Save the file
  - Then visit http://autosupercom in your browser.
- If you want to update the dashboard logic, edit the Python source files and rebuild the .exe using PyInstaller (see previous instructions if needed). 