import {
  ShieldAlert,
  Bug,
  FileText,
  CheckCircle,
} from "lucide-react";

import "./RecentActivity.css";

const activities = [
  {
    icon: <ShieldAlert size={18} />,
    title: "SQL Injection detected",
    time: "2 min ago",
    type: "critical",
  },
  {
    icon: <Bug size={18} />,
    title: "Malware quarantined",
    time: "10 min ago",
    type: "warning",
  },
  {
    icon: <FileText size={18} />,
    title: "Weekly report generated",
    time: "25 min ago",
    type: "info",
  },
  {
    icon: <CheckCircle size={18} />,
    title: "Endpoint scan completed",
    time: "1 hour ago",
    type: "success",
  },
];

const RecentActivity = () => {
  return (
    <div className="activity-card">
      <div className="activity-header">
        <h3>Recent Activity</h3>
      </div>

      <div className="activity-list">
        {activities.map((activity, index) => (
          <div className="activity-item" key={index}>
            <div className={`activity-icon ${activity.type}`}>
              {activity.icon}
            </div>

            <div className="activity-content">
              <h4>{activity.title}</h4>
              <span>{activity.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecentActivity;