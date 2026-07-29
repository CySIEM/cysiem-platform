import {
  Server,
  Database,
  Bot,
  ShieldCheck,
  Cpu,
  HardDrive,
  MemoryStick,
} from "lucide-react";

import "./SystemHealth.css";

const services = [
  { icon: <Server size={18} />, name: "Backend API", status: "Online" },
  { icon: <Bot size={18} />, name: "AI Copilot", status: "Running" },
  { icon: <Database size={18} />, name: "Database", status: "Connected" },
  { icon: <ShieldCheck size={18} />, name: "Wazuh Agent", status: "Active" },
];

const resources = [
  { icon: <Cpu size={18} />, name: "CPU Usage", value: "24%" },
  { icon: <MemoryStick size={18} />, name: "Memory Usage", value: "61%" },
  { icon: <HardDrive size={18} />, name: "Disk Usage", value: "38%" },
];

const SystemHealth = () => {
  return (
    <div className="system-health-card">
      <h3>System Health</h3>

      <div className="services">
        {services.map((service, index) => (
          <div className="service-item" key={index}>
            <div className="service-left">
              {service.icon}
              <span>{service.name}</span>
            </div>

            <span className="status online">{service.status}</span>
          </div>
        ))}
      </div>

      <hr />

      <div className="resources">
        {resources.map((resource, index) => (
          <div className="resource-item" key={index}>
            <div className="resource-left">
              {resource.icon}
              <span>{resource.name}</span>
            </div>

            <strong>{resource.value}</strong>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SystemHealth;