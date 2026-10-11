import { useMemo, useState } from 'react';
import { Activity, AlertCircle, ArrowUpRight, BadgeCheck, Check, ChevronDown, ChevronUp, CircleHelp, Clipboard, ExternalLink, FileSearch, Globe2, LockKeyhole, RotateCcw, Search, ShieldAlert, ShieldCheck, X } from 'lucide-react';

const emptyForm = { company_name: '', message_text: '', recruiter_name: '', recruiter_email: '', application_url: '', job_listing_url: '' };
const labels = { supported: 'Some support found', conflicting: 'Conflicting evidence', needs_verification: 'Needs verification', risk_signal: 'Risk signal' };
const readable = (value = '') => String(value).replaceAll('_', ' ');
const toneFor = (status = '') => status === 'elevated_risk_signals' || status === 'conflicting_evidence' ? 'risk' : status === 'some_claims_supported' ? 'supported' : status === 'investigation_incomplete' ? 'incomplete' : 'review';
function Field({ label, name, value, onChange, placeholder, type = 'text', required = false, maxLength }) { return <div className="field"><label htmlFor={name}>{label}{required && <span className="required"> *</span>}</label><input id={name} name={name} type={type} value={value} onChange={onChange} placeholder={placeholder} required={required} maxLength={maxLength} /></div>; }
function Skeleton() { return <div className="skeleton" aria-label="Investigation in progress" aria-live="polite"><div className="sk-head"><i /><b /><span /></div><div className="sk-note"><span className="live-dot" /> Searching public sources and assembling the evidence trail</div>{[0,1,2].map(n => <div className="sk-row" key={n}><i /><div><b /><span /></div></div>)}</div>; }
function App() {
  const [form, setForm] = useState(emptyForm); const [report, setReport] = useState(null); const [loading, setLoading] = useState(false); const [error, setError] = useState(''); const [tab, setTab] = useState('findings'); const [expanded, setExpanded] = useState({}); const [copied, setCopied] = useState(false);
  const evidenceByClaim = useMemo(() => (report?.evidence || []).reduce((map, item) => ((map[item.claim_id] ||= []).push(item), map), {}), [report]);
  const sourceById = useMemo(() => Object.fromEntries((report?.sources || []).map(source => [source.id, source])), [report]);
  const findingByClaim = useMemo(() => Object.fromEntries((report?.findings || []).map(finding => [finding.claim_id, finding])), [report]);
  const setField = event => {
    setForm(current => ({ ...current, [event.target.name]: event.target.value }));
    // Never leave a previous report visible while the user edits a new case.
    setReport(null);
    setError('');
  };
  async function investigate(event) {
    event.preventDefault();
    setError('');
    setReport(null);
    setTab('findings');

    const message = form.message_text.trim();
    // A URL-only message must be a complete, parseable HTTP(S) URL. Ordinary
    // pasted job-offer text remains valid even when it contains URLs.
    if (/^https?:\\/\\/\\s*$/i.test(message)) {
      setError('Enter a complete URL, or paste the job-offer message. "http://" by itself is incomplete.');
      return;
    }
    if (/^https?:\\/\\/\\S+$/i.test(message)) {
      try {
        const parsed = new URL(message);
        if (!['http:', 'https:'].includes(parsed.protocol) || !parsed.hostname) {
          throw new Error('invalid URL');
        }
      } catch {
        setError('Enter a valid, complete http:// or https:// URL, or paste the job-offer message.');
        return;
      }
    }

    setLoading(true);
    try {
      const payload = { company_name: form.company_name.trim(), message_text: form.message_text.trim() };
      if (form.recruiter_name.trim() || form.recruiter_email.trim()) { payload.recruiter_details = {}; if (form.recruiter_name.trim()) payload.recruiter_details.name = form.recruiter_name.trim(); if (form.recruiter_email.trim()) payload.recruiter_details.email = form.recruiter_email.trim(); }
      if (form.application_url.trim()) payload.application_url = form.application_url.trim(); if (form.job_listing_url.trim()) payload.job_listing_url = form.job_listing_url.trim();
      const response = await fetch('/api/investigate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'The request was rejected. Check the fields and backend logs.');
      setReport(body); setExpanded(Object.fromEntries((body.claims || []).map((claim, index) => [claim.id, index === 0])));
    } catch (err) { setError(err.message || 'Could not reach TrustLens AI. Start the backend and try again.'); } finally { setLoading(false); }
  }
  function loadExample() { setForm({ company_name: 'Northstar Digital', message_text: 'Congratulations. You have been selected for the Junior Software Engineer role at Northstar Digital. To reserve your onboarding slot, pay a refundable registration fee of ₹1,850 by tonight. Send the receipt to our recruitment coordinator after payment.', recruiter_name: '', recruiter_email: 'talent.northstar@gmail.com', application_url: 'https://northstar-careers.example/apply', job_listing_url: '' }); setError(''); setReport(null); }
  function reset() { setForm(emptyForm); setReport(null); setError(''); setTab('findings'); }
  async function copyReport() { try { await navigator.clipboard.writeText(JSON.stringify(report, null, 2)); setCopied(true); window.setTimeout(() => setCopied(false), 1800); } catch { setError('Clipboard access was blocked. You can still review the report on screen.'); } }
  const overall = report?.overall_finding || {}; const tone = toneFor(overall.status); const queries = report?.search_queries || []; const completed = queries.filter(q => q.status === 'completed').length; const failed = queries.filter(q => q.status === 'failed').length;
  const iconFor = status => status === 'supported' ? <Check size={15} /> : status === 'risk_signal' || status === 'conflicting' ? <AlertCircle size={15} /> : <CircleHelp size={15} />;
  return <div className="app-shell" id="top">
    <header className="site-header"><a className="brand" href="#top" aria-label="TrustLens AI home"><span className="brand-mark"><ShieldCheck size={22} strokeWidth={1.7} /></span><span className="brand-name">trustlens<span> / ai</span><small>INDEPENDENT JOB-OFFER CHECKS</small></span></a><div className="header-meta"><span className="live-dot" /> EVIDENCE WORKSPACE <i /> <code>MVP 0.2</code></div></header>
    <main className="page-content">
      <section className="page-heading"><div><p className="eyebrow"><span>01</span> RECRUITMENT INVESTIGATION</p><h1>Before you say yes,<br /><em>look closer.</em></h1><p className="intro">Check the claims behind a job offer. Trace each finding to public sources, and keep uncertainty visible.</p></div><aside className="principle"><LockKeyhole size={18} /><div><strong>Evidence before verdicts</strong><p>Search results are signals, not proof of a person's identity or an offer's authenticity.</p></div></aside></section>
      <div className="desk-label"><span>INVESTIGATION DESK</span><span>INPUT <b>→</b> REVIEW</span></div>
      <section className="workspace">
        <aside className="intake"><div className="section-heading"><div><p className="section-code">A / INTAKE</p><h2>What did they send you?</h2></div><FileSearch size={22} /></div><p className="section-intro">Add the message and details you can verify independently.</p>
          <form onSubmit={investigate} className="intake-form"><Field label="Company or organisation" name="company_name" value={form.company_name} onChange={setField} placeholder="e.g. Northstar Digital" required maxLength={160} />
            <div className="field"><div className="label-line"><label htmlFor="message_text">Message or job offer<span className="required"> *</span></label><span className="counter">{form.message_text.length.toLocaleString('en-US')} / 12,000</span></div><textarea id="message_text" name="message_text" value={form.message_text} onChange={setField} placeholder={'Paste the email, text message, or offer letter…\n\nInclude the role, salary, links, contact details, and any request for money.'} required rows={7} maxLength={12000} /><p className="hint">Remove personal details you do not need to investigate.</p></div>
            <details className="optional" open={Boolean(form.recruiter_name || form.recruiter_email || form.application_url || form.job_listing_url)}><summary><span>Additional details</span><small>OPTIONAL</small><ChevronDown size={15} /></summary><div className="optional-fields"><Field label="Recruiter name" name="recruiter_name" value={form.recruiter_name} onChange={setField} placeholder="Name as shown in message" maxLength={160} /><Field label="Recruiter email" name="recruiter_email" value={form.recruiter_email} onChange={setField} placeholder="name@company.com" type="email" maxLength={254} /><Field label="Application URL" name="application_url" value={form.application_url} onChange={setField} placeholder="https://…" type="url" maxLength={2048} /><Field label="Job listing URL" name="job_listing_url" value={form.job_listing_url} onChange={setField} placeholder="https://…" type="url" maxLength={2048} /></div></details>
            {error && <div className="error" role="alert"><AlertCircle size={17} /><p>{error}</p><button type="button" onClick={() => setError('')} aria-label="Dismiss error"><X size={15} /></button></div>}
            <button className="submit" type="submit" disabled={loading || !form.company_name.trim() || !form.message_text.trim()}><span>{loading ? 'Investigating sources' : 'Investigate this offer'}</span>{loading ? <span className="dots"><i /><i /><i /></span> : <ArrowUpRight size={18} />}</button><div className="form-note"><ShieldCheck size={14} /><span>Nothing is saved as an account or case history in this MVP.</span></div>
          </form>
          {!report && !loading && <div className="example"><p>NEED A TEST CASE?</p><button type="button" onClick={loadExample}>Load a sample suspicious offer <ArrowUpRight size={14} /></button></div>}{report && <div className="example"><button type="button" onClick={reset}><RotateCcw size={14} /> Start a new investigation</button></div>}
        </aside>
        <section className="results" aria-label="Investigation report" aria-live="polite" aria-busy={loading}>
          {!report && !loading && <div className="empty"><div className="empty-top"><span>TL / FIELD NOTE</span><code>NO CASE OPEN</code></div><div className="empty-icon"><Search size={25} /></div><p className="eyebrow">B / EVIDENCE REVIEW</p><h2>A claim is only<br />the beginning.</h2><p className="empty-copy">Your report connects extracted claims to search queries, public sources, and the limits of what those sources can establish.</p><div className="steps"><div><span>01</span><div><strong>Extract claims</strong><p>Identify the company, role, links, and requests.</p></div></div><div><span>02</span><div><strong>Search in public</strong><p>Look for relevant, independently published information.</p></div></div><div><span>03</span><div><strong>Follow the source</strong><p>Review what supports a claim and what remains unknown.</p></div></div></div><div className="empty-bottom"><span className="live-dot" /> WAITING FOR YOUR FIRST INVESTIGATION</div></div>}
          {loading && <Skeleton />}
          {report && <><div className={`overall tone-${tone}`}><div className="report-top"><span className="eyebrow">B / INVESTIGATION FINDING</span><code>{report.investigation_id}</code></div><div className="verdict"><span className="verdict-icon">{tone === 'risk' ? <ShieldAlert size={25} /> : tone === 'supported' ? <BadgeCheck size={25} /> : <CircleHelp size={25} />}</span><div><small>OVERALL ASSESSMENT</small><h2>{overall.label || 'Needs verification'}</h2></div></div><p className="summary">{overall.summary || report.explanation}</p><div className="metrics"><div><span>CLAIMS</span><strong>{(report.claims || []).length}</strong></div><div><span>SOURCES</span><strong>{(report.sources || []).length}</strong></div><div><span>SEARCHES</span><strong>{completed}<small> / {queries.length}</small></strong></div></div>{failed > 0 && <p className="partial-warning"><AlertCircle size={15} /> {failed} search{failed === 1 ? '' : 'es'} failed. Treat this report as incomplete.</p>}<div className="report-actions"><button type="button" onClick={copyReport}><Clipboard size={14} /> {copied ? 'Copied report JSON' : 'Copy report JSON'}</button><button type="button" onClick={() => window.print()}>Print report <ArrowUpRight size={14} /></button></div></div>
            <nav className="tabs" aria-label="Report sections"><button type="button" className={tab === 'findings' ? 'active' : ''} aria-current={tab === 'findings' ? 'page' : undefined} onClick={() => setTab('findings')}>Findings <span>{(report.findings || []).length}</span></button><button type="button" className={tab === 'sources' ? 'active' : ''} aria-current={tab === 'sources' ? 'page' : undefined} onClick={() => setTab('sources')}>Sources <span>{(report.sources || []).length}</span></button><button type="button" className={tab === 'trail' ? 'active' : ''} aria-current={tab === 'trail' ? 'page' : undefined} onClick={() => setTab('trail')}>Search trail</button></nav>
            {tab === 'findings' && <div className="finding-list">{(report.claims || []).map((claim, index) => { const finding = findingByClaim[claim.id] || { status: 'needs_verification', summary: 'No finding was returned for this claim.' }; const evidence = evidenceByClaim[claim.id] || []; const isOpen = expanded[claim.id] ?? index === 0; return <article className="finding" key={claim.id}><button type="button" className="finding-toggle" aria-expanded={isOpen} onClick={() => setExpanded(old => ({ ...old, [claim.id]: !isOpen }))}><span className={`finding-icon status-${finding.status}`}>{iconFor(finding.status)}</span><span className="finding-title"><small>{readable(claim.type || 'claim')} · {readable(claim.importance || 'normal')} priority</small><strong>{claim.text}</strong><span className={`status-label status-${finding.status}`}>{labels[finding.status] || readable(finding.status)}</span></span>{isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}</button>{isOpen && <div className="finding-detail"><p>{finding.summary}</p><div className="evidence-heading">LINKED EVIDENCE <span>{evidence.length}</span></div>{evidence.length ? evidence.map(item => { const source = sourceById[item.source_id]; return <div className="evidence-row" key={item.id}><span className={`relation relation-${item.relation}`}>{readable(item.relation)}</span><div><p>{item.summary}</p>{source && <a href={source.url} target="_blank" rel="noopener noreferrer">{source.title || source.domain} <ExternalLink size={12} /></a>}</div><small>{readable(item.strength)}</small></div>; }) : <p className="muted">No source was linked to this claim.</p>}</div>}</article>; })}{!report.claims?.length && <div className="no-results"><strong>No claims extracted</strong><p>Try adding more detail from the original message.</p></div>}</div>}
            {tab === 'sources' && <div className="source-list">{(report.sources || []).map((source, index) => <article className="source" key={source.id}><span className="source-num">{String(index + 1).padStart(2, '0')}</span><div><div className="source-meta"><span>{readable(source.source_type || 'web result')}</span><span>{source.domain}</span></div><a className="source-title" href={source.url} target="_blank" rel="noopener noreferrer">{source.title || source.domain || 'Open source'} <ExternalLink size={13} /></a><p>{source.snippet || 'The search provider returned no description for this page.'}</p><div className="source-foot">QUERY {source.query_id || '—'} <a href={source.url} target="_blank" rel="noopener noreferrer">Open source <ArrowUpRight size={13} /></a></div></div></article>)}{!report.sources?.length && <div className="no-results"><Globe2 size={20} /><strong>No sources returned</strong><p>Check the search trail for failed searches or empty results.</p></div>}</div>}
            {tab === 'trail' && <div className="trail">{(report.investigation_trail || []).map((group, index) => { const claim = (report.claims || []).find(item => item.id === group.claim_id); return <section className="trail-group" key={group.claim_id}><div className="trail-title"><span>{String(index + 1).padStart(2, '0')}</span><strong>{claim?.text || group.claim_id}</strong></div><ol>{(group.steps || []).map((step, stepIndex) => <li key={`${group.claim_id}-${stepIndex}`}><span>{readable(step.type)}</span><p>{step.content}</p></li>)}</ol></section>; })}{!report.investigation_trail?.length && <p className="muted">No search trail was returned by the API.</p>}</div>}
            <div className="caveat"><LockKeyhole size={15} /><p><strong>Read this as an investigation, not a verdict.</strong> Search snippets can be incomplete or misleading. Verify through contact details obtained independently from the organisation's official website.</p></div></>}
        </section>
      </section>
      <footer className="footer"><span><ShieldCheck size={15} /> TRUSTLENS / AI</span><p>Evidence is inspectable. Uncertainty is part of the report.</p><code>BUILD 0.2</code></footer>
    </main>
  </div>;
}
export default App;
