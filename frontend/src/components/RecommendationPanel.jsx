import { useEffect, useState } from "react";
import { getRecommendations } from "../services/api";
import "./RecommendationPanel.css";

const RecommendationPanel = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadRecommendations = async () => {
      try {
        const data = await getRecommendations();
        setRecommendations(data);
      } catch (error) {
        console.error("Failed to load recommendations:", error);
        setRecommendations([]);
      } finally {
        setLoading(false);
      }
    };

    loadRecommendations();
  }, []);

  return (
    <div className="recommend-card">
      <h3>AI Recommendations</h3>

      {loading ? (
        <p>Loading recommendations...</p>
      ) : recommendations.length === 0 ? (
        <p>No recommendations available.</p>
      ) : (
        <ul>
          {recommendations.map((item, index) => (
            <li key={index}>✔ {item}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default RecommendationPanel;