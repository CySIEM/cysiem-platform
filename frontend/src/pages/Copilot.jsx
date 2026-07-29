import { useState } from "react";
import { askCopilot } from "../services/api";
import "./Copilot.css";

const Copilot = () => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return;

    setLoading(true);
    setAnswer("");

    try {
      const data = await askCopilot(question);

      setAnswer(
        data.answer ||
        data.response ||
        "No response received from AI."
      );
    } catch (error) {
      console.error(error);
      setAnswer("Sorry for Inconvenience, please try again later.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="copilot-page">
      <h1>AI Security Copilot</h1>

      <p>Ask any cybersecurity question powered by RAG + Ollama.</p>

      <textarea
        placeholder="Example: Explain SQL Injection"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />

      <button onClick={handleAsk}>Ask AI</button>

      {loading && <div className="loading">Thinking...</div>}

      {answer && (
        <div className="answer-box">
          <h3>Response</h3>
          <p>{answer}</p>
        </div>
      )}
    </div>
  );
};

export default Copilot;