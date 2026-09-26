import { Link } from 'react-router-dom';
import './Home.css';

const features = [
  { title: 'AI Analysis', description: 'DINOv2-based X-ray classification', icon: 'scan', tone: 'blue' },
  { title: 'Risk Assessment', description: 'T-score and Z-score estimation', icon: 'chart', tone: 'amber' },
  { title: 'Clinical Support', description: 'Evidence-based guidance with RAG and LLM', icon: 'support', tone: 'green' },
  { title: 'Patient Management', description: 'Track patient analysis history', icon: 'patients', tone: 'violet' },
];

const FeatureIcon = ({ name }: { name: string }) => {
  const paths: Record<string, string> = {
    scan: 'M4 8V5a1 1 0 0 1 1-1h3m8 0h3a1 1 0 0 1 1 1v3m0 8v3a1 1 0 0 1-1 1h-3m-8 0H5a1 1 0 0 1-1-1v-3M8 12h8m-4-4v8',
    chart: 'M4 19V5m0 14h17M8 15l3-4 3 2 5-7',
    support: 'M12 3a9 9 0 1 0 9 9m-9-5v5l4 2m3-10 1-2m1 5h-2',
    patients: 'M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20m7-9a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8-6a3.5 3.5 0 0 1 0 6.8M17 14.7a4 4 0 0 1 4 4V20',
  };

  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="feature-icon-svg">
      <path d={paths[name]} />
    </svg>
  );
};

const Home = () => {
  return (
    <div className="home-page page-container">
      <section className="home-hero">
        <div className="home-hero-copy">
          <p className="eyebrow">AI-assisted screening workspace</p>
          <h1>Knee Osteoporosis AI</h1>
          <p className="home-subtitle">AI-Assisted Screening and Evidence-Based Clinical Decision Support</p>
          <p className="home-description">
            Analyze knee X-ray images and patient clinical information to predict osteoporosis
            conditions, estimate T-score and Z-score, and get evidence-based clinical support.
          </p>
          <div className="home-actions">
            <Link to="/patients" className="button button-primary">New Analysis <span aria-hidden="true">→</span></Link>
            <Link to="/patients" className="button button-secondary">View Patients</Link>
          </div>
        </div>
        <div className="home-hero-visual" aria-hidden="true">
          <div className="hero-visual-glow" />
          <div className="hero-visual-card">
            <div className="hero-visual-mark"><span>K</span></div>
            <div className="hero-visual-lines"><i /><i /><i /><i /><i /></div>
            <div className="hero-visual-caption">
              <span>Analysis workflow</span>
              <strong>X-ray and clinical context</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="feature-grid" aria-label="Application capabilities">
        {features.map((feature) => (
          <article className="feature-card" key={feature.title}>
            <div className={`feature-icon feature-icon-${feature.tone}`}>
              <FeatureIcon name={feature.icon} />
            </div>
            <h2>{feature.title}</h2>
            <p>{feature.description}</p>
          </article>
        ))}
      </section>
    </div>
  );
};

export default Home;
