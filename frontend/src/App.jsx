import React, { useState, useEffect } from 'react';
import {
  fetchOverview,
  fetchCostRecords,
  fetchResources,
  fetchAlertRules,
  fetchAlertIncidents,
  resolveAlertIncident,
  fetchRecommendations,
  updateRecommendationStatus,
  triggerCloudSync
} from './services/api';
import {
  LayoutDashboard,
  DollarSign,
  TrendingUp,
  PiggyBank,
  AlertTriangle,
  Server,
  RefreshCw,
  BookOpen,
  Activity,
  Cpu,
  Database,
  Sliders,
  Sparkles
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [provider, setProvider] = useState('ALL');
  const [environment, setEnvironment] = useState('ALL');
  const [days, setDays] = useState(30);

  const [overview, setOverview] = useState(null);
  const [costs, setCosts] = useState([]);
  const [resources, setResources] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [rules, setRules] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    loadOverview();
  }, [provider, environment, days]);

  const loadOverview = async () => {
    try {
      const res = await fetchOverview(provider, environment, days);
      setOverview(res.data);
    } catch (err) {
      console.error('Failed to load overview', err);
    }
  };

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      await triggerCloudSync(days);
      await loadOverview();
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="bg-[#111827] border-b border-slate-800 sticky top-0 z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600 p-2 rounded-lg text-white shadow-lg">
              <LayoutDashboard className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white flex items-center gap-2">
                DevOps Cloud Lens
                <span className="text-[10px] bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded-full">React 18</span>
              </h1>
              <p className="text-xs text-slate-400">AWS • Azure • GCP Cost & Resource Monitor</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <a href="/docs" target="_blank" className="text-xs text-slate-400 hover:text-white flex items-center gap-1 border border-slate-700 px-3 py-1.5 rounded-lg">
              <BookOpen className="w-3.5 h-3.5" />
              <span>Swagger</span>
            </a>
            <button
              onClick={handleSync}
              disabled={isSyncing}
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Syncing...' : 'Sync Clouds'}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Sub-nav & Filters */}
      <div className="bg-[#131b2e] border-b border-slate-800 py-3 px-6">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex space-x-1 bg-slate-900/60 p-1 rounded-lg border border-slate-800 text-xs">
            {['overview', 'costs', 'resources', 'optimization', 'alerts'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 rounded-md capitalize font-semibold transition ${
                  activeTab === tab ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-3 text-xs">
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-200 rounded px-2.5 py-1"
            >
              <option value="ALL">All Clouds</option>
              <option value="AWS">AWS</option>
              <option value="Azure">Azure</option>
              <option value="GCP">GCP</option>
            </select>

            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-slate-200 rounded px-2.5 py-1"
            >
              <option value="ALL">All Environments</option>
              <option value="production">Production</option>
              <option value="staging">Staging</option>
              <option value="development">Development</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main KPI Row */}
      {overview && (
        <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-6 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-[#161f36] border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400">Month-to-Date Spend</span>
              <div className="text-2xl font-bold text-white mt-1">
                ${overview.total_spend_month_to_date.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <span className="text-xs text-emerald-400 mt-1 block">
                {overview.month_over_month_change_pct >= 0 ? '+' : ''}{overview.month_over_month_change_pct}% MoM
              </span>
            </div>

            <div className="bg-[#161f36] border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400">Projected Run-rate</span>
              <div className="text-2xl font-bold text-white mt-1">
                ${overview.projected_spend_month_end.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
              <span className="text-[11px] text-slate-400">End of calendar month</span>
            </div>

            <div className="bg-[#161f36] border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400">FinOps Potential Savings</span>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                ${overview.total_potential_savings.toLocaleString(undefined, { minimumFractionDigits: 2 })}/mo
              </div>
              <span className="text-[11px] text-slate-400">Idle & rightsizing detected</span>
            </div>

            <div className="bg-[#161f36] border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400">Active Alert Incidents</span>
              <div className="text-2xl font-bold text-rose-400 mt-1">
                {overview.active_alerts_count}
              </div>
              <span className="text-[11px] text-slate-400">Threshold violations</span>
            </div>

            <div className="bg-[#161f36] border border-slate-800 rounded-xl p-4">
              <span className="text-xs text-slate-400">Cloud Assets Tracked</span>
              <div className="text-2xl font-bold text-white mt-1">
                {overview.total_resources_monitored}
              </div>
              <span className="text-xs text-amber-400">{overview.idle_resources_count} Idle Resources</span>
            </div>
          </div>
        </main>
      )}
    </div>
  );
}
