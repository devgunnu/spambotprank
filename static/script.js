// Dashboard JavaScript functionality
let refreshInterval;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    setupEventListeners();
    startAutoRefresh();
});

function setupEventListeners() {
    // Modal close functionality
    const modal = document.getElementById('callModal');
    const closeBtn = document.querySelector('.close');
    
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    }
    
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    }
}

async function loadDashboard() {
    try {
        await Promise.all([
            loadAnalytics(),
            loadRecentCalls(),
            checkSystemStatus()
        ]);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showError('Failed to load dashboard data');
    }
}

async function loadAnalytics() {
    try {
        const response = await fetch('/api/analytics/summary');
        const data = await response.json();
        
        document.getElementById('totalCalls').textContent = data.total_calls_today;
        document.getElementById('avgDuration').textContent = data.avg_duration_today;
        document.getElementById('timeWasted').textContent = data.total_time_wasted;
        document.getElementById('bestPersona').textContent = data.most_effective_persona;
    } catch (error) {
        console.error('Error loading analytics:', error);
        document.getElementById('totalCalls').textContent = 'Error';
        document.getElementById('avgDuration').textContent = 'Error';
        document.getElementById('timeWasted').textContent = 'Error';
        document.getElementById('bestPersona').textContent = 'Error';
    }
}

async function loadRecentCalls() {
    try {
        const response = await fetch('/api/calls');
        const calls = await response.json();
        
        const tbody = document.getElementById('callsTableBody');
        tbody.innerHTML = '';
        
        if (calls.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6">No calls yet</td></tr>';
            return;
        }
        
        calls.forEach(call => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${formatTime(call.start_time)}</td>
                <td>${formatPhoneNumber(call.caller_number)}</td>
                <td>${formatDuration(call.duration)}</td>
                <td>${formatPersona(call.persona_used)}</td>
                <td><span class="status-badge ${call.status}">${call.status}</span></td>
                <td>
                    <button class="btn" onclick="viewCallDetails(${call.id})">View</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading recent calls:', error);
        document.getElementById('callsTableBody').innerHTML = 
            '<tr><td colspan="6">Error loading calls</td></tr>';
    }
}

async function checkSystemStatus() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        const statusIndicator = document.getElementById('systemStatus');
        const statusText = document.getElementById('statusText');
        const lastUpdate = document.getElementById('lastUpdate');
        
        if (data.status === 'healthy') {
            statusIndicator.classList.remove('offline');
            statusText.textContent = 'Online';
            statusText.style.color = '#28a745';
        } else {
            statusIndicator.classList.add('offline');
            statusText.textContent = 'Offline';
            statusText.style.color = '#dc3545';
        }
        
        lastUpdate.textContent = new Date().toLocaleTimeString();
    } catch (error) {
        console.error('Error checking system status:', error);
        const statusIndicator = document.getElementById('systemStatus');
        const statusText = document.getElementById('statusText');
        
        statusIndicator.classList.add('offline');
        statusText.textContent = 'Offline';
        statusText.style.color = '#dc3545';
    }
}

async function viewCallDetails(callId) {
    try {
        const response = await fetch(`/api/calls/${callId}`);
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        const modal = document.getElementById('callModal');
        const detailsDiv = document.getElementById('callDetails');
        
        // Build call details HTML
        let html = `
            <div class="call-info">
                <h3>Call Information</h3>
                <p><strong>Caller:</strong> ${formatPhoneNumber(data.call.caller_number)}</p>
                <p><strong>Start Time:</strong> ${formatDateTime(data.call.start_time)}</p>
                <p><strong>End Time:</strong> ${formatDateTime(data.call.end_time)}</p>
                <p><strong>Duration:</strong> ${formatDuration(data.call.duration)}</p>
                <p><strong>Persona:</strong> ${formatPersona(data.call.persona_used)}</p>
                <p><strong>Status:</strong> ${data.call.status}</p>
            </div>
        `;
        
        if (data.conversation && data.conversation.length > 0) {
            html += '<div class="conversation-section"><h3>Conversation</h3>';
            data.conversation.forEach(msg => {
                html += `
                    <div class="conversation-item ${msg.speaker}">
                        <div class="conversation-meta">
                            ${msg.speaker.toUpperCase()} - ${formatDateTime(msg.timestamp)}
                            ${msg.confidence_score ? ` (${Math.round(msg.confidence_score * 100)}% confidence)` : ''}
                        </div>
                        <div class="conversation-message">${msg.message}</div>
                    </div>
                `;
            });
            html += '</div>';
        }
        
        detailsDiv.innerHTML = html;
        modal.style.display = 'block';
    } catch (error) {
        console.error('Error loading call details:', error);
        showError('Failed to load call details');
    }
}

function startAutoRefresh() {
    // Refresh every 30 seconds
    refreshInterval = setInterval(loadDashboard, 30000);
}

function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

// Utility functions
function formatTime(timestamp) {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleTimeString();
}

function formatDateTime(timestamp) {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleString();
}

function formatDuration(duration) {
    if (!duration) return '-';
    const minutes = Math.floor(duration / 60);
    const seconds = Math.floor(duration % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function formatPhoneNumber(phone) {
    if (!phone) return '-';
    // Basic phone number formatting
    return phone.replace(/(\d{1})(\d{3})(\d{3})(\d{4})/, '+$1 ($2) $3-$4');
}

function formatPersona(persona) {
    if (!persona) return '-';
    return persona.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function showError(message) {
    // Simple error display - could be enhanced with a toast notification
    console.error(message);
    alert(message);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});
