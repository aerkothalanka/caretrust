import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const procedures = [
  { id: 'eye_care', label: 'Eye care' },
  { id: 'cardiac_surgery', label: 'Cardiac surgery' },
  { id: 'icu_care', label: 'ICU care' },
  { id: 'dialysis', label: 'Dialysis' },
  { id: 'oncology', label: 'Oncology' },
  { id: 'maternity_obgyn', label: 'Maternity / OBGYN' },
  { id: 'emergency_trauma', label: 'Emergency / trauma' },
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

function Layout({ children, procedureLabel, onPlayVoice }) {
  return (
    <div className="app">
      <aside className="side">
        <div className="brand">Care<span>Signal</span></div>
        <nav className="nav">
          <button className="active">Procedure Explorer</button>
          <button>Trust Cards</button>
          <button>Human Verification</button>
          <button>Chart Assistant</button>
          <button>Shortlists</button>
        </nav>
        <div className="call">
          <h3>Digital Call Assistant</h3>
          <p>Call CareSignal to verify a facility, ranking, and evidence for <b>{procedureLabel}</b>.</p>
          <a href="tel:+14155550126">Call CareSignal</a>
          <button onClick={onPlayVoice}>Play sample voice</button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

function Metrics({ facilities }) {
  const top = facilities[0]?.score ?? 0;
  const verified = facilities.filter((f) => f.human_verified || f.human_verification_status === 'verified' || String(f.confidence_label).toLowerCase().includes('verified')).length;
  return (
    <div className="metricrow">
      <div className="metric"><strong>10,088</strong><small>facilities indexed</small></div>
      <div className="metric"><strong>{facilities.length}</strong><small>current matches</small></div>
      <div className="metric"><strong>{Number(top).toFixed(1)}</strong><small>top score / 10</small></div>
      <div className="metric"><strong>{verified}</strong><small>human verified shown</small></div>
    </div>
  );
}

function FacilityRankingTable({ facilities, selectedId, onSelect }) {
  return (
    <section className="card rankings">
      <h2>Ranked facilities</h2>
      <table className="rank">
        <thead><tr><th>Rank</th><th>Facility</th><th>Location</th><th>Score</th><th>Confidence</th></tr></thead>
        <tbody>
          {facilities.map((f, i) => (
            <tr key={f.unique_id} className={selectedId === f.unique_id ? 'selected' : ''} onClick={() => onSelect(f)}>
              <td>#{f.rank || i + 1}</td>
              <td><b>{f.name}</b><br /><small>{f.evidence_summary || f.description || (f.evidence_snippets || []).slice(0, 1).join(' ')}</small></td>
              <td>{f.city || f.address_city}, {f.state || f.address_stateOrRegion}</td>
              <td><ScorePill score={f.score || f.final_score} /></td>
              <td><span className={`badge ${classForConfidence(displayConfidence(f))}`}>{displayConfidence(f)}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function TrustCard({ facility, procedureLabel }) {
  if (!facility) return null;
  const rawBreakdown = facility.score_breakdown || {};
  const entries = Array.isArray(rawBreakdown)
    ? rawBreakdown.map((item) => [item.label || item.key, item.score ?? 0, item.max_score])
    : Object.entries(rawBreakdown).map(([key, val]) => [key, val, undefined]);
  return (
    <aside className="card trust">
      <div className="trustHeader">
        <h2>Trust Card</h2>
        <ScorePill score={facility.score || facility.final_score} />
      </div>
      <p><b>Claim:</b> {facility.name} appears to support {procedureLabel}.</p>
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

function VerificationForm({ facility, procedure, onVerified }) {
  const [status, setStatus] = useState('verified');
  const [notes, setNotes] = useState('Verified by phone or visit.');
  const submit = async () => {
    const payload = {
      unique_id: facility.unique_id,
      facility_name: facility.name,
      procedure,
      status,
      verifier_name: 'CareSignal demo user',
      notes,
    };
    try { await api('/api/verifications', { method: 'POST', body: JSON.stringify(payload) }); } catch (_) {}
    onVerified(payload);
  };
  return (
    <section className="card verification">
      <h2>Human verification</h2>
      <p>Call or visit the facility, then update CareSignal so future rankings improve.</p>
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

function VoiceAssistantPanel({ facility, procedureLabel, onPlayVoice }) {
  return (
    <section className="card assistant voicePanel">
      <h2>CareSignal Voice</h2>
      <div className="bubble">Ask why {facility?.name || 'this facility'} ranks this way for {procedureLabel}.</div>
      <div className="bubble">The assistant reads evidence, uncertainty, and a verification checklist using TTS.</div>
      <button onClick={onPlayVoice}>Play sample human voice</button>
    </section>
  );
}

function ChartAssistant({ procedure, procedureLabel }) {
  const [question, setQuestion] = useState(`Show top 10 ${procedureLabel} facilities and explain why they rank high.`);
  const [answer, setAnswer] = useState(null);
  const ask = async () => {
    try {
      setAnswer(await api('/api/assistant/query', { method: 'POST', body: JSON.stringify({ question, procedure }) }));
    } catch (_) {
      setAnswer({ answer: `Top ${procedureLabel} facilities are ranked by evidence support, source quality, contactability, location completeness, and human verification.`, data: fallbackFacilities });
    }
  };
  return (
    <section className="card chartAssistant">
      <h2>Ask the chart assistant</h2>
      <textarea value={question} onChange={(e) => setQuestion(e.target.value)} />
      <button onClick={ask}>Generate chart and explanation</button>
      {answer && <div className="assistantAnswer"><p>{answer.answer}</p><div className="bars">{(answer.data || []).slice(0, 5).map((row) => <div key={row.unique_id || row.name}><span>{row.name}</span><i style={{ width: `${Math.min(100, (row.score || row.final_score || 5) * 10)}%` }} /></div>)}</div></div>}
    </section>
  );
}

function App() {
  const [procedure, setProcedure] = useState('eye_care');
  const [facilities, setFacilities] = useState(fallbackFacilities);
  const [selected, setSelected] = useState(fallbackFacilities[0]);
  const procedureLabel = useMemo(() => procedures.find((p) => p.id === procedure)?.label || procedure, [procedure]);

  useEffect(() => {
    let mounted = true;
    api(`/api/facilities/top?procedure=${encodeURIComponent(procedure)}&limit=10`)
      .then((data) => {
        const rows = data.facilities || data.data || data;
        if (mounted && Array.isArray(rows) && rows.length) {
          setFacilities(rows);
          setSelected(rows[0]);
        }
      })
      .catch(() => {
        if (mounted) {
          setFacilities(fallbackFacilities.map((f, i) => ({ ...f, rank: i + 1 })));
          setSelected(fallbackFacilities[0]);
        }
      });
    return () => { mounted = false; };
  }, [procedure]);

  const playVoice = async () => {
    const audio = new Audio('/api/voice/sample');
    try { await audio.play(); } catch { window.open('/api/voice/sample', '_blank'); }
  };

  const onVerified = () => {
    const updated = { ...selected, human_verified: true, human_verification_status: 'verified', confidence_label: 'Human verified', score: Math.min(10, Number(selected.score || 0) + 1.5) };
    setSelected(updated);
    setFacilities((rows) => rows.map((f) => f.unique_id === updated.unique_id ? updated : f).sort((a, b) => (b.score || 0) - (a.score || 0)).map((f, i) => ({ ...f, rank: i + 1 })));
  };

  return (
    <Layout procedureLabel={procedureLabel} onPlayVoice={playVoice}>
      <div className="top">
        <div className="title"><h1>Top facilities for {procedureLabel}</h1><p>Ranked by evidence quality, uncertainty, and human verification. Score is out of 10.</p></div>
        <div className="filters"><select value={procedure} onChange={(e) => setProcedure(e.target.value)}>{procedures.map((p) => <option key={p.id} value={p.id}>{p.label}</option>)}</select><span className="chip">India</span><span className="chip">Human verified: all</span></div>
      </div>
      <Metrics facilities={facilities} />
      <div className="grid">
        <FacilityRankingTable facilities={facilities} selectedId={selected?.unique_id} onSelect={setSelected} />
        <TrustCard facility={selected} procedureLabel={procedureLabel} />
        <VerificationForm facility={selected} procedure={procedure} onVerified={onVerified} />
        <VoiceAssistantPanel facility={selected} procedureLabel={procedureLabel} onPlayVoice={playVoice} />
        <ChartAssistant procedure={procedure} procedureLabel={procedureLabel} />
      </div>
    </Layout>
  );
}

createRoot(document.getElementById('root')).render(<App />);
