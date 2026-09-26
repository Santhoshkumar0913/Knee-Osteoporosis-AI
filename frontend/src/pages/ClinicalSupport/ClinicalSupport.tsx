import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { downloadClinicalSupportPdf, getAnalysis, getAnalysisImageUrl, getClinicalSupport, getPatient } from '../../services/api';
import type { Analysis, ClinicalSupportResponse, Patient } from '../../types';
import { formatDateOnly } from '../../utils/date';
import './ClinicalSupport.css';

const ClinicalSupport = () => {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [clinicalSupport, setClinicalSupport] = useState<ClinicalSupportResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    if (!analysisId) return;
    let active = true;
    getAnalysis(parseInt(analysisId))
      .then(async (data) => {
        if (!active) return;
        setAnalysis(data);
        setImageError(false);
        const patientData = await getPatient(data.patient_id);
        if (!active) return;
        setPatient(patientData);
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setError('Failed to load analysis');
        console.error('Error loading analysis:', err);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [analysisId]);

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

  const handleDownloadPdf = async () => {
    if (!analysisId || !clinicalSupport) return;

    try {
      setDownloadingPdf(true);
      setPdfError(null);
      const pdf = await downloadClinicalSupportPdf(parseInt(analysisId), clinicalSupport);
      const downloadUrl = URL.createObjectURL(pdf);
      const link = document.createElement('a');
      link.href = downloadUrl;
      const safePatientCode = (patient?.patient_code || 'patient').replace(/[^a-zA-Z0-9._-]/g, '_');
      link.download = `clinical_support_report_${safePatientCode}_${analysisId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 0);
    } catch (err) {
      setPdfError('Failed to download the PDF report. Please try again.');
      console.error('Error downloading Clinical Support PDF:', err);
    } finally {
      setDownloadingPdf(false);
    }
  };

  if (loading) {
    return <div className="loading page-container">Loading analysis...</div>;
  }

  if (!analysis) {
    return <div className="error page-container">Analysis not found</div>;
  }

  return (
    <div className="clinical-support-container page-container">
      <div className="breadcrumb">
        <Link to="/patients">Patients</Link>
        <span aria-hidden="true">›</span>
        {patient && <><Link to={`/patients/${patient.id}`}>{patient.patient_code}</Link><span aria-hidden="true">›</span></>}
        <Link to={`/analyses/${analysisId}`}>Analysis</Link>
        <span aria-hidden="true">›</span>
        <span>Clinical Support</span>
      </div>

      <div className="page-heading clinical-page-heading">
        <div>
          <h1>Clinical Support</h1>
          <p>Evidence-grounded information based on this saved analysis.</p>
        </div>
        <Link to={`/analyses/${analysisId}`} className="button button-secondary">Back to Analysis</Link>
      </div>

      {error && (
        <div className="error-section">
          <div className="error-message">{error}</div>
          <button
            className="retry-button"
            onClick={handleGenerateSupport}
            disabled={generating}
          >
            {generating ? 'Retrying...' : 'Retry'}
          </button>
        </div>
      )}

      <section className="analysis-summary xray-summary surface-card">
        <h2>Original X-ray</h2>
        {imageError ? (
          <p className="xray-error" role="status">The saved X-ray image could not be loaded.</p>
        ) : (
          <img
            className="clinical-xray-image"
            src={getAnalysisImageUrl(analysis.id)}
            alt="Original knee X-ray uploaded for this analysis"
            onError={() => setImageError(true)}
          />
        )}
      </section>

      <section className="analysis-summary patient-summary surface-card">
        <h2>Patient Information</h2>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="label">Patient Code</span>
            <span className="value">{patient?.patient_code || '—'}</span>
          </div>
          <div className="summary-item">
            <span className="label">Name</span>
            <span className="value">{patient?.name || '—'}</span>
          </div>
          <div className="summary-item">
            <span className="label">Analysis Date</span>
            <span className="value">{formatDateOnly(analysis.created_at)}</span>
          </div>
        </div>
      </section>

      <section className="analysis-summary prediction-summary surface-card">
        <h2>AI Prediction</h2>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="label">Predicted Class</span>
            <span className={`value status-text status-${analysis.predicted_diagnosis.toLowerCase()}`}>{analysis.predicted_diagnosis}</span>
          </div>
          <div className="summary-item">
            <span className="label">Confidence</span>
            <span className="value">{(analysis.confidence * 100).toFixed(1)}%</span>
          </div>
          <div className="summary-item">
            <span className="label">Normal</span>
            <span className="value">{(analysis.normal_probability * 100).toFixed(1)}%</span>
          </div>
          <div className="summary-item">
            <span className="label">Osteopenia</span>
            <span className="value">{(analysis.osteopenia_probability * 100).toFixed(1)}%</span>
          </div>
          <div className="summary-item">
            <span className="label">Osteoporosis</span>
            <span className="value">{(analysis.osteoporosis_probability * 100).toFixed(1)}%</span>
          </div>
        </div>
      </section>

      <section className="analysis-summary bone-summary surface-card">
        <h2>Bone Scores</h2>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="label">Model-estimated T-score</span>
            <span className="value">{analysis.t_score.toFixed(2)}</span>
          </div>
          <div className="summary-item">
            <span className="label">T-score Range:</span>
            <span className="value">{analysis.t_score_lower.toFixed(2)} to {analysis.t_score_upper.toFixed(2)}</span>
          </div>
          <div className="summary-item">
            <span className="label">Model-estimated Z-score</span>
            <span className="value">{analysis.z_score.toFixed(2)}</span>
          </div>
          <div className="summary-item">
            <span className="label">Z-score Range:</span>
            <span className="value">{analysis.z_score_lower.toFixed(2)} to {analysis.z_score_upper.toFixed(2)}</span>
          </div>
        </div>
      </section>

      <section className="analysis-summary context-summary surface-card">
        <h2>Clinical Context</h2>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="label">Age:</span>
            <span className="value">{analysis.age}</span>
          </div>
          <div className="summary-item">
            <span className="label">Gender:</span>
            <span className="value">{analysis.gender}</span>
          </div>
          <div className="summary-item">
            <span className="label">Height:</span>
            <span className="value">{analysis.height.toFixed(2)} m</span>
          </div>
          <div className="summary-item">
            <span className="label">Weight:</span>
            <span className="value">{analysis.weight} kg</span>
          </div>
          <div className="summary-item">
            <span className="label">BMI:</span>
            <span className="value">{analysis.bmi.toFixed(1)}</span>
          </div>
          <div className="summary-item">
            <span className="label">Joint Pain:</span>
            <span className="value">{analysis.joint_pain}</span>
          </div>
          <div className="summary-item">
            <span className="label">Number of Pregnancies:</span>
            <span className="value">{analysis.pregnancies}</span>
          </div>
          <div className="summary-item">
            <span className="label">Menopausal Status:</span>
            <span className="value">{analysis.gender.toLowerCase() === 'male' ? 'Not applicable' : analysis.menopausal_status || 'Not specified'}</span>
          </div>
          <div className="summary-item">
            <span className="label">Smoking:</span>
            <span className="value">{analysis.smoking || 'Not specified'}</span>
          </div>
          <div className="summary-item">
            <span className="label">Alcohol:</span>
            <span className="value">{analysis.alcohol || 'Not specified'}</span>
          </div>
          <div className="summary-item">
            <span className="label">Previous Fracture:</span>
            <span className="value">{analysis.previous_fracture || 'Not specified'}</span>
          </div>
          <div className="summary-item">
            <span className="label">Long-term Steroid Use:</span>
            <span className="value">{analysis.long_term_steroid_use || 'Not specified'}</span>
          </div>
        </div>
      </section>

      {!clinicalSupport ? (
        <div className="generate-section surface-card">
          <p>
            Get evidence-based clinical support information based on your analysis results
            and medical literature.
          </p>
          <button
            className="button button-primary generate-button"
            onClick={handleGenerateSupport}
            disabled={generating}
          >
            {generating ? 'Generating...' : 'Generate Clinical Support'}
          </button>
        </div>
      ) : (
        <div className="clinical-support-content surface-card">
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
              className="button button-secondary regenerate-button"
              onClick={handleGenerateSupport}
              disabled={generating}
            >
              {generating ? 'Regenerating...' : 'Regenerate'}
            </button>
            <button
              className="button button-primary download-pdf-button"
              onClick={handleDownloadPdf}
              disabled={downloadingPdf || generating}
            >
              {downloadingPdf ? 'Preparing PDF...' : 'Download PDF Report'}
            </button>
          </div>
          {pdfError && <p className="pdf-error" role="alert">{pdfError}</p>}
        </div>
      )}

      <div className="page-actions">
        <button
          className="button button-secondary back-button"
          onClick={() => navigate(`/analyses/${analysisId}`)}
        >
          Back to Analysis Results
        </button>
      </div>
    </div>
  );
};

export default ClinicalSupport;
