/**
 * URL Trust & Safety Analysis Platform
 * Frontend Application Logic
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000';

// State
let currentAnalysis = {
    url: null,
    technicalData: null,
    report: null,
    plan: null
};

// DOM Elements
const elements = {
    urlInput: document.getElementById('urlInput'),
    analyzeBtn: document.getElementById('analyzeBtn'),
    deepAnalysis: document.getElementById('deepAnalysis'),

    inputSection: document.getElementById('inputSection'),
    progressSection: document.getElementById('progressSection'),
    planSection: document.getElementById('planSection'),
    analysisSection: document.getElementById('analysisSection'),
    technicalSection: document.getElementById('technicalSection'),
    reportSection: document.getElementById('reportSection'),
    followupSection: document.getElementById('followupSection'),

    currentPhase: document.getElementById('currentPhase'),
    progressPercent: document.getElementById('progressPercent'),
    progressFill: document.getElementById('progressFill'),
    progressMessage: document.getElementById('progressMessage'),

    planContent: document.getElementById('planContent'),
    analysisContent: document.getElementById('analysisContent'),
    technicalContent: document.getElementById('technicalContent'),
    reportContent: document.getElementById('reportContent'),

    followupInput: document.getElementById('followupInput'),
    followupBtn: document.getElementById('followupBtn'),
    followupHistory: document.getElementById('followupHistory')
};

// Event Listeners
elements.analyzeBtn.addEventListener('click', startAnalysis);
elements.urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') startAnalysis();
});

elements.followupBtn.addEventListener('click', askFollowup);
elements.followupInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') askFollowup();
});

/**
 * Start URL Analysis
 */
async function startAnalysis() {
    const url = elements.urlInput.value.trim();

    if (!url) {
        alert('Please enter a URL to analyze');
        return;
    }

    // Validate URL format
    try {
        new URL(url);
    } catch (e) {
        alert('Please enter a valid URL (including http:// or https://)');
        return;
    }

    // Reset state
    currentAnalysis = {
        url: url,
        technicalData: null,
        report: null,
        plan: null
    };

    // Update UI
    elements.analyzeBtn.disabled = true;
    elements.analyzeBtn.classList.add('loading');
    elements.analyzeBtn.textContent = 'Analyzing...';

    // Show progress section
    elements.progressSection.classList.remove('hidden');
    elements.planSection.classList.add('hidden');
    elements.analysisSection.classList.add('hidden');
    elements.technicalSection.classList.add('hidden');
    elements.reportSection.classList.add('hidden');
    elements.followupSection.classList.add('hidden');

    // Clear previous content
    elements.analysisContent.textContent = '';
    elements.planContent.innerHTML = '';
    elements.technicalContent.innerHTML = '';
    elements.reportContent.innerHTML = '';

    // Start SSE connection
    const eventSource = new EventSource(
        `${API_BASE_URL}/api/analyze?url=${encodeURIComponent(url)}&deep_analysis=${elements.deepAnalysis.checked}`,
        { withCredentials: false }
    );

    // Handle SSE events
    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleAnalysisEvent(data);
        } catch (e) {
            console.error('Error parsing event:', e);
        }
    };

    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.classList.remove('loading');
        elements.analyzeBtn.textContent = 'Analyze URL';

        elements.progressMessage.textContent = 'Connection error. Please try again.';
    };

    // Handle completion
    eventSource.addEventListener('complete', () => {
        eventSource.close();
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.classList.remove('loading');
        elements.analyzeBtn.textContent = 'Analyze Another URL';
    });
}

/**
 * Handle different types of analysis events
 */
function handleAnalysisEvent(data) {
    switch (data.type) {
        case 'status':
            updateProgress(data.progress || 0, data.message);
            break;

        case 'phase':
            updatePhase(data.phase, data.progress || 0);
            break;

        case 'thinking':
            elements.progressMessage.textContent = data.message;
            break;

        case 'data':
            if (data.category === 'technical') {
                currentAnalysis.technicalData = data.data;
                displayTechnicalData(data.data);
                updateProgress(data.progress || 30);
            }
            break;

        case 'plan':
            currentAnalysis.plan = data.plan;
            displayInvestigationPlan(data.plan);
            updateProgress(data.progress || 40);
            break;

        case 'reasoning':
            displayReasoning(data.content);
            if (data.progress) {
                updateProgress(data.progress);
            }
            break;

        case 'progress':
            updateProgress(data.progress, data.message);
            break;

        case 'report':
            currentAnalysis.report = data.report;
            displayReport(data.report);
            updateProgress(100, 'Analysis complete!');
            elements.followupSection.classList.remove('hidden');
            break;

        case 'complete':
            console.log('Analysis completed');
            break;

        case 'error':
            showError(data.message);
            break;

        default:
            console.log('Unknown event type:', data.type);
    }
}

