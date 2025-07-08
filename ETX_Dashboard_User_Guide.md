# ETX Dashboard Web Application — User Guide

---

## Overview

The **ETX Dashboard** is a local web application for managing your workflow between Github, your local machine, and remote ETX servers. It provides a modern, user-friendly interface for configuring, running, and monitoring all related jobs—no command line required.

---

## How to Start

1. **Double-click `run_dashboard.exe`** (as Administrator).
2. The dashboard will automatically open in your default web browser at [http://127.0.0.1](http://127.0.0.1).
3. You will see the ETX Dashboard interface.

---

## Main Features

### 1. **Job Controls**

- **Github → Local**  
  Download and extract a Github project to your local machine.

- **Local → ETX**  
  Upload a local folder to one or more remote ETX directories.

- **Run ETX Commands**  
  Execute custom commands on your remote ETX server(s) via SSH.

- **Delete Local Folders**  
  Clean up all local files/folders related to the workflow.

- **Pipeline (All)**  
  Run all steps in sequence: download, upload, and execute remote commands.

---

### 2. **Settings Form**

- All configuration is managed through a form on the right side of the dashboard.
- **Each parameter has its own field:**
  - Project URL (Github)
  - Local and remote paths
  - SSH credentials
  - Remote commands (multi-line)
  - And more
- **Multi-line fields** (like remote commands and target directories) are supported.
- **Save** your changes with the Save button. The dashboard will use your new settings for all jobs.

---

### 3. **Live Job Log**

- See real-time output from any running job.
- Errors and progress are displayed as they happen.

---

### 4. **Job History**

- View a table of previous job runs, including:
  - Job type
  - Start and end time
  - Status (success/error)
  - Downloadable log files

---

### 5. **Responsive, Modern UI**

- Built with Bootstrap for a clean, professional look.
- Works in all modern browsers.
- Mobile-friendly layout.

---

## Typical Workflow

1. **Configure your settings** in the form (right side).
2. **Click a job control button** to start a job (e.g., Github → Local).
3. **Monitor progress** in the live log area.
4. **Review job history** and download logs as needed.
5. **Repeat or chain jobs** as your workflow requires.

---

## Advanced Features

- **Multiple Remote Targets:**  
  Upload to several remote directories at once (one per line).
- **Parallel Remote Commands:**  
  Use blank lines in the remote commands field to define parallel execution blocks.
- **Automatic Browser Launch:**  
  The dashboard opens automatically when you start the app.

---

## Troubleshooting

- If the dashboard does not open, ensure you are running `run_dashboard.exe` as Administrator.
- If you change settings, always click Save before running a job.
- For network or SSH issues, check your credentials and network/firewall settings.

---

## Customization & Maintenance

- All logic is editable in the Python source files.
- To update the dashboard logic, edit the code and rebuild the `.exe` if needed.
- For advanced users, you can add new job types, custom UI, or integrate with other systems.

---

## Support

For further help, contact your system administrator or the developer who provided this dashboard.

---

**Enjoy your streamlined ETX workflow!** 