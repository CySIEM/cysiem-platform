import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Activity, ShieldAlert, GitCommit, FileText, Bot, BookOpen, Clock, 
  TerminalSquare, Fingerprint, Lock, Shield, Server, Box, AlertTriangle, LogOut
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

const API_URL = 'http://127.0.0.1:8000/api';
const COLORS = ['#6366f1', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']; // Vibrant light mode colors

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState('');
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [userProfile, setUserProfile] = useState(null);

  const [activeTab, setActiveTab] = useState('overview');
  const [data, setData] = useState(null);
  const [chatInput, setChatInput] = useState("");
  const [chatLog, setChatLog] = useState([
    { role: 'bot', text: 'System operational. Connected to FastAPI Backend. I have full context on the current threat landscape. How can I assist?' }
  ]);
  const [time, setTime] = useState("");
  const [liveLogs, setLiveLogs] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('cysiem_token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      verifyUser();
    }
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC');
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (activeTab === 'logs' && isAuthenticated) {
      const msgs = [
        { l: 'INFO', s: 'DataCollection', m: 'Ingested 4,321 events from Firewall-US-East' },
        { l: 'INFO', s: 'AssetIntel', m: 'Enriched 12 IPs with CMDB context' },
        { l: 'WARNING', s: 'DetectionAI', m: 'Anomaly score 0.84 detected on user' },
        { l: 'CRITICAL', s: 'DetectionAI', m: 'Signature match: Cobalt Strike Beacon' },
        { l: 'INFO', s: 'Correlation', m: 'Grouped 14 alerts into Incident' },
        { l: 'INFO', s: 'RAG', m: 'Generated playbook recommendation' },
      ];
      setLiveLogs(msgs.slice(0, 3));
      const interval = setInterval(() => {
        setLiveLogs(prev => {
          const updated = [...prev, msgs[Math.floor(Math.random() * msgs.length)]];
          return updated.length > 50 ? updated.slice(updated.length - 50) : updated;
        });
      }, 1500);
      return () => clearInterval(interval);
    }
  }, [activeTab, isAuthenticated]);

  const verifyUser = async () => {
    try {
      const res = await axios.get(`${API_URL}/auth/me`);
      setUserProfile(res.data);
      setIsAuthenticated(true);
      fetchData();
    } catch (err) {
      localStorage.removeItem('cysiem_token');
      delete axios.defaults.headers.common['Authorization'];
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError('');
    try {
      if (authMode === 'register') {
        await axios.post(`${API_URL}/auth/register`, { username, password });
        setAuthMode('login');
        setAuthError('Account created! Please log in.');
      } else {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        const res = await axios.post(`${API_URL}/auth/login`, formData, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        const token = res.data.access_token;
        localStorage.setItem('cysiem_token', token);
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        await verifyUser();
      }
    } catch (err) {
      setAuthError(err.response?.data?.detail || "Authentication failed");
    } finally {
      setAuthLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('cysiem_token');
    delete axios.defaults.headers.common['Authorization'];
    setIsAuthenticated(false);
    setUserProfile(null);
    setData(null);
    setUsername('');
    setPassword('');
  };

  const fetchData = async () => {
    try {
      const res = await axios.get(`${API_URL}/dashboard/init`);
      setData(res.data);
    } catch (err) {
      console.error("Failed to fetch dashboard data", err);
    }
  };

  const sendCopilot = async (msg) => {
    if (!msg.trim()) return;
    const newLog = [...chatLog, { role: 'user', text: msg }];
    setChatLog(newLog);
    setChatInput("");
    try {
      const res = await axios.post(`${API_URL}/copilot/chat`, { query: msg });
      setChatLog([...newLog, { role: 'bot', text: res.data.reply }]);
    } catch (err) {
      setChatLog([...newLog, { role: 'bot', text: "Error connecting to AI Fabric." }]);
    }
  };

  // --- Auth Screen ---
  if (!isAuthenticated) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-slate-50 z-50">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100 via-slate-50 to-slate-50 opacity-70"></div>
        <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl p-10 shadow-2xl relative z-10">
          <div className="text-center mb-10">
            <div className="w-16 h-16 mx-auto bg-gradient-to-br from-indigo-500 to-violet-500 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/30 mb-6">
              <Fingerprint className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">CySIEM Intelligence</h1>
            <p className="text-xs font-bold tracking-widest text-slate-500 mt-2 uppercase">Beta Release Access</p>
          </div>
          <form onSubmit={handleAuth} className="space-y-5">
            <div>
              <label className="block text-xs font-bold tracking-widest text-slate-500 mb-2">USERNAME</label>
              <input type="text" required value={username} onChange={e => setUsername(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner" />
            </div>
            <div>
              <label className="block text-xs font-bold tracking-widest text-slate-500 mb-2">PASSWORD</label>
              <input type="password" required value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 text-sm font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all shadow-inner" />
            </div>
            {authError && (
              <div className={`text-xs font-medium p-3 rounded-lg border ${authError.includes('created') ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
                {authError}
              </div>
            )}
            <button type="submit" disabled={authLoading} className="w-full py-4 mt-2 bg-gradient-to-r from-indigo-600 to-violet-600 rounded-lg text-white font-bold text-sm tracking-wide shadow-lg shadow-indigo-500/30 hover:shadow-indigo-500/50 hover:-translate-y-0.5 transition-all">
              {authLoading ? 'PROCESSING...' : (authMode === 'login' ? 'AUTHENTICATE' : 'CREATE ACCOUNT')}
            </button>
            <div className="text-center mt-4">
              <button type="button" onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setAuthError(''); }} className="text-xs font-medium text-indigo-600 hover:text-indigo-800 transition-colors">
                {authMode === 'login' ? 'Need an account? Register here.' : 'Already have an account? Login here.'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  const volChartData = data?.charts?.volData?.map((v, i) => ({ time: `${i}:00`, value: v })) || [];
  const donutChartData = data?.charts?.donutData?.map((v, i) => ({ name: ['Malware', 'Phishing', 'DDoS', 'Insider', 'Exploit', 'Misc'][i], value: v })) || [];
  const mitreChartData = data?.charts?.mitreData?.map((v, i) => ({ name: `T10${i}`, value: v })) || [];
  const radarChartData = data?.charts?.radarData?.map((v, i) => ({ subject: ['Endpoint', 'Network', 'Cloud', 'Identity', 'Email', 'Web'][i], A: v, fullMark: 100 })) || [];
  
  const initials = userProfile?.username ? userProfile.username.substring(0, 2).toUpperCase() : 'AD';

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 overflow-hidden font-sans selection:bg-indigo-500/20">
      
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-10">
        <div className="p-6 border-b border-slate-100 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="font-bold text-slate-900 tracking-tight leading-tight">CySIEM</div>
            <div className="text-[9px] font-bold tracking-[0.2em] text-slate-400 uppercase">Beta Platform</div>
          </div>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          <NavItem active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} icon={<Activity size={18} />} label="Overview" />
          <NavItem active={activeTab === 'pipeline'} onClick={() => setActiveTab('pipeline')} icon={<Box size={18} />} label="Architecture" />
          <NavItem active={activeTab === 'threats'} onClick={() => setActiveTab('threats')} icon={<ShieldAlert size={18} />} label="Threat Intel" />
          <NavItem active={activeTab === 'incidents'} onClick={() => setActiveTab('incidents')} icon={<GitCommit size={18} />} label="Incidents" badge={data?.incidents?.open?.length || 0} badgeColor="bg-red-100 text-red-700" />
          <NavItem active={activeTab === 'logs'} onClick={() => setActiveTab('logs')} icon={<TerminalSquare size={18} />} label="Event Logs" />
          <NavItem active={activeTab === 'copilot'} onClick={() => setActiveTab('copilot')} icon={<Bot size={18} />} label="AI Copilot" badge="RAG" badgeColor="bg-indigo-100 text-indigo-700" />
          <NavItem active={activeTab === 'playbooks'} onClick={() => setActiveTab('playbooks')} icon={<BookOpen size={18} />} label="Playbooks" />
        </nav>
        <div className="p-5 bg-slate-50/50 border-t border-slate-200 flex items-center gap-2 text-[10px] font-bold tracking-wider text-slate-500 uppercase">
          <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]"></div>
          Live Database Sync
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative">
        
        {/* Header */}
        <header className="h-16 bg-white/80 backdrop-blur-md border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-10 shadow-sm">
          <div className="text-xs font-bold tracking-widest text-slate-400">
            CYSIEM <span className="mx-2 text-slate-200">/</span> <span className="text-slate-800">{activeTab.toUpperCase()}</span>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-[11px] font-mono font-medium text-slate-500 flex items-center gap-2 bg-slate-100 px-3 py-1.5 rounded-full border border-slate-200">
              <Clock size={12} className="text-slate-400" /> {time}
            </div>
            <div className="flex items-center gap-3 pl-6 border-l border-slate-200 relative group cursor-pointer">
              <div className="w-9 h-9 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center font-bold text-xs text-indigo-600 shadow-sm">{initials}</div>
              <div className="text-xs">
                <div className="font-bold text-slate-900">{userProfile?.username || 'User'}</div>
                <div className="text-slate-500 font-medium">{userProfile?.role || 'Analyst'}</div>
              </div>
              {/* Dropdown menu */}
              <div className="absolute right-0 top-12 pt-2 hidden group-hover:block w-40">
                <div className="bg-white border border-slate-200 rounded-lg shadow-xl overflow-hidden py-1">
                  <button onClick={logout} className="w-full text-left px-4 py-2 flex items-center gap-2 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors">
                    <LogOut size={14} /> Logout
                  </button>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Scrollable Area */}
        <div className="flex-1 overflow-y-auto p-8 bg-slate-50">
          {!data ? (
            <div className="h-full flex flex-col items-center justify-center gap-4 text-slate-400 font-mono text-sm">
              <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin"></div>
              SYNCING WITH BACKEND...
            </div>
          ) : (
            <div className="max-w-[1600px] mx-auto">
              
              {/* OVERVIEW TAB */}
              {activeTab === 'overview' && (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  {/* KPI Bar */}
                  <div className="grid grid-cols-5 gap-4">
                    <StatCard val={data.stats.active_alerts} label="Active Alerts" trend="+12%" color="indigo" />
                    <StatCard val={data.stats.open_incidents} label="Open Incidents" trend="-3%" color="violet" />
                    <StatCard val={data.stats.events_per_hour} label="Events / Hour" trend="+4%" color="blue" />
                    <StatCard val={data.stats.assets_monitored} label="Assets Monitored" trend="0%" color="emerald" />
                    <StatCard val={data.stats.security_score} label="Security Score" trend="+1.2" color="slate" />
                  </div>

                  <div className="grid grid-cols-3 gap-6">
                    {/* Line Chart */}
                    <div className="col-span-2 bg-white border border-slate-200 rounded-xl p-6 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
                      <div className="mb-6">
                        <h3 className="font-bold text-slate-900">Global Threat Volume</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Ingestion & Detection Rate (24H)</p>
                      </div>
                      <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={volChartData}>
                            <defs>
                              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                            <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dy={10} />
                            <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} dx={-10} />
                            <RechartsTooltip 
                              contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }} 
                              itemStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                            />
                            <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#6366f1', stroke: '#fff', strokeWidth: 2 }} fillOpacity={1} fill="url(#colorValue)" />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Radar Chart */}
                    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
                      <div className="mb-2">
                        <h3 className="font-bold text-slate-900">MITRE ATT&CK Coverage</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Detection Fabric Tactics Radar</p>
                      </div>
                      <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarChartData}>
                            <PolarGrid stroke="#e2e8f0" />
                            <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10, fontWeight: 500 }} />
                            <Radar name="Coverage" dataKey="A" stroke="#8b5cf6" strokeWidth={2} fill="#8b5cf6" fillOpacity={0.2} />
                            <RechartsTooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Pie Chart */}
                    <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
                      <div className="mb-2">
                        <h3 className="font-bold text-slate-900">Threat Breakdown</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Classified by AI Engine</p>
                      </div>
                      <div className="h-72">
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart>
                            <Pie data={donutChartData} innerRadius={65} outerRadius={90} paddingAngle={2} dataKey="value" stroke="none">
                              {donutChartData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                            </Pie>
                            <RechartsTooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }} />
                          </PieChart>
                        </ResponsiveContainer>
                      </div>
                    </div>

                    {/* Alert Table */}
                    <div className="col-span-2 bg-white border border-slate-200 rounded-xl p-6 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
                      <div className="mb-6 flex justify-between items-end">
                        <div>
                          <h3 className="font-bold text-slate-900">Database Alert Stream</h3>
                          <p className="text-xs text-slate-500 mt-0.5">Live SQLite queries from Detection Fabric</p>
                        </div>
                        <button className="text-xs font-bold text-indigo-600 hover:text-indigo-800">VIEW ALL</button>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                          <thead>
                            <tr className="text-[10px] font-bold tracking-widest text-slate-400 uppercase border-b border-slate-100">
                              <th className="pb-3 font-medium">Severity</th>
                              <th className="pb-3 font-medium">Alert Definition</th>
                              <th className="pb-3 font-medium">Source</th>
                              <th className="pb-3 font-medium">Destination</th>
                              <th className="pb-3 font-medium">Tactic</th>
                              <th className="pb-3 font-medium text-right">Time</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.alerts.map((a, i) => (
                              <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/80 transition-colors group">
                                <td className="py-3">
                                  <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${a.sev === 'critical' ? 'bg-red-100 text-red-700' : (a.sev === 'high' ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700')}`}>
                                    {a.sev}
                                  </span>
                                </td>
                                <td className="py-3 font-semibold text-slate-800">{a.name}</td>
                                <td className="py-3 font-mono text-xs text-slate-500">{a.src}</td>
                                <td className="py-3 font-mono text-xs text-slate-500">{a.dst}</td>
                                <td className="py-3 font-mono text-xs font-semibold text-indigo-600">{a.mitre}</td>
                                <td className="py-3 font-mono text-xs text-slate-400 text-right">{a.time}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ARCHITECTURE TAB */}
              {activeTab === 'pipeline' && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">System Architecture</h1>
                    <p className="text-slate-500">End-to-end data ingestion and analysis pipeline</p>
                  </div>
                  <div className="bg-white border border-slate-200 rounded-2xl p-10 flex flex-col gap-0 max-w-4xl shadow-sm">
                    <PipelineStage team="TEAM 1" name="Data Collection" desc="Ingests logs from EDR, Firewalls, and Cloud Providers." tags={['Logstash', 'Filebeat', 'Kafka']} color="bg-blue-500" />
                    <PipelineStage team="TEAM 2" name="Asset Intelligence" desc="Enriches logs with CMDB context and vulnerability data." tags={['Context Engine', 'Asset DB']} color="bg-cyan-500" />
                    <PipelineStage team="TEAM 3" name="Detection Fabric" desc="AI models flag anomalies and malicious signatures." tags={['Hugging Face', 'PyTorch']} color="bg-emerald-500" />
                    <PipelineStage team="TEAM 4" name="Correlation" desc="Groups isolated alerts into actionable incidents." tags={['Graph DB', 'Rule Engine']} color="bg-amber-500" />
                    <PipelineStage team="TEAM 5" name="Knowledge Base" desc="RAG pipeline providing automated recommendations." tags={['Ollama', 'ChromaDB', 'FAISS']} color="bg-rose-500" />
                    <PipelineStage team="TEAM 6" name="Dashboard & Beta Backend" desc="Provides visualization, SQLite database, and Playbooks." tags={['React', 'FastAPI', 'SQLite']} color="bg-indigo-500" isLast />
                  </div>
                </div>
              )}

              {/* THREATS TAB */}
              {activeTab === 'threats' && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Threat Intelligence</h1>
                    <p className="text-slate-500">Active campaigns queried from SQLite Database</p>
                  </div>
                  <div className="grid grid-cols-2 gap-6">
                    {data.threats.map((t, i) => (
                      <div key={i} className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer group">
                        <div className="flex justify-between items-start mb-3">
                          <h3 className="font-bold text-lg text-slate-900 group-hover:text-indigo-600 transition-colors">{t.title}</h3>
                          <span className="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider bg-red-100 text-red-700">{t.sev}</span>
                        </div>
                        <div className="inline-block px-2 py-1 bg-slate-100 border border-slate-200 rounded text-xs font-mono font-bold text-slate-600 mb-4">{t.mitre}</div>
                        <p className="text-sm text-slate-600 mb-6 leading-relaxed">{t.desc}</p>
                        <div className="flex justify-between items-center text-xs text-slate-500 pt-4 border-t border-slate-100">
                          <span className="flex items-center gap-1 font-semibold text-emerald-600">
                            <Activity size={14} /> Confidence: {t.conf}%
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock size={14} /> {t.t}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* INCIDENTS TAB */}
              {activeTab === 'incidents' && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Incident Correlation</h1>
                    <p className="text-slate-500">Automatically grouped alerts managed by the Correlation Fabric.</p>
                  </div>
                  <div className="grid grid-cols-3 gap-6">
                    {['open', 'investigating', 'resolved'].map((col) => (
                      <div key={col} className="flex flex-col gap-4 bg-slate-100/50 p-4 rounded-xl border border-slate-200/50">
                        <div className="text-[11px] font-bold tracking-widest text-slate-500 uppercase pb-3 border-b-2 border-slate-200 flex justify-between items-center">
                          <span className="flex items-center gap-2">
                            <div className={`w-2 h-2 rounded-full ${col==='open'?'bg-red-500':col==='investigating'?'bg-amber-500':'bg-emerald-500'}`}></div>
                            {col}
                          </span>
                          <span className="bg-white px-2 py-0.5 rounded-full shadow-sm border border-slate-200">{data.incidents[col].length}</span>
                        </div>
                        {data.incidents[col].map((inc) => (
                          <div key={inc.id} className="bg-white border border-slate-200 p-4 rounded-lg shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:border-indigo-300 transition-all cursor-pointer">
                            <div className="text-xs font-mono font-bold text-indigo-600 mb-2">{inc.id}</div>
                            <div className="text-sm font-bold text-slate-800 mb-4 leading-snug">{inc.title}</div>
                            <div className="flex justify-between items-center text-[10px]">
                              <span className={`px-2 py-1 rounded-md font-bold uppercase tracking-wider ${inc.sev === 'critical' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'}`}>{inc.sev}</span>
                              <span className="text-slate-500 flex items-center gap-1"><div className="w-4 h-4 bg-slate-100 rounded-full flex items-center justify-center text-slate-600 text-[8px] font-bold">{inc.who?.[0]||'?'}</div>{inc.who}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* LOGS TAB - Intentionally kept Dark for authentic terminal feel */}
              {activeTab === 'logs' && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 h-[calc(100vh-180px)] flex flex-col">
                  <div className="mb-6">
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Event Log Stream</h1>
                    <p className="text-slate-500">Live terminal feed from all data sources (Terminal theme)</p>
                  </div>
                  <div className="flex-1 bg-[#0f172a] rounded-xl overflow-hidden flex flex-col shadow-xl ring-1 ring-slate-900/10">
                    <div className="bg-[#1e293b] px-4 py-3 border-b border-white/10 flex items-center gap-3">
                      <div className="flex gap-2">
                        <div className="w-3 h-3 rounded-full bg-[#ff5f56]"></div>
                        <div className="w-3 h-3 rounded-full bg-[#ffbd2e]"></div>
                        <div className="w-3 h-3 rounded-full bg-[#27c93f]"></div>
                      </div>
                      <div className="text-xs font-mono text-slate-400">cysiem@core-cluster:~$ tail -f /var/log/security.log</div>
                    </div>
                    <div className="flex-1 overflow-y-auto p-5 font-mono text-xs text-slate-300 leading-loose flex flex-col-reverse terminal-scroll">
                      <div>
                        {liveLogs.map((log, i) => (
                          <LogLine key={i} level={log.l} source={log.s} msg={log.m} />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* COPILOT TAB */}
              {activeTab === 'copilot' && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 h-[calc(100vh-180px)] max-w-5xl mx-auto">
                  <div className="flex h-full bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-lg shadow-slate-200/50">
                    <div className="w-72 bg-slate-50/80 border-r border-slate-200 p-6 flex flex-col">
                      <div className="flex items-center gap-3 mb-8">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
                          <Bot size={20} />
                        </div>
                        <div>
                          <div className="font-bold text-slate-900 text-sm">Intelligence Copilot</div>
                          <div className="text-[10px] font-bold text-indigo-600">Powered by RAG Pipeline</div>
                        </div>
                      </div>
                      <div className="text-[10px] font-bold tracking-widest text-slate-400 mb-4 uppercase">Suggested Queries</div>
                      <div className="space-y-2 flex-1">
                        <CopilotBtn onClick={() => sendCopilot("Summarize the last 24 hours of threat activity.")}>Summarize 24h Activity</CopilotBtn>
                        <CopilotBtn onClick={() => sendCopilot("What are the top MITRE ATT&CK techniques observed?")}>Top MITRE Techniques</CopilotBtn>
                        <CopilotBtn onClick={() => sendCopilot("Provide remediation steps for active C2 beacon.")}>Remediation for C2</CopilotBtn>
                      </div>
                    </div>
                    <div className="flex-1 flex flex-col bg-white">
                      <div className="flex-1 p-6 overflow-y-auto space-y-6">
                        {chatLog.map((c, i) => (
                          <div key={i} className={`flex gap-4 max-w-[85%] ${c.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
                            <div className={`w-8 h-8 rounded-full shrink-0 flex items-center justify-center text-xs font-bold shadow-sm ${c.role === 'user' ? 'bg-indigo-50 border border-indigo-100 text-indigo-600' : 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white'}`}>
                              {c.role === 'user' ? initials : <Bot size={14} />}
                            </div>
                            <div className={`p-4 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${c.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-sm' : 'bg-slate-50 border border-slate-200 text-slate-800 rounded-tl-sm'}`}>
                              {c.text}
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="p-4 border-t border-slate-200 bg-white">
                        <div className="flex gap-2 p-1 bg-slate-50 border border-slate-200 rounded-xl focus-within:ring-2 focus-within:ring-indigo-500/50 focus-within:border-indigo-500 transition-all">
                          <input 
                            type="text" 
                            value={chatInput}
                            onChange={(e) => setChatInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && sendCopilot(chatInput)}
                            placeholder="Query threat intel, incidents, or ask for remediation..." 
                            className="flex-1 bg-transparent px-4 py-2 text-sm text-slate-900 focus:outline-none placeholder-slate-400" 
                          />
                          <button onClick={() => sendCopilot(chatInput)} className="w-10 h-10 flex items-center justify-center text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 shadow-md shadow-indigo-500/20 transition-colors">
                            <Bot size={18} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* PLAYBOOKS TAB */}
              {activeTab === 'playbooks' && (
                <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className="mb-8">
                    <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-2">Response Playbooks</h1>
                    <p className="text-slate-500">Automated response workflows generated by AI</p>
                  </div>
                  <div className="grid grid-cols-3 gap-6">
                    {data.playbooks.map((pb, i) => (
                      <div key={i} className="bg-white border border-slate-200 p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow flex flex-col h-full relative overflow-hidden group">
                        <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-indigo-500/5 to-violet-500/5 rounded-bl-[100px] -z-0"></div>
                        <div className="flex gap-4 items-center mb-5 relative z-10">
                          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100"><BookOpen size={24} /></div>
                          <div>
                            <div className="text-[10px] font-mono font-bold text-indigo-600 mb-1">{pb.id}</div>
                            <div className="font-bold text-slate-900 leading-tight">{pb.title}</div>
                          </div>
                        </div>
                        <p className="text-sm text-slate-600 mb-8 flex-1 relative z-10">{pb.desc}</p>
                        <button className="w-full py-3 bg-slate-900 rounded-lg text-white font-bold text-xs tracking-widest hover:bg-indigo-600 transition-colors shadow-md relative z-10">
                          EXECUTE PLAYBOOK
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// Components
const NavItem = ({ active, onClick, icon, label, badge, badgeColor }) => (
  <button onClick={onClick} className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold transition-all ${active ? 'bg-indigo-50 text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'}`}>
    <span className={active ? "text-indigo-600" : "text-slate-400"}>{icon}</span> 
    <span>{label}</span>
    {badge && <span className={`ml-auto px-2 py-0.5 rounded-md text-[10px] font-bold ${badgeColor}`}>{badge}</span>}
  </button>
);

const StatCard = ({ val, label, trend, color }) => {
  const isPos = trend.startsWith('+');
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-[0_2px_10px_rgba(0,0,0,0.02)] relative overflow-hidden group">
      <div className={`absolute -right-6 -top-6 w-24 h-24 bg-${color}-500/5 rounded-full group-hover:scale-150 transition-transform duration-500`}></div>
      <div className="flex justify-between items-start mb-2 relative z-10">
        <div className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">{label}</div>
        <div className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${isPos ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-600'}`}>{trend}</div>
      </div>
      <div className="text-3xl font-bold font-mono tracking-tighter text-slate-900 relative z-10">{val}</div>
    </div>
  );
};

const PipelineStage = ({ team, name, desc, tags, color, isLast }) => (
  <div className="flex gap-8 group">
    <div className="w-48 text-right pt-4">
      <div className={`text-[10px] font-bold tracking-widest mb-1 uppercase ${color.replace('bg-', 'text-')}`}>{team}</div>
      <div className="font-bold text-slate-900">{name}</div>
    </div>
    <div className="flex flex-col items-center w-10">
      <div className={`w-6 h-6 border-2 rounded-full flex items-center justify-center z-10 mt-4 bg-white ${color.replace('bg-', 'border-')}`}>
        <div className={`w-2 h-2 rounded-full ${color}`}></div>
      </div>
      {!isLast && <div className="w-0.5 flex-1 bg-slate-200 -my-2 min-h-[80px] group-hover:bg-slate-300 transition-colors"></div>}
    </div>
    <div className="flex-1 pt-4 pb-8">
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 shadow-sm group-hover:shadow-md transition-shadow">
        <p className="text-sm text-slate-600 mb-4">{desc}</p>
        <div className="flex gap-2 flex-wrap">
          {tags.map(t => <span key={t} className="px-2.5 py-1 bg-white border border-slate-200 text-slate-600 text-[10px] font-bold rounded-md shadow-sm">{t}</span>)}
        </div>
      </div>
    </div>
  </div>
);

const CopilotBtn = ({ children, onClick }) => (
  <button onClick={onClick} className="w-full text-left px-4 py-3 bg-white border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:shadow-sm hover:text-indigo-700 transition-all">
    {children}
  </button>
);

const LogLine = ({ level, source, msg }) => {
  const colors = { CRITICAL: 'text-[#ff5f56] font-bold', WARNING: 'text-[#ffbd2e] font-bold', INFO: 'text-[#44C4A1] font-bold' };
  return (
    <div className="border-b border-slate-700/50 py-1.5 flex gap-4 hover:bg-slate-800/30 px-2 -mx-2 rounded transition-colors">
      <span className="text-slate-500 shrink-0">{new Date().toISOString().substring(11,19)}</span>
      <span className={`w-20 shrink-0 ${colors[level]}`}>{level}</span>
      <span className="w-32 shrink-0 text-[#94a3b8] truncate">[{source}]</span>
      <span className="flex-1 text-slate-300">{msg}</span>
    </div>
  );
};
