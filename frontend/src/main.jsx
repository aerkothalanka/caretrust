import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const SERVICE_FALLBACK = [
  { service_id: 'cardiac_surgery', service_label: 'Cardiac surgery', specialty_group: 'Cardiology / CTVS' },
  { service_id: 'eye_care', service_label: 'Eye surgery / eye care', specialty_group: 'Ophthalmology' },
  { service_id: 'icu_critical_care', service_label: 'ICU / critical care', specialty_group: 'Critical Care' },
  { service_id: 'dialysis', service_label: 'Dialysis', specialty_group: 'Nephrology' },
  { service_id: 'oncology', service_label: 'Oncology', specialty_group: 'Oncology' },
  { service_id: 'maternity_obgyn', service_label: 'Maternity / OBGYN', specialty_group: 'Maternity / OBGYN' },
  { service_id: 'emergency_trauma', service_label: 'Emergency / trauma', specialty_group: 'Emergency / Trauma' },
];
const TABS = [
  { id: 'explorer', label: 'Explorer' },
  { id: 'map', label: 'Map + Radius' },
  { id: 'verification', label: 'Verification' },
  { id: 'assistant', label: 'Chat Assistant' },
];
const fallbackFacilities = [
  { unique_id: 'fallback-aravind-madurai', name: 'Aravind Eye Hospital, Madurai', country: 'India', state: 'Tamil Nadu', city: 'Madurai', pincode: '625020', latitude: 9.9252, longitude: 78.1198, score: 8.5, confidence_label: 'High', specialties: ['Ophthalmology'], evidence_summary: 'Cataract, retina, glaucoma and ophthalmic equipment evidence appears in source fields.', source_urls: ['https://aravind.org/hospitals/madurai/'], uncertainty_flags: ['Verify live procedure availability before referral.'] },
  { unique_id: 'fallback-narayana-bengaluru', name: 'Narayana Institute of Cardiac Sciences', country: 'India', state: 'Karnataka', city: 'Bengaluru', pincode: '560099', latitude: 12.811, longitude: 77.6948, score: 8.2, confidence_label: 'High', specialties: ['Cardiology / CTVS'], evidence_summary: 'Cardiac surgery, cath lab, cardiac ICU and coronary intervention evidence found.', source_urls: ['https://www.narayanahealth.org'], uncertainty_flags: ['Human verification recommended for current surgical capacity.'] },
  { unique_id: 'fallback-fortis-delhi', name: 'Fortis Escorts Heart Institute', country: 'India', state: 'Delhi', city: 'New Delhi', pincode: '110025', latitude: 28.5613, longitude: 77.2749, score: 7.8, confidence_label: 'Medium', specialties: ['Cardiology / CTVS'], evidence_summary: 'Heart institute with cardiac surgery and critical care source evidence.', source_urls: ['https://www.fortishealthcare.com'], uncertainty_flags: ['Confirm procedure-specific eligibility and referral pathway.'] },
];
const api = async (path, options) => {
  const res = await fetch(path, { headers: { 'content-type': 'application/json' }, ...options });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
};
const fmt = (value) => Number(value || 0).toFixed(1);
const fmtCompactScore = (value) => {
  const n = Number(value || 0);
  return Number.isFinite(n) ? n.toFixed(2).replace(/\.?0+$/, '') : '0';
};
const TERM_LABELS = {
  internalMedicine: 'Internal medicine',
  generalSurgery: 'General surgery',
  orthopedicSurgery: 'Orthopedic surgery',
  physicalMedicineAndRehabilitation: 'Physical medicine & rehabilitation',
  oralAndMaxillofacialSurgery: 'Oral & maxillofacial surgery',
  critical: 'Critical care',
  criti: 'Critical care',
  ambulance: 'Ambulance service',
};
function humanizeTerm(value) {
  const raw = String(value || '').trim().replace(/^['"\[]+|['"\]]+$/g, '');
  if (!raw || raw === 'null' || raw === 'undefined') return '';
  if (TERM_LABELS[raw]) return TERM_LABELS[raw];
  const spaced = raw
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/[_-]+/g, ' ')
    .replace(/\bctvs\b/ig, 'CTVS')
    .replace(/\bicu\b/ig, 'ICU')
    .replace(/\bcabg\b/ig, 'CABG')
    .replace(/\boct\b/ig, 'OCT')
    .replace(/\s+/g, ' ')
    .trim();
  return spaced.replace(/\b\w/g, (c) => c.toUpperCase()).replace(/\b(And|Or|Of)\b/g, (w) => w.toLowerCase());
}
function termList(values, limit = 6) {
  let items = Array.isArray(values) ? values : [];
  if (!items.length && typeof values === 'string') {
    try {
      const parsed = JSON.parse(values);
      items = Array.isArray(parsed) ? parsed : [values];
    } catch (_) {
      items = values.split(/[,;|]+/);
    }
  }
  const seen = new Set();
  return items.map(humanizeTerm).filter((x) => x && !seen.has(x) && seen.add(x)).slice(0, limit);
}
function EvidencePillGroup({ title, items, empty }) {
  return <div className="trustPillGroup"><h3>{title}</h3>{items.length ? <div className="trustPills">{items.map((item) => <span key={item}>{item}</span>)}</div> : <p>{empty}</p>}</div>;
}
function displayConfidence(f = {}) {
  if (f.human_verified || f.human_verification_status === 'verified') return 'Human verified';
  const score = Number(f.score || f.final_score || 0);
  if (score >= 8) return 'High';
  if (score >= 6) return 'Medium';
  return f.confidence_label || 'Needs review';
}
function classForConfidence(label = '') {
  const t = label.toLowerCase();
  if (t.includes('verified') || t.includes('high')) return 'hi';
  if (t.includes('medium')) return 'med';
  return 'low';
}
function normalizeFacility(f, rank) {
  return { ...f, rank: f.rank || rank + 1, country: f.country || 'India', latitude: toNum(f.latitude), longitude: toNum(f.longitude), score: Number(f.score || f.final_score || 0) };
}
function toNum(v) { const n = Number(v); return Number.isFinite(n) ? n : null; }
function distanceKm(a, b) {
  if (![a?.latitude, a?.longitude, b?.latitude, b?.longitude].every((v) => Number.isFinite(Number(v)))) return null;
  const R = 6371, dLat = rad(b.latitude - a.latitude), dLon = rad(b.longitude - a.longitude);
  const lat1 = rad(a.latitude), lat2 = rad(b.latitude);
  const h = Math.sin(dLat/2)**2 + Math.cos(lat1)*Math.cos(lat2)*Math.sin(dLon/2)**2;
  return 2 * R * Math.asin(Math.sqrt(h));
}
const rad = (d) => d * Math.PI / 180;
function AppHeader({ activeTab, setActiveTab }) {
  return <header className="topbar">
    <div className="brandNav">
      <div className="brandBlock"><div className="brand">Care<span>Trust</span></div><div className="brandSub">Facility Trust Desk</div></div>
      <nav className="tabs" aria-label="Main sections">{TABS.map((tab) => <button key={tab.id} className={`${activeTab === tab.id ? 'active' : ''} ${tab.id === 'assistant' ? 'assistantTab' : ''}`.trim()} onClick={() => setActiveTab(tab.id)}>{tab.label}</button>)}</nav>
    </div>
    <div className="callTop"><b>Digital call assistant</b><a href="tel:+18887078012">Call +1 888 707 8012</a></div>
  </header>;
}
function FilterBar({ filters, values, setters, services }) {
  const opts = (items, allLabel) => [{ value: '', label: allLabel }, ...(items || [])];
  return <section className="filterCard">
    <label><span>Country</span><select value={values.country} onChange={(e) => setters.setCountry(e.target.value)}>{opts(filters.countries, 'All countries').map((o) => <option key={o.value || o.label} value={o.value}>{o.label}</option>)}</select></label>
    <label><span>State / region</span><select value={values.state} onChange={(e) => setters.setState(e.target.value)}>{opts(filters.states, 'All states').map((o) => <option key={o.value || o.label} value={o.value}>{o.label}</option>)}</select></label>
    <label><span>City</span><select value={values.city} onChange={(e) => setters.setCity(e.target.value)}>{opts(filters.cities, 'All cities').map((o) => <option key={o.value || o.label} value={o.value}>{o.label}</option>)}</select></label>
    <label><span>Postal code</span><select value={values.pincode} onChange={(e) => setters.setPincode(e.target.value)}>{opts(filters.pincodes, 'All postal codes').map((o) => <option key={o.value || o.label} value={o.value}>{o.label}</option>)}</select></label>
    <label><span>Service</span><select value={values.service} onChange={(e) => setters.setService(e.target.value)}>{services.map((s) => <option key={s.service_id} value={s.service_id}>{s.service_label}</option>)}</select></label>
    <label><span>Radius</span><select value={values.radius} onChange={(e) => setters.setRadius(Number(e.target.value))}>{[25, 50, 100, 250, 500, 750].map((km) => <option key={km} value={km}>{km} km</option>)}</select></label>
  </section>;
}
function Metrics({ facilities, selected, radius }) {
  const verified = facilities.filter((f) => displayConfidence(f) === 'Human verified').length;
  return <div className="metricrow kpiRow" aria-label="CareTrust KPI cards">
    <div className="metric kpiCard"><small>Visible facilities</small><strong>{facilities.length}</strong></div>
    <div className="metric kpiCard"><small>Top score / 10</small><strong>{fmt(facilities[0]?.score)}</strong></div>
    <div className="metric kpiCard"><small>Human verified</small><strong>{verified}</strong></div>
    <div className="metric kpiCard"><small>Map radius</small><strong>{radius} km</strong></div>
    <div className="metric kpiCard wide"><small>Radius center</small><strong>{selected?.name || 'None'}</strong></div>
  </div>;
}
function FacilityTable({ facilities, selected, setSelected, onOpenTrust }) {
  const choose = (f) => { setSelected(f); onOpenTrust(f); };
  return <section className="card rankings"><div className="cardTitle"><h2>Ranked facilities</h2><span>Click View for specialties, procedures, evidence, and score details</span></div><table className="rank"><thead><tr><th>Rank</th><th>Facility</th><th>Location</th><th>Score</th><th>Status</th><th>Trust</th></tr></thead><tbody>{facilities.map((f, i) => <tr key={f.unique_id} className={selected?.unique_id === f.unique_id ? 'selected' : ''} onClick={() => choose(f)}><td>{i + 1}</td><td><b>{f.name}</b></td><td>{[f.city, f.state, f.pincode].filter(Boolean).join(', ')}</td><td><b>{fmt(f.score)}</b></td><td><span className={`badge ${classForConfidence(displayConfidence(f))}`}>{displayConfidence(f)}</span></td><td><button className="trustOpenBtn" onClick={(e) => { e.stopPropagation(); choose(f); }}>View</button></td></tr>)}</tbody></table>{!facilities.length && <p className="empty">No facilities match these filters. Try All states or a wider service.</p>}</section>;
}
function TrustCard({ facility, serviceLabel, onClose }) {
  if (!facility) return null;
  const raw = facility.score_breakdown || [];
  const entries = Array.isArray(raw) ? raw.map((x) => [x.label || x.key, x.score || 0, x.max_score]) : Object.entries(raw).map(([k, v]) => [k, v]);
  const sources = facility.source_urls || [facility.source_url, facility.website].filter(Boolean);
  const specialties = termList(facility.specialties, 12);
  const procedures = termList(facility.procedures, 12);
  const equipment = termList(facility.equipment, 8);
  return <div className="trustModal" role="dialog" aria-modal="true" aria-label={`Trust Card for ${facility.name}`} onClick={onClose}><aside className="card trust trustSheet" onClick={(e) => e.stopPropagation()}><button className="trustClose" aria-label="Close Trust Card" onClick={onClose}>×</button><div className="trustHero"><div><span className="eyebrow">Facility Trust Card</span><h2>{facility.name}</h2><p>{[facility.city, facility.state, facility.pincode].filter(Boolean).join(', ') || 'Location pending'}</p></div><div className="scoreBubble"><b>{fmt(facility.score)}</b><span>/10</span></div></div><div className="trustClaim"><span className={`badge ${classForConfidence(displayConfidence(facility))}`}>{displayConfidence(facility)}</span><p><b>Claim:</b> Supports {serviceLabel}.</p></div><div className="trustSection trustEvidenceLead"><EvidencePillGroup title="Specialties" items={specialties} empty="No specialty claims extracted yet." /><EvidencePillGroup title="Procedures" items={procedures} empty="No procedure claims extracted yet." />{equipment.length > 0 && <EvidencePillGroup title="Equipment / services" items={equipment} empty="" />}{facility.description && <p className="trustDescription">{facility.description.slice(0, 240)}</p>}</div><div className="trustSection"><h3>Score breakdown</h3><div className="why">{entries.slice(0, 8).map(([k, v, m]) => <div key={k}><b>{fmtCompactScore(v)}{m ? `/${fmtCompactScore(m)}` : ''}</b><span>{humanizeTerm(k)}</span></div>)}</div></div><div className="sources trustSection"><h3>Sources</h3>{sources.slice(0, 3).map((url) => <a key={url} href={url} target="_blank" rel="noreferrer">{url}</a>)}{!sources.length && <span>No source URL available yet.</span>}</div><p className="footer"><b>Uncertainty:</b> {(facility.uncertainty_flags || ['Treat extracted claims as claims to verify, not ground truth.']).join('; ')}</p></aside></div>;
}

function googleMapZoom(radius) {
  return radius <= 50 ? 10 : radius <= 150 ? 8 : radius <= 350 ? 7 : 6;
}
function googleEmbedSrc(center, radius) {
  const lat = Number(center?.latitude), lng = Number(center?.longitude);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return '';
  return `https://maps.google.com/maps?ll=${encodeURIComponent(`${lat},${lng}`)}&q=${encodeURIComponent(`${lat},${lng}`)}&z=${googleMapZoom(radius)}&t=m&output=embed`;
}
function GoogleMapView({ center, radius }) {
  const embedSrc = googleEmbedSrc(center, radius);
  if (!embedSrc) return <div className="googleMapWrap"><div className="mapOverlay"><b>Google Maps unavailable</b><span>Select a facility with latitude/longitude to load the map.</span></div></div>;
  return <div className="googleMapWrap"><iframe title={`Google map for ${center?.name || 'selected facility'}`} className="googleMapFrame" src={embedSrc} loading="lazy" referrerPolicy="no-referrer-when-downgrade" /></div>;
}

function RadiusMap({ facilities, selected, setSelected, radius, setRadius, onOpenTrust }) {
  const center = selected || facilities[0];
  const visible = useMemo(() => facilities.map((f) => ({ facility: f, distance: distanceKm(center, f) })).filter(({ facility, distance }) => distance === null || distance <= radius || facility.unique_id === center?.unique_id), [facilities, center?.unique_id, center?.latitude, center?.longitude, radius]);
  return <section className="card mapCard"><div className="cardTitle"><h2>Google Maps radius</h2><span>{visible.length} facilities inside radius</span></div><div className="radiusControl"><label>Radius: <b>{radius} km</b><input type="range" min="25" max="750" step="25" value={radius} onChange={(e) => setRadius(Number(e.target.value))} /></label></div><GoogleMapView center={center} radius={radius} /><div className="mapList">{visible.slice(0, 8).map(({ facility: f, distance }) => <button key={f.unique_id} onClick={() => { setSelected(f); onOpenTrust(f); }}><b>{f.name}</b><span>{distance?.toFixed(0) || 0} km • {f.city || f.state} • View Trust Card</span></button>)}</div></section>;
}
function VerificationForm({ facility, service, serviceLabel, onVerified }) {
  const [status, setStatus] = useState('verified'); const [notes, setNotes] = useState('Verified by phone or visit.');
  if (!facility) return null;
  const submit = async () => { const payload = { unique_id: facility.unique_id, procedure: service, status, verifier_name: 'CareTrust demo user', notes }; try { const result = await api('/api/verifications', { method: 'POST', body: JSON.stringify(payload) }); onVerified(status, result.facility); } catch (_) { onVerified(status); } };
  return <section className="card verification"><div className="cardTitle"><h2>Human verification</h2><span>{facility.name}</span></div><p>Call or visit the facility, verify {serviceLabel}, then feed confirmed facts back into ranking.</p><div className="checklist"><label><input type="checkbox" /> Service currently available</label><label><input type="checkbox" /> Equipment/facilities confirmed</label><label><input type="checkbox" /> Specialists/referral pathway confirmed</label></div><select value={status} onChange={(e) => setStatus(e.target.value)}><option value="verified">Verified</option><option value="needs_review">Needs review</option><option value="rejected">Rejected</option></select><textarea value={notes} onChange={(e) => setNotes(e.target.value)} /><button onClick={submit}>Submit verification</button></section>;
}
function AssistantPanel({ service, serviceLabel, selected, onPlayVoice }) {
  const [question, setQuestion] = useState(`Show top ${serviceLabel} facilities and explain evidence.`); const [answer, setAnswer] = useState(null);
  const ask = async () => { try { setAnswer(await api('/api/assistant/query', { method: 'POST', body: JSON.stringify({ question, procedure: service, unique_id: selected?.unique_id }) })); } catch (_) { setAnswer({ answer: 'Rankings combine evidence fields, sources, contactability, location completeness and human verification.', data: [] }); } };
  return <section className="card chartAssistant"><div className="cardTitle"><h2>Chat assistant</h2><span>Safe query templates</span></div><textarea value={question} onChange={(e) => setQuestion(e.target.value)} /><div className="assistantActions"><button onClick={ask}>Generate answer</button><button className="voiceSampleBtn" onClick={onPlayVoice}>Voice sample</button></div>{answer && <div className="assistantAnswer"><p>{answer.answer}</p><div className="bars">{(answer.data || []).slice(0, 6).map((row, i) => <div key={row.facility || row.name || i}><span>{row.facility || row.name || row.state}</span><i style={{ width: `${Math.min(100, (row.score || row.average_score || 5) * 10)}%` }} /></div>)}</div></div>}</section>;
}
function Shortlists({ selected, shortlists, onAdd }) { return <section className="card"><div className="cardTitle"><h2>Shortlists</h2><span>Planner decisions</span></div><button onClick={onAdd} disabled={!selected}>Add selected facility</button><div className="shortlistItems">{shortlists.map((x) => <div key={x.id} className="shortlistItem"><b>{x.name}</b><small>{x.meta}</small></div>)}{!shortlists.length && <p className="empty">No shortlisted facilities yet.</p>}</div></section>; }
function ServiceTable({ services }) { return <section className="card"><div className="cardTitle"><h2>Services grouped by specialty</h2><span>Derived table preview</span></div><table className="rank"><thead><tr><th>Service</th><th>Specialty group</th><th>Keywords</th></tr></thead><tbody>{services.map((s) => <tr key={s.service_id}><td>{s.service_label}</td><td>{s.specialty_group}</td><td><small>{s.keywords}</small></td></tr>)}</tbody></table></section>; }

function App() {
  const [activeTab, setActiveTab] = useState('explorer');
  const [filters, setFilters] = useState({ countries: [{ value: 'India', label: 'India' }], states: [], cities: [], pincodes: [], services: SERVICE_FALLBACK });
  const [country, setCountry] = useState('India'), [state, setState] = useState(''), [city, setCity] = useState(''), [pincode, setPincode] = useState(''), [service, setService] = useState('cardiac_surgery');
  const [facilities, setFacilities] = useState(fallbackFacilities); const [selected, setSelected] = useState(fallbackFacilities[0]); const [trustOpen, setTrustOpen] = useState(false); const [radius, setRadius] = useState(250); const [shortlists, setShortlists] = useState([]);
  const services = filters.services?.length ? filters.services : SERVICE_FALLBACK;
  const serviceDef = services.find((s) => s.service_id === service) || services[0]; const serviceLabel = serviceDef?.service_label || 'Selected service';
  useEffect(() => { api('/api/filters').then((data) => { setFilters((old) => ({ ...old, ...data })); }).catch(() => {}); }, []);
  useEffect(() => { let mounted = true; const params = new URLSearchParams({ procedure: service, limit: '100' }); if (country) params.set('country', country); if (state) params.set('state', state); if (city) params.set('city', city); if (pincode) params.set('pincode', pincode); api(`/api/facilities/top?${params}`).then((data) => { const rows = (Array.isArray(data) ? data : data.facilities || data.data || []).map(normalizeFacility); if (mounted) { setFacilities(rows); setSelected(rows[0] || null); } }).catch(() => { const rows = fallbackFacilities.map(normalizeFacility).filter((f) => (!country || f.country === country) && (!state || f.state === state) && (!city || f.city === city) && (!pincode || f.pincode === pincode)); if (mounted) { setFacilities(rows); setSelected(rows[0] || null); } }); return () => { mounted = false; }; }, [country, state, city, pincode, service]);
  useEffect(() => { const onKey = (e) => { if (e.key === 'Escape') setTrustOpen(false); }; window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey); }, []);
  const playVoice = async () => { const audio = new Audio('/api/voice/sample'); try { await audio.play(); } catch { window.open('/api/voice/sample', '_blank'); } };
  const openTrust = (facility = selected) => { if (facility) { setSelected(facility); setTrustOpen(true); } };
  const onVerified = (status, apiFacility) => { if (!selected) return; const delta = status === 'verified' ? 1.5 : status === 'rejected' ? -2 : 0.5; const updated = normalizeFacility(apiFacility || { ...selected, human_verification_status: status, human_verified: status === 'verified', score: Math.max(0, Math.min(10, Number(selected.score || 0) + delta)) }, 0); setSelected(updated); setFacilities((rows) => rows.map((f) => f.unique_id === updated.unique_id ? updated : f).sort((a, b) => b.score - a.score)); };
  const addShortlist = async () => { if (!selected) return; setShortlists((x) => [{ id: `${selected.unique_id}-${Date.now()}`, name: selected.name, meta: `${serviceLabel} • ${selected.city || selected.state || 'India'}` }, ...x]); try { await api('/api/shortlists', { method: 'POST', body: JSON.stringify({ unique_id: selected.unique_id, procedure: service, notes: `${serviceLabel} shortlist` }) }); } catch (_) {} };
  return <><AppHeader activeTab={activeTab} setActiveTab={setActiveTab} /><main className="main"><section className="hero filtersOnly"><FilterBar filters={filters} values={{ country, state, city, pincode, service, radius }} setters={{ setCountry, setState, setCity, setPincode, setService, setRadius }} services={services} /></section><Metrics facilities={facilities} selected={selected} radius={radius} />{activeTab === 'explorer' && <div className="grid single"><FacilityTable facilities={facilities} selected={selected} setSelected={setSelected} onOpenTrust={openTrust} /></div>}{activeTab === 'map' && <div className="grid single"><RadiusMap facilities={facilities} selected={selected} setSelected={setSelected} radius={radius} setRadius={setRadius} onOpenTrust={openTrust} /></div>}{activeTab === 'verification' && <div className="grid"><VerificationForm facility={selected} service={service} serviceLabel={serviceLabel} onVerified={onVerified} /><section className="card"><div className="cardTitle"><h2>Selected facility</h2><span>{selected?.name || 'None selected'}</span></div><button className="trustOpenWide" onClick={() => openTrust()} disabled={!selected}>Open Trust Card</button><button className="trustOpenWide shortlistInline" onClick={addShortlist} disabled={!selected}>Add to shortlist</button><button className="trustOpenWide shortlistInline" onClick={() => setActiveTab('shortlists')} disabled={!shortlists.length}>View shortlists</button><p className="empty">Shortlisted facilities this session: {shortlists.length}</p></section></div>}{activeTab === 'assistant' && <div className="grid"><RadiusMap facilities={facilities} selected={selected} setSelected={setSelected} radius={radius} setRadius={setRadius} onOpenTrust={openTrust} /><AssistantPanel service={service} serviceLabel={serviceLabel} selected={selected} onPlayVoice={playVoice} /></div>}{activeTab === 'shortlists' && <div className="grid"><Shortlists selected={selected} shortlists={shortlists} onAdd={addShortlist} /><ServiceTable services={services} /></div>}{trustOpen && <TrustCard facility={selected} serviceLabel={serviceLabel} onClose={() => setTrustOpen(false)} />}</main></>;
}

createRoot(document.getElementById('root')).render(<App />);
