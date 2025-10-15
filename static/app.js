// API Configuration
const API_BASE = 'http://localhost:8000';
let currentSessionId = '';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    mermaid.initialize({ startOnLoad: true, theme: 'dark' });
});

function initializeApp() {
    // Load saved session if exists
    const savedSession = localStorage.getItem('sessionId');
    if (savedSession) {
        currentSessionId = savedSession;
        updateSessionDisplay();
    }
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => switchFeature(item.dataset.feature));
    });

    // New Session
    document.getElementById('newSessionBtn').addEventListener('click', createNewSession);

    // Explain
    document.getElementById('explainBtn').addEventListener('click', handleExplain);
    document.getElementById('explainInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) handleExplain();
    });

    // Flashcards
    document.getElementById('flashcardBtn').addEventListener('click', handleFlashcards);

    // Quiz
    document.getElementById('quizBtn').addEventListener('click', handleQuiz);

    // Flowchart
    document.getElementById('flowchartBtn').addEventListener('click', handleFlowchart);

    // Debug
    document.getElementById('debugBtn').addEventListener('click', handleDebug);

    // PDF Upload
    document.getElementById('uploadBtn').addEventListener('click', () => {
        document.getElementById('pdfInput').click();
    });
    document.getElementById('pdfInput').addEventListener('change', handlePDFUpload);

    // Drag and drop
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--primary)';
    });
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = 'var(--border)';
    });
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--border)';
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            uploadPDF(file);
        }
    });
}

function switchFeature(feature) {
    // Update nav
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.nav-item').classList.add('active');

    // Update panels
    document.querySelectorAll('.feature-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    document.getElementById(`${feature}Panel`).classList.add('active');

    // Update title
    const titles = {
        explain: 'Explain Concepts',
        flashcards: 'Generate Flashcards',
        quiz: 'Create Quiz',
        flowchart: 'Visualize with Flowcharts',
        debug: 'Debug Code',
        pdf: 'Upload PDF Documents'
    };
    document.getElementById('featureTitle').textContent = titles[feature];
}

function showLoading() {
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function updateSessionDisplay() {
    const display = document.getElementById('sessionId');
    display.textContent = currentSessionId ? currentSessionId.substring(0, 8) + '...' : 'Not started';
}

function createNewSession() {
    currentSessionId = '';
    localStorage.removeItem('sessionId');
    updateSessionDisplay();
    
    // Clear all response areas
    document.querySelectorAll('.response-area').forEach(area => {
        area.innerHTML = '';
    });
    
    showNotification('New session started!', 'success');
}

async function handleExplain() {
    const input = document.getElementById('explainInput').value.trim();
    const level = document.getElementById('levelSelect').value;
    const responseArea = document.getElementById('explainResponse');

    if (!input) {
        showNotification('Please enter a question', 'error');
        return;
    }

    showLoading();
    
    try {
        const response = await fetch(`${API_BASE}/api/explain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: input,
                levels: level,
                session_id: currentSessionId
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            currentSessionId = data.session_id;
            localStorage.setItem('sessionId', currentSessionId);
            updateSessionDisplay();

            responseArea.innerHTML = `
                <div class="response-card markdown-content">
                    <h3>📚 Explanation</h3>
                    ${marked.parse(data.explanation)}
                </div>
                <div class="response-card markdown-content">
                    <h3>💡 Example</h3>
                    ${marked.parse(data.example)}
                </div>
                ${data.pdf_chunks ? `
                    <div class="response-card">
                        <h3>📄 PDF References (${data.pdf_chunks.length})</h3>
                        ${data.pdf_chunks.map(chunk => `
                            <div class="pdf-chunk">
                                <strong>Page ${chunk.page_number}</strong> (Score: ${chunk.relevance_score.toFixed(2)})
                                <p>${chunk.chunk_text.substring(0, 200)}...</p>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            `;
            
            document.getElementById('explainInput').value = '';
        } else {
            showNotification('Error: ' + data.detail, 'error');
        }
    } catch (error) {
        showNotification('Connection error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function handleFlashcards() {
    const topic = document.getElementById('flashcardTopic').value.trim();
    const count = parseInt(document.getElementById('flashcardCount').value);
    const responseArea = document.getElementById('flashcardResponse');

    if (!topic) {
        showNotification('Please enter a topic', 'error');
        return;
    }

    if (!currentSessionId) {
        showNotification('Please create a session first (use Explain)', 'error');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/api/flashcards`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: topic,
                count: count,
                session_id: currentSessionId
            })
        });

        const data = await response.json();

        if (response.ok) {
            responseArea.innerHTML = `
                <h3 style="margin-bottom: 20px; color: var(--primary);">
                    📇 ${data.flashcards.length} Flashcards (Click to flip)
                </h3>
                ${data.flashcards.map((card, index) => `
                    <div class="flashcard" onclick="this.classList.toggle('flipped')">
                        <div class="flashcard-front">
                            <h4>Question ${index + 1}</h4>
                            <p>${card.question}</p>
                            <small style="color: var(--text-muted);">Click to reveal answer</small>
                        </div>
                        <div class="flashcard-back">
                            <h4>Answer</h4>
                            <p>${card.answer}</p>
                            <small style="color: var(--text-muted);">Click to see question</small>
                        </div>
                    </div>
                `).join('')}
            `;
        } else {
            showNotification('Error: ' + data.detail, 'error');
        }
    } catch (error) {
        showNotification('Connection error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function handleQuiz() {
    const topic = document.getElementById('quizTopic').value.trim();
    const count = parseInt(document.getElementById('quizCount').value);
    const responseArea = document.getElementById('quizResponse');

    if (!topic) {
        showNotification('Please enter a topic', 'error');
        return;
    }

    if (!currentSessionId) {
        showNotification('Please create a session first (use Explain)', 'error');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/api/quiz`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: topic,
                count: count,
                session_id: currentSessionId
            })
        });

        const data = await response.json();

        if (response.ok) {
            responseArea.innerHTML = `
                <h3 style="margin-bottom: 20px; color: var(--primary);">
                    ✅ ${data.questions.length} Questions
                </h3>
                ${data.questions.map((q, index) => `
                    <div class="quiz-question">
                        <h4>${index + 1}. ${q.question}</h4>
                        <div class="quiz-options">
                            ${q.options.map((opt, i) => `
                                <div class="quiz-option" onclick="checkAnswer(this, ${i}, ${q.options.indexOf(q.correct_answer)})">
                                    ${String.fromCharCode(65 + i)}. ${opt}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            `;
        } else {
            showNotification('Error: ' + data.detail, 'error');
        }
    } catch (error) {
        showNotification('Connection error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function checkAnswer(element, selected, correct) {
    const options = element.parentElement.querySelectorAll('.quiz-option');
    options.forEach(opt => opt.style.pointerEvents = 'none');
    
    if (selected === correct) {
        element.classList.add('correct');
        showNotification('✅ Correct!', 'success');
    } else {
        element.classList.add('incorrect');
        options[correct].classList.add('correct');
        showNotification('❌ Incorrect. Check the correct answer.', 'error');
    }
}

async function handleFlowchart() {
    const concept = document.getElementById('flowchartTopic').value.trim();
    const responseArea = document.getElementById('flowchartResponse');

    if (!concept) {
        showNotification('Please enter a concept', 'error');
        return;
    }

    if (!currentSessionId) {
        showNotification('Please create a session first (use Explain)', 'error');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/api/flowchart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                concept: concept,
                session_id: currentSessionId
            })
        });

        const data = await response.json();

        if (response.ok) {
            responseArea.innerHTML = `
                <div class="response-card">
                    <h3>📊 ${data.concept}</h3>
                    <div class="mermaid">
                        ${data.mermaid_code}
                    </div>
                </div>
                <div class="response-card">
                    <h3>📝 Steps</h3>
                    <ol>
                        ${data.steps.map(step => `<li>${step}</li>`).join('')}
                    </ol>
                </div>
            `;
            
            // Re-initialize mermaid for the new diagram
            mermaid.init(undefined, document.querySelectorAll('.mermaid'));
        } else {
            showNotification('Error: ' + data.detail, 'error');
        }
    } catch (error) {
        showNotification('Connection error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function handleDebug() {
    const code = document.getElementById('debugCode').value.trim();
    const responseArea = document.getElementById('debugResponse');

    if (!code) {
        showNotification('Please enter code to debug', 'error');
        return;
    }

    showLoading();

    try {
        const response = await fetch(`${API_BASE}/api/debug-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: 'python',
                session_id: currentSessionId
            })
        });

        const data = await response.json();

        if (response.ok) {
            if (!currentSessionId) {
                currentSessionId = data.session_id;
                localStorage.setItem('sessionId', currentSessionId);
                updateSessionDisplay();
            }

            const exitCodeClass = data.exit_code === 0 ? 'exit-code-success' : 'exit-code-error';
            
            responseArea.innerHTML = `
                <div class="debug-metrics">
                    <div class="metric-card">
                        <div class="metric-label">Exit Code</div>
                        <div class="metric-value ${exitCodeClass}">
                            ${data.exit_code} ${data.exit_code === 0 ? '✓' : '✗'}
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Runtime</div>
                        <div class="metric-value">${data.runtime_duration}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Memory</div>
                        <div class="metric-value">${data.memory_usage}</div>
                    </div>
                </div>

                ${data.execution_output ? `
                    <div class="debug-section">
                        <h4>📝 Output</h4>
                        <pre><code>${escapeHtml(data.execution_output)}</code></pre>
                    </div>
                ` : ''}

                ${data.error_logs ? `
                    <div class="debug-section">
                        <h4>❌ Error: ${data.error_type}</h4>
                        <pre><code>${escapeHtml(data.error_logs)}</code></pre>
                    </div>
                ` : ''}

                ${data.stack_trace ? `
                    <div class="debug-section">
                        <h4>📋 Stack Trace</h4>
                        <pre><code>${escapeHtml(data.stack_trace)}</code></pre>
                    </div>
                ` : ''}

                ${data.syntax_errors.length > 0 ? `
                    <div class="debug-section">
                        <h4>⚠️ Syntax Errors</h4>
                        <ul>
                            ${data.syntax_errors.map(err => `<li>${err}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                <div class="debug-section markdown-content">
                    <h4>🤖 AI Analysis</h4>
                    ${marked.parse(data.ai_analysis)}
                </div>

                ${data.suggestions.length > 0 ? `
                    <div class="debug-section">
                        <h4>💡 Suggestions</h4>
                        <ul>
                            ${data.suggestions.map(sug => `<li>${sug}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            `;
        } else {
            showNotification('Error: ' + (data.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        showNotification('Connection error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function handlePDFUpload() {
    const file = document.getElementById('pdfInput').files[0];
    if (file) {
        uploadPDF(file);
    }
}

async function uploadPDF(file) {
    if (!currentSessionId) {
        showNotification('Please create a session first (use Explain)', 'error');
        return;
    }

    const progressArea = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const responseArea = document.getElementById('pdfResponse');

    progressArea.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = 'Uploading...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                progressFill.style.width = percent + '%';
                progressText.textContent = `Uploading... ${Math.round(percent)}%`;
            }
        });

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                progressText.textContent = 'Upload complete! ✓';
                
                responseArea.innerHTML = `
                    <div class="response-card">
                        <h3>✅ PDF Uploaded Successfully</h3>
                        <p><strong>Filename:</strong> ${data.filename}</p>
                        <p><strong>Pages:</strong> ${data.pages}</p>
                        <p><strong>Chunks:</strong> ${data.chunks}</p>
                        <p><strong>Session:</strong> ${data.session_id}</p>
                        <p style="margin-top: 16px; color: var(--text-secondary);">
                            You can now ask questions about this PDF using the Explain feature!
                        </p>
                    </div>
                `;
                
                showNotification('PDF uploaded successfully!', 'success');
            } else {
                const error = JSON.parse(xhr.responseText);
                showNotification('Upload failed: ' + error.detail, 'error');
            }
            
            setTimeout(() => {
                progressArea.style.display = 'none';
            }, 2000);
        });

        xhr.addEventListener('error', () => {
            showNotification('Upload failed', 'error');
            progressArea.style.display = 'none';
        });

        xhr.open('POST', `${API_BASE}/api/session/${currentSessionId}/upload-pdf`);
        xhr.send(formData);

    } catch (error) {
        showNotification('Upload error: ' + error.message, 'error');
        progressArea.style.display = 'none';
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--primary)'};
        color: white;
        border-radius: 8px;
        box-shadow: var(--shadow);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
