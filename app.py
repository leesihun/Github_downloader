import os
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import re

# Import job functions
from Github_to_Local_to_ETX import download_github_to_local, upload_local_to_etx, delete_local_folders
from run_ETX import run_remote_etx

app = Flask(__name__)
LOG_DIR = 'job_logs'
SETTINGS_FILE = 'settings.txt'

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# In-memory job status and logs
job_status = {}
job_logs = {}
job_history = []  # List of dicts: {id, type, start, end, status, log_file}

# Helper to run a job in a thread and capture logs
def run_job(job_type, func):
    job_id = f"{job_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log_file = os.path.join(LOG_DIR, f"{job_id}.log")
    job_status[job_id] = 'running'
    job_logs[job_id] = ''
    start_time = datetime.now()
    def target():
        with open(log_file, 'w', encoding='utf-8') as f:
            def log_writer(msg):
                f.write(msg)
                f.flush()
                job_logs[job_id] += msg
            # Patch print to capture output
            import builtins
            orig_print = builtins.print
            builtins.print = lambda *args, **kwargs: log_writer(' '.join(str(a) for a in args) + '\n')
            try:
                func()
                job_status[job_id] = 'success'
            except Exception as e:
                job_status[job_id] = 'error'
                log_writer(f"[ERROR] {e}\n")
            finally:
                builtins.print = orig_print
                end_time = datetime.now()
                job_history.append({
                    'id': job_id,
                    'type': job_type,
                    'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': job_status[job_id],
                    'log_file': log_file
                })
    t = threading.Thread(target=target, daemon=True)
    t.start()
    return job_id

@app.route('/')
def index():
    return render_template('index.html', settings=read_settings(), job_history=job_history)

@app.route('/run_job', methods=['POST'])
def run_job_route():
    job_type = request.json.get('job_type')
    
    if job_type == 'github_to_local':
        job_id = run_job('github_to_local', download_github_to_local)
    elif job_type == 'local_to_etx':
        job_id = run_job('local_to_etx', upload_local_to_etx)
    elif job_type == 'run_etx_commands':
        job_id = run_job('run_etx_commands', run_remote_etx)
    elif job_type == 'delete_local_folders':
        job_id = run_job('delete_local_folders', delete_local_folders)
    elif job_type == 'pipeline':
        def pipeline():
            download_github_to_local()
            upload_local_to_etx()
            run_remote_etx()
        job_id = run_job('pipeline', pipeline)
    else:
        return jsonify({'error': 'Unknown job type'}), 400
    return jsonify({'job_id': job_id})

@app.route('/job_status/<job_id>')
def job_status_route(job_id):
    return jsonify({'status': job_status.get(job_id, 'unknown')})

@app.route('/job_log/<job_id>')
def job_log_route(job_id):
    return jsonify({'log': job_logs.get(job_id, '')})

@app.route('/job_history')
def job_history_route():
    return jsonify({'history': job_history[-20:]})

@app.route('/download_log/<job_id>')
def download_log(job_id):
    log_file = os.path.join(LOG_DIR, f"{job_id}.log")
    if os.path.exists(log_file):
        return send_from_directory(LOG_DIR, f"{job_id}.log", as_attachment=True)
    return '', 404

# Settings editor
@app.route('/settings', methods=['GET', 'POST'])
def settings_route():
    if request.method == 'POST':
        new_settings = request.form.get('settings')
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            f.write(new_settings)
        return jsonify({'success': True})
    else:
        return jsonify({'settings': read_settings()})

def read_settings():
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        return f.read()

def parse_settings_txt_to_json(settings_txt):
    settings = {}
    key = None
    values = []
    for line in settings_txt.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            if key:
                if len(values) == 1:
                    settings[key] = values[0]
                else:
                    settings[key] = values
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if value:
                values = [value]
            else:
                values = []
        else:
            values.append(line)
    if key:
        if len(values) == 1:
            settings[key] = values[0]
        else:
            settings[key] = values
    return settings

def write_settings_json_to_txt(settings):
    lines = []
    for k, v in settings.items():
        if isinstance(v, list):
            lines.append(f"{k}=")
            for item in v:
                lines.append(str(item))
        else:
            lines.append(f"{k}={v}")
    return '\n'.join(lines) + '\n'

@app.route('/settings_json', methods=['GET', 'POST'])
def settings_json_route():
    if request.method == 'POST':
        settings = request.json
        txt = write_settings_json_to_txt(settings)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            f.write(txt)
        return jsonify({'success': True})
    else:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            txt = f.read()
        settings = parse_settings_txt_to_json(txt)
        return jsonify(settings)

# Static files for frontend
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Flask template auto-reload
app.config['TEMPLATES_AUTO_RELOAD'] = True

if __name__ == '__main__':
    app.run(debug=True, port=5000) 