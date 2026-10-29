import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const HISTORY_KEY = 'spam-email-detection.scan-history'
const DRIFT_SUMMARY_KEY = 'spam-email-detection.drift-summary'
const SUBJECT_LIMIT = 200
const BODY_LIMIT = 19_800

function normalizePrediction(prediction) {
  const confidence = Number(prediction?.confidence)
  const label = typeof prediction?.label === 'string' ? prediction.label.toLowerCase() : ''
  if (!['spam', 'ham', 'uncertain'].includes(label) || !Number.isFinite(confidence) || confidence < 0 || confidence > 1) return null
  return { ...prediction, label, confidence }
}

function readHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]') } catch { return [] }
}

function saveHistory(record) {
  const next = [record, ...readHistory().filter(item => item.id !== record.id)].slice(0, 100)
  localStorage.setItem(HISTORY_KEY, JSON.stringify(next))
  return next
}

function readDriftSummary() {
  try {
    const summary = JSON.parse(localStorage.getItem(DRIFT_SUMMARY_KEY) || 'null')
    return summary && typeof summary === 'object' ? summary : null
  } catch { return null }
}

function saveDriftSummary(summary) {
  const savedSummary = { ...summary, saved_at: new Date().toISOString() }
  localStorage.setItem(DRIFT_SUMMARY_KEY, JSON.stringify(savedSummary))
  return savedSummary
}

function navigate(path) { window.location.hash = path }

function App() {
  const [route, setRoute] = useState(window.location.hash.slice(1) || '/dashboard')
  const [history, setHistory] = useState(readHistory)
  const [service, setService] = useState({ status: 'checking', modelLoaded: false })

  useEffect(() => {
    const onHashChange = () => setRoute(window.location.hash.slice(1) || '/dashboard')
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 5_000)
    fetch(`${API_URL}/health`, { signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error('Health check failed')
      return response.json()
    }).then(health => setService({ status: health.status === 'ok' ? 'online' : 'offline', modelLoaded: health.model_loaded === true }))
      .catch(() => setService({ status: 'offline', modelLoaded: false }))
      .finally(() => clearTimeout(timeout))
    return () => { clearTimeout(timeout); controller.abort() }
  }, [])

  function onScan(record) {
    const next = saveHistory(record)
    setHistory(next)
  }

  const page = route === '/new-check' ? 'New Check' : route === '/history' ? 'History' : route === '/monitoring' ? 'Monitoring' : route === '/project-info' ? 'Project Info' : 'Dashboard'
  return <div className="app-shell">
    <Sidebar route={route} service={service} />
    <div className="app-main"><Topbar page={page} service={service} />
      <main className="dashboard-content">
        {route === '/new-check' ? <NewCheck service={service} onScan={onScan} /> : route === '/history' ? <HistoryPage history={history} /> : route === '/monitoring' ? <MonitoringPage /> : route === '/project-info' ? <ProjectInfo service={service} /> : <Dashboard history={history} service={service} />}
      </main>
    </div>
  </div>
}

function Sidebar({ route, service }) {
  const [open, setOpen] = useState(false)
  const items = [['/dashboard', '⌂', 'Dashboard'], ['/new-check', '+', 'New Check'], ['/history', '◷', 'History'], ['/monitoring', '△', 'Monitoring'], ['/project-info', 'i', 'Project Info']]
  return <aside className={`sidebar ${open ? 'is-open' : ''}`}>
    <button className="mobile-menu" onClick={() => setOpen(!open)} aria-label="Toggle navigation">☰</button>
    <div className="brand"><span className="brand-mark">✦</span><span>Spam Email<br /><b>Detection</b></span></div>
    <nav aria-label="Primary navigation">{items.map(([path, icon, label]) => <a className={route === path ? 'active' : ''} href={`#${path}`} key={path} onClick={() => setOpen(false)}><span className="nav-icon">{icon}</span>{label}</a>)}</nav>
    <div className="sidebar-footer"><span className={`service-dot ${service.status}`} /> {service.status === 'online' ? (service.modelLoaded ? 'Model connected' : 'Demo mode') : service.status === 'checking' ? 'Checking service' : 'Offline'}</div>
  </aside>
}

