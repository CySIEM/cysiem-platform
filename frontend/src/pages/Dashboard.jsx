import { useEffect, useState } from "react";

import "./Dashboard.css";

import StatCard from "../components/StatCard";
import ThreatChart from "../components/ThreatChart";
import AlertTable from "../components/AlertTable";
import RecommendationPanel from "../components/RecommendationPanel";
import TopThreats from "../components/TopThreats";
import MitreSummary from "../components/MitreSummary";
import RecentActivity from "../components/RecentActivity";
import SystemHealth from "../components/SystemHealth";
import QuickActions from "../components/QuickActions";

import { getDashboardStats } from "../services/api";

const Dashboard = () => {
  const [stats, setStats] = useState({
    critical: "...",
    high: "...",
    medium: "...",
    assets: "...",
  });

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const data = await getDashboardStats();

        setStats({
          critical: data.critical ?? 0,
          high: data.high ?? 0,
          medium: data.medium ?? 0,
          assets: data.assets ?? 0,
        });
      } catch (error) {
        console.error("Failed to load dashboard:", error);

        setStats({
          critical: 0,
          high: 0,
          medium: 0,
          assets: 0,
        });
      }
    };

    loadDashboard();
  }, []);

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>

      <p className="subtitle">
        Welcome to CySIEM Platform
      </p>

      {/* Statistics Cards */}
      <div className="cards">
        <StatCard
          title="Critical Alerts"
          value={stats.critical}
          color="#EF4444"
        />

        <StatCard
          title="High Severity"
          value={stats.high}
          color="#F97316"
        />

        <StatCard
          title="Medium Severity"
          value={stats.medium}
          color="#FACC15"
        />

        <StatCard
          title="Assets Monitored"
          value={stats.assets}
          color="#3B82F6"
        />
      </div>

      {/* Threat Activity */}
      <div className="dashboard-section">
        <ThreatChart />
      </div>

      {/* Alerts + Recent Activity */}
      <div className="bottom-section">
        <AlertTable />
        <RecentActivity />
      </div>

      {/* AI Recommendations + System Health */}
      <div className="analytics-section">
        <RecommendationPanel />
        <SystemHealth />
      </div>

      {/* Top Threats + MITRE ATT&CK */}
      <div className="analytics-section">
        <TopThreats />
        <MitreSummary />
      </div>

      {/* Quick Actions */}
      <div className="dashboard-section">
        <QuickActions />
      </div>
    </div>
  );
};

export default Dashboard;