import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const SERVICES = [
  { id: 'eye_care', label: 'Eye surgery / eye care', short: 'Eye surgery' },
  { id: 'cardiac_surgery', label: 'Cardiac surgery', short: 'Cardiac surgery' },
];

const REGIONS = [
  { value: '', label: 'All India' },
  { value: 'Delhi', label: 'Delhi' },
  { value: 'Karnataka', label: 'Karnataka' },
  { value: 'Maharashtra', label: 'Maharashtra' },
  { value: 'Tamil Nadu', label: 'Tamil Nadu' },
  { value: 'Telangana', label: 'Telangana' },
];

const AGE_GROUPS = [
  { value: 'all', label: 'All age groups' },
  { value: 'child', label: 'Children' },
  { value: 'adult', label: 'Adults' },
  { value: 'senior', label: 'Seniors' },
];

const TABS = [
  { id: 'explorer', label: 'Procedure Explorer' },
  { id: 'trust', label: 'Trust Cards' },
  { id: 'verification', label: 'Human Verification' },
  { id: 'assistant', label: 'Chart Assistant' },
  { id: 'shortlists', label: 'Shortlists' },
];

const fallbackFacilities = [
  {
    unique_id: 'aravind-eye-hospital',
    rank: 1,
    name: 'Aravind Eye Hospital',
    city: 'Hyderabad',
    state: 'Telangana',
    score: 8.7,
    confidence_label: 'Human verified',
    human_verified: true,
    evidence_summary: 'Ophthalmology, cataract, retina and diagnostic evidence appear in facility text.',
    source_urls: ['https://example.org/source/aravind'],
    uncertainty_flags: ['Some source text may be aggregated from multiple pages'],
    score_breakdown: {
      specialties: 1.5,
      procedure: 1.4,
      equipment: 0.9,
      capability: 0.9,
      description: 1,
      sources: 0.9,
      contact: 0.7,
      location: 0.5,
      human: 1.0,
      freshness: 0.1,
    },
  },
  {
    unique_id: 'sankara-nethralaya',
    rank: 2,
    name: 'Sankara Nethralaya',
    city: 'Chennai',
    state: 'Tamil Nadu',
    score: 8.3,
    confidence_label: 'High',
    evidence_summary: 'Specialty and procedure fields strongly support eye care capability.',
    source_urls: ['https://example.org/source/sankara'],
    uncertainty_flags: ['Verify live availability before referral'],
    score_breakdown: { specialties: 1.5, procedure: 1.5, equipment: 0.7, capability: 0.9, description: 0.8, sources: 0.9, contact: 0.75, location: 0.5, human: 0.5, freshness: 0.25 },
  },
  {
    unique_id: 'lv-prasad-eye-institute',
    rank: 3,
    name: 'LV Prasad Eye Institute',
    city: 'Hyderabad',
    state: 'Telangana',
    score: 7.9,
    confidence_label: 'Medium',
    evidence_summary: 'Strong source URLs and equipment mentions, with some uncertainty.',
    source_urls: ['https://example.org/source/lvpei'],
    uncertainty_flags: ['Needs procedure-specific human verification'],
    score_breakdown: { specialties: 1.4, procedure: 1.2, equipment: 0.8, capability: 0.8, description: 0.9, sources: 0.8, contact: 0.7, location: 0.5, human: 0.5, freshness: 0.3 },
  },
];

const api = async (path, options) => {
  const res = await fetch(path, { headers: { 'content-type': 'application/json' }, ...options });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
};

function displayConfidence(f = {}) {
  if (f.human_verified || f.human_verification_status === 'verified') return 'Human verified';
  if ((f.score || f.final_score || 0) >= 8) return 'High';
  if ((f.score || f.final_score || 0) >= 6) return 'Medium';
  return f.confidence_label || 'Needs review';
}

function classForConfidence(label = '') {
  const text = label.toLowerCase();
  if (text.includes('verified') || text.includes('high')) return 'hi';
  if (text.includes('medium')) return 'med';
  return 'low';
}

function ScorePill({ score }) {
  return <div className="score">{Number(score || 0).toFixed(1)}</div>;
}