function Topbar({ page, service }) {
  const status = service.status === 'online' ? (service.modelLoaded ? 'Service online' : 'API online · Demo mode') : service.status === 'checking' ? 'Checking service' : 'Service offline'
  return <header className="topbar"><div><p className="breadcrumb">Workspace / {page}</p><h1>{page}</h1></div><div className={`top-status ${service.status}`}><span className="service-dot" />{status}</div></header>
}

function Dashboard({ history, service }) {
  const today = new Date().toLocaleDateString()
  const scansToday = history.filter(item => new Date(item.timestamp).toLocaleDateString() === today).length
  const spamCount = history.filter(item => item.label === 'spam').length
  return <div className="page-stack"><div className="page-intro"><div><p className="kicker">Overview</p><h2>Good morning, welcome back.</h2><p>Review your email security activity and start a new analysis.</p></div><button className="primary-button" onClick={() => navigate('/new-check')}>Start new check <span>→</span></button></div>
    <div className="stat-grid"><StatCard icon="◎" label="Total scans" value={history.length} detail="Successful predictions" /><StatCard icon="◷" label="Today's scans" value={scansToday} detail="Based on local date" /><StatCard icon="⚠" label="Spam detected" value={spamCount} detail="Across saved scans" /></div>
    <section className="welcome-panel"><div><p className="kicker">Spam Email Detection</p><h2>Analyze suspicious emails with confidence.</h2><p>Use the DistilBERT classification service to review a message, understand its returned signals, and choose a safer next step.</p><div className="info-badges"><span>DistilBERT classification</span><span>FastAPI prediction service</span><span>{service.modelLoaded ? 'Model connected' : 'Demo mode'}</span></div></div><span className="welcome-mark">✦</span></section>
    <section className="activity-section"><div className="section-header"><div><p className="kicker">Recent activity</p><h2>Latest email scans</h2></div><button className="link-button" onClick={() => navigate('/history')}>View all history →</button></div><ActivityList history={history.slice(0, 5)} /></section>
  </div>
}

function StatCard({ icon, label, value, detail }) { return <article className="stat-card"><span className="stat-icon">{icon}</span><div><p>{label}</p><strong>{value}</strong><small>{detail}</small></div></article> }

function ActivityList({ history }) {
  if (!history.length) return <div className="empty-list"><span>◷</span><h3>No email scans yet</h3><p>Start your first email check to see activity here.</p><button className="secondary-button" onClick={() => navigate('/new-check')}>Analyze an email</button></div>
  return <div className="activity-list">{history.map(item => <button className="activity-row" key={item.id} onClick={() => navigate('/history')}><span className={`activity-icon ${item.label}`}>{item.label === 'spam' ? '!' : '✓'}</span><span className="activity-copy"><b>{item.subject || 'No subject'}</b><small>{new Date(item.timestamp).toLocaleString()}</small></span><span className={`label-pill ${item.label}`}>{item.label === 'spam' ? 'Spam' : 'Legitimate'}</span><span className="row-score">{Math.round(item.confidence * 100)}%</span><span className="chevron">›</span></button>)}</div>
}

