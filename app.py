import os
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import re
import json
import queue
import uuid

# Import job functions
from Github_to_Local_to_ETX import download_github_to_local, upload_local_to_etx, delete_local_folders
from run_ETX import run_remote_etx, load_settings, ETXRemoteExecutor

app = Flask(__name__)
LOG_DIR = 'job_logs'
SETTINGS_FILE = 'settings.txt'

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# In-memory job status and logs
job_status = {}
job_logs = {}
job_history = []  # List of dicts: {id, type, start, end, status, log_file}

# Interactive terminal sessions
terminal_sessions = {}  # session_id -> {executor, input_queue, output_queue, active}
terminal_outputs = {}   # session_id -> output_text

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
        # Start interactive terminal session and automatically execute "run all"
        try:
            session_id = str(uuid.uuid4())
            config = load_settings()
            
            # Create executor
            executor = ETXRemoteExecutor(config)
            
            # Initialize session for ETX commands with interactive terminal
            terminal_sessions[session_id] = {
                'executor': executor,
                'input_queue': queue.Queue(),
                'output_queue': queue.Queue(),
                'active': True,
                'mode': 'etx_commands_auto',
                'thread': None
            }
            terminal_outputs[session_id] = ""
            
            # Start session thread that shows terminal interface and auto-executes "run all"
            def run_etx_commands_session():
                try:
                    # Show terminal welcome message
                    terminal_outputs[session_id] += f"🚀 ETX Commands Terminal - Session {session_id[:8]}\n"
                    terminal_outputs[session_id] += f"📋 Connected to: {config.get('REMOTE_HOST', 'Unknown')}\n"
                    terminal_outputs[session_id] += f"👤 User: {config.get('REMOTE_USER', 'Unknown')}\n"
                    terminal_outputs[session_id] += "="*60 + "\n"
                    
                    commands = [cmd for cmd in config.get('REMOTE_COMMANDS', []) if cmd.strip() and not cmd.startswith('#')]
                    if not commands:
                        terminal_outputs[session_id] += "❌ No commands found in settings.txt\n"
                        terminal_sessions[session_id]['active'] = False
                        return
                    
                    terminal_outputs[session_id] += f"📝 Found {len(commands)} commands to execute\n"
                    terminal_outputs[session_id] += "🤖 Automatically executing 'run all' command...\n\n"
                    
                    # Simulate typing the "run all" command
                    time.sleep(1)
                    terminal_outputs[session_id] += "$ run all\n"
                    
                    # Combine all commands into one line with && for execution
                    combined_command = " && ".join(commands)
                    terminal_outputs[session_id] += f"🚀 Running all {len(commands)} commands as one combined command:\n"
                    terminal_outputs[session_id] += "="*60 + "\n"
                    terminal_outputs[session_id] += f"📝 Combined Command: {combined_command}\n"
                    terminal_outputs[session_id] += f"⏳ Executing combined command...\n"
                    
                    try:
                        result = executor.execute_single_command(combined_command)
                        terminal_outputs[session_id] += f"✅ All commands completed successfully\n"
                        if result and result.strip():
                            # Show the full output since it's a combined command
                            output_lines = result.strip().split('\n')
                            if len(output_lines) > 20:
                                terminal_outputs[session_id] += f"Output (first 20 lines):\n"
                                for line in output_lines[:20]:
                                    terminal_outputs[session_id] += f"  {line}\n"
                                terminal_outputs[session_id] += f"  ... ({len(output_lines)-20} more lines)\n"
                            else:
                                terminal_outputs[session_id] += f"Output:\n"
                                for line in output_lines:
                                    terminal_outputs[session_id] += f"  {line}\n"
                    except Exception as e:
                        terminal_outputs[session_id] += f"❌ Combined command failed: {str(e)}\n"
                    
                    terminal_outputs[session_id] += "\n" + "="*60 + "\n"
                    terminal_outputs[session_id] += "🎉 All commands execution completed!\n"
                    terminal_outputs[session_id] += "\n💡 You can now type additional commands or 'exit' to close.\n"
                    
                    # Keep session active for additional commands
                    # terminal_sessions[session_id]['active'] = True  # Already set above
                    
                except Exception as e:
                    terminal_outputs[session_id] += f"\n❌ Session Error: {str(e)}\n"
                    terminal_sessions[session_id]['active'] = False
            
            # Start the thread
            thread = threading.Thread(target=run_etx_commands_session, daemon=True)
            thread.start()
            terminal_sessions[session_id]['thread'] = thread
            
            return jsonify({'job_id': 'etx_commands_terminal', 'terminal_session': session_id})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
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

# Interactive Terminal Routes