/**
 * Update progress bar and message
 */
function updateProgress(percent, message = null) {
    elements.progressPercent.textContent = `${percent}%`;
    elements.progressFill.style.width = `${percent}%`;

    if (message) {
        elements.progressMessage.textContent = message;
    }
}

/**
 * Update current phase
 */
function updatePhase(phase, progress) {
    elements.currentPhase.textContent = phase;
    updateProgress(progress);
}

/**
 * Display investigation plan
 */
function displayInvestigationPlan(plan) {
    elements.planSection.classList.remove('hidden');

    const ol = document.createElement('ol');
    plan.forEach(step => {
        const li = document.createElement('li');
        li.textContent = step;
        ol.appendChild(li);
    });

    elements.planContent.innerHTML = '';
    elements.planContent.appendChild(ol);
}

/**
 * Display AI reasoning in real-time
 */
function displayReasoning(content) {
    elements.analysisSection.classList.remove('hidden');
    elements.analysisContent.textContent += content;

    // Auto-scroll to bottom
    elements.analysisContent.scrollTop = elements.analysisContent.scrollHeight;
}

/**
 * Display technical analysis data
 */
function displayTechnicalData(data) {
    elements.technicalSection.classList.remove('hidden');
    elements.technicalContent.innerHTML = '';

    // URL Structure
    const urlStruct = data.url_structure || {};
    const urlStructItem = createTechItem(
        'URL Structure',
        [
            `Domain: ${urlStruct.fqdn || 'N/A'}`,
            `Scheme: ${urlStruct.scheme || 'N/A'}`,
            `URL Length: ${urlStruct.url_length || 0} characters`,
            `Suspicious Patterns: ${urlStruct.suspicious_patterns?.join(', ') || 'None'}`
        ]
    );
    elements.technicalContent.appendChild(urlStructItem);

    // SSL/TLS Info
    const sslInfo = data.ssl_info || {};
    const sslItem = createTechItem(
        'SSL/TLS Certificate',
        [
            `Valid SSL: ${sslInfo.has_ssl ? '✓ Yes' : '✗ No'}`,
            `Issuer: ${sslInfo.issuer?.organizationName || 'N/A'}`,
            `Valid Until: ${sslInfo.valid_until || 'N/A'}`
        ],
        sslInfo.has_ssl ? 'low' : 'high'
    );
    elements.technicalContent.appendChild(sslItem);

    // HTTP Response
    const httpResp = data.http_response || {};
    const httpItem = createTechItem(
        'HTTP Response',
        [
            `Status Code: ${httpResp.status_code || 'N/A'}`,
            `Redirects: ${httpResp.redirect_chain?.length || 0}`,
            `Content Type: ${httpResp.content_type || 'N/A'}`
        ]
    );
    elements.technicalContent.appendChild(httpItem);

    // Content Analysis
    const content = data.content_analysis || {};
    if (Object.keys(content).length > 0) {
        const contentItem = createTechItem(
            'Content Analysis',
            [
                `Page Title: ${content.title || 'N/A'}`,
                `Forms: ${content.forms_count || 0}`,
                `External Scripts: ${content.external_scripts_count || 0}`,
                `iFrames: ${content.iframes_count || 0}`
            ],
            content.iframes_count > 0 || content.forms_count > 2 ? 'medium' : 'low'
        );
        elements.technicalContent.appendChild(contentItem);
    }

    // Web Reputation
    const webRep = data.web_reputation || {};
    if (webRep.search_performed) {
        const repInfo = [
            `Reputation Score: ${webRep.reputation_score || 'N/A'}/100`,
            `Risk Level: ${webRep.risk_level || 'UNKNOWN'}`,
            `Scam Reports: ${webRep.scam_indicators?.length || 0}`,
            `User Complaints: ${webRep.user_complaints?.length || 0}`,
            `Search Backend: ${webRep.search_backend || 'Unknown'}`,
            `Results Analyzed: ${webRep.total_results_analyzed || 0}`
        ];

        // Determine risk level based on reputation
        let repRiskLevel = 'low';
        if (webRep.reputation_score < 30 || webRep.risk_level === 'CRITICAL' || webRep.risk_level === 'HIGH') {
            repRiskLevel = 'high';
        } else if (webRep.reputation_score < 50 || webRep.risk_level === 'MEDIUM') {
            repRiskLevel = 'medium';
        }

        const repItem = createTechItem(
            '🌐 Web Reputation Analysis',
            repInfo,
            repRiskLevel
        );
        elements.technicalContent.appendChild(repItem);

        // Show scam details if found
        if (webRep.scam_indicators && webRep.scam_indicators.length > 0) {
            const scamDetails = webRep.scam_indicators.slice(0, 3).map((scam, idx) =>
                `${idx + 1}. ${scam.title || 'Scam report'} [${scam.severity.toUpperCase()}]`
            );
            const scamItem = createTechItem(
                `⚠️ Scam Reports Found (${webRep.scam_indicators.length})`,
                scamDetails,
                'high'
            );
            elements.technicalContent.appendChild(scamItem);
        }
    } else if (webRep.error) {
        const repItem = createTechItem(
            '🌐 Web Reputation Analysis',
            [`Not available: ${webRep.error}`],
            null
        );
        elements.technicalContent.appendChild(repItem);
    }

    // Risk Indicators
    const indicators = data.risk_indicators || [];
    if (indicators.length > 0) {
        const riskList = indicators.map(ind =>
            `[${ind.type.toUpperCase()}] ${ind.indicator}`
        );
        const riskItem = createTechItem(
            `Risk Indicators (${indicators.length})`,
            riskList,
            indicators.some(i => i.type === 'high' || i.type === 'critical') ? 'high' : 'medium'
        );
        elements.technicalContent.appendChild(riskItem);
    }
}