function NewCheck({ service, onScan }) {
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const combinedText = subject.trim() ? `Subject: ${subject.trim()}\n\n${body}` : body
  const isValid = body.trim().length > 0 && combinedText.length <= 20_000
  const samples = { legitimate: { subject: 'Project review meeting - Thursday at 10:00 AM', body: 'Hello Maya,\n\nCould we meet on Thursday at 10:00 AM to review the latest project progress? Please let me know if that time works for you.\n\nBest regards,\nAlex' }, spam: { subject: 'Urgent: Claim your exclusive reward now', body: 'Congratulations! You have been selected for a limited-time reward. Click the link below and verify your details immediately to claim your free prize. Act now before this offer expires.' } }
  const update = setter => event => { setter(event.target.value); setResult(null); setError('') }
  function clearForm() { setSubject(''); setBody(''); setResult(null); setError(''); setNotice('') }
  async function pasteEmail() { setError(''); setNotice(''); if (!navigator.clipboard?.readText) return setError('Clipboard unavailable. Paste manually with Ctrl+V.'); try { const value = await navigator.clipboard.readText(); if (!value) return setNotice('The clipboard is empty. Copy an email first.'); setBody(value); setResult(null); setNotice('Email pasted into the message body.') } catch { setError('Clipboard permission was denied. Paste manually with Ctrl+V.') } }
  function loadSample(type) { setSubject(samples[type].subject); setBody(samples[type].body); setResult(null); setNotice(`${type === 'spam' ? 'Spam' : 'Legitimate'} demonstration loaded. Review it before analyzing.`) }
  async function classify(event) {
    event.preventDefault(); setError(''); setNotice('')
    if (!body.trim()) return setError('Enter an email body before analyzing. A subject is optional.')
    if (combinedText.length > 20_000) return setError('This email is too long for the analysis service.')
    setLoading(true); setResult(null)
    try {
      const controller = new AbortController(); const timeout = setTimeout(() => controller.abort(), 15_000)
      const response = await fetch(`${API_URL}/predict`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ text: combinedText }), signal: controller.signal }); clearTimeout(timeout)
      if (!response.ok) throw new Error('The prediction service could not analyze this email. Please try again.')
      const prediction = normalizePrediction(await response.json()); if (!prediction) throw new Error('The prediction service returned an invalid result.')
      setResult(prediction)
      onScan({ id: `${Date.now()}-${Math.random().toString(36).slice(2)}`, subject: subject.trim(), label: prediction.label, confidence: prediction.confidence, modelVersion: prediction.model_version, verdict: prediction.verdict, riskLevel: prediction.risk_level, summary: prediction.summary, topSignals: prediction.top_signals, recommendedActions: prediction.recommended_actions, timestamp: new Date().toISOString() })
    } catch (requestError) { setError(requestError.name === 'AbortError' ? 'The analysis took too long. Please try again.' : requestError.message || 'The prediction service could not be reached.') } finally { setLoading(false) }
  }
  return <div className="page-stack"><div className="page-intro compact"><div><p className="kicker">Email analysis</p><h2>New Email Check</h2><p>Enter an email subject and body to analyze its spam classification.</p></div></div><section className="scanner-grid"><form className="input-card" onSubmit={classify} noValidate><div className="card-heading"><div><p className="section-kicker">Analyze message</p><h2>Email content</h2></div><span className="card-index">01</span></div><p className="form-label">EMAIL TO ANALYZE</p><div className="field-group"><label htmlFor="subject">Subject <span>(optional)</span></label><input id="subject" value={subject} onChange={update(setSubject)} maxLength={SUBJECT_LIMIT} placeholder="e.g. Project review meeting" /><span className="counter">{subject.length} / {SUBJECT_LIMIT}</span></div><div className="field-group body-group"><label htmlFor="email-body">Email body</label><textarea id="email-body" value={body} onChange={update(setBody)} maxLength={BODY_LIMIT} placeholder="Paste or type the full email message here..." /><div className="field-meta"><span>Include the sender's message for better context.</span><span className="counter">{body.length.toLocaleString()} / {BODY_LIMIT}</span></div></div><div className="tool-row"><button className="secondary-button" type="button" onClick={pasteEmail}>Paste email</button><label className="sample-select-label" htmlFor="sample-email">Sample email<select id="sample-email" value="" onChange={event => event.target.value && loadSample(event.target.value)}><option value="">Choose a demo</option><option value="legitimate">Legitimate example</option><option value="spam">Spam example</option></select></label><button className="text-button" type="button" onClick={clearForm} disabled={!subject && !body && !error && !result}>Clear</button></div>{error && <p className="form-message error" role="alert">{error}</p>}{notice && <p className="form-message notice" role="status">{notice}</p>}<div className="form-footer"><span className="field-hint">{isValid ? 'Ready for analysis' : 'A non-empty email body is required'}</span><button className="analyze-button" type="submit" disabled={loading || !isValid}>{loading ? <><span className="spinner" /> Analyzing email...</> : <>Analyze email <span>→</span></>}</button></div></form><ResultCard result={result} service={service} /></section></div>
}

