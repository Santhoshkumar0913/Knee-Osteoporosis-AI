import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getPatient, createAnalysis } from '../../services/api';
import type { Patient } from '../../types';
import './NewAnalysis.css';

const NewAnalysis = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Form state
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [height, setHeight] = useState('');
  const [weight, setWeight] = useState('');
  const [jointPain, setJointPain] = useState('');
  const [pregnancies, setPregnancies] = useState('');
  // Phase 2 additional clinical fields
  const [menopausalStatus, setMenopausalStatus] = useState('');
  const [smoking, setSmoking] = useState('');
  const [alcohol, setAlcohol] = useState('');
  const [previousFracture, setPreviousFracture] = useState('');
  const [longTermSteroidUse, setLongTermSteroidUse] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);

  useEffect(() => {
    if (patientId) {
      loadPatient();
    }
  }, [patientId]);

  const loadPatient = async () => {
    try {
      setLoading(true);
      const data = await getPatient(parseInt(patientId!));
      setPatient(data);
      setError(null);
    } catch (err) {
      setError('Failed to load patient');
      console.error('Error loading patient:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculateBMI = () => {
    if (height && weight) {
      const h = parseFloat(height);
      const w = parseFloat(weight);
      if (h > 0 && w > 0) {
        return (w / (h * h)).toFixed(2);
      }
    }
    return '';
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const allowedTypes = ['image/png', 'image/jpeg', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        setError('Please upload a PNG, JPG, JPEG, or WEBP image');
        return;
      }

      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        setError('Image size must be less than 10MB');
        return;
      }

      setImage(file);
      setError(null);

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!patient || !image) {
      setError('Please fill in all required fields and upload an image');
      return;
    }

    // Validate form
    if (!age || !gender || !height || !weight || !jointPain) {
      setError('Please fill in all required fields');
      return;
    }

    const ageNum = parseInt(age);
    const heightNum = parseFloat(height);
    const weightNum = parseFloat(weight);
    const pregnanciesNum = parseInt(pregnancies || '0');

    // Gender-specific validation
    if (gender === 'female' && !pregnancies) {
      setError('Number of pregnancies is required for female patients');
      return;
    }

    if (gender === 'male' && pregnanciesNum !== 0) {
      setError('Number of pregnancies must be 0 for male patients');
      return;
    }

    try {
      setAnalyzing(true);
      setError(null);

      const analysisData = {
        patient_id: patient.id,
        age: ageNum,
        gender,
        height: heightNum,
        weight: weightNum,
        joint_pain: jointPain,
        pregnancies: pregnanciesNum,
        // Phase 2 additional clinical fields
        menopausal_status: gender === 'female' ? menopausalStatus || undefined : undefined,
        smoking: smoking || undefined,
        alcohol: alcohol || undefined,
        previous_fracture: previousFracture || undefined,
        long_term_steroid_use: longTermSteroidUse || undefined,
        image
      };

      const result = await createAnalysis(analysisData);
      navigate(`/analyses/${result.id}`);
    } catch (err) {
      setError('Analysis failed. Please try again.');
      console.error('Error creating analysis:', err);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading patient information...</div>;
  }

  if (!patient) {
    return <div className="error">Patient not found</div>;
  }

  const bmi = calculateBMI();

  return (
    <div className="new-analysis-container">
      <div className="breadcrumb">
        <span>Patient: {patient.patient_code} — {patient.name}</span>
      </div>

      <h1>New Analysis</h1>

      {error && <div className="error-message">{error}</div>}

      <form onSubmit={handleSubmit} className="analysis-form">
        <div className="form-section">
          <h2>X-ray Upload</h2>
          <div className="image-upload">
            {!imagePreview ? (
              <div className="upload-area">
                <div className="upload-icon">📷</div>
                <p>Drag & drop knee X-ray image here</p>
                <p className="upload-hint">or</p>
                <input
                  type="file"
                  id="imageInput"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={handleImageChange}
                  style={{ display: 'none' }}
                />
                <label htmlFor="imageInput" className="upload-button">
                  Choose Image
                </label>
                <p className="file-info">Supported formats: PNG, JPG, JPEG, WEBP (max 10MB)</p>
              </div>
            ) : (
              <div className="image-preview">
                <img src={imagePreview} alt="X-ray preview" />
                <button
                  type="button"
                  className="change-image-button"
                  onClick={() => {
                    setImage(null);
                    setImagePreview(null);
                  }}
                >
                  Change Image
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="form-section">
          <h2>Clinical Information</h2>
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="age">Age *</label>
              <input
                id="age"
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                min="1"
                max="150"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="gender">Gender *</label>
              <select
                id="gender"
                value={gender}
                onChange={(e) => {
                  setGender(e.target.value);
                  if (e.target.value === 'male') {
                    setPregnancies('0');
                    setMenopausalStatus('');
                  }
                }}
                required
              >
                <option value="">Select gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="height">Height (m) *</label>
              <input
                id="height"
                type="number"
                step="0.01"
                value={height}
                onChange={(e) => setHeight(e.target.value)}
                min="0.5"
                max="3"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="weight">Weight (kg) *</label>
              <input
                id="weight"
                type="number"
                step="0.1"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                min="1"
                max="300"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="bmi">BMI (auto-calculated)</label>
              <input
                id="bmi"
                type="text"
                value={bmi}
                readOnly
                className="readonly-field"
              />
            </div>

            <div className="form-group">
              <label htmlFor="jointPain">Joint Pain *</label>
              <select
                id="jointPain"
                value={jointPain}
                onChange={(e) => setJointPain(e.target.value)}
                required
              >
                <option value="">Select option</option>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="pregnancies">
                Number of Pregnancies {gender === 'male' ? '(auto-set to 0)' : '*'}
              </label>
              <input
                id="pregnancies"
                type="number"
                value={pregnancies}
                onChange={(e) => setPregnancies(e.target.value)}
                min="0"
                max="20"
                disabled={gender === 'male'}
                required={gender === 'female'}
              />
            </div>

            <div className="form-group">
              <label htmlFor="menopausalStatus">Menopausal Status</label>
              <select
                id="menopausalStatus"
                value={menopausalStatus}
                onChange={(e) => setMenopausalStatus(e.target.value)}
                disabled={gender !== 'female'}
              >
                <option value="">Select option</option>
                <option value="premenopausal">Premenopausal</option>
                <option value="perimenopausal">Perimenopausal</option>
                <option value="postmenopausal">Postmenopausal</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="smoking">Smoking</label>
              <select
                id="smoking"
                value={smoking}
                onChange={(e) => setSmoking(e.target.value)}
              >
                <option value="">Select option</option>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="alcohol">Alcohol</label>
              <select
                id="alcohol"
                value={alcohol}
                onChange={(e) => setAlcohol(e.target.value)}
              >
                <option value="">Select option</option>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="previousFracture">Previous Fracture</label>
              <select
                id="previousFracture"
                value={previousFracture}
                onChange={(e) => setPreviousFracture(e.target.value)}
              >
                <option value="">Select option</option>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="longTermSteroidUse">Long-term Steroid Use</label>
              <select
                id="longTermSteroidUse"
                value={longTermSteroidUse}
                onChange={(e) => setLongTermSteroidUse(e.target.value)}
              >
                <option value="">Select option</option>
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            className="cancel-button"
            onClick={() => navigate(`/patients/${patient.id}`)}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="submit-button"
            disabled={analyzing || !image}
          >
            {analyzing ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>
      </form>

      {analyzing && (
        <div className="analysis-progress">
          <h3>Analyzing X-ray...</h3>
          <div className="progress-steps">
            <div className="progress-step completed">✓ Image uploaded</div>
            <div className="progress-step completed">✓ X-ray classification</div>
            <div className="progress-step active">● Estimating bone scores</div>
            <div className="progress-step">○ Preparing results</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewAnalysis;
