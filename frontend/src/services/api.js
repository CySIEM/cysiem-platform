import axios from "axios";

// ===============================
// Axios Instance
// ===============================

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// ===============================
// AI Security Copilot
// ===============================

export const askCopilot = async (question) => {
  try {
    const response = await api.post("/ask", {
      question,
    });

    return response.data;
  } catch (error) {
    console.error("AI Copilot Error:", error);
    throw error;
  }
};

// ===============================
// Dashboard Statistics
// ===============================

export const getDashboardStats = async () => {
  try {
    const response = await api.get("/dashboard");
    return response.data;
  } catch (error) {
    console.error("Dashboard API Error:", error);

    return {
      critical: 0,
      high: 0,
      medium: 0,
      assets: 0,
    };
  }
};

// ===============================
// Recent Alerts
// ===============================

export const getAlerts = async () => {
  try {
    const response = await api.get("/alerts");
    return response.data;
  } catch (error) {
    console.error("Alerts API Error:", error);
    return [];
  }
};

// ===============================
// Threat Activity
// ===============================

export const getThreatActivity = async () => {
  try {
    const response = await api.get("/threats");
    return response.data;
  } catch (error) {
    console.error("Threat Activity API Error:", error);
    return [];
  }
};

// ===============================
// AI Recommendations
// ===============================

export const getRecommendations = async () => {
  try {
    const response = await api.get("/recommendations");
    return response.data;
  } catch (error) {
    console.error("Recommendations API Error:", error);
    return [];
  }
};

// ===============================
// Reports
// ===============================

export const getReports = async () => {
  try {
    const response = await api.get("/reports");
    return response.data;
  } catch (error) {
    console.error("Reports API Error:", error);
    return [];
  }
};

export default api;