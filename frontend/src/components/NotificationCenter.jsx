import {
  Bell,
  ShieldAlert,
  Bug,
  FileText,
  CheckCircle,
} from "lucide-react";

import "./NotificationCenter.css";

const notifications = [
  {
    icon: <ShieldAlert size={18} />,
    title: "Critical SQL Injection detected",
    time: "2 min ago",
    type: "critical",
  },
  {
    icon: <Bug size={18} />,
    title: "Malware quarantined successfully",
    time: "10 min ago",
    type: "warning",
  },
  {
    icon: <FileText size={18} />,
    title: "Weekly security report generated",
    time: "30 min ago",
    type: "info",
  },
  {
    icon: <CheckCircle size={18} />,
    title: "System scan completed",
    time: "1 hour ago",
    type: "success",
  },
];

const NotificationCenter = () => {
  return (
    <div className="notification-card">
      <div className="notification-header">
        <div className="title">
          <Bell size={20} />
          <h3>Notifications</h3>
        </div>

        <button className="mark-btn">
          Mark all as read
        </button>
      </div>

      <div className="notification-list">
        {notifications.map((item, index) => (
          <div className="notification-item" key={index}>
            <div className={`notification-icon ${item.type}`}>
              {item.icon}
            </div>

            <div className="notification-content">
              <h4>{item.title}</h4>
              <span>{item.time}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NotificationCenter;