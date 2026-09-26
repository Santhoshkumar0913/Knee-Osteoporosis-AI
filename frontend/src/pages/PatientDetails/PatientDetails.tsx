import { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPatient, getPatientAnalyses, deletePatient, deleteAnalysis } from '../../services/api';
import type { Patient, AnalysisListItem } from '../../types';
import { formatDateOnly } from '../../utils/date';
import './PatientDetails.css';

const PatientDetails = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadPatientData = useCallback(async () => {
    if (!patientId) return;
    try {
      const [patientData, analysesData] = await Promise.all([
        getPatient(parseInt(patientId!)),
        getPatientAnalyses(parseInt(patientId!))
      ]);
      setPatient(patientData);
      setAnalyses(analysesData);
      setError(null);
    } catch (err) {
      setError('Failed to load patient data');
      console.error('Error loading patient data:', err);
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    if (!patientId) return;
    let active = true;
    const parsedPatientId = parseInt(patientId);
    Promise.all([getPatient(parsedPatientId), getPatientAnalyses(parsedPatientId)])
      .then(([patientData, analysesData]) => {
        if (!active) return;
        setPatient(patientData);
        setAnalyses(analysesData);
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setError('Failed to load patient data');
        console.error('Error loading patient data:', err);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [patientId]);

  const handleDeletePatient = async () => {
    if (!patient) return;
    
    if (!window.confirm(`Are you sure you want to delete patient "${patient.name}"? This will also delete all their analyses and images.`)) {
      return;
    }

    try {
      await deletePatient(patient.id);
      navigate('/patients');
    } catch (err) {
      setError('Failed to delete patient');
      console.error('Error deleting patient:', err);
    }
  };

  const handleDeleteAnalysis = async (analysisId: number) => {
    if (!window.confirm('Are you sure you want to delete this analysis?')) {
      return;
    }

    try {
      await deleteAnalysis(analysisId);
      await loadPatientData();
    } catch (err) {
      setError('Failed to delete analysis');
      console.error('Error deleting analysis:', err);
    }
  };

  if (loading) {
    return <div className="loading">Loading patient details...</div>;
  }

  if (!patient) {
    return <div className="error">Patient not found</div>;
  }

  return (
    <div className="patient-details-container page-container">
      <div className="breadcrumb">
        <Link to="/patients">Patients</Link>
        <span aria-hidden="true">›</span>
        <span>{patient.patient_code}</span>
      </div>

      <div className="patient-header page-heading">
        <div className="patient-info">
          <h1>Patient Details</h1>
          <p className="patient-meta">{patient.patient_code} <span aria-hidden="true">·</span> {patient.name}</p>
        </div>
        <div className="patient-actions">
          <Link 
            to={`/patients/${patient.id}/analysis/new`}
            className="button button-primary"
          >
            + New Analysis
          </Link>
          <button 
            className="button button-danger"
            onClick={handleDeletePatient}
          >
            Delete Patient
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <section className="patient-information surface-card" aria-labelledby="patient-information-title">
        <h2 id="patient-information-title">Patient Information</h2>
        <dl className="patient-information-grid">
          <div><dt>Patient ID</dt><dd>{patient.id}</dd></div>
          <div><dt>Patient Code</dt><dd>{patient.patient_code}</dd></div>
          <div><dt>Name</dt><dd>{patient.name}</dd></div>
          <div><dt>Created Date</dt><dd>{formatDateOnly(patient.created_at)}</dd></div>
          <div><dt>Total Analyses</dt><dd>{patient.analyses_count ?? analyses.length}</dd></div>
        </dl>
      </section>

      <section className="analyses-section surface-card" aria-labelledby="analysis-history-title">
        <div className="section-heading">
          <div>
            <h2 id="analysis-history-title">Analysis History</h2>
            <p>Previous saved analyses for this patient.</p>
          </div>
        </div>
        
        {analyses.length === 0 ? (
          <div className="empty-state">
            <p>No analyses yet. Create your first analysis to get started.</p>
          </div>
        ) : (
          <div className="analyses-table">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Prediction</th>
                  <th>Confidence</th>
                  <th>T-score</th>
                  <th>Z-score</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {analyses.map((analysis) => (
                  <tr key={analysis.id}>
                    <td>{formatDateOnly(analysis.created_at)}</td>
                    <td><span className={`status-pill status-${analysis.predicted_diagnosis.toLowerCase()}`}>{analysis.predicted_diagnosis}</span></td>
                    <td>{(analysis.confidence * 100).toFixed(2)}%</td>
                    <td>{analysis.t_score.toFixed(2)}</td>
                    <td>{analysis.z_score.toFixed(2)}</td>
                    <td>
                      <div className="history-actions">
                      <Link 
                        to={`/analyses/${analysis.id}`}
                        className="button button-secondary button-small"
                      >
                        View
                      </Link>
                      <button 
                        className="button button-danger button-small"
                        onClick={() => handleDeleteAnalysis(analysis.id)}
                      >
                        Delete
                      </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};

export default PatientDetails;