@app.route('/terminal/start', methods=['POST'])
def start_terminal():
    """Start a new interactive terminal session"""
    session_id = str(uuid.uuid4())
    mode = request.json.get('mode', 'automated')  # 'automated', 'interactive', 'step_by_step'
    
    try:
        # Load configuration
        config = load_settings()
        
        # Create executor
        executor = ETXRemoteExecutor(config)
        
        # Configure mode
        if mode == 'interactive':
            executor.set_interactive_mode(True)
        
        # Initialize session
        terminal_sessions[session_id] = {
            'executor': executor,
            'input_queue': queue.Queue(),
            'output_queue': queue.Queue(),
            'active': True,
            'mode': mode,
            'thread': None
        }
        terminal_outputs[session_id] = ""
        
        # Start session thread
        def run_terminal_session():
            try:
                if mode == 'interactive':
                    # For interactive mode, we'll handle commands as they come
                    terminal_outputs[session_id] += f"🚀 Interactive Terminal Started - Session {session_id[:8]}\n"
                    terminal_outputs[session_id] += f"📋 Connected to: {config.get('REMOTE_HOST', 'Unknown')}\n"
                    terminal_outputs[session_id] += f"👤 User: {config.get('REMOTE_USER', 'Unknown')}\n"
                    terminal_outputs[session_id] += "="*60 + "\n"
                    terminal_outputs[session_id] += "Type commands below or choose from predefined commands:\n\n"
                    
                    # Show available predefined commands
                    commands = config.get('REMOTE_COMMANDS', [])
                    if commands:
                        terminal_outputs[session_id] += f"📝 Available predefined commands ({len(commands)}):\n"
                        for i, cmd in enumerate(commands[:5], 1):
                            if cmd.strip() and not cmd.startswith('#'):
                                terminal_outputs[session_id] += f"  {i}. {cmd}\n"
                        if len(commands) > 5:
                            terminal_outputs[session_id] += f"  ... and {len(commands)-5} more\n"
                        terminal_outputs[session_id] += "\n"
                    
                    terminal_outputs[session_id] += "Ready for commands!\n"
                    
                else:
                    # For automated mode, run all commands
                    terminal_outputs[session_id] += f"🤖 Automated Terminal Started - Session {session_id[:8]}\n"
                    terminal_outputs[session_id] += "="*60 + "\n"
                    success = executor.execute_commands()
                    
                    if success:
                        terminal_outputs[session_id] += "\n✅ All commands completed successfully!\n"
                    else:
                        terminal_outputs[session_id] += "\n❌ Some commands failed. Check logs for details.\n"
                    
                    terminal_sessions[session_id]['active'] = False
                    
            except Exception as e:
                terminal_outputs[session_id] += f"\n❌ Terminal Error: {str(e)}\n"
                terminal_sessions[session_id]['active'] = False
        
        # Start the thread
        thread = threading.Thread(target=run_terminal_session, daemon=True)
        thread.start()
        terminal_sessions[session_id]['thread'] = thread
        
        return jsonify({'session_id': session_id, 'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/terminal/send', methods=['POST'])
def send_terminal_command():
    """Send a command to an interactive terminal session"""
    session_id = request.json.get('session_id')
    command = request.json.get('command', '').strip()
    
    if session_id not in terminal_sessions:
        return jsonify({'error': 'Session not found', 'success': False}), 404
    
    session = terminal_sessions[session_id]
    
    if not session['active']:
        return jsonify({'error': 'Session is not active', 'success': False}), 400
    
    # Add command to output for display
    terminal_outputs[session_id] += f"$ {command}\n"
    
    # Handle special commands
    if command.lower() == 'exit':
        terminal_outputs[session_id] += "👋 Goodbye!\n"
        session['active'] = False
        return jsonify({'success': True})
    elif command.lower() == 'help':
        terminal_outputs[session_id] += """
🚀 Interactive Terminal Help:
  help       - Show this help
  exit       - Exit the terminal session
  clear      - Clear the terminal
  status     - Show session status
  list       - List predefined commands
  run <n>    - Run predefined command number <n>
  run all    - Run all predefined commands combined with && (1 && 2 && ... && end)
  
You can also type any shell command directly.
"""
        return jsonify({'success': True})
    elif command.lower() == 'clear':
        terminal_outputs[session_id] = f"🚀 Interactive Terminal - Session {session_id[:8]}\n"
        return jsonify({'success': True})
    elif command.lower() == 'status':
        terminal_outputs[session_id] += f"📊 Session Status: {'Active' if session['active'] else 'Inactive'}\n"
        terminal_outputs[session_id] += f"🔧 Mode: {session['mode']}\n"
        return jsonify({'success': True})
    elif command.lower() == 'list':
        config = load_settings()
        commands = [cmd for cmd in config.get('REMOTE_COMMANDS', []) if cmd.strip() and not cmd.startswith('#')]
        terminal_outputs[session_id] += f"📝 Predefined Commands ({len(commands)}):\n"
        for i, cmd in enumerate(commands, 1):
            terminal_outputs[session_id] += f"  {i}. {cmd}\n"
        terminal_outputs[session_id] += f"\nUse 'run <number>' to execute a command, or 'run all' to execute all {len(commands)} commands combined with &&.\n"
        return jsonify({'success': True})
    elif command.lower().startswith('run '):
        try:
            cmd_part = command.split(' ', 1)[1]
            config = load_settings()
            commands = [cmd for cmd in config.get('REMOTE_COMMANDS', []) if cmd.strip() and not cmd.startswith('#')]
            
            if cmd_part.lower() == 'all':
                # Combine all commands into one line with &&
                combined_command = " && ".join(commands)
                terminal_outputs[session_id] += f"🚀 Running all {len(commands)} commands as one combined command:\n"
                terminal_outputs[session_id] += "="*60 + "\n"
                terminal_outputs[session_id] += f"📝 Combined Command: {combined_command}\n"
                terminal_outputs[session_id] += f"⏳ Executing combined command...\n"
                
                try:
                    executor = session['executor']
                    result = executor.execute_single_command(combined_command)
                    terminal_outputs[session_id] += f"✅ All commands completed successfully\n"
                    if result and result.strip():
                        # Show the full output since it's a combined command
                        output_lines = result.strip().split('\n')
                        if len(output_lines) > 20:
                            terminal_outputs[session_id] += f"Output (first 20 lines):\n"
                            for line in output_lines[:20]:
                                terminal_outputs[session_id] += f"  {line}\n"
                            terminal_outputs[session_id] += f"  ... ({len(output_lines)-20} more lines)\n"
                        else:
                            terminal_outputs[session_id] += f"Output:\n"
                            for line in output_lines:
                                terminal_outputs[session_id] += f"  {line}\n"
                except Exception as e:
                    terminal_outputs[session_id] += f"❌ Combined command failed: {str(e)}\n"
                
                terminal_outputs[session_id] += "\n" + "="*60 + "\n"
                terminal_outputs[session_id] += "🎉 All commands execution completed!\n"
                
            else:
                cmd_num = int(cmd_part)
                if 1 <= cmd_num <= len(commands):
                    selected_cmd = commands[cmd_num - 1]
                    terminal_outputs[session_id] += f"🎯 Running command {cmd_num}: {selected_cmd}\n"
                    
                    # Execute the actual command
                    try:
                        executor = session['executor']
                        result = executor.execute_single_command(selected_cmd)
                        terminal_outputs[session_id] += f"✅ Command executed successfully\n"
                        if result:
                            terminal_outputs[session_id] += f"Output: {result}\n"
                    except Exception as e:
                        terminal_outputs[session_id] += f"❌ Command failed: {str(e)}\n"
                else:
                    terminal_outputs[session_id] += f"❌ Invalid command number: {cmd_num}\n"
        except ValueError:
            terminal_outputs[session_id] += f"❌ Invalid command format. Use 'run <number>' or 'run all'\n"
        return jsonify({'success': True})
    else:
        # Execute actual command via SSH
        try:
            executor = session['executor']
            terminal_outputs[session_id] += f"⏳ Executing: {command}\n"
            result = executor.execute_single_command(command)
            terminal_outputs[session_id] += f"✅ Command executed successfully\n"
            if result:
                terminal_outputs[session_id] += f"Output: {result}\n"
        except Exception as e:
            terminal_outputs[session_id] += f"❌ Command failed: {str(e)}\n"
        return jsonify({'success': True})

@app.route('/terminal/output/<session_id>')
def get_terminal_output(session_id):
    """Get terminal output for a session"""
    if session_id not in terminal_outputs:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'output': terminal_outputs[session_id],
        'active': terminal_sessions.get(session_id, {}).get('active', False)
    })

@app.route('/terminal/stop/<session_id>', methods=['POST'])
def stop_terminal(session_id):
    """Stop a terminal session"""
    if session_id in terminal_sessions:
        terminal_sessions[session_id]['active'] = False
        terminal_outputs[session_id] += "\n🔴 Terminal session stopped.\n"
        return jsonify({'success': True})
    return jsonify({'error': 'Session not found'}), 404

# Static files for frontend
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Flask template auto-reload
app.config['TEMPLATES_AUTO_RELOAD'] = True

if __name__ == '__main__':
    app.run(debug=True, port=5000) 