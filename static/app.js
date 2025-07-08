let currentJobId = null;
let logInterval = null;
let settingsSaveTimeout = null;

function showStatus(msg, type='info') {
    const el = document.getElementById('job-status');
    el.innerHTML = `<span class='alert alert-${type} py-1 px-2 mb-0'>${msg}</span>`;
}

function startJob(jobType) {
    showStatus('Starting job...', 'info');
    fetch('/run_job', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({job_type: jobType})
    })
    .then(r => r.json())
    .then(data => {
        if (data.job_id) {
            currentJobId = data.job_id;
            showStatus('Job started: ' + currentJobId, 'success');
            pollLog();
        } else {
            showStatus('Failed to start job', 'danger');
        }
    });
}

function pollLog() {
    if (!currentJobId) return;
    clearInterval(logInterval);
    const logEl = document.getElementById('job-log');
    logEl.textContent = '';
    logInterval = setInterval(() => {
        fetch(`/job_log/${currentJobId}`)
            .then(r => r.json())
            .then(data => {
                logEl.textContent = data.log;
                logEl.scrollTop = logEl.scrollHeight;
            });
        fetch(`/job_status/${currentJobId}`)
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    showStatus('Job finished successfully!', 'success');
                    clearInterval(logInterval);
                    updateHistory();
                } else if (data.status === 'error') {
                    showStatus('Job failed!', 'danger');
                    clearInterval(logInterval);
                    updateHistory();
                }
            });
    }, 1500);
}

function updateHistory() {
    fetch('/job_history')
        .then(r => r.json())
        .then(data => {
            const tbody = document.querySelector('#history-table tbody');
            tbody.innerHTML = '';
            for (const job of data.history.reverse()) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${job.type}</td>
                    <td>${job.start}</td>
                    <td>${job.end}</td>
                    <td><span class="badge bg-${job.status === 'success' ? 'success' : (job.status === 'error' ? 'danger' : 'secondary')}">${job.status}</span></td>
                    <td><a href="/download_log/${job.id}" class="btn btn-sm btn-outline-secondary">Log</a></td>
                `;
                tbody.appendChild(tr);
            }
        });
}

function setJobButtonsEnabled(enabled) {
    document.getElementById('run-github-to-local').disabled = !enabled;
    document.getElementById('run-local-to-etx').disabled = !enabled;
    document.getElementById('run-etx-commands').disabled = !enabled;
    document.getElementById('delete-local-folders').disabled = !enabled;
    document.getElementById('run-pipeline').disabled = !enabled;
}

function loadSettingsForm() {
    fetch('/settings_json')
        .then(r => r.json())
        .then(settings => {
            for (const key in settings) {
                const el = document.getElementById(key);
                if (!el) continue;
                if (el.type === 'checkbox') {
                    el.checked = (settings[key] === true || settings[key] === 'true' || settings[key] === 1 || settings[key] === '1');
                } else if (el.tagName === 'TEXTAREA' && Array.isArray(settings[key])) {
                    el.value = settings[key].join('\n');
                } else {
                    el.value = settings[key];
                }
            }
        });
}

document.getElementById('settings-form').onsubmit = function(e) {
    e.preventDefault();
    const form = e.target;
    const data = {};
    for (const el of form.elements) {
        if (!el.name) continue;
        if (el.type === 'checkbox') {
            data[el.name] = el.checked;
        } else if (el.tagName === 'TEXTAREA') {
            // Split by newlines, filter empty lines
            data[el.name] = el.value.split(/\r?\n/).filter(x => x.length > 0);
        } else {
            data[el.name] = el.value;
        }
    }
    fetch('/settings_json', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            document.getElementById('settings-status').textContent = 'Saved!';
            setTimeout(() => {
                document.getElementById('settings-status').textContent = '';
            }, 1000);
        }
    });
};



// Simplified job execution without hostname selection

window.onload = function() {
    loadSettingsForm();
    updateHistory();
    
    // Set up job button handlers
    document.getElementById('run-github-to-local').onclick = () => startJob('github_to_local');
    document.getElementById('run-local-to-etx').onclick = () => startJob('local_to_etx');
    document.getElementById('run-etx-commands').onclick = () => startJob('run_etx_commands');
    document.getElementById('delete-local-folders').onclick = () => startJob('delete_local_folders');
    document.getElementById('run-pipeline').onclick = () => startJob('pipeline');
}; 