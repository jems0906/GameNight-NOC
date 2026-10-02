import { useEffect, useMemo, useState } from 'react';
import { flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, ArrowDownRight, ArrowUpRight, Bell, BookOpen, Check, ChevronDown, CircleHelp, ClipboardList, Clock3, Command, ExternalLink, FileText, Gauge, LifeBuoy, Menu, Monitor, Network, Plus, Radio, RefreshCw, Search, Server, ShieldAlert, Siren, Wifi, X } from 'lucide-react';
import { api } from './api/client.js';

const NAV = [
  { id: 'overview', label: 'Overview', icon: Gauge },
  { id: 'infrastructure', label: 'Infrastructure', icon: Network },
  { id: 'alerts', label: 'Alert queue', icon: Bell },
  { id: 'incidents', label: 'Incidents', icon: Siren },
  { id: 'vendors', label: 'Vendor tickets', icon: LifeBuoy },
  { id: 'cisco', label: 'Cisco toolkit', icon: Command },
  { id: 'handoffs', label: 'Shift handoffs', icon: ClipboardList },
  { id: 'stakeholder', label: 'Stakeholder update', icon: FileText },
];
const REFRESH_MS = 45000;
const STATUS_ORDER = { new: 'acknowledged', acknowledged: 'investigating', investigating: 'resolved', 'vendor engaged': 'resolved' };
const CHART_DATA = [
  { time: '21:00', latency: 18, loss: 0.1 }, { time: '22:00', latency: 21, loss: 0.2 },
  { time: '23:00', latency: 19, loss: 0.1 }, { time: '00:00', latency: 26, loss: 0.6 },
  { time: '01:00', latency: 24, loss: 0.3 }, { time: '02:00', latency: 42, loss: 1.8 },
  { time: '03:00', latency: 31, loss: 0.5 },
];
const EMPTY = { overview: {}, infrastructure: [], alerts: [], incidents: [], vendors: [], commands: [], handoffs: [], handoffTrends: { count: 0, snapshots: [] }, stakeholder: { updates: [] }, gameDay: {} };
const titleCase = (value = '') => value.replaceAll('_', ' ').replace(/\b\w/g, (character) => character.toUpperCase());
const formatTime = (value) => value ? new Intl.DateTimeFormat('en', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }).format(new Date(value)) : '—';

