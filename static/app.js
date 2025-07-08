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



// Handle GPU/CPU toggle and hostname selection
function updateHostnameOptions(isGPU) {
    const hostnameSelect = document.getElementById('hostname-select');
    const resourceLabel = document.getElementById('resource-type-label');
    
    hostnameSelect.innerHTML = '';
    
    if (isGPU) {
        // GPU mode: login05-10
        for (let i = 5; i <= 10; i++) {
            const option = document.createElement('option');
            option.value = `login${i.toString().padStart(2, '0')}`;
            option.textContent = `login${i.toString().padStart(2, '0')}`;
            if (i === 10) option.selected = true; // Default to login10 for GPU
            hostnameSelect.appendChild(option);
        }
        resourceLabel.textContent = 'GPU Mode';
    } else {
        // CPU mode: login01-04
        for (let i = 1; i <= 4; i++) {
            const option = document.createElement('option');
            option.value = `login${i.toString().padStart(2, '0')}`;
            option.textContent = `login${i.toString().padStart(2, '0')}`;
            if (i === 4) option.selected = true; // Default to login04 for CPU
            hostnameSelect.appendChild(option);
        }
        resourceLabel.textContent = 'CPU Mode';
    }
}

function startJobWithHostname(jobType) {
    const selectedHostname = document.getElementById('hostname-select').value;
    const isGPU = document.getElementById('gpu-toggle').checked;
    
    showStatus('Starting job...', 'info');
    fetch('/run_job', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            job_type: jobType,
            hostname: selectedHostname,
            is_gpu: isGPU
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.job_id) {
            currentJobId = data.job_id;
            showStatus(`Job started: ${currentJobId} (${selectedHostname})`, 'success');
            pollLog();
        } else {
            showStatus('Failed to start job', 'danger');
        }
    });
}

window.onload = function() {
    loadSettingsForm();
    updateHistory();
    
    // Initialize hostname options
    updateHostnameOptions(false); // Default to CPU mode
    
    // Add event listener for GPU toggle
    document.getElementById('gpu-toggle').addEventListener('change', function() {
        updateHostnameOptions(this.checked);
    });
    
    // Update job button handlers to include hostname
    document.getElementById('run-github-to-local').onclick = () => startJob('github_to_local');
    document.getElementById('run-local-to-etx').onclick = () => startJob('local_to_etx');
    document.getElementById('run-etx-commands').onclick = () => startJobWithHostname('run_etx_commands');
    document.getElementById('delete-local-folders').onclick = () => startJob('delete_local_folders');
    document.getElementById('run-pipeline').onclick = () => startJobWithHostname('pipeline');
}; 