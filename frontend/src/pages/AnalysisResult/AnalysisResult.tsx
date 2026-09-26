import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { getAnalysis, getAnalysisImageUrl } from '../../services/api';
import type { Analysis } from '../../types';
import { formatDateOnly } from '../../utils/date';
import './AnalysisResult.css';

const AnalysisResult = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    if (!analysisId) return;
    let active = true;
    getAnalysis(parseInt(analysisId))
      .then((data) => {
        if (!active) return;
        setImageError(false);
        setAnalysis(data);
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setError('Failed to load analysis results');
        console.error('Error loading analysis:', err);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [analysisId]);

  const formatProbability = (value: number) => {
    return (value * 100).toFixed(2);
  };

  const formatScore = (value: number) => {
    return value.toFixed(2);
  };

  if (loading) {
    return <div className="loading page-container">Loading analysis results...</div>;
  }

  if (!analysis) {
    return <div className="error page-container">Analysis not found</div>;
  }

  return (
    <div className="analysis-result-container page-container">
      <div className="breadcrumb">
        <Link to="/patients">Patients</Link>
        <span> / </span>
        <Link to={`/patients/${analysis.patient_id}`}>Patient Details</Link>
        <span> / </span>
        <span>Analysis Result</span>
      </div>

      <div className="page-heading analysis-page-heading">
        <div>
          <h1>Analysis Result</h1>
          <p>Analysis date: {formatDateOnly(analysis.created_at)}</p>
        </div>
        <button
          className="button button-primary"
          onClick={() => navigate(`/analyses/${analysisId}/clinical-support`)}
        >
          View Clinical Support <span aria-hidden="true">→</span>
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="results-grid">
        <section className="result-card xray-card surface-card" aria-labelledby="original-xray-title">
          <h2 id="original-xray-title">Original X-ray</h2>
          {imageError ? (
            <p className="xray-error" role="status">
              The saved X-ray image could not be loaded.
            </p>
          ) : (
            <img
              className="original-xray-image"
              src={getAnalysisImageUrl(analysis.id)}
              alt="Original knee X-ray uploaded for this analysis"
              onError={() => setImageError(true)}
            />
          )}
        </section>

        {/* X-ray Classification */}
        <div className="result-card classification-card surface-card">
          <h2>Model Prediction</h2>
          <div className="classification-result">
            <div className="predicted-class">
              <span className="label">Predicted Class</span>
              <span className={`value status-text status-${analysis.predicted_diagnosis.toLowerCase()}`}>{analysis.predicted_diagnosis}</span>
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
                  className={`bar${analysis.predicted_class === 1 ? ' status-normal' : ''}`}
                  style={{ width: `${formatProbability(analysis.normal_probability)}%` }}
                ></div>
              </div>
              <span className="value">{formatProbability(analysis.normal_probability)}%</span>
            </div>
            <div className="probability-bar">
              <span className="label">Osteopenia</span>
              <div className="bar-container">
                <div 
                  className={`bar${analysis.predicted_class === 2 ? ' status-osteopenia' : ''}`}
                  style={{ width: `${formatProbability(analysis.osteopenia_probability)}%` }}
                ></div>
              </div>
              <span className="value">{formatProbability(analysis.osteopenia_probability)}%</span>
            </div>
            <div className="probability-bar">
              <span className="label">Osteoporosis</span>
              <div className="bar-container">
                <div 
                  className={`bar${analysis.predicted_class === 3 ? ' status-osteoporosis' : ''}`}
                  style={{ width: `${formatProbability(analysis.osteoporosis_probability)}%` }}
                ></div>
              </div>
              <span className="value">{formatProbability(analysis.osteoporosis_probability)}%</span>
            </div>
          </div>
        </div>

        {/* Bone Score Estimates */}
        <div className="result-card scores-card surface-card">
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
        <div className="result-card patient-info-card surface-card">
          <h2>Clinical Context</h2>
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
            <div className="detail-row">
              <span className="label">Menopausal Status:</span>
              <span className="value">{analysis.gender.toLowerCase() === 'male' ? 'Not applicable' : analysis.menopausal_status || 'Not specified'}</span>
            </div>
            <div className="detail-row">
              <span className="label">Smoking:</span>
              <span className="value">{analysis.smoking || 'Not specified'}</span>
            </div>
            <div className="detail-row">
              <span className="label">Alcohol:</span>
              <span className="value">{analysis.alcohol || 'Not specified'}</span>
            </div>
            <div className="detail-row">
              <span className="label">Previous Fracture:</span>
              <span className="value">{analysis.previous_fracture || 'Not specified'}</span>
            </div>
            <div className="detail-row">
              <span className="label">Long-term Steroid Use:</span>
              <span className="value">{analysis.long_term_steroid_use || 'Not specified'}</span>
            </div>
            <div className="detail-row">
              <span className="label">Model Version:</span>
              <span className="value">{analysis.model_version}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="result-actions">
        <Link 
          to={`/patients/${analysis.patient_id}`}
          className="button button-secondary"
        >
          View Patient History
        </Link>
        <button
          className="button button-primary"
          onClick={() => navigate(`/patients/${analysis.patient_id}/analysis/new`)}
        >
          New Analysis
        </button>
      </div>
    </div>
  );
};

export default AnalysisResult;
