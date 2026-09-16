import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home/Home';
import Patients from './pages/Patients/Patients';
import PatientDetails from './pages/PatientDetails/PatientDetails';
import NewAnalysis from './pages/NewAnalysis/NewAnalysis';
import AnalysisResult from './pages/AnalysisResult/AnalysisResult';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/patients" element={<Patients />} />
          <Route path="/patients/:patientId" element={<PatientDetails />} />
          <Route path="/patients/:patientId/analysis/new" element={<NewAnalysis />} />
          <Route path="/analyses/:analysisId" element={<AnalysisResult />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
