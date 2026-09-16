import axios from 'axios';
import type { Patient, PatientCreate, Analysis, AnalysisCreate, AnalysisListItem } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Patient endpoints
export const getPatients = async (): Promise<Patient[]> => {
  const response = await api.get('/patients');
  return response.data;
};

export const getPatient = async (patientId: number): Promise<Patient> => {
  const response = await api.get(`/patients/${patientId}`);
  return response.data;
};

export const createPatient = async (patient: PatientCreate): Promise<Patient> => {
  const response = await api.post('/patients', patient);
  return response.data;
};

export const deletePatient = async (patientId: number): Promise<void> => {
  await api.delete(`/patients/${patientId}`);
};

// Analysis endpoints
export const createAnalysis = async (analysis: AnalysisCreate): Promise<Analysis> => {
  const formData = new FormData();
  formData.append('patient_id', analysis.patient_id.toString());
  formData.append('age', analysis.age.toString());
  formData.append('gender', analysis.gender);
  formData.append('height', analysis.height.toString());
  formData.append('weight', analysis.weight.toString());
  formData.append('joint_pain', analysis.joint_pain);
  formData.append('pregnancies', analysis.pregnancies.toString());
  formData.append('image', analysis.image);

  const response = await api.post('/analyses', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getPatientAnalyses = async (patientId: number): Promise<AnalysisListItem[]> => {
  const response = await api.get(`/analyses/patient/${patientId}`);
  return response.data;
};

export const getAnalysis = async (analysisId: number): Promise<Analysis> => {
  const response = await api.get(`/analyses/${analysisId}`);
  return response.data;
};

export const deleteAnalysis = async (analysisId: number): Promise<void> => {
  await api.delete(`/analyses/${analysisId}`);
};

export default api;