/**
 * Create a technical item card
 */
function createTechItem(title, items, riskLevel = null) {
    const div = document.createElement('div');
    div.className = 'tech-item';

    const h4 = document.createElement('h4');
    h4.textContent = title;
    div.appendChild(h4);

    items.forEach(item => {
        const p = document.createElement('p');
        p.innerHTML = item;
        div.appendChild(p);
    });

    if (riskLevel) {
        const badge = document.createElement('span');
        badge.className = `risk-badge risk-${riskLevel}`;
        badge.textContent = riskLevel.toUpperCase();
        div.appendChild(badge);
    }

    return div;
}

/**
 * Display final report
 */
function displayReport(report) {
    elements.reportSection.classList.remove('hidden');
    elements.reportContent.innerHTML = '';

    // Verdict Banner
    const verdictBanner = document.createElement('div');
    verdictBanner.className = `verdict-banner verdict-${report.verdict.toLowerCase()}`;
    verdictBanner.innerHTML = `
        <div>VERDICT: ${report.verdict}</div>
        <div style="font-size: 1rem; margin-top: 0.5rem;">
            Risk Score: ${report.risk_score}/100 |
            Confidence: ${report.confidence}%
        </div>
    `;
    elements.reportContent.appendChild(verdictBanner);

    // Summary
    const summarySection = createReportSection('Executive Summary', report.summary);
    elements.reportContent.appendChild(summarySection);

    // Category
    const categorySection = createReportSection(
        'Category Classification',
        `Primary: ${report.primary_category || 'N/A'}<br>
         Secondary: ${report.secondary_categories?.join(', ') || 'N/A'}`
    );
    elements.reportContent.appendChild(categorySection);

    // Detailed Rationale
    const rationaleSection = createReportSection(
        'Detailed Rationale',
        report.detailed_rationale || 'No detailed rationale provided'
    );
    elements.reportContent.appendChild(rationaleSection);

    // Key Findings
    if (report.key_findings && report.key_findings.length > 0) {
        const findingsSection = document.createElement('div');
        findingsSection.className = 'report-section-item';

        const h4 = document.createElement('h4');
        h4.textContent = 'Key Findings';
        findingsSection.appendChild(h4);

        report.key_findings.forEach(finding => {
            const findingDiv = document.createElement('div');
            findingDiv.className = 'finding-item';
            findingDiv.innerHTML = `
                <strong>${finding.finding}</strong>
                <p><strong>Evidence:</strong> ${finding.evidence}</p>
                <p><strong>Severity:</strong> <span class="risk-badge risk-${finding.severity}">${finding.severity.toUpperCase()}</span></p>
                <p class="citation">Citation: ${finding.citation}</p>
            `;
            findingsSection.appendChild(findingDiv);
        });

        elements.reportContent.appendChild(findingsSection);
    }

    // Recommendations
    if (report.recommendations && report.recommendations.length > 0) {
        const recSection = createReportSection(
            'Recommendations',
            '<ul>' + report.recommendations.map(rec => `<li>${rec}</li>`).join('') + '</ul>'
        );
        elements.reportContent.appendChild(recSection);
    }

    // Threat Indicators
    if (report.threat_indicators && report.threat_indicators.length > 0) {
        const threatSection = createReportSection(
            'Threat Indicators',
            '<ul>' + report.threat_indicators.map(ti => `<li>${ti}</li>`).join('') + '</ul>'
        );
        elements.reportContent.appendChild(threatSection);
    }

    // Analyst Notes
    if (report.analyst_notes) {
        const notesSection = createReportSection('Analyst Notes', report.analyst_notes);
        elements.reportContent.appendChild(notesSection);
    }

    // Timestamp
    const timestamp = document.createElement('p');
    timestamp.style.cssText = 'color: var(--text-secondary); text-align: center; margin-top: 2rem; font-size: 0.9rem;';
    timestamp.textContent = `Analysis completed at: ${new Date(report.timestamp).toLocaleString()}`;
    elements.reportContent.appendChild(timestamp);
}