function ResultCard({ result, service }) {
  if (!result) return <aside className="result-card empty"><div className="empty-icon">✦</div><h2>Your analysis will appear here</h2><p>Enter an email and click Analyze email to review the returned classification.</p></aside>
  const demo = result.model_version === 'demo-fallback'
  const title = result.verdict || (result.label === 'spam' ? 'Spam detected' : result.label === 'ham' ? 'Likely legitimate' : 'Uncertain - review manually')
  return <aside className={`result-card ${result.label}`} aria-live="polite"><div className="card-heading"><div><p className="section-kicker">Classification result</p><h2>Verdict</h2></div><span className="card-index">02</span></div><div className="verdict-head"><p className="eyebrow">VERDICT</p><span className="risk-badge">{result.label === 'spam' ? '⚠ HIGH RISK' : result.label === 'ham' ? '✓ LOW RISK' : '! REVIEW'}</span></div><div className="verdict-row"><div><strong className="verdict-title">{title}</strong><p className="summary">{result.summary || 'The service returned a classification without an additional explanation.'}</p></div><div className="confidence-box"><span>MODEL SCORE</span><b>{Math.round(result.confidence * 100)}%</b><small>returned confidence</small></div></div><div className="meter"><i style={{ width: `${result.confidence * 100}%` }} /></div><p className="score-note">This is the confidence returned for the predicted class. The API does not provide separate class probabilities.</p><details className="analysis-details"><summary>How to interpret this result</summary><p>Signals are supplementary backend analysis, not a complete explanation of every DistilBERT decision.</p></details><div className="detail-grid"><section className="signals-panel"><p className="detail-title">TOP SIGNALS</p>{Array.isArray(result.top_signals) && result.top_signals.length ? <ul>{result.top_signals.map(item => <li key={item}>{item}</li>)}</ul> : <p className="detail-empty">Additional explanation is unavailable.</p>}</section><section className="actions-panel"><p className="detail-title">RECOMMENDED ACTIONS</p>{Array.isArray(result.recommended_actions) && result.recommended_actions.length ? <ul>{result.recommended_actions.map(item => <li key={item}>{item}</li>)}</ul> : <p className="detail-empty">Review the sender and context before acting.</p>}</section></div><small className="model-note">Model: {result.model_version || 'reported by API'} {demo && '· DEMO MODE'}</small></aside>
}

function HistoryPage({ history }) {
  const [filter, setFilter] = useState('all'); const [search, setSearch] = useState('')
  const records = history.filter(item => (filter === 'all' || item.label === filter) && (item.subject || 'No subject').toLowerCase().includes(search.toLowerCase()))
  return <div className="page-stack"><div className="page-intro compact"><div><p className="kicker">Review center</p><h2>Scan History</h2><p>View emails previously analyzed by the Spam Email Detection system.</p></div></div><section className="history-card"><div className="history-toolbar"><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Search by subject" aria-label="Search history" /><div className="filter-group">{[['all','All'],['spam','Spam'],['ham','Legitimate']].map(([key,label]) => <button className={filter === key ? 'selected' : ''} onClick={() => setFilter(key)} key={key}>{label}</button>)}</div></div><p className="matching-count">{records.length} matching {records.length === 1 ? 'scan' : 'scans'} · Browser-local history</p>{records.length ? <div className="history-table"><div className="history-table-head"><span>Subject</span><span>Classification</span><span>Model score</span><span>Scanned</span></div>{records.map(item => <div className="history-row" key={item.id}><span><b>{item.subject || 'No subject'}</b><small>{item.modelVersion || 'Model version unavailable'}</small></span><span className={`label-pill ${item.label}`}>{item.label === 'spam' ? 'Spam' : 'Legitimate'}</span><span>{Math.round(item.confidence * 100)}%</span><span>{new Date(item.timestamp).toLocaleString()}</span></div>)}</div> : <div className="empty-list"><span>◷</span><h3>No matching scans</h3><p>Your successful predictions will appear here.</p></div>}</section></div>
}

