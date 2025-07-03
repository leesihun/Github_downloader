let currentJobId = null;
let logInterval = null;

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

document.getElementById('run-github-to-local').onclick = () => startJob('github_to_local');
document.getElementById('run-local-to-etx').onclick = () => startJob('local_to_etx');
document.getElementById('run-etx-commands').onclick = () => startJob('run_etx_commands');
document.getElementById('delete-local-folders').onclick = () => startJob('delete_local_folders');
document.getElementById('run-pipeline').onclick = () => startJob('pipeline');

document.getElementById('settings-form').onsubmit = function(e) {
    e.preventDefault();
    const text = document.getElementById('settings-text').value;
    fetch('/settings', {
        method: 'POST',
        body: new URLSearchParams({settings: text})
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            document.getElementById('settings-status').textContent = 'Saved!';
            setTimeout(() => document.getElementById('settings-status').textContent = '', 2000);
        }
    });
};

window.onload = function() {
    updateHistory();
}; 