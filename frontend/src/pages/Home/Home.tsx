import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  return (
    <div className="home-container">
      <div className="home-content">
        <h1 className="home-title">Knee Osteoporosis AI</h1>
        <p className="home-subtitle">
          AI-assisted screening using knee X-ray images and patient clinical information.
        </p>
        <Link to="/patients" className="home-button">
          Start Analysis
        </Link>
      </div>
    </div>
  );
};

export default Home;
