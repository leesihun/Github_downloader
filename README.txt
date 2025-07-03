# How to Build and Run the ETX Dashboard as an .exe

1. Install PyInstaller (if not already):
   pip install pyinstaller

2. Place your custom icon file (e.g., autosupercom.ico) in the project root.

3. Build the .exe:
   pyinstaller --noconsole --onefile --icon=autosupercom.ico run_dashboard.py

   - --noconsole: Runs in the background (no black window)
   - --onefile: Single .exe output
   - --icon: Sets the custom icon for the .exe

4. The .exe will be in the dist/ folder as run_dashboard.exe

5. To access the app at http://autosupercom, edit your hosts file:
   - Open C:\Windows\System32\drivers\etc\hosts as Administrator
   - Add this line:
     127.0.0.1   autosupercom
   - Save the file

6. Double-click run_dashboard.exe **as Administrator** to start the server in the background (port 80 requires admin privileges).

7. Open your browser to http://autosupercom

# You only need to click the .exe and visit http://autosupercom 