function App() {
  const [page, setPage] = useState('overview');
  const [data, setData] = useState(EMPTY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [modal, setModal] = useState('');
  const [mobileNav, setMobileNav] = useState(false);
  const [toast, setToast] = useState('');

  async function refresh() {
    try {
      const [overview, infrastructure, alerts, incidents, vendors, commands, handoffs, handoffTrends, stakeholder, gameDay] = await Promise.all([
        api.get('/dashboards/overview'), api.get('/infrastructure'), api.get('/alerts'), api.get('/incidents'),
        api.get('/vendor-tickets'), api.get('/cisco/commands'), api.get('/handoffs'), api.get('/handoffs/trends'), api.get('/reports/stakeholder-update'), api.get('/dashboards/game-day'),
      ]);
      setData({ overview, infrastructure, alerts, incidents, vendors, commands, handoffs, handoffTrends, stakeholder, gameDay });
      setError('');
    } catch (reason) {
      setError(reason.message || 'Unable to reach the NOC API.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = window.setTimeout(() => setToast(''), 3200);
    return () => window.clearTimeout(timer);
  }, [toast]);

  async function mutate(action, success) {
    try {
      await action();
      await refresh();
      setToast(success);
      setModal('');
    } catch (reason) {
      setToast(reason.message || 'Action failed');
    }
  }

  const activePage = NAV.find((item) => item.id === page);
  const pageTitle = activePage?.label || 'Overview';

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}>
        <a className="brand" href="#overview" onClick={() => setPage('overview')}>
          <span className="brand-mark"><Activity size={20} strokeWidth={2.5} /></span>
          <span><strong>GAME<span>NIGHT</span></strong><small>VENUE OPERATIONS</small></span>
        </a>
        <div className="venue-switcher"><span className="venue-crest">LA</span><span><strong>Lakeshore Arena</strong><small>Harbor City · Central</small></span><ChevronDown size={15} /></div>
        <div className="nav-label">OPERATIONS</div>
        <nav className="primary-nav" aria-label="Primary navigation">
          {NAV.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${page === id ? 'active' : ''}`} onClick={() => { setPage(id); setMobileNav(false); }}><Icon size={17} /><span>{label}</span>{id === 'alerts' && data.overview.alerts_active > 0 && <b className="nav-count">{data.overview.alerts_active}</b>}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <div className="on-call"><span className="on-call-dot" /><div><strong>Night operations</strong><small>3 operators on shift</small></div><span className="avatar">MR</span></div>
          <div className="sidebar-foot"><span>Build 1.0.0</span><span>API {error ? 'offline' : 'connected'}</span></div>
        </div>
      </aside>
      {mobileNav && <button aria-label="Close navigation" className="mobile-scrim" onClick={() => setMobileNav(false)} />}

      <main className="main-area">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label="Open navigation" onClick={() => setMobileNav(true)}><Menu size={19} /></button>
          <div className="breadcrumb"><span>Operations</span><span className="slash">/</span><strong>{pageTitle}</strong></div>
          <div className="topbar-right"><div className="live-state"><span className="live-dot" />LIVE MONITORING</div><span className="topbar-divider" /><span className="utc-clock">{new Intl.DateTimeFormat('en', { timeZone: 'UTC', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }).format(new Date())} UTC</span><button className="icon-button" title="Refresh data" aria-label="Refresh data" onClick={refresh}><RefreshCw size={16} /></button></div>
        </header>
        {error && <div className="connection-banner"><ShieldAlert size={16} /> API connection unavailable: {error} <button onClick={refresh}>Retry</button></div>}
        <div className="page-content">
          {loading && !data.infrastructure.length ? <div className="loading-state"><span className="spinner" />Connecting to venue systems…</div> : null}
          {page === 'overview' && <Overview data={data} setPage={setPage} />}
          {page === 'infrastructure' && <Infrastructure data={data} query={query} setQuery={setQuery} />}
          {page === 'alerts' && <Alerts data={data} mutate={mutate} />}
          {page === 'incidents' && <Incidents data={data} mutate={mutate} onCreate={() => setModal('incident')} />}
          {page === 'vendors' && <Vendors data={data} mutate={mutate} onCreate={() => setModal('vendor')} />}
          {page === 'cisco' && <CiscoToolkit commands={data.commands} />}
          {page === 'handoffs' && <Handoffs data={data} mutate={mutate} />}
          {page === 'stakeholder' && <Stakeholder data={data} />}
        </div>
      </main>
      {modal === 'incident' && <IncidentModal onClose={() => setModal('')} onSubmit={(body) => mutate(() => api.post('/incidents', body), 'Incident created')} />}
      {modal === 'vendor' && <VendorModal onClose={() => setModal('')} onSubmit={(body) => mutate(() => api.post('/vendor-tickets', body), 'Vendor ticket added')} />}
      {toast && <div className="toast"><Check size={16} />{toast}</div>}
    </div>
  );
}

function PageHeading({ eyebrow, title, description, actions }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{actions && <div className="heading-actions">{actions}</div>}</div>;
}

function StatusPill({ status }) {
  const kind = ['up', 'resolved', 'healthy', 'current'].includes(status?.toLowerCase()) ? 'good' : ['critical', 'failed', 'down'].includes(status?.toLowerCase()) ? 'critical' : ['warning', 'investigating', 'vendor engaged'].includes(status?.toLowerCase()) ? 'warning' : 'neutral';
  return <span className={`status-pill ${kind}`}><i />{titleCase(status || 'unknown')}</span>;
}

function Overview({ data, setPage }) {
  const { overview: stats, infrastructure, alerts, incidents, gameDay } = data;
  const hotAlerts = alerts.filter((item) => item.status !== 'resolved').slice(0, 4);
  const criticalAssets = infrastructure.filter((item) => item.status !== 'up').slice(0, 4);
  return <>
    <div className="event-strip"><div className="event-mark">HC</div><div className="event-info"><span className="eyebrow">EVENT NIGHT · LAKESHORE ARENA</span><strong>Harbor City <span>vs</span> Lakeview</strong></div><div className="event-meta"><span><i className="event-dot" />{gameDay.event_status || 'Pre-game operations'}</span><small>Doors 19:00 local · Event ops active</small></div><div className="event-readiness"><strong>{gameDay.network_ready_pct ?? 0}%</strong><span>NETWORK READY</span></div></div>
    <PageHeading eyebrow="FRIDAY · OVERNIGHT SHIFT" title="Good evening, Morgan" description="Venue systems are under observation. Here's the operational picture." actions={<button className="button button-secondary" onClick={() => setPage('handoffs')}><ClipboardList size={16} /> Prepare handoff</button>} />
    <section className="metric-grid" aria-label="Operations summary">
      <Metric label="Systems online" value={`${stats.devices_up ?? 0}/${stats.devices_total ?? 0}`} icon={Monitor} note={`${stats.devices_degraded ?? 0} degraded`} trend="steady" />
      <Metric label="Active alerts" value={stats.alerts_active ?? 0} icon={Bell} note={`${stats.alerts_critical ?? 0} critical`} tone="coral" trend="attention" />
      <Metric label="Open incidents" value={stats.incidents_active ?? 0} icon={Siren} note="Across venue operations" trend="steady" />
      <Metric label="Vendor tickets" value={stats.vendors_open ?? 0} icon={LifeBuoy} note="Awaiting provider updates" trend="steady" />
    </section>
    <div className="dashboard-grid">
      <section className="panel network-panel"><div className="panel-heading"><div><span className="eyebrow">NETWORK PERFORMANCE</span><h2>Core circuit latency</h2></div><span className="chart-legend"><i />Latency <small>· 7 hours</small></span></div><div className="chart-area"><ResponsiveContainer width="100%" height="100%"><AreaChart data={CHART_DATA} margin={{ top: 12, right: 8, left: -18, bottom: 0 }}><defs><linearGradient id="latencyFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3ba987" stopOpacity={0.2} /><stop offset="100%" stopColor="#3ba987" stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="#e9eeeb" vertical={false} /><XAxis dataKey="time" tick={{ fill: '#84918a', fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis tick={{ fill: '#84918a', fontSize: 11 }} axisLine={false} tickLine={false} unit=" ms" /><Tooltip contentStyle={{ borderRadius: 6, borderColor: '#e2e9e5', fontSize: 12 }} /><Area type="monotone" dataKey="latency" name="Latency" stroke="#16836a" strokeWidth={2.5} fill="url(#latencyFill)" activeDot={{ r: 4 }} /></AreaChart></ResponsiveContainer></div><div className="chart-footer"><span><b className="chart-current">42 ms</b> primary circuit · current</span><span className="chart-change"><ArrowUpRight size={14} /> 12 ms vs. baseline</span></div></section>
      <section className="panel event-health"><div className="panel-heading"><div><span className="eyebrow">VENUE READINESS</span><h2>Systems to watch</h2></div><button className="text-button" onClick={() => setPage('infrastructure')}>All systems <ArrowUpRight size={14} /></button></div><div className="health-list">{criticalAssets.map((item) => <div className="health-row" key={item.id}><span className={`health-icon ${item.status}`}><AssetIcon category={item.category} /></span><div className="health-name"><strong>{item.name}</strong><small>{item.location}</small></div><StatusPill status={item.status} /></div>)}{criticalAssets.length === 0 && <EmptyState text="All monitored systems are healthy." />}</div></section>
      <section className="panel alert-panel"><div className="panel-heading"><div><span className="eyebrow">NEEDS ATTENTION</span><h2>Latest alerts</h2></div><button className="text-button" onClick={() => setPage('alerts')}>Alert queue <ArrowUpRight size={14} /></button></div><div className="alert-list">{hotAlerts.map((item) => <div className="alert-row" key={item.id}><span className={`severity-mark ${item.severity}`} /><div className="alert-content"><strong>{item.title}</strong><span>{item.source} <i>·</i> {formatTime(item.created_at)} UTC</span></div><StatusPill status={item.severity} /></div>)}{hotAlerts.length === 0 && <EmptyState text="No active alerts." />}</div></section>
      <section className="panel incident-panel"><div className="panel-heading"><div><span className="eyebrow">ACTIVE WORK</span><h2>Incident watch</h2></div><button className="text-button" onClick={() => setPage('incidents')}>All incidents <ArrowUpRight size={14} /></button></div><div className="incident-list">{incidents.filter((item) => !['resolved', 'handoff complete'].includes(item.status)).slice(0, 3).map((item) => <div className="incident-row" key={item.id}><span className={`priority-flag ${item.priority?.toLowerCase()}`}>{item.priority}</span><div className="incident-content"><strong>{item.title}</strong><span>{item.number} <i>·</i> {item.owner}</span></div><StatusPill status={item.status} /></div>)}</div></section>
    </div>
    <footer className="data-foot"><span><span className="live-dot" /> Monitoring heartbeat nominal</span><span>Updated {formatTime(stats.updated_at)} UTC <i>·</i> Auto-refresh 45 sec</span></footer>
  </>;
}

function Metric({ label, value, icon: Icon, note, tone, trend }) {
  return <div className="metric-card"><div className="metric-top"><span>{label}</span><span className={`metric-icon ${tone || ''}`}><Icon size={17} /></span></div><div className="metric-value">{value}</div><div className="metric-note"><span className={trend === 'attention' ? 'note-attention' : ''}>{trend === 'attention' ? <ArrowDownRight size={13} /> : <ArrowUpRight size={13} />}{note}</span><span className="metric-source">LAST 15 MIN</span></div></div>;
}

function AssetIcon({ category }) {
  if (category?.includes('Wireless')) return <Wifi size={15} />;
  if (category?.includes('Circuit') || category?.includes('Switch')) return <Network size={15} />;
  if (category?.includes('Server') || category?.includes('VM')) return <Server size={15} />;
  if (category?.includes('Backup')) return <Clock3 size={15} />;
  return <Activity size={15} />;
}

function Infrastructure({ data, query, setQuery }) {
  const [category, setCategory] = useState('All assets');
  const categories = ['All assets', ...new Set(data.infrastructure.map((item) => item.category))];
  const filtered = useMemo(() => data.infrastructure.filter((item) => (category === 'All assets' || item.category === category) && `${item.name} ${item.category} ${item.location} ${item.address}`.toLowerCase().includes(query.toLowerCase())), [data.infrastructure, category, query]);
  const columns = useMemo(() => [
    { accessorKey: 'name', header: 'ASSET', cell: ({ row }) => <div className="asset-cell"><span className="asset-icon"><AssetIcon category={row.original.category} /></span><span><strong>{row.original.name}</strong><small>{row.original.category} · {row.original.address}</small></span></div> },
    { accessorKey: 'location', header: 'LOCATION' },
    { id: 'telemetry', header: 'TELEMETRY', cell: ({ row }) => <MetricSummary metrics={row.original.metrics} /> },
    { accessorKey: 'status', header: 'STATUS', cell: ({ getValue }) => <StatusPill status={getValue()} /> },
    { accessorKey: 'last_check', header: 'LAST CHECK', cell: ({ getValue }) => <span className="mono-text">{formatTime(getValue())} UTC</span> },
  ], []);
  const table = useReactTable({ data: filtered, columns, getCoreRowModel: getCoreRowModel() });
  return <><PageHeading eyebrow={`ASSET INVENTORY · ${data.infrastructure.length} MONITORED`} title="Infrastructure" description="Health and telemetry across venue systems." actions={<div className="search-field"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Find an asset…" /></div>} /><div className="filter-tabs">{categories.map((item) => <button key={item} className={category === item ? 'selected' : ''} onClick={() => setCategory(item)}>{item}</button>)}</div><div className="panel table-panel"><div className="table-wrap"><table><thead>{table.getHeaderGroups().map((group) => <tr key={group.id}>{group.headers.map((header) => <th key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead><tbody>{table.getRowModel().rows.map((row) => <tr key={row.id}>{row.getVisibleCells().map((cell) => <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody></table></div><div className="table-foot">Showing {filtered.length} of {data.infrastructure.length} assets <span>Source: simulated SolarWinds NPM inventory</span></div></div></>;
}

function MetricSummary({ metrics = {} }) {
  const preferred = ['latency_ms', 'packet_loss_pct', 'cpu_pct', 'memory_pct', 'disk_pct', 'clients', 'ports_up', 'signal_dbm', 'result', 'replication', 'power_state'];
  const key = preferred.find((candidate) => metrics[candidate] !== undefined);
  if (!key) return <span className="muted-text">No telemetry</span>;
  const labels = { latency_ms: 'Latency', packet_loss_pct: 'Packet loss', cpu_pct: 'CPU', memory_pct: 'Memory', disk_pct: 'Disk', clients: 'Clients', ports_up: 'Ports up', signal_dbm: 'Signal', result: 'Last run', replication: 'Replication', power_state: 'Power' };
  const units = { latency_ms: ' ms', packet_loss_pct: '%', cpu_pct: '%', memory_pct: '%', disk_pct: '%' };
  return <span className="telemetry-value">{labels[key]} <b>{metrics[key]}{units[key] || ''}</b></span>;
}

function Alerts({ data, mutate }) {
  const [filter, setFilter] = useState('Active');
  const visible = data.alerts.filter((item) => filter === 'All' || (filter === 'Active' ? item.status !== 'resolved' : item.severity === filter.toLowerCase()));
  const next = (alert) => STATUS_ORDER[alert.status] || 'resolved';
  return <><PageHeading eyebrow="MONITORING · SOLARWINDS MODEL" title="Alert queue" description="Acknowledge, investigate, and resolve conditions across the venue." actions={<span className="queue-count"><span className="live-dot" />{data.alerts.filter((item) => item.status !== 'resolved').length} active</span>} /><div className="filter-tabs">{['Active', 'All', 'Critical', 'Warning', 'Info'].map((item) => <button className={filter === item ? 'selected' : ''} key={item} onClick={() => setFilter(item)}>{item}</button>)}</div><div className="panel table-panel"><div className="table-wrap"><table><thead><tr><th>SEVERITY</th><th>ALERT</th><th>SOURCE</th><th>CREATED</th><th>LIFECYCLE</th><th /></tr></thead><tbody>{visible.map((item) => <tr key={item.id}><td><span className={`severity-label ${item.severity}`}><i />{titleCase(item.severity)}</span></td><td><strong>{item.title}</strong><small className="cell-subtext">{item.detail}</small></td><td className="mono-text">{item.source}</td><td className="mono-text">{formatTime(item.created_at)} UTC</td><td><StatusPill status={item.status} /></td><td><div className="alert-actions"><button className="small-action" disabled={item.status === 'resolved'} onClick={() => mutate(() => api.patch(`/alerts/${item.id}`, { status: next(item) }), `Alert moved to ${next(item)}`)}>{item.status === 'resolved' ? 'Resolved' : next(item) === 'resolved' ? 'Resolve' : titleCase(next(item))}</button><button className="small-action" onClick={() => mutate(() => api.post(`/alerts/${item.id}/incident`, {}), 'Incident created from alert')}>Create incident</button></div></td></tr>)}</tbody></table>{visible.length === 0 && <EmptyState text="No alerts in this view." />}</div><div className="table-foot">Alert lifecycle: new → acknowledged → investigating → resolved <span>Rule evaluation interval: 60 sec</span></div></div></>;
}

function Incidents({ data, mutate, onCreate }) {
  const [selected, setSelected] = useState(null);
  const visible = selected ? data.incidents.filter((item) => item.id === selected) : data.incidents;
  return <><PageHeading eyebrow="INCIDENT RESPONSE · PRIORITY MATRIX" title="Incidents" description="Document impact, coordinate response, and preserve the troubleshooting timeline." actions={<button className="button button-primary" onClick={onCreate}><Plus size={16} /> New incident</button>} /><div className="incident-summary"><span><b>{data.incidents.filter((item) => !['resolved', 'handoff complete'].includes(item.status)).length}</b> active incidents</span><span className="priority-summary"><i className="p1">P1</i> Immediate <i className="p2">P2</i> High <i className="p3">P3</i> Standard <i className="p4">P4</i> Low</span><label>Sort <select value={selected || ''} onChange={(event) => setSelected(event.target.value ? Number(event.target.value) : null)}><option value="">All incidents</option>{data.incidents.map((item) => <option value={item.id} key={item.id}>{item.number}</option>)}</select></label></div><div className="incident-cards">{visible.map((item) => <IncidentCard key={item.id} incident={item} mutate={mutate} />)}</div>{visible.length === 0 && <EmptyState text="No incidents recorded." />}</>;
}

function IncidentCard({ incident, mutate }) {
  const [action, setAction] = useState('');
  const [resolution, setResolution] = useState('');
  const nextStatus = STATUS_ORDER[incident.status] || (incident.status === 'resolved' ? 'handoff complete' : 'investigating');
  const saveAction = () => {
    if (!action.trim()) return;
    mutate(() => api.patch(`/incidents/${incident.id}`, { action: action.trim() }), 'Timeline updated');
    setAction('');
  };
  const advance = () => mutate(() => api.patch(`/incidents/${incident.id}`, {
    status: nextStatus,
    ...(nextStatus === 'resolved' ? { resolution: resolution.trim() || 'Resolved by operations team.' } : {}),
  }), `Incident moved to ${nextStatus}`);

  return <article className="panel incident-card">
    <div className="incident-card-top">
      <span className={`priority-flag ${incident.priority?.toLowerCase()}`}>{incident.priority}</span>
      <span className="incident-number">{incident.number} <i>·</i> {incident.category}</span>
      <StatusPill status={incident.status} />
      <span className="incident-owner">Owner: <b>{incident.owner}</b></span>
    </div>
    <h2>{incident.title}</h2>
    <p className="business-impact"><span>BUSINESS IMPACT</span>{incident.business_impact || 'Impact assessment pending.'}</p>
    <div className="incident-meta">
      <span>Impact <b>{titleCase(incident.impact)}</b></span>
      <span>Urgency <b>{titleCase(incident.urgency)}</b></span>
      <span>Opened <b>{formatTime(incident.created_at)} UTC</b></span>
    </div>
    <div className="timeline">
      <span className="timeline-label">LATEST ACTIVITY</span>
      {(incident.timeline || []).slice(-3).reverse().map((entry, index) => <div className="timeline-entry" key={`${entry.at}-${index}`}>
        <span className="timeline-dot" /><span>{entry.action}</span><time>{formatTime(entry.at)} UTC</time>
      </div>)}
    </div>
    {nextStatus === 'resolved' && incident.status !== 'resolved' && <label className="resolution-entry">RESOLUTION NOTES
      <input value={resolution} onChange={(event) => setResolution(event.target.value)} placeholder="Record the fix and verification…" />
    </label>}
    <div className="incident-actions">
      <input aria-label="Add troubleshooting note" value={action} onChange={(event) => setAction(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && saveAction()} placeholder="Add a troubleshooting step…" />
      <button className="button button-secondary" disabled={!action.trim()} onClick={saveAction}>Log step</button>
      {incident.status !== 'handoff complete' && <button className="button button-primary" onClick={advance}>{titleCase(nextStatus)}</button>}
    </div>
  </article>;
}

function Vendors({ data, mutate, onCreate }) {
  const [updates, setUpdates] = useState({});
  const saveUpdate = (event, item) => {
    event.preventDefault();
    const value = updates[item.id]?.trim();
    if (!value) return;
    mutate(() => api.patch(`/vendor-tickets/${item.id}`, { last_update: value }), 'Provider update saved');
    setUpdates((current) => ({ ...current, [item.id]: '' }));
  };

  return <>
    <PageHeading eyebrow="EXTERNAL PROVIDERS · SLA WATCH" title="Vendor coordination" description="Track circuit-provider escalations, response targets, and latest updates." actions={<button className="button button-primary" onClick={onCreate}><Plus size={16} /> Add ticket</button>} />
    <div className="vendor-summary">
      <div><span>OPEN PROVIDER CASES</span><b>{data.vendors.filter((item) => item.status !== 'resolved').length}</b></div>
      <div><span>PROVIDERS ENGAGED</span><b>{new Set(data.vendors.filter((item) => item.status !== 'resolved').map((item) => item.provider)).size}</b></div>
      <div><span>ESCALATIONS WITH UPDATES</span><b>{data.vendors.filter((item) => item.last_update).length}</b></div>
    </div>
    <div className="vendor-list">{data.vendors.map((item) => <article className="panel vendor-card" key={item.id}>
      <div className="vendor-provider"><span className="provider-logo">{item.provider.slice(0, 2).toUpperCase()}</span><div><strong>{item.provider}</strong><small>{item.circuit_id}</small></div></div>
      <div className="vendor-ticket"><span>PROVIDER TICKET</span><b>{item.ticket_number}</b></div>
      <div className="vendor-sla"><span>SLA TARGET</span><b>{item.sla_target || 'Not set'}</b></div>
      <StatusPill status={item.status} />
      <div className="vendor-update">
        <span>LATEST PROVIDER UPDATE · {formatTime(item.updated_at)} UTC</span>
        <p>{item.last_update || 'No provider update logged.'}</p>
        {!!item.history?.length && <div className="vendor-history">{item.history.slice(-3).reverse().map((entry, index) => <small key={`${entry.at}-${index}`}><b>{titleCase(entry.status)}</b> · {entry.update || 'Status changed'} · {formatTime(entry.at)} UTC</small>)}</div>}
        <form className="vendor-update-form" onSubmit={(event) => saveUpdate(event, item)}>
          <input aria-label={`Log provider update for ${item.ticket_number}`} value={updates[item.id] || ''} onChange={(event) => setUpdates((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Log a provider update…" />
          <button className="icon-button" type="submit" title="Save provider update" aria-label="Save provider update" disabled={!updates[item.id]?.trim()}><Check size={15} /></button>
        </form>
      </div>
      <div className="vendor-contact"><LifeBuoy size={14} />{item.contact || 'Contact not recorded'}</div>
      <div className="vendor-controls">
        <select value={item.status} aria-label={`Update status for ${item.ticket_number}`} onChange={(event) => mutate(() => api.patch(`/vendor-tickets/${item.id}`, { status: event.target.value }), 'Vendor ticket updated')}><option value="open">Open</option><option value="awaiting vendor">Awaiting vendor</option><option value="vendor investigating">Vendor investigating</option><option value="resolved">Resolved</option></select>
        <button className="icon-button" title="Mark resolved" aria-label="Mark resolved" onClick={() => mutate(() => api.patch(`/vendor-tickets/${item.id}`, { status: 'resolved' }), 'Vendor ticket resolved')}><Check size={16} /></button>
      </div>
    </article>)}</div>
  </>;
}

function CiscoToolkit({ commands }) {
  const [output, setOutput] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [busy, setBusy] = useState(false);
  async function analyze() {
    if (!output.trim()) return;
    setBusy(true);
    try { setAnalysis(await api.post('/cisco/analyze', { output })); }
    catch (error) { setAnalysis({ error: error.message }); }
    finally { setBusy(false); }
  }
  return <><PageHeading eyebrow="LAYER 1 / LAYER 2 · CISCO IOS" title="Cisco toolkit" description="Command reference and first-pass diagnostic prompts for switch troubleshooting." /><div className="cisco-grid"><section className="panel command-panel"><div className="panel-heading"><div><span className="eyebrow">FIELD REFERENCE</span><h2>Common commands</h2></div><BookOpen size={18} className="heading-icon" /></div><div className="command-list">{commands.map((item) => <div className="command-row" key={item.command}><div className="command-meta"><span className="layer-tag">{item.layer}</span><a href={item.runbook} target="_blank" rel="noreferrer" title="Open Cisco reference">Runbook <ExternalLink size={12} /></a></div><code>{item.command}</code><p>{item.purpose}</p></div>)}</div></section><section className="panel analyzer-panel"><div className="panel-heading"><div><span className="eyebrow">OUTPUT TRIAGE</span><h2>Paste CLI output</h2></div><CircleHelp size={18} className="heading-icon" /></div><label htmlFor="cli-output" className="field-label">SIMULATED OR REDACTED SWITCH OUTPUT</label><textarea id="cli-output" className="cli-input" value={output} onChange={(event) => setOutput(event.target.value)} placeholder={'Switch# show interfaces counters errors\nPort        Align-Err  FCS-Err  Xmit-Err  Rcv-Err\nGi1/0/1     0          12       0         4'} /><button className="button button-primary analyze-button" disabled={!output.trim() || busy} onClick={analyze}><Command size={15} />{busy ? 'Analyzing…' : 'Analyze output'}</button>{analysis && <div className="analysis-result"><div className="analysis-heading"><ShieldAlert size={16} /> Diagnostic suggestions</div>{analysis.error ? <p>{analysis.error}</p> : <>{analysis.findings.map((item, index) => <div className="finding" key={index}><strong>{item.finding}</strong><p>{item.next}</p></div>)}<p className="disclaimer">{analysis.disclaimer}</p></>}</div>}</section></div></>;
}

function Handoffs({ data, mutate }) {
  const [operator, setOperator] = useState('Morgan Rivera');
  const [selected, setSelected] = useState(null);
  const [handoffQuery, setHandoffQuery] = useState('');
  const filteredHandoffs = data.handoffs.filter((item) => `${item.operator} ${item.shift} ${item.created_at}`.toLowerCase().includes(handoffQuery.toLowerCase()));
  const trendSnapshots = data.handoffTrends.snapshots.slice(-5).reverse();
  const trendMax = Math.max(1, ...trendSnapshots.map((item) => item.open_incidents + item.active_alerts + item.degraded_systems));
  const active = selected ? data.handoffs.find((item) => item.id === selected) : filteredHandoffs[0];
  const save = () => mutate(() => api.post('/handoffs', { operator, shift: 'Overnight' }), 'Shift handoff generated and saved');
  return <>
    <PageHeading eyebrow="SHIFT CHANGE · OPERATIONAL CONTINUITY" title="Shift handoffs" description="Generate a concise, persisted report for the incoming operations team." actions={<div className="handoff-actions"><input value={operator} aria-label="Shift operator" onChange={(event) => setOperator(event.target.value)} /><button className="button button-primary" onClick={save}><ClipboardList size={16} /> Generate handoff</button></div>} />
    <div className="handoff-layout">
      <aside className="panel handoff-history">
        <div className="panel-heading"><div><span className="eyebrow">ARCHIVE</span><h2>Previous handoffs</h2></div></div>
        <div className="handoff-search"><Search size={14} /><input value={handoffQuery} onChange={(event) => setHandoffQuery(event.target.value)} placeholder="Search archive…" /></div>
        {!!trendSnapshots.length && <div className="handoff-trends"><span className="eyebrow">RECENT SHIFT TRENDS</span>{trendSnapshots.map((item) => {
          const load = item.open_incidents + item.active_alerts + item.degraded_systems;
          return <div className="handoff-trend" key={item.id}>
            <div><b>{item.operator}</b><small>{item.open_incidents} incidents · {item.critical_alerts} critical · {item.degraded_systems} degraded</small></div>
            <span className="trend-bar"><i style={{ width: `${Math.max(5, load / trendMax * 100)}%` }} /></span>
          </div>;
        })}</div>}
        {filteredHandoffs.map((item) => <button key={item.id} className={`handoff-history-item ${active?.id === item.id ? 'selected' : ''}`} onClick={() => setSelected(item.id)}><span>{item.operator}</span><small>{formatTime(item.created_at)} UTC · {new Date(item.created_at).toLocaleDateString()}</small><b>{item.shift}</b></button>)}
        {!filteredHandoffs.length && <EmptyState text={data.handoffs.length ? 'No matching handoffs.' : 'No handoffs saved yet.'} />}
      </aside>
      <section className="panel report-panel">{active ? <HandoffReport handoff={active} /> : <div className="empty-report"><ClipboardList size={30} /><h2>Ready for shift change</h2><p>Generate a handoff to capture open work, active alerts, vendor updates, and follow-up actions.</p></div>}</section>
    </div>
  </>;
}

function HandoffReport({ handoff }) {
  const report = handoff.report || {};
  return <><div className="report-heading"><div><span className="eyebrow">{handoff.shift.toUpperCase()} SHIFT REPORT</span><h2>Operations handoff</h2><p>Prepared by {handoff.operator} · {new Date(handoff.created_at).toLocaleString()}</p></div><button className="icon-button print-button" title="Print handoff" aria-label="Print handoff" onClick={() => window.print()}><FileText size={17} /></button></div><div className="report-health"><span className="report-health-mark"><Activity size={17} /></span><div><b>{report.infrastructure_summary?.total || 0} systems monitored</b><small>{report.infrastructure_summary?.degraded?.length ? `Degraded: ${report.infrastructure_summary.degraded.join(', ')}` : 'All systems currently healthy'}</small></div></div><ReportSection title="Open incidents" items={report.open_incidents} empty="No open incidents." render={(item) => <><b>{item.number} · {item.title}</b><span>{item.priority} · {titleCase(item.status)} · Last action: {item.last_action}</span></>} /><ReportSection title="Active alerts" items={report.active_alerts} empty="No active alerts." render={(item) => <><b>{item.title}</b><span>{titleCase(item.severity)} · {item.source}</span></>} /><ReportSection title="Open vendor tickets" items={report.open_vendor_tickets} empty="No open provider cases." render={(item) => <><b>{item.provider} · {item.ticket_number}</b><span>{titleCase(item.status)} · {item.last_update || 'No recent update'}</span></>} /><ReportSection title="Resolved this shift" items={report.resolved_this_shift} empty="No incidents resolved this shift." render={(item) => <><b>{item.number} · {item.title}</b><span>{item.resolution || 'Resolution not recorded.'}</span></>} /><ReportSection title="Follow-up for day shift" items={(report.follow_up_actions || []).map((action, index) => ({ id: index, action }))} empty="No follow-up actions." render={(item) => <b>{item.action}</b>} /></>;
}

function ReportSection({ title, items = [], empty, render }) {
  return <section className="report-section"><h3>{title}<span>{items.length}</span></h3>{items.length ? <div className="report-items">{items.map((item, index) => <div className="report-item" key={item.id || item.number || index}>{render(item)}</div>)}</div> : <p className="report-empty">{empty}</p>}</section>;
}

function Stakeholder({ data }) {
  const [copied, setCopied] = useState(false);
  const text = data.stakeholder.updates.map((item) => `${item.incident}: ${item.issue}. Impact: ${item.impact || 'Assessment in progress'}. Current status: ${item.status}. ${item.what_were_doing} Estimated resolution: ${item.estimated_resolution}.`).join('\n\n');
  async function copy() {
    await navigator.clipboard.writeText(text || 'No active operational incidents.');
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }
  return <><PageHeading eyebrow="BUSINESS COMMUNICATION · PLAIN LANGUAGE" title="Stakeholder update" description="A concise, audience-ready status summary generated from active incidents." actions={<button className="button button-secondary" onClick={copy}><ClipboardList size={16} />{copied ? 'Copied' : 'Copy update'}</button>} /><div className="stakeholder-layout"><section className="panel stakeholder-intro"><span className="stakeholder-kicker"><Radio size={15} /> OPERATIONAL STATUS</span><h2>Venue technology update</h2><p>Generated {new Date(data.stakeholder.generated_at || Date.now()).toLocaleString()}</p><div className="stakeholder-callout"><span className="callout-dot" /><span>{data.stakeholder.updates.length ? `${data.stakeholder.updates.length} issue${data.stakeholder.updates.length === 1 ? '' : 's'} currently being managed` : 'No active incidents are affecting venue operations.'}</span></div></section><section className="stakeholder-updates">{data.stakeholder.updates.map((item) => <article className="panel stakeholder-card" key={item.incident}><div className="stakeholder-card-top"><b>{item.incident}</b><StatusPill status={item.status} /></div><h3>{item.issue}</h3><div className="stakeholder-field"><span>BUSINESS IMPACT</span><p>{item.impact || 'Impact assessment is in progress.'}</p></div><div className="stakeholder-field"><span>WHAT WE'RE DOING</span><p>{item.what_were_doing}</p></div><div className="stakeholder-field estimate"><Clock3 size={14} /><span>ESTIMATED RESOLUTION</span><b>{item.estimated_resolution}</b></div></article>)}{!data.stakeholder.updates.length && <div className="panel empty-report"><Check size={28} /><h2>Operations stable</h2><p>No active incidents to communicate at this time.</p></div>}</section></div></>;
}

function IncidentModal({ onClose, onSubmit }) {
  const [form, setForm] = useState({ title: '', category: 'Infrastructure', impact: 'department', urgency: 'normal', business_impact: '', owner: 'Morgan Rivera' });
  const change = (key) => (event) => setForm((value) => ({ ...value, [key]: event.target.value }));
  const submit = (event) => { event.preventDefault(); onSubmit(form); };
  return <Modal title="Create incident" onClose={onClose}><form onSubmit={submit} className="modal-form"><label>Incident title<input required minLength="3" value={form.title} onChange={change('title')} placeholder="e.g. Concourse access switches unreachable" /></label><div className="form-row"><label>Impact<select value={form.impact} onChange={change('impact')}><option value="individual">Individual</option><option value="department">Department</option><option value="multiple_departments">Multiple departments</option><option value="venue_wide">Venue-wide</option></select></label><label>Urgency<select value={form.urgency} onChange={change('urgency')}><option value="low">Low</option><option value="normal">Normal</option><option value="high">High</option><option value="critical">Critical</option></select></label></div><label>Business impact<textarea required value={form.business_impact} onChange={change('business_impact')} placeholder="What venue or business function is affected?" /></label><label>Assigned owner<input value={form.owner} onChange={change('owner')} /></label><p className="modal-hint">Priority is calculated automatically from impact and urgency.</p><div className="modal-actions"><button type="button" className="button button-secondary" onClick={onClose}>Cancel</button><button className="button button-primary" type="submit"><Plus size={15} /> Create incident</button></div></form></Modal>;
}

function VendorModal({ onClose, onSubmit }) {
  const [form, setForm] = useState({ provider: '', circuit_id: '', ticket_number: '', contact: '', sla_target: '', last_update: '', status: 'open' });
  const change = (key) => (event) => setForm((value) => ({ ...value, [key]: event.target.value }));
  const submit = (event) => { event.preventDefault(); onSubmit(form); };
  return <Modal title="Add vendor ticket" onClose={onClose}><form onSubmit={submit} className="modal-form"><div className="form-row"><label>Provider<input required value={form.provider} onChange={change('provider')} placeholder="AT&T" /></label><label>Circuit ID<input required value={form.circuit_id} onChange={change('circuit_id')} placeholder="CIR-CHI-4401" /></label></div><label>Provider ticket number<input required value={form.ticket_number} onChange={change('ticket_number')} placeholder="Provider reference" /></label><div className="form-row"><label>SLA target<input value={form.sla_target} onChange={change('sla_target')} placeholder="Response due 03:30 UTC" /></label><label>Vendor contact<input value={form.contact} onChange={change('contact')} placeholder="NOC phone or email" /></label></div><label>Latest update<textarea value={form.last_update} onChange={change('last_update')} placeholder="Summary of the latest provider communication" /></label><div className="modal-actions"><button type="button" className="button button-secondary" onClick={onClose}>Cancel</button><button className="button button-primary" type="submit"><Plus size={15} /> Add ticket</button></div></form></Modal>;
}

function Modal({ title, onClose, children }) {
  useEffect(() => { const close = (event) => event.key === 'Escape' && onClose(); window.addEventListener('keydown', close); return () => window.removeEventListener('keydown', close); }, [onClose]);
  return <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><header><h2 id="modal-title">{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={18} /></button></header>{children}</section></div>;
}

function EmptyState({ text }) {
  return <div className="empty-state"><Check size={17} /><span>{text}</span></div>;
}

export default App;
