import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getPatient, getPatientAnalyses, deletePatient, deleteAnalysis } from '../../services/api';
import type { Patient, AnalysisListItem } from '../../types';
import './PatientDetails.css';

const PatientDetails = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (patientId) {
      loadPatientData();
    }
  }, [patientId]);

  const loadPatientData = async () => {
    try {
      setLoading(true);
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
  };

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
      loadPatientData();
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
    <div className="patient-details-container">
      <div className="breadcrumb">
        <Link to="/patients">Patients</Link>
        <span> / </span>
        <span>{patient.patient_code}</span>
      </div>

      <div className="patient-header">
        <div className="patient-info">
          <h1>{patient.patient_code} — {patient.name}</h1>
          <p className="patient-meta">
            Created: {new Date(patient.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="patient-actions">
          <Link 
            to={`/patients/${patient.id}/analysis/new`}
            className="action-button primary-button"
          >
            + New Analysis
          </Link>
          <button 
            className="action-button danger-button"
            onClick={handleDeletePatient}
          >
            Delete Patient
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="analyses-section">
        <h2>Analysis History</h2>
        
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
                  <th>Diagnosis</th>
                  <th>Confidence</th>
                  <th>T-score</th>
                  <th>Z-score</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {analyses.map((analysis) => (
                  <tr key={analysis.id}>
                    <td>{new Date(analysis.created_at).toLocaleDateString()}</td>
                    <td>{analysis.predicted_diagnosis}</td>
                    <td>{(analysis.confidence * 100).toFixed(2)}%</td>
                    <td>{analysis.t_score.toFixed(2)}</td>
                    <td>{analysis.z_score.toFixed(2)}</td>
                    <td>
                      <Link 
                        to={`/analyses/${analysis.id}`}
                        className="action-button view-button"
                      >
                        View
                      </Link>
                      <button 
                        className="action-button delete-button"
                        onClick={() => handleDeleteAnalysis(analysis.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientDetails;