function MonitoringPage() {
  const [summary, setSummary] = useState(readDriftSummary)
  const [error, setError] = useState('')
  useEffect(() => {
    const savedSummary = readDriftSummary()
    fetch(`${API_URL}/monitoring/summary`).then(response => {
      if (!response.ok) throw new Error('No monitoring report has been generated yet.')
      return response.json()
    }).then(report => {
      setSummary(saveDriftSummary(report))
      setError('')
    }).catch(requestError => {
      if (!savedSummary) setError(requestError.message)
    })
  }, [])
  return <div className="page-stack"><div className="page-intro compact"><div><p className="kicker">Model operations</p><h2>Data Drift Monitoring</h2><p>Review changes between the reference email dataset and the latest current dataset.</p></div>{summary && <a className="primary-button report-link" href={`${API_URL}/monitoring/report`} target="_blank" rel="noreferrer">Open HTML report <span>↗</span></a>}</div>{error && <section className="monitoring-empty"><span>△</span><h3>Monitoring report unavailable</h3><p>{error} Run the monitoring command before opening this page.</p></section>}{summary && <><div className="monitoring-grid"><StatCard icon="△" label="Drift status" value={summary.drift_detected ? 'Detected' : 'Stable'} detail={summary.report_engine} /><StatCard icon="↔" label="Text length shift" value={`${(Number(summary.text_length_shift || 0) * 100).toFixed(1)}%`} detail="Reference vs current" /><StatCard icon="◎" label="Rows compared" value={`${summary.reference_rows} / ${summary.current_rows}`} detail="Reference / current" /></div><section className={`monitoring-banner ${summary.drift_detected ? 'drift' : 'stable'}`}><div><p className="kicker">Monitoring decision</p><h3>{summary.drift_detected ? 'Dataset drift detected' : 'No material drift detected'}</h3><p>{summary.drift_detected ? 'The current email data differs from the reference profile. Review the report before retraining.' : 'The current email data is within the configured text-length drift threshold.'}</p></div><span className="monitoring-status">{summary.evidently_report_generated ? 'Evidently AI report' : 'Lightweight check'}</span></section><section className="info-card monitoring-details"><h3>Report details</h3><p>Reference rows: <b>{summary.reference_rows}</b> · Current rows: <b>{summary.current_rows}</b> · Engine: <b>{summary.report_engine}</b></p>{summary.report_note && <p className="info-note">{summary.report_note}</p>}</section></>}</div>
}

function ProjectInfo({ service }) {
  const tech = [['DistilBERT / NLP','Email classification','Implemented'],['FastAPI','Prediction API','Connected'],['MLflow','Experiment tracking','Configured'],['DVC','Dataset and pipeline versioning','Configured'],['GitHub Actions','CI/CD workflows','Configured'],['Docker','Containerization','Configured'],['Evidently AI','Monitoring and drift reports','Configured']]
  return <div className="page-stack"><div className="page-intro compact"><div><p className="kicker">Academic project</p><h2>Spam Email Detection</h2><p>An NLP-based spam email classification system using DistilBERT to classify emails as Spam or Legitimate.</p></div></div><section className="info-card"><h3>Project objective</h3><p>Provide a practical email screening workflow with a FastAPI serving layer and an MLOps foundation for model tracking, dataset versioning, monitoring, and lifecycle automation.</p><h3>Current implementation</h3><div className="architecture"><span>EMAIL INPUT</span><b>→</b><span>FASTAPI</span><b>→</b><span>DISTILBERT</span><b>→</b><span>VERDICT</span></div></section><section className="tech-grid">{tech.map(([name, description, status]) => <article className="tech-card" key={name}><div><h3>{name}</h3><p>{description}</p></div><span className={`status-tag ${status.toLowerCase()}`}>{status}</span></article>)}</section><p className="info-note">Service status: {service.status === 'online' ? (service.modelLoaded ? 'API and trained model connected.' : 'API connected; demo fallback is active because no trained artifact is loaded.') : 'The API is currently unavailable.'}</p></div>
}

createRoot(document.getElementById('root')).render(<App />)