/**
 * Create a report section
 */
function createReportSection(title, content) {
    const section = document.createElement('div');
    section.className = 'report-section-item';

    const h4 = document.createElement('h4');
    h4.textContent = title;
    section.appendChild(h4);

    const p = document.createElement('div');
    p.innerHTML = content;
    p.style.lineHeight = '1.8';
    section.appendChild(p);

    return section;
}

/**
 * Ask follow-up question
 */
async function askFollowup() {
    const question = elements.followupInput.value.trim();

    if (!question) {
        alert('Please enter a question');
        return;
    }

    if (!currentAnalysis.url) {
        alert('Please analyze a URL first');
        return;
    }

    // Add question to history
    const questionDiv = document.createElement('div');
    questionDiv.className = 'followup-item';
    questionDiv.innerHTML = `
        <div class="followup-question">
            <strong>Q:</strong> ${question}
        </div>
        <div class="followup-answer" id="answer-${Date.now()}">
            <strong>A:</strong> <span class="loading-text">Thinking...</span>
        </div>
    `;
    elements.followupHistory.appendChild(questionDiv);

    const answerDiv = questionDiv.querySelector('.followup-answer');
    const answerContent = answerDiv.querySelector('.loading-text');

    // Clear input
    elements.followupInput.value = '';

    // Disable button
    elements.followupBtn.disabled = true;
    elements.followupBtn.classList.add('loading');

    // Make request
    try {
        const response = await fetch(`${API_BASE_URL}/api/followup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: currentAnalysis.url,
                question: question,
                previous_context: {
                    technical_data: currentAnalysis.technicalData,
                    report: currentAnalysis.report
                }
            })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        answerContent.textContent = '';
        answerContent.classList.remove('loading-text');

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const text = decoder.decode(value);
            const lines = text.split('\n\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'response') {
                            answerContent.textContent += data.content;
                        } else if (data.type === 'error') {
                            answerContent.textContent = `Error: ${data.message}`;
                        }
                    } catch (e) {
                        console.error('Parse error:', e);
                    }
                }
            }
        }

    } catch (error) {
        answerContent.textContent = `Error: ${error.message}`;
    } finally {
        elements.followupBtn.disabled = false;
        elements.followupBtn.classList.remove('loading');
    }

    // Scroll to bottom
    elements.followupHistory.scrollTop = elements.followupHistory.scrollHeight;
}

/**
 * Show error message
 */
function showError(message) {
    elements.progressMessage.textContent = `Error: ${message}`;
    elements.progressMessage.style.color = 'var(--danger-color)';

    setTimeout(() => {
        elements.progressMessage.style.color = '';
    }, 5000);
}

// Initialize
console.log('URL Safety Analysis Platform loaded');
console.log('API Base URL:', API_BASE_URL);