function Layout({ children, activeTab, onTabChange, serviceLabel, onPlayVoice }) {
  return (
    <div className="appShell">
      <header className="topbar">
        <div className="brandBlock">
          <div className="brand">Care<span>Signal</span></div>
          <p>Evidence-backed facility rankings with human verification.</p>
        </div>
        <nav className="tabs" aria-label="CareSignal sections">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              className={activeTab === tab.id ? 'active' : ''}
              onClick={() => onTabChange(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
        <div className="callTop">
          <span>Digital Call Assistant</span>
          <a href="tel:+14155550126">Call CareSignal</a>
          <button onClick={onPlayVoice}>Play voice</button>
          <small>Verify rankings and evidence for {serviceLabel}.</small>
        </div>
      </header>
      <main className="main">{children}</main>
    </div>
  );
}

function FilterBar({ region, setRegion, service, setService, ageGroup, setAgeGroup }) {
  return (
    <section className="filterCard" aria-label="Facility filters">
      <label>
        <span>1. Region</span>
        <select value={region} onChange={(e) => setRegion(e.target.value)}>
          {REGIONS.map((r) => <option key={r.label} value={r.value}>{r.label}</option>)}
        </select>
      </label>
      <label>
        <span>2. Service</span>
        <select value={service} onChange={(e) => setService(e.target.value)}>
          {SERVICES.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}
        </select>
      </label>
      <label>
        <span>3. Age group</span>
        <select value={ageGroup} onChange={(e) => setAgeGroup(e.target.value)}>
          {AGE_GROUPS.map((a) => <option key={a.value} value={a.value}>{a.label}</option>)}
        </select>
      </label>
    </section>
  );
}

function Metrics({ facilities, regionLabel, ageLabel }) {
  const top = facilities[0]?.score ?? 0;
  const verified = facilities.filter((f) => f.human_verified || f.human_verification_status === 'verified' || String(f.confidence_label).toLowerCase().includes('verified')).length;
  return (
    <div className="metricrow">
      <div className="metric"><strong>10,088</strong><small>facilities indexed</small></div>
      <div className="metric"><strong>{facilities.length}</strong><small>current matches</small></div>
      <div className="metric"><strong>{Number(top).toFixed(1)}</strong><small>top score / 10</small></div>
      <div className="metric"><strong>{verified}</strong><small>human verified shown</small></div>
      <div className="metric wide"><strong>{regionLabel}</strong><small>selected region</small></div>
      <div className="metric wide"><strong>{ageLabel}</strong><small>selected age group</small></div>
    </div>
  );
}

function FacilityRankingTable({ facilities, selectedId, onSelect }) {
  return (
    <section className="card rankings">
      <div className="cardTitle"><h2>Ranked facilities</h2><span>Top 10 by service</span></div>
      <table className="rank">
        <thead><tr><th>Rank</th><th>Facility</th><th>Location</th><th>Score</th><th>Confidence</th></tr></thead>
        <tbody>
          {facilities.map((f, i) => (
            <tr key={f.unique_id} className={selectedId === f.unique_id ? 'selected' : ''} onClick={() => onSelect(f)}>
              <td>#{f.rank || i + 1}</td>
              <td><b>{f.name}</b><br /><small>{f.evidence_summary || f.description || (f.evidence_snippets || []).slice(0, 1).join(' ')}</small></td>
              <td>{f.city || f.address_city || 'Unknown'}, {f.state || f.address_stateOrRegion || 'India'}</td>
              <td><ScorePill score={f.score || f.final_score} /></td>
              <td><span className={`badge ${classForConfidence(displayConfidence(f))}`}>{displayConfidence(f)}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
      {!facilities.length && <p className="empty">No facilities match this region/service combination yet.</p>}
    </section>
  );
}

function TrustCard({ facility, serviceLabel }) {
  if (!facility) return null;
  const rawBreakdown = facility.score_breakdown || {};
  const entries = Array.isArray(rawBreakdown)
    ? rawBreakdown.map((item) => [item.label || item.key, item.score ?? 0, item.max_score])
    : Object.entries(rawBreakdown).map(([key, val]) => [key, val, undefined]);
  return (
    <aside className="card trust">
      <div className="trustHeader">
        <div><h2>Trust Card</h2><small>Why this facility ranks here</small></div>
        <ScorePill score={facility.score || facility.final_score} />
      </div>
      <p><b>Claim:</b> {facility.name} appears to support {serviceLabel}.</p>
      <div className="evidence">{facility.evidence_summary || (facility.evidence_snippets || []).slice(0, 2).join(' ') || facility.description || 'Evidence appears in facility text fields.'}</div>
      <div className="why">
        {entries.slice(0, 10).map(([key, val, max]) => <div key={key}><b>+{Number(val || 0).toFixed(2)}{max ? `/${max}` : ''}</b><br />{key}</div>)}
      </div>
      <div className="sources">
        <b>Sources</b>
        {(facility.source_urls || [facility.source_url, facility.website].filter(Boolean)).slice(0, 3).map((url) => <a key={url} href={url} target="_blank" rel="noreferrer">{url}</a>)}
      </div>
      <p className="footer"><b>Uncertainty:</b> {(facility.uncertainty_flags || ['Treat extracted claims as claims to verify, not ground truth.']).join('; ')}</p>
    </aside>
  );
}

function VerificationForm({ facility, service, serviceLabel, onVerified }) {
  const [status, setStatus] = useState('verified');
  const [notes, setNotes] = useState('Verified by phone or visit.');
  if (!facility) return null;
  const submit = async () => {
    const payload = {
      unique_id: facility.unique_id,
      facility_name: facility.name,
      procedure: service,
      status,
      verifier_name: 'CareSignal demo user',
      notes,
    };
    try { await api('/api/verifications', { method: 'POST', body: JSON.stringify(payload) }); } catch (_) {}
    onVerified(payload);
  };
  return (
    <section className="card verification">
      <div className="cardTitle"><h2>Human verification</h2><span>{facility.name}</span></div>
      <p>Call or visit the facility, verify {serviceLabel} capability, then update CareSignal so future rankings improve.</p>
      <div className="checklist">
        <label><input type="checkbox" /> Staff confirmed this service is currently available</label>
        <label><input type="checkbox" /> Required equipment/facilities observed or confirmed</label>
        <label><input type="checkbox" /> Specialists or referral pathway confirmed</label>
      </div>
      <select value={status} onChange={(e) => setStatus(e.target.value)}>
        <option value="verified">Verified</option>
        <option value="needs_review">Needs review</option>
        <option value="rejected">Rejected</option>
      </select>
      <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
      <button onClick={submit}>Submit verification</button>
    </section>
  );
}

function VoiceAssistantPanel({ facility, serviceLabel, onPlayVoice }) {
  return (
    <section className="card assistant voicePanel">
      <div className="cardTitle"><h2>CareSignal Voice</h2><span>Digital call assistant</span></div>
      <div className="bubble">User calls CareSignal and asks why {facility?.name || 'this facility'} ranks this way for {serviceLabel}.</div>
      <div className="bubble">The assistant reads evidence, uncertainty, and a verification checklist using TTS.</div>
      <button onClick={onPlayVoice}>Play sample human voice</button>
    </section>
  );
}

function ChartAssistant({ service, serviceLabel, regionLabel, ageLabel }) {
  const [question, setQuestion] = useState(`Show top 10 ${serviceLabel} facilities in ${regionLabel} for ${ageLabel} and explain why they rank high.`);
  const [answer, setAnswer] = useState(null);
  useEffect(() => {
    setQuestion(`Show top 10 ${serviceLabel} facilities in ${regionLabel} for ${ageLabel} and explain why they rank high.`);
  }, [serviceLabel, regionLabel, ageLabel]);
  const ask = async () => {
    try {
      setAnswer(await api('/api/assistant/query', { method: 'POST', body: JSON.stringify({ question, procedure: service }) }));
    } catch (_) {
      setAnswer({ answer: `Top ${serviceLabel} facilities are ranked by evidence support, source quality, contactability, location completeness, and human verification.`, data: fallbackFacilities });
    }
  };
  return (
    <section className="card chartAssistant">
      <div className="cardTitle"><h2>Ask the chart assistant</h2><span>Tables + explanations</span></div>
      <textarea value={question} onChange={(e) => setQuestion(e.target.value)} />
      <button onClick={ask}>Generate chart and explanation</button>
      {answer && <div className="assistantAnswer"><p>{answer.answer}</p><div className="bars">{(answer.data || []).slice(0, 5).map((row) => <div key={row.unique_id || row.name}><span>{row.name}</span><i style={{ width: `${Math.min(100, (row.score || row.final_score || 5) * 10)}%` }} /></div>)}</div></div>}
    </section>
  );
}

function ShortlistPanel({ selected, shortlists, onAddShortlist }) {
  return (
    <section className="card shortlistPanel">
      <div className="cardTitle"><h2>Shortlists</h2><span>Planner decisions</span></div>
      <p>Save facilities that should be reviewed, trusted, or used in a planning scenario.</p>
      <button onClick={onAddShortlist} disabled={!selected}>Add selected facility</button>
      <div className="shortlistItems">
        {shortlists.map((item) => (
          <div key={item.id} className="shortlistItem"><b>{item.name}</b><small>{item.serviceLabel} • {item.regionLabel}</small></div>
        ))}
        {!shortlists.length && <p className="empty">No shortlist items yet.</p>}
      </div>
    </section>
  );
}

function App() {
  const [service, setService] = useState('eye_care');
  const [region, setRegion] = useState('');
  const [ageGroup, setAgeGroup] = useState('all');
  const [activeTab, setActiveTab] = useState('explorer');
  const [facilities, setFacilities] = useState(fallbackFacilities);
  const [selected, setSelected] = useState(fallbackFacilities[0]);
  const [shortlists, setShortlists] = useState([]);

  const serviceDef = useMemo(() => SERVICES.find((p) => p.id === service) || SERVICES[0], [service]);
  const serviceLabel = serviceDef.short;
  const regionLabel = useMemo(() => REGIONS.find((r) => r.value === region)?.label || 'All India', [region]);
  const ageLabel = useMemo(() => AGE_GROUPS.find((a) => a.value === ageGroup)?.label || 'All age groups', [ageGroup]);

  useEffect(() => {
    let mounted = true;
    const params = new URLSearchParams({ procedure: service, limit: '10' });
    if (region) params.set('state', region);
    api(`/api/facilities/top?${params.toString()}`)
      .then((data) => {
        const rows = data.facilities || data.data || data;
        if (mounted && Array.isArray(rows) && rows.length) {
          const ranked = rows.map((f, i) => ({ ...f, rank: f.rank || i + 1 }));
          setFacilities(ranked);
          setSelected(ranked[0]);
        } else if (mounted) {
          setFacilities([]);
          setSelected(null);
        }
      })
      .catch(() => {
        if (mounted) {
          const local = fallbackFacilities
            .filter((f) => !region || f.state === region)
            .map((f, i) => ({ ...f, rank: i + 1 }));
          setFacilities(local);
          setSelected(local[0] || null);
        }
      });
    return () => { mounted = false; };
  }, [service, region]);

  const playVoice = async () => {
    const audio = new Audio('/api/voice/sample');
    try { await audio.play(); } catch { window.open('/api/voice/sample', '_blank'); }
  };

  const onVerified = () => {
    if (!selected) return;
    const updated = { ...selected, human_verified: true, human_verification_status: 'verified', confidence_label: 'Human verified', score: Math.min(10, Number(selected.score || 0) + 1.5) };
    setSelected(updated);
    setFacilities((rows) => rows.map((f) => f.unique_id === updated.unique_id ? updated : f).sort((a, b) => (b.score || 0) - (a.score || 0)).map((f, i) => ({ ...f, rank: i + 1 })));
  };

  const addShortlist = async () => {
    if (!selected) return;
    const item = { id: `${selected.unique_id}-${Date.now()}`, name: selected.name, serviceLabel, regionLabel };
    setShortlists((items) => [item, ...items]);
    try {
      await api('/api/shortlists', { method: 'POST', body: JSON.stringify({ unique_id: selected.unique_id, procedure: service, notes: `${serviceLabel} shortlist for ${regionLabel}` }) });
    } catch (_) {}
  };

  return (
    <Layout activeTab={activeTab} onTabChange={setActiveTab} serviceLabel={serviceLabel} onPlayVoice={playVoice}>
      <div className="hero">
        <div className="title"><h1>Top facilities for {serviceLabel}</h1><p>Ranked by evidence quality, uncertainty, and human verification. Score is out of 10.</p></div>
        <FilterBar region={region} setRegion={setRegion} service={service} setService={setService} ageGroup={ageGroup} setAgeGroup={setAgeGroup} />
      </div>
      <Metrics facilities={facilities} regionLabel={regionLabel} ageLabel={ageLabel} />

      {activeTab === 'explorer' && <div className="grid"><FacilityRankingTable facilities={facilities} selectedId={selected?.unique_id} onSelect={setSelected} /><TrustCard facility={selected} serviceLabel={serviceLabel} /></div>}
      {activeTab === 'trust' && <div className="grid"><TrustCard facility={selected} serviceLabel={serviceLabel} /><FacilityRankingTable facilities={facilities} selectedId={selected?.unique_id} onSelect={setSelected} /></div>}
      {activeTab === 'verification' && <div className="grid"><VerificationForm facility={selected} service={service} serviceLabel={serviceLabel} onVerified={onVerified} /><VoiceAssistantPanel facility={selected} serviceLabel={serviceLabel} onPlayVoice={playVoice} /></div>}
      {activeTab === 'assistant' && <div className="grid"><ChartAssistant service={service} serviceLabel={serviceLabel} regionLabel={regionLabel} ageLabel={ageLabel} /><VoiceAssistantPanel facility={selected} serviceLabel={serviceLabel} onPlayVoice={playVoice} /></div>}
      {activeTab === 'shortlists' && <div className="grid"><ShortlistPanel selected={selected} shortlists={shortlists} onAddShortlist={addShortlist} /><TrustCard facility={selected} serviceLabel={serviceLabel} /></div>}
    </Layout>
  );
}

createRoot(document.getElementById('root')).render(<App />);
