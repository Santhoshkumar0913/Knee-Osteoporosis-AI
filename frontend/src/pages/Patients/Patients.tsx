import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPatients, createPatient, deletePatient } from '../../services/api';
import type { Patient } from '../../types';
import './Patients.css';

const Patients = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPatientName, setNewPatientName] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      setLoading(true);
      const data = await getPatients();
      setPatients(data);
      setError(null);
    } catch (err) {
      setError('Failed to load patients');
      console.error('Error loading patients:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePatient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPatientName.trim()) return;

    try {
      setCreating(true);
      await createPatient({ name: newPatientName.trim() });
      setNewPatientName('');
      setShowCreateModal(false);
      loadPatients();
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
      loadPatients();
    } catch (err) {
      setError('Failed to delete patient');
      console.error('Error deleting patient:', err);
    }
  };

  if (loading) {
    return <div className="loading">Loading patients...</div>;
  }

  return (
    <div className="patients-container">
      <div className="patients-header">
        <h1>Patients</h1>
        <button 
          className="create-button"
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
        <div className="patients-table">
          <table>
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Name</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr key={patient.id}>
                  <td>{patient.patient_code}</td>
                  <td>{patient.name}</td>
                  <td>{new Date(patient.created_at).toLocaleDateString()}</td>
                  <td>
                    <Link 
                      to={`/patients/${patient.id}`}
                      className="action-button view-button"
                    >
                      View
                    </Link>
                    <button 
                      className="action-button delete-button"
                      onClick={() => handleDeletePatient(patient.id, patient.name)}
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

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Patient</h2>
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
                  className="cancel-button"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="submit-button"
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
