import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getAnalysis } from '../../services/api';
import type { Analysis } from '../../types';
import './AnalysisResult.css';

const AnalysisResult = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (analysisId) {
      loadAnalysis();
    }
  }, [analysisId]);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      const data = await getAnalysis(parseInt(analysisId!));
      setAnalysis(data);
      setError(null);
    } catch (err) {
      setError('Failed to load analysis results');
      console.error('Error loading analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatProbability = (value: number) => {
    return (value * 100).toFixed(2);
  };

  const formatScore = (value: number) => {
    return value.toFixed(2);
  };

  if (loading) {
    return <div className="loading">Loading analysis results...</div>;
  }

  if (!analysis) {
    return <div className="error">Analysis not found</div>;
  }

  return (
    <div className="analysis-result-container">
      <div className="breadcrumb">
        <Link to="/patients">Patients</Link>
        <span> / </span>
        <Link to={`/patients/${analysis.patient_id}`}>Patient Details</Link>
        <span> / </span>
        <span>Analysis Result</span>
      </div>

      <h1>Analysis Results</h1>

      {error && <div className="error-message">{error}</div>}

      <div className="results-grid">
        {/* X-ray Classification */}
        <div className="result-card classification-card">
          <h2>X-ray Classification</h2>
          <div className="classification-result">
            <div className="predicted-class">
              <span className="label">Predicted Class</span>
              <span className="value">{analysis.predicted_diagnosis}</span>
            </div>
            <div className="confidence">
              <span className="label">Confidence</span>
              <span className="value">{formatProbability(analysis.confidence)}%</span>
            </div>
          </div>
          
          <div className="probabilities">
            <h3>Class Probabilities</h3>
            <div className="probability-bar">
              <span className="label">Normal</span>
              <div className="bar-container">
                <div 
                  className="bar" 
                  style={{ width: `${formatProbability(analysis.normal_probability)}%` }}
                ></div>
              </div>
              <span className="value">{formatProbability(analysis.normal_probability)}%</span>
            </div>
            <div className="probability-bar">
              <span className="label">Osteopenia</span>
              <div className="bar-container">
                <div 
                  className="bar highlighted" 
                  style={{ width: `${formatProbability(analysis.osteopenia_probability)}%` }}
                ></div>
              </div>
              <span className="value">{formatProbability(analysis.osteopenia_probability)}%</span>
            </div>
            <div className="probability-bar">
              <span className="label">Osteoporosis</span>
              <div className="bar-container">
                <div 
                  className="bar" 
                  style={{ width: `${formatProbability(analysis.osteoporosis_probability)}%` }}
                ></div>
              </div>
              <span className="value">{formatProbability(analysis.osteoporosis_probability)}%</span>
            </div>
          </div>
        </div>

        {/* Bone Score Estimates */}
        <div className="result-card scores-card">
          <h2>Bone Score Estimates</h2>
          
          <div className="score-result">
            <h3>Model-estimated T-score</h3>
            <div className="score-value">{formatScore(analysis.t_score)}</div>
            <div className="score-range">
              Estimated range: {formatScore(analysis.t_score_lower)} to {formatScore(analysis.t_score_upper)}
            </div>
          </div>

          <div className="score-result">
            <h3>Model-estimated Z-score</h3>
            <div className="score-value">{formatScore(analysis.z_score)}</div>
            <div className="score-range">
              Estimated range: {formatScore(analysis.z_score_lower)} to {formatScore(analysis.z_score_upper)}
            </div>
          </div>

          <div className="disclaimer">
            <p>These are model estimates, not measured DXA/QUS values. The ranges represent empirical prediction-error margins.</p>
          </div>
        </div>

        {/* Patient Information */}
        <div className="result-card patient-info-card">
          <h2>Patient Information</h2>
          <div className="patient-details">
            <div className="detail-row">
              <span className="label">Patient ID:</span>
              <span className="value">{analysis.patient_id}</span>
            </div>
            <div className="detail-row">
              <span className="label">Age:</span>
              <span className="value">{analysis.age} years</span>
            </div>
            <div className="detail-row">
              <span className="label">Gender:</span>
              <span className="value">{analysis.gender}</span>
            </div>
            <div className="detail-row">
              <span className="label">Height:</span>
              <span className="value">{analysis.height} m</span>
            </div>
            <div className="detail-row">
              <span className="label">Weight:</span>
              <span className="value">{analysis.weight} kg</span>
            </div>
            <div className="detail-row">
              <span className="label">BMI:</span>
              <span className="value">{analysis.bmi}</span>
            </div>
            <div className="detail-row">
              <span className="label">Joint Pain:</span>
              <span className="value">{analysis.joint_pain}</span>
            </div>
            <div className="detail-row">
              <span className="label">Number of Pregnancies:</span>
              <span className="value">{analysis.pregnancies}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="result-actions">
        <Link 
          to={`/patients/${analysis.patient_id}`}
          className="action-button secondary-button"
        >
          View Patient History
        </Link>
        <button
          className="action-button primary-button"
          onClick={() => navigate(`/patients/${analysis.patient_id}/analysis/new`)}
        >
          New Analysis
        </button>
      </div>
    </div>
  );
};

export default AnalysisResult;
