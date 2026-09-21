import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getAnalysis, getClinicalSupport } from '../../services/api';
import type { Analysis, ClinicalSupportResponse } from '../../types';
import './ClinicalSupport.css';

const ClinicalSupport = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [clinicalSupport, setClinicalSupport] = useState<ClinicalSupportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
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
      setError('Failed to load analysis');
      console.error('Error loading analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSupport = async () => {
    if (!analysisId) return;

    try {
      setGenerating(true);
      setError(null);
      const data = await getClinicalSupport(parseInt(analysisId));
      setClinicalSupport(data);
    } catch (err) {
      setError('Failed to generate clinical support. Please try again.');
      console.error('Error generating clinical support:', err);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading analysis...</div>;
  }

  if (!analysis) {
    return <div className="error">Analysis not found</div>;
  }

  return (
    <div className="clinical-support-container">
      <div className="breadcrumb">
        <span>Analysis ID: {analysisId}</span>
      </div>

      <h1>Clinical Support</h1>

      {error && <div className="error-message">{error}</div>}

      <div className="analysis-summary">
        <h2>Analysis Summary</h2>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="label">Patient ID:</span>
            <span className="value">{analysis.patient_id}</span>
          </div>
          <div className="summary-item">
            <span className="label">Diagnosis:</span>
            <span className="value">{analysis.predicted_diagnosis}</span>
          </div>
          <div className="summary-item">
            <span className="label">Confidence:</span>
            <span className="value">{(analysis.confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="summary-item">
            <span className="label">T-score:</span>
            <span className="value">{analysis.t_score.toFixed(2)}</span>
          </div>
          <div className="summary-item">
            <span className="label">Z-score:</span>
            <span className="value">{analysis.z_score.toFixed(2)}</span>
          </div>
        </div>
      </div>

      {!clinicalSupport ? (
        <div className="generate-section">
          <p>
            Get evidence-based clinical support information based on your analysis results
            and medical literature.
          </p>
          <button
            className="generate-button"
            onClick={handleGenerateSupport}
            disabled={generating}
          >
            {generating ? 'Generating...' : 'Generate Clinical Support'}
          </button>
        </div>
      ) : (
        <div className="clinical-support-content">
          <div className="support-section">
            <h3>Explanation</h3>
            <p>{clinicalSupport.explanation}</p>
          </div>

          {clinicalSupport.what_you_can_do_now.length > 0 && (
            <div className="support-section">
              <h3>What You Can Do Now</h3>
              <ul>
                {clinicalSupport.what_you_can_do_now.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {clinicalSupport.talk_to_your_doctor_about.length > 0 && (
            <div className="support-section">
              <h3>Talk to Your Doctor About</h3>
              <ul>
                {clinicalSupport.talk_to_your_doctor_about.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {clinicalSupport.testing_and_follow_up.length > 0 && (
            <div className="support-section">
              <h3>Testing and Follow-up</h3>
              <ul>
                {clinicalSupport.testing_and_follow_up.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {clinicalSupport.treatment_information.length > 0 && (
            <div className="support-section">
              <h3>Treatment Information</h3>
              <ul>
                {clinicalSupport.treatment_information.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="support-section">
            <h3>Sources</h3>
            <ul className="sources-list">
              {clinicalSupport.sources.map((source, index) => (
                <li key={index}>
                  {source.organization} — {source.year}
                </li>
              ))}
            </ul>
          </div>

          <div className="grounding-note">
            <p>{clinicalSupport.grounding_note}</p>
          </div>

          <div className="disclaimer">
            <p>{clinicalSupport.disclaimer}</p>
          </div>

          <div className="support-actions">
            <button
              className="regenerate-button"
              onClick={handleGenerateSupport}
              disabled={generating}
            >
              {generating ? 'Regenerating...' : 'Regenerate'}
            </button>
          </div>
        </div>
      )}

      <div className="page-actions">
        <button
          className="back-button"
          onClick={() => navigate(`/analyses/${analysisId}`)}
        >
          Back to Analysis Results
        </button>
      </div>
    </div>
  );
};

export default ClinicalSupport;