import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, ShieldAlert, GitCommit, FileText, Bot, BookOpen, Clock, 
  TerminalSquare, Fingerprint, Lock, Shield, Server, Box, AlertTriangle, LogOut, CheckCircle2, X
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';

const API_URL = 'http://127.0.0.1:8000/api';
const COLORS = ['#6366f1', '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444']; 

export default function App() {
  const [theme, setTheme] = useState("light");
  const toggleTheme = () => setTheme(theme === "light" ? "dark" : "light");
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authMode, setAuthMode] = useState('login'); 
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
  
  // Interactive States
  const [toasts, setToasts] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [playbookLoading, setPlaybookLoading] = useState({});

  const addToast = (msg, type = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, msg, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
  };

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
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [activeTab, isAuthenticated]);

  const verifyUser = async () => {
    try {
      const res = await axios.get(`${API_URL}/auth/me`);
      setUserProfile(res.data);
      setIsAuthenticated(true);
      fetchData();
      addToast(`Welcome back, ${res.data.username}`, 'success');
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
        addToast('Account created successfully. Please login.', 'success');
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
      addToast('Error syncing with backend', 'error');
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
      addToast('AI Copilot connection failed', 'error');
    }
  };

  const executePlaybook = (id) => {
    setPlaybookLoading(prev => ({...prev, [id]: true}));
    addToast(`Initializing Playbook ${id}...`, 'info');
    setTimeout(() => {
      setPlaybookLoading(prev => ({...prev, [id]: false}));
      addToast(`Playbook ${id} executed successfully on endpoint.`, 'success');
    }, 2500);
  };

  // --- Auth Screen ---
  if (!isAuthenticated) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-slate-50 dark:bg-slate-950 z-50">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-100/50 via-slate-50 to-slate-50"
        ></motion.div>
        
        <motion.div 
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
          className="w-full max-w-md bg-white dark:bg-slate-900/70 backdrop-blur-xl border border-slate-200 dark:border-slate-800/60 rounded-3xl p-10 shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)] relative z-10"
        >
          <div className="text-center mb-10">
            <motion.div 
              initial={{ scale: 0.8, rotate: -10 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ duration: 0.5, delay: 0.3, type: "spring" }}
              className="w-16 h-16 mx-auto bg-gradient-to-br from-indigo-500 to-violet-500 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/30 mb-6"
            >
              <Fingerprint className="w-8 h-8 text-white" />
            </motion.div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-50">CySIEM</h1>
            <p className="text-[10px] font-bold tracking-[0.3em] text-slate-400 mt-2 uppercase">Platform Access</p>
          </div>
          <form onSubmit={handleAuth} className="space-y-5">
            <div>
              <label className="block text-xs font-bold tracking-widest text-slate-500 mb-2">USERNAME</label>
              <input type="text" required value={username} onChange={e => setUsername(e.target.value)} className="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3.5 text-sm font-medium text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all shadow-inner" />
            </div>
            <div>
              <label className="block text-xs font-bold tracking-widest text-slate-500 mb-2">PASSWORD</label>
              <input type="password" required value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl px-4 py-3.5 text-sm font-medium text-slate-900 dark:text-slate-50 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500 transition-all shadow-inner" />
            </div>
            
            <AnimatePresence>
              {authError && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="text-xs font-semibold p-3 rounded-xl bg-red-50 text-red-600 border border-red-100"
                >
                  {authError}
                </motion.div>
              )}
            </AnimatePresence>

            <motion.button 
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              type="submit" 
              disabled={authLoading} 
              className="w-full py-4 mt-4 bg-gradient-to-r from-indigo-600 to-violet-600 rounded-xl text-white font-bold text-sm tracking-widest shadow-xl shadow-indigo-500/20 hover:shadow-indigo-500/40 transition-all flex items-center justify-center gap-2"
            >
              {authLoading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div> : (authMode === 'login' ? 'AUTHENTICATE' : 'CREATE ACCOUNT')}
            </motion.button>
            <div className="text-center mt-4">
              <button type="button" onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setAuthError(''); }} className="text-xs font-semibold text-slate-500 hover:text-indigo-600 transition-colors">
                {authMode === 'login' ? 'Need an account? Register here' : 'Already have an account? Login here'}
              </button>
            </div>
          </form>
        </motion.div>
        {/* Render Toasts on Login Screen too */}
        <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3">
          <AnimatePresence>
            {toasts.map(t => <Toast key={t.id} msg={t.msg} type={t.type} />)}
          </AnimatePresence>
        </div>
      </div>
    );
  }

  const volChartData = data?.charts?.volData?.map((v, i) => ({ time: `${i}:00`, value: v })) || [];
  const donutChartData = data?.charts?.donutData?.map((v, i) => ({ name: ['Malware', 'Phishing', 'DDoS', 'Insider', 'Exploit', 'Misc'][i], value: v })) || [];
  const mitreChartData = data?.charts?.mitreData?.map((v, i) => ({ name: `T10${i}`, value: v })) || [];
  const radarChartData = data?.charts?.radarData?.map((v, i) => ({ subject: ['Endpoint', 'Network', 'Cloud', 'Identity', 'Email', 'Web'][i], A: v, fullMark: 100 })) || [];
  
  const initials = userProfile?.username ? userProfile.username.substring(0, 2).toUpperCase() : 'AD';

  const pageVariants = {
    initial: { opacity: 0, y: 15 },
    animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1], staggerChildren: 0.1 } }
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 overflow-hidden font-sans selection:bg-indigo-500/20">
      
      {/* Sidebar */}
      <aside className="w-64 bg-white dark:bg-slate-900/60 backdrop-blur-xl border-r border-slate-200 dark:border-slate-800/60 flex flex-col shadow-[4px_0_24px_rgba(0,0,0,0.02)] z-20">
        <div className="p-6 border-b border-slate-100 dark:border-slate-800/50 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="font-bold text-slate-900 dark:text-slate-50 tracking-tight leading-tight">CySIEM</div>
            <div className="text-[9px] font-bold tracking-[0.2em] text-slate-400 uppercase">Beta Platform</div>
          </div>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          <NavItem active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} icon={<Activity size={18} />} label="Overview" />
          <NavItem active={activeTab === 'pipeline'} onClick={() => setActiveTab('pipeline')} icon={<Box size={18} />} label="Architecture" />
          <NavItem active={activeTab === 'threats'} onClick={() => setActiveTab('threats')} icon={<ShieldAlert size={18} />} label="Threat Intel" />
          <NavItem active={activeTab === 'incidents'} onClick={() => setActiveTab('incidents')} icon={<GitCommit size={18} />} label="Incidents" badge={data?.incidents?.open?.length || 0} badgeColor="bg-rose-100 text-rose-700" />
          <NavItem active={activeTab === 'logs'} onClick={() => setActiveTab('logs')} icon={<TerminalSquare size={18} />} label="Event Logs" />
          <NavItem active={activeTab === 'copilot'} onClick={() => setActiveTab('copilot')} icon={<Bot size={18} />} label="AI Copilot" badge="RAG" badgeColor="bg-indigo-100 text-indigo-700" />
          <NavItem active={activeTab === 'playbooks'} onClick={() => setActiveTab('playbooks')} icon={<BookOpen size={18} />} label="Playbooks" />
        </nav>
        <div className="p-5 bg-gradient-to-t from-slate-100/80 to-transparent border-t border-slate-200 dark:border-slate-800/60 flex items-center gap-2 text-[10px] font-bold tracking-wider text-slate-500 uppercase">
          <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)] animate-pulse"></div>
          Live Sync Active
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden relative bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-50/40 via-slate-50 to-slate-50">
        
        {/* Header */}
        <header className="h-16 bg-white dark:bg-slate-900/70 backdrop-blur-xl border-b border-slate-200 dark:border-slate-800/60 px-8 flex items-center justify-between sticky top-0 z-10 shadow-[0_4px_20px_-10px_rgba(0,0,0,0.02)]">
          <motion.div 
            key={activeTab}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-xs font-bold tracking-widest text-slate-400"
          >
            CYSIEM <span className="mx-2 text-slate-200">/</span> <span className="text-slate-800 dark:text-slate-200">{activeTab.toUpperCase()}</span>
          </motion.div>
          <div className="flex items-center gap-6">
            <button onClick={toggleTheme} className="w-9 h-9 rounded-full bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
              {theme === "light" ? <Lock size={14}/> : <Activity size={14}/>}
            </button>
            <div className="text-[11px] font-mono font-medium text-slate-500 flex items-center gap-2 bg-slate-100 dark:bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-800/50">
              <Clock size={12} className="text-slate-400" /> {time}
            </div>
            <div className="flex items-center gap-3 pl-6 border-l border-slate-200 dark:border-slate-800/60 relative group cursor-pointer">
              <div className="w-9 h-9 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center font-bold text-xs text-indigo-600 shadow-sm">{initials}</div>
              <div className="text-xs">
                <div className="font-bold text-slate-900 dark:text-slate-50">{userProfile?.username || 'User'}</div>
                <div className="text-slate-500 font-medium">{userProfile?.role || 'Analyst'}</div>
              </div>
              {/* Dropdown menu */}
              <div className="absolute right-0 top-12 pt-2 hidden group-hover:block w-40">
                <motion.div 
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-white dark:bg-slate-900/90 backdrop-blur-xl border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl overflow-hidden py-1"
                >
                  <button onClick={logout} className="w-full text-left px-4 py-2.5 flex items-center gap-2 text-xs font-semibold text-rose-600 hover:bg-rose-50 transition-colors">
                    <LogOut size={14} /> End Session
                  </button>
                </motion.div>
              </div>
            </div>
          </div>
        </header>

        {/* Scrollable Area */}
        <div className="flex-1 overflow-y-auto p-8">
          <AnimatePresence mode="wait">
            {!data ? (
              <motion.div 
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="h-full flex flex-col items-center justify-center gap-4 text-slate-400 font-mono text-sm"
              >
                <div className="w-8 h-8 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"></div>
                SYNCING WITH FABRIC...
              </motion.div>
            ) : (
              <motion.div 
                key={activeTab}
                variants={pageVariants}
                initial="initial"
                animate="animate"
                className="max-w-[1600px] mx-auto"
              >
                
                {/* OVERVIEW TAB */}
                {activeTab === 'overview' && (
                  <div className="space-y-6">
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
                      <motion.div variants={pageVariants} className="col-span-2 bg-white dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200 dark:border-slate-800/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)] relative overflow-hidden">
                        <div className="mb-6 relative z-10">
                          <h3 className="font-bold text-slate-900 dark:text-slate-50 text-lg tracking-tight">Global Threat Volume</h3>
                          <p className="text-xs text-slate-500 mt-0.5">Ingestion & Detection Rate (24H)</p>
                        </div>
                        <div className="h-72 relative z-10">
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
                                contentStyle={{ backgroundColor: 'rgba(255,255,255,0.95)', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)', backdropFilter: 'blur(8px)' }} 
                                itemStyle={{ color: '#0f172a', fontWeight: 'bold' }}
                              />
                              <Line type="monotone" dataKey="value" stroke="#6366f1" strokeWidth={3} dot={false} activeDot={{ r: 6, fill: '#6366f1', stroke: '#fff', strokeWidth: 3 }} fillOpacity={1} fill="url(#colorValue)" />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      </motion.div>

                      {/* Radar Chart */}
                      <motion.div variants={pageVariants} className="bg-white dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200 dark:border-slate-800/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                        <div className="mb-2">
                          <h3 className="font-bold text-slate-900 dark:text-slate-50 tracking-tight">MITRE Coverage</h3>
                          <p className="text-xs text-slate-500 mt-0.5">Detection Fabric Radar</p>
                        </div>
                        <div className="h-72">
                          <ResponsiveContainer width="100%" height="100%">
                            <RadarChart cx="50%" cy="50%" outerRadius="65%" data={radarChartData}>
                              <PolarGrid stroke="#f1f5f9" />
                              <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10, fontWeight: 600 }} />
                              <Radar name="Coverage" dataKey="A" stroke="#8b5cf6" strokeWidth={2} fill="#8b5cf6" fillOpacity={0.2} />
                              <RechartsTooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)' }} />
                            </RadarChart>
                          </ResponsiveContainer>
                        </div>
                      </motion.div>

                      {/* Pie Chart */}
                      <motion.div variants={pageVariants} className="bg-white dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200 dark:border-slate-800/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                        <div className="mb-2">
                          <h3 className="font-bold text-slate-900 dark:text-slate-50 tracking-tight">Threat Breakdown</h3>
                          <p className="text-xs text-slate-500 mt-0.5">Classified by AI Engine</p>
                        </div>
                        <div className="h-72">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie data={donutChartData} innerRadius={65} outerRadius={90} paddingAngle={4} dataKey="value" stroke="none">
                                {donutChartData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                              </Pie>
                              <RechartsTooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)' }} />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                      </motion.div>

                      {/* Alert Table */}
                      <motion.div variants={pageVariants} className="col-span-2 bg-white dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200 dark:border-slate-800/60 rounded-2xl p-6 shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
                        <div className="mb-6 flex justify-between items-end">
                          <div>
                            <h3 className="font-bold text-slate-900 dark:text-slate-50 text-lg tracking-tight">Database Alert Stream</h3>
                            <p className="text-xs text-slate-500 mt-0.5">Live SQLite queries from Detection Fabric</p>
                          </div>
                          <button onClick={() => addToast('Querying full historical alert database...', 'info')} className="text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors bg-indigo-50 px-3 py-1.5 rounded-lg">VIEW ALL</button>
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-sm">
                            <thead>
                              <tr className="text-[10px] font-bold tracking-widest text-slate-400 uppercase border-b border-slate-100 dark:border-slate-800/50">
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
                                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 dark:bg-slate-950/80 transition-colors group">
                                  <td className="py-4">
                                    <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${a.sev === 'critical' ? 'bg-rose-100 text-rose-700' : (a.sev === 'high' ? 'bg-orange-100 text-orange-700' : 'bg-yellow-100 text-yellow-700')}`}>
                                      {a.sev}
                                    </span>
                                  </td>
                                  <td className="py-4 font-semibold text-slate-800 dark:text-slate-200">{a.name}</td>
                                  <td className="py-4 font-mono text-xs text-slate-500">{a.src}</td>
                                  <td className="py-4 font-mono text-xs text-slate-500">{a.dst}</td>
                                  <td className="py-4 font-mono text-xs font-bold text-indigo-600">{a.mitre}</td>
                                  <td className="py-4 font-mono text-xs text-slate-400 text-right">{a.time}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </motion.div>
                    </div>
                  </div>
                )}

                {/* ARCHITECTURE TAB */}
                {activeTab === 'pipeline' && (
                  <div>
                    <div className="mb-8">
                      <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-50 tracking-tight mb-2">System Architecture</h1>
                      <p className="text-slate-500">End-to-end data ingestion and analysis pipeline</p>
                    </div>
                    <div className="bg-white dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200 dark:border-slate-800/60 rounded-3xl p-10 flex flex-col gap-0 max-w-4xl shadow-[0_8px_30px_rgb(0,0,0,0.02)]">
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
                  <div>
                    <div className="mb-8">
                      <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-50 tracking-tight mb-2">Threat Intelligence</h1>
                      <p className="text-slate-500">Active campaigns queried from SQLite Database</p>
                    </div>
                    <div className="grid grid-cols-2 gap-6">
                      {data.threats.map((t, i) => (
                        <motion.div 
                          key={i} 
                          variants={pageVariants}
                          whileHover={{ y: -4, boxShadow: '0 20px 40px -15px rgba(0,0,0,0.05)' }}
                          onClick={() => addToast(`Fetching complete STIX package for ${t.title}...`, 'info')}
                          className="bg-white dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200 dark:border-slate-800/60 rounded-2xl p-8 shadow-sm hover:border-indigo-300 transition-colors cursor-pointer group relative overflow-hidden"
                        >
                          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-bl-[100px] -z-0 group-hover:bg-indigo-500/10 transition-colors"></div>
                          <div className="flex justify-between items-start mb-4 relative z-10">
                            <h3 className="font-bold text-xl text-slate-900 dark:text-slate-50 group-hover:text-indigo-600 transition-colors tracking-tight">{t.title}</h3>
                            <span className="px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-widest bg-rose-100 text-rose-700">{t.sev}</span>
                          </div>
                          <div className="inline-block px-2.5 py-1 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-800/60 rounded-md text-xs font-mono font-bold text-slate-600 dark:text-slate-400 mb-5 relative z-10">{t.mitre}</div>
                          <p className="text-sm text-slate-600 dark:text-slate-400 mb-8 leading-relaxed relative z-10">{t.desc}</p>
                          <div className="flex justify-between items-center text-xs font-semibold text-slate-500 pt-5 border-t border-slate-100 dark:border-slate-800/50 relative z-10">
                            <span className="flex items-center gap-1.5 text-emerald-600 bg-emerald-50 px-2 py-1 rounded-md">
                              <Activity size={14} /> Confidence: {t.conf}%
                            </span>
                            <span className="flex items-center gap-1.5 bg-slate-50 dark:bg-slate-950 px-2 py-1 rounded-md">
                              <Clock size={14} /> {t.t}
                            </span>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* INCIDENTS TAB */}
                {activeTab === 'incidents' && (
                  <div>
                    <div className="mb-8">
                      <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-50 tracking-tight mb-2">Incident Correlation</h1>
                      <p className="text-slate-500">Automatically grouped alerts managed by the Correlation Fabric.</p>
                    </div>
                    <div className="grid grid-cols-3 gap-6">
                      {['open', 'investigating', 'resolved'].map((col) => (
                        <div key={col} className="flex flex-col gap-4 bg-slate-200/30 p-5 rounded-3xl border border-slate-200 dark:border-slate-800/50 backdrop-blur-sm">
                          <div className="text-[11px] font-bold tracking-widest text-slate-500 uppercase pb-4 border-b-2 border-slate-200 dark:border-slate-800/50 flex justify-between items-center">
                            <span className="flex items-center gap-2">
                              <div className={`w-2.5 h-2.5 rounded-full ${col==='open'?'bg-rose-500':col==='investigating'?'bg-amber-500':'bg-emerald-500'} shadow-sm`}></div>
                              {col}
                            </span>
                            <span className="bg-white dark:bg-slate-900 px-2.5 py-0.5 rounded-full shadow-sm border border-slate-200 dark:border-slate-800/60 text-slate-700 dark:text-slate-300">{data.incidents[col].length}</span>
                          </div>
                          {data.incidents[col].map((inc) => (
                            <motion.div 
                              key={inc.id}
                              variants={pageVariants}
                              whileHover={{ y: -3, scale: 1.01 }}
                              onClick={() => setSelectedIncident(inc)}
                              className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800/60 p-5 rounded-2xl shadow-sm hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer group"
                            >
                              <div className="text-xs font-mono font-bold text-indigo-600 mb-2.5 bg-indigo-50 inline-block px-2 py-0.5 rounded-md">{inc.id}</div>
                              <div className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-5 leading-snug group-hover:text-indigo-700 transition-colors">{inc.title}</div>
                              <div className="flex justify-between items-center text-[10px]">
                                <span className={`px-2.5 py-1 rounded-md font-bold uppercase tracking-wider ${inc.sev === 'critical' ? 'bg-rose-100 text-rose-700' : 'bg-orange-100 text-orange-700'}`}>{inc.sev}</span>
                                <span className="text-slate-500 flex items-center gap-1.5 font-medium"><div className="w-5 h-5 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-800 rounded-full flex items-center justify-center text-slate-600 dark:text-slate-400 text-[9px] font-bold">{inc.who?.[0]||'?'}</div>{inc.who}</span>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* LOGS TAB - Intentionally kept Dark for authentic terminal feel */}
                {activeTab === 'logs' && (
                  <div className="h-[calc(100vh-180px)] flex flex-col">
                    <div className="mb-6">
                      <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-50 tracking-tight mb-2">Event Log Stream</h1>
                      <p className="text-slate-500">Live terminal feed from all data sources (Terminal theme)</p>
                    </div>
                    <motion.div variants={pageVariants} className="flex-1 bg-[#09090b] rounded-2xl overflow-hidden flex flex-col shadow-2xl ring-1 ring-slate-900/10">
                      <div className="bg-[#18181b] px-5 py-3.5 border-b border-white/5 flex items-center gap-4">
                        <div className="flex gap-2.5">
                          <div className="w-3.5 h-3.5 rounded-full bg-[#ff5f56] shadow-[0_0_10px_rgba(255,95,86,0.4)]"></div>
                          <div className="w-3.5 h-3.5 rounded-full bg-[#ffbd2e] shadow-[0_0_10px_rgba(255,189,46,0.4)]"></div>
                          <div className="w-3.5 h-3.5 rounded-full bg-[#27c93f] shadow-[0_0_10px_rgba(39,201,63,0.4)]"></div>
                        </div>
                        <div className="text-xs font-mono font-medium text-slate-400">cysiem@core-cluster:~$ tail -f /var/log/security.log</div>
                      </div>
                      <div className="flex-1 overflow-y-auto p-6 font-mono text-sm text-slate-300 leading-loose flex flex-col-reverse terminal-scroll">
                        <div>
                          {liveLogs.map((log, i) => (
                            <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} className="border-b border-slate-800/50 py-2 flex gap-4 hover:bg-slate-800/30 px-3 -mx-3 rounded transition-colors">
                              <span className="text-slate-500 shrink-0">{new Date().toISOString().substring(11,19)}</span>
                              <span className={`w-20 shrink-0 font-bold ${log.l === 'CRITICAL' ? 'text-[#ff5f56]' : (log.l === 'WARNING' ? 'text-[#ffbd2e]' : 'text-[#44C4A1]')}`}>{log.l}</span>
                              <span className="w-32 shrink-0 text-[#64748b] truncate">[{log.s}]</span>
                              <span className="flex-1 text-slate-300">{log.m}</span>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    </motion.div>
                  </div>
                )}

                {/* COPILOT TAB */}
                {activeTab === 'copilot' && (
                  <div className="h-[calc(100vh-180px)] max-w-5xl mx-auto">
                    <motion.div variants={pageVariants} className="flex h-full bg-white dark:bg-slate-900/80 backdrop-blur-xl border border-slate-200 dark:border-slate-800/80 rounded-3xl overflow-hidden shadow-[0_20px_40px_-15px_rgba(0,0,0,0.05)]">
                      <div className="w-80 bg-slate-50 dark:bg-slate-950/50 border-r border-slate-200 dark:border-slate-800/60 p-8 flex flex-col relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 rounded-bl-full -z-0"></div>
                        <div className="flex items-center gap-4 mb-10 relative z-10">
                          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
                            <Bot size={24} />
                          </div>
                          <div>
                            <div className="font-bold text-slate-900 dark:text-slate-50 text-base tracking-tight">Intelligence Copilot</div>
                            <div className="text-[10px] font-bold tracking-widest text-indigo-600 uppercase mt-0.5">Powered by RAG</div>
                          </div>
                        </div>
                        <div className="text-[10px] font-bold tracking-widest text-slate-400 mb-5 uppercase relative z-10">Suggested Queries</div>
                        <div className="space-y-3 flex-1 relative z-10">
                          <CopilotBtn onClick={() => sendCopilot("Summarize the last 24 hours of threat activity.")}>Summarize 24h Activity</CopilotBtn>
                          <CopilotBtn onClick={() => sendCopilot("What are the top MITRE ATT&CK techniques observed?")}>Top MITRE Techniques</CopilotBtn>
                          <CopilotBtn onClick={() => sendCopilot("Provide remediation steps for active C2 beacon.")}>Remediation for C2</CopilotBtn>
                        </div>
                      </div>
                      <div className="flex-1 flex flex-col bg-white dark:bg-slate-900">
                        <div className="flex-1 p-8 overflow-y-auto space-y-8">
                          {chatLog.map((c, i) => (
                            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className={`flex gap-4 max-w-[85%] ${c.role === 'user' ? 'ml-auto flex-row-reverse' : ''}`}>
                              <div className={`w-10 h-10 rounded-2xl shrink-0 flex items-center justify-center text-sm font-bold shadow-md ${c.role === 'user' ? 'bg-indigo-50 border border-indigo-100 text-indigo-600' : 'bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-indigo-500/20'}`}>
                                {c.role === 'user' ? initials : <Bot size={18} />}
                              </div>
                              <div className={`p-5 rounded-3xl text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${c.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-sm' : 'bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/60 text-slate-800 dark:text-slate-200 rounded-tl-sm'}`}>
                                {c.text}
                              </div>
                            </motion.div>
                          ))}
                        </div>
                        <div className="p-6 border-t border-slate-200 dark:border-slate-800/60 bg-white dark:bg-slate-900">
                          <div className="flex gap-2 p-1.5 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl focus-within:ring-4 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 transition-all shadow-inner">
                            <input 
                              type="text" 
                              value={chatInput}
                              onChange={(e) => setChatInput(e.target.value)}
                              onKeyPress={(e) => e.key === 'Enter' && sendCopilot(chatInput)}
                              placeholder="Query threat intel, incidents, or ask for remediation..." 
                              className="flex-1 bg-transparent px-5 py-3 text-sm text-slate-900 dark:text-slate-50 focus:outline-none placeholder-slate-400 font-medium" 
                            />
                            <button onClick={() => sendCopilot(chatInput)} className="w-12 h-12 flex items-center justify-center text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 shadow-lg shadow-indigo-500/20 transition-all active:scale-95">
                              <Bot size={20} />
                            </button>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  </div>
                )}

                {/* PLAYBOOKS TAB */}
                {activeTab === 'playbooks' && (
                  <div>
                    <div className="mb-8">
                      <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-50 tracking-tight mb-2">Response Playbooks</h1>
                      <p className="text-slate-500">Automated response workflows generated by AI</p>
                    </div>
                    <div className="grid grid-cols-3 gap-6">
                      {data.playbooks.map((pb, i) => (
                        <motion.div key={i} variants={pageVariants} className="bg-white dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200 dark:border-slate-800/60 p-8 rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.02)] flex flex-col h-full relative overflow-hidden group">
                          <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-indigo-500/5 to-violet-500/5 rounded-bl-[100px] -z-0 group-hover:scale-110 transition-transform duration-500"></div>
                          <div className="flex gap-5 items-center mb-6 relative z-10">
                            <div className="w-14 h-14 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100 shadow-sm"><BookOpen size={24} /></div>
                            <div>
                              <div className="text-[10px] font-mono font-bold text-indigo-600 mb-1.5 bg-indigo-50 inline-block px-2 py-0.5 rounded">{pb.id}</div>
                              <div className="font-bold text-slate-900 dark:text-slate-50 text-lg leading-tight tracking-tight">{pb.title}</div>
                            </div>
                          </div>
                          <p className="text-sm text-slate-600 dark:text-slate-400 mb-10 flex-1 relative z-10 leading-relaxed">{pb.desc}</p>
                          <motion.button 
                            whileHover={userProfile?.role === 'admin' ? { scale: 1.02 } : {}}
                            whileTap={userProfile?.role === 'admin' ? { scale: 0.98 } : {}}
                            onClick={() => executePlaybook(pb.id)}
                            disabled={playbookLoading[pb.id] || userProfile?.role !== 'admin'}
                            className={`w-full py-4 rounded-xl font-bold text-xs tracking-widest transition-all relative z-10 shadow-lg flex items-center justify-center gap-2 ${playbookLoading[pb.id] ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 border border-slate-200 dark:border-slate-800' : (userProfile?.role !== 'admin' ? 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-200 dark:border-slate-800' : 'bg-slate-900 text-white hover:bg-indigo-600 hover:shadow-indigo-500/25')}`}
                          >
                            {playbookLoading[pb.id] ? (
                               <><div className="w-4 h-4 border-2 border-slate-400/30 border-t-slate-400 rounded-full animate-spin"></div> EXECUTING...</>
                            ) : (userProfile?.role !== 'admin' ? <><Lock size={14} /> ADMIN ONLY</> : 'EXECUTE PLAYBOOK')}
                          </motion.button>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Global Toast Container */}
        <div className="fixed bottom-8 right-8 z-50 flex flex-col gap-3 pointer-events-none">
          <AnimatePresence>
            {toasts.map(t => <Toast key={t.id} msg={t.msg} type={t.type} />)}
          </AnimatePresence>
        </div>

        {/* Incident Detail Modal */}
        <AnimatePresence>
          {selectedIncident && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/20 backdrop-blur-sm p-4"
              onClick={() => setSelectedIncident(null)}
            >
              <motion.div 
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-white dark:bg-slate-900 rounded-3xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-2xl overflow-hidden"
              >
                <div className="p-8 border-b border-slate-100 dark:border-slate-800/50 flex justify-between items-start bg-slate-50 dark:bg-slate-950/50">
                  <div>
                    <div className="text-[10px] font-mono font-bold text-indigo-600 mb-2 bg-indigo-50 inline-block px-2 py-0.5 rounded">{selectedIncident.id}</div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-50 tracking-tight">{selectedIncident.title}</h2>
                  </div>
                  <button onClick={() => setSelectedIncident(null)} className="p-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-full text-slate-400 hover:text-slate-900 dark:text-slate-50 shadow-sm transition-colors">
                    <X size={20} />
                  </button>
                </div>
                <div className="p-8 space-y-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-2xl border border-slate-100 dark:border-slate-800/50">
                      <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-1">Severity</div>
                      <div className={`inline-block px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${selectedIncident.sev === 'critical' ? 'bg-rose-100 text-rose-700' : 'bg-orange-100 text-orange-700'}`}>{selectedIncident.sev}</div>
                    </div>
                    <div className="bg-slate-50 dark:bg-slate-950 p-4 rounded-2xl border border-slate-100 dark:border-slate-800/50">
                      <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-1">Assigned Analyst</div>
                      <div className="text-sm font-semibold text-slate-900 dark:text-slate-50 flex items-center gap-2"><div className="w-6 h-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-full flex items-center justify-center text-slate-600 dark:text-slate-400 text-[10px] font-bold shadow-sm">{selectedIncident.who?.[0]}</div>{selectedIncident.who}</div>
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] font-bold tracking-widest text-slate-400 uppercase mb-3">Incident Timeline</div>
                    <div className="space-y-4 border-l-2 border-slate-200 dark:border-slate-800 ml-2 pl-4">
                      <div className="relative">
                        <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-slate-300 ring-4 ring-white"></div>
                        <div className="text-xs text-slate-500 mb-1">10:42 AM</div>
                        <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">Initial alert generated by EDR</div>
                      </div>
                      <div className="relative">
                        <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-indigo-500 ring-4 ring-white"></div>
                        <div className="text-xs text-slate-500 mb-1">10:45 AM</div>
                        <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">Correlation Engine merged 3 related alerts</div>
                      </div>
                    </div>
                  </div>
                  <div className="pt-4 flex gap-3">
                    <button onClick={() => { addToast('Assigning incident to your queue...', 'success'); setSelectedIncident(null); }} className="flex-1 py-3 bg-indigo-600 text-white font-bold text-xs tracking-widest rounded-xl shadow-lg shadow-indigo-500/25 hover:bg-indigo-700 transition-colors">CLAIM INCIDENT</button>
                    <button onClick={() => { setActiveTab('playbooks'); setSelectedIncident(null); }} className="flex-1 py-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs tracking-widest rounded-xl shadow-sm hover:border-indigo-300 hover:text-indigo-600 transition-colors">RUN PLAYBOOK</button>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

// Components
const Toast = ({ msg, type }) => {
  const isSuccess = type === 'success';
  const isError = type === 'error';
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
      className="bg-white dark:bg-slate-900/90 backdrop-blur-xl border border-slate-200 dark:border-slate-800/60 shadow-[0_10px_30px_-10px_rgba(0,0,0,0.1)] rounded-2xl p-4 flex items-center gap-3 w-80 pointer-events-auto"
    >
      <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${isSuccess ? 'bg-emerald-50 text-emerald-500' : (isError ? 'bg-rose-50 text-rose-500' : 'bg-indigo-50 text-indigo-500')}`}>
        {isSuccess ? <CheckCircle2 size={16} /> : (isError ? <AlertTriangle size={16} /> : <Activity size={16} />)}
      </div>
      <div className="text-sm font-medium text-slate-800 dark:text-slate-200 leading-tight">{msg}</div>
    </motion.div>
  );
};

const NavItem = ({ active, onClick, icon, label, badge, badgeColor }) => (
  <button onClick={onClick} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all relative ${active ? 'bg-indigo-50/80 text-indigo-700 shadow-[inset_0_2px_4px_rgba(0,0,0,0.02)]' : 'text-slate-500 hover:text-slate-900 dark:text-slate-50 hover:bg-slate-100 dark:bg-slate-800/80'}`}>
    {active && <motion.div layoutId="activeNav" className="absolute left-0 w-1 h-6 bg-indigo-600 rounded-r-full" />}
    <span className={active ? "text-indigo-600" : "text-slate-400"}>{icon}</span> 
    <span>{label}</span>
    {badge && <span className={`ml-auto px-2.5 py-0.5 rounded-md text-[10px] font-bold shadow-sm ${badgeColor}`}>{badge}</span>}
  </button>
);

const StatCard = ({ val, label, trend, color }) => {
  const isPos = trend.startsWith('+');
  return (
    <motion.div whileHover={{ y: -4, boxShadow: '0 10px 25px -5px rgba(0,0,0,0.05)' }} className="bg-white dark:bg-slate-900/80 backdrop-blur-sm border border-slate-200 dark:border-slate-800/60 rounded-2xl p-5 shadow-sm relative overflow-hidden group transition-all">
      <div className={`absolute -right-6 -top-6 w-24 h-24 bg-${color}-500/5 rounded-full group-hover:scale-150 group-hover:bg-${color}-500/10 transition-all duration-700 ease-out`}></div>
      <div className="flex justify-between items-start mb-3 relative z-10">
        <div className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">{label}</div>
        <div className={`text-[10px] font-bold px-2 py-0.5 rounded-md shadow-sm ${isPos ? 'bg-emerald-50 text-emerald-600 border border-emerald-100' : 'bg-slate-50 dark:bg-slate-950 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800'}`}>{trend}</div>
      </div>
      <div className="text-3xl font-bold font-mono tracking-tighter text-slate-900 dark:text-slate-50 relative z-10">{val}</div>
    </motion.div>
  );
};

const PipelineStage = ({ team, name, desc, tags, color, isLast }) => (
  <div className="flex gap-8 group">
    <div className="w-48 text-right pt-4">
      <div className={`text-[10px] font-bold tracking-widest mb-1 uppercase ${color.replace('bg-', 'text-')}`}>{team}</div>
      <div className="font-bold text-slate-900 dark:text-slate-50 text-lg">{name}</div>
    </div>
    <div className="flex flex-col items-center w-10">
      <div className={`w-8 h-8 border-4 rounded-full flex items-center justify-center z-10 mt-3.5 bg-white dark:bg-slate-900 shadow-sm transition-transform group-hover:scale-110 duration-300 ${color.replace('bg-', 'border-')}`}>
        <div className={`w-2.5 h-2.5 rounded-full ${color}`}></div>
      </div>
      {!isLast && <div className="w-0.5 flex-1 bg-slate-200 -my-2 min-h-[80px] group-hover:bg-slate-300 transition-colors"></div>}
    </div>
    <div className="flex-1 pt-4 pb-10">
      <div className="bg-slate-50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800/60 rounded-2xl p-6 shadow-sm group-hover:shadow-md transition-shadow group-hover:bg-white dark:bg-slate-900">
        <p className="text-sm text-slate-600 dark:text-slate-400 mb-5 leading-relaxed">{desc}</p>
        <div className="flex gap-2 flex-wrap">
          {tags.map(t => <span key={t} className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 text-[10px] font-bold rounded-lg shadow-sm">{t}</span>)}
        </div>
      </div>
    </div>
  </div>
);

const CopilotBtn = ({ children, onClick }) => (
  <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={onClick} className="w-full text-left px-5 py-4 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800/60 rounded-2xl text-xs font-bold text-slate-700 dark:text-slate-300 hover:border-indigo-300 hover:shadow-md hover:text-indigo-700 transition-all">
    {children}
  </motion.button>
);
