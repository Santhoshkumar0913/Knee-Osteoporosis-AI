export interface Patient {
  id: number;
  patient_code: string;
  name: string;
  created_at: string;
  analyses_count?: number;
}

export interface Analysis {
  id: number;
  patient_id: number;
  image_path: string;
  created_at: string;
  
  // Clinical inputs
  age: number;
  gender: string;
  height: number;
  weight: number;
  bmi: number;
  joint_pain: string;
  pregnancies: number;
  
  // DINOv2 results
  predicted_class: number;
  predicted_diagnosis: string;
  normal_probability: number;
  osteopenia_probability: number;
  osteoporosis_probability: number;
  confidence: number;
  
  // T-score results
  t_score: number;
  t_score_lower: number;
  t_score_upper: number;
  
  // Z-score results
  z_score: number;
  z_score_lower: number;
  z_score_upper: number;
  
  // Model version
  model_version: string;
}

export interface AnalysisListItem {
  id: number;
  patient_id: number;
  created_at: string;
  predicted_diagnosis: string;
  confidence: number;
  t_score: number;
  z_score: number;
}

export interface PatientCreate {
  name: string;
}

export interface AnalysisCreate {
  patient_id: number;
  age: number;
  gender: string;
  height: number;
  weight: number;
  joint_pain: string;
  pregnancies: number;
  image: File;
}
