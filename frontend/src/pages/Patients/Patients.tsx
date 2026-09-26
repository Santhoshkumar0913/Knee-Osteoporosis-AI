import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getPatients, createPatient, deletePatient } from '../../services/api';
import type { Patient } from '../../types';
import { formatDateOnly } from '../../utils/date';
import './Patients.css';

const Patients = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPatientName, setNewPatientName] = useState('');
  const [creating, setCreating] = useState(false);

  const loadPatients = useCallback(async () => {
    try {
      const data = await getPatients();
      setPatients(data);
      setError(null);
    } catch (err) {
      setError('Failed to load patients');
      console.error('Error loading patients:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    getPatients()
      .then((data) => {
        if (!active) return;
        setPatients(data);
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setError('Failed to load patients');
        console.error('Error loading patients:', err);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, []);

  const handleCreatePatient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPatientName.trim()) return;

    try {
      setCreating(true);
      await createPatient({ name: newPatientName.trim() });
      setNewPatientName('');
      setShowCreateModal(false);
      await loadPatients();
    } catch (err) {
      setError('Failed to create patient');
      console.error('Error creating patient:', err);
    } finally {
      setCreating(false);
    }
  };

  const handleDeletePatient = async (patientId: number, patientName: string) => {
    if (!window.confirm(`Are you sure you want to delete patient "${patientName}"? This will also delete all their analyses and images.`)) {
      return;
    }

    try {
      await deletePatient(patientId);
      await loadPatients();
    } catch (err) {
      setError('Failed to delete patient');
      console.error('Error deleting patient:', err);
    }
  };

  if (loading) {
    return <div className="loading">Loading patients...</div>;
  }

  return (
    <div className="patients-container page-container">
      <div className="patients-header page-heading">
        <div>
          <h1>Patients</h1>
          <p>Manage patients and their analysis history.</p>
        </div>
        <button 
          className="button button-primary create-button"
          onClick={() => setShowCreateModal(true)}
        >
          + New Patient
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {patients.length === 0 ? (
        <div className="empty-state">
          <p>No patients yet. Create your first patient to get started.</p>
        </div>
      ) : (
        <div className="patients-table surface-card">
          <table>
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Name</th>
                <th>Created Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr key={patient.id}>
                  <td>{patient.patient_code}</td>
                  <td>{patient.name}</td>
                  <td>{formatDateOnly(patient.created_at)}</td>
                  <td>
                    <div className="table-actions">
                      <Link
                        to={`/patients/${patient.id}`}
                        className="button button-secondary button-small view-button"
                      >
                        View
                      </Link>
                      <button
                        className="button button-danger button-small delete-button"
                        onClick={() => handleDeletePatient(patient.id, patient.name)}
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

      {showCreateModal && (
        <div className="modal-overlay" onMouseDown={() => setShowCreateModal(false)}>
          <div
            className="modal-content"
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-patient-title"
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="modal-heading">
              <div>
                <h2 id="create-patient-title">Create New Patient</h2>
                <p>Enter the patient name to create a record.</p>
              </div>
              <button type="button" className="modal-close" aria-label="Close dialog" onClick={() => setShowCreateModal(false)}>×</button>
            </div>
            <form onSubmit={handleCreatePatient}>
              <div className="form-group">
                <label htmlFor="patientName">Patient Name</label>
                <input
                  id="patientName"
                  type="text"
                  value={newPatientName}
                  onChange={(e) => setNewPatientName(e.target.value)}
                  placeholder="Enter patient name"
                  required
                />
              </div>
              <div className="modal-actions">
                <button 
                  type="button"
                  className="button button-secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="button button-primary"
                  disabled={creating}
                >
                  {creating ? 'Creating...' : 'Create Patient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Patients;
