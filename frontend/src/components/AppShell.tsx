import { useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import './AppShell.css';

type NavigationIconName = 'home' | 'patients' | 'analysis';

const NavigationIcon = ({ name }: { name: NavigationIconName }) => {
  const paths: Record<NavigationIconName, string> = {
    home: 'M3 10.8 12 3l9 7.8v9.7a.5.5 0 0 1-.5.5h-5.7v-6.2H9.2V21H3.5a.5.5 0 0 1-.5-.5z',
    patients: 'M16 20v-1.5a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4V20m7-9a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8-6a3.5 3.5 0 0 1 0 6.8M17 14.7a4 4 0 0 1 4 4V20',
    analysis: 'M12 3v18m-9-9h18M7.5 7.5l9 9m0-9-9 9',
  };

  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="navigation-icon">
      <path d={paths[name]} />
    </svg>
  );
};

const AppShell = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const startAnalysis = () => {
    setMobileMenuOpen(false);
    navigate('/patients');
  };

  return (
    <div className="app-shell">
      <header className="mobile-header">
        <Link className="brand brand-compact" to="/" aria-label="Knee Osteoporosis AI home">
          <span className="brand-mark">K</span>
          <span>Knee Osteoporosis AI</span>
        </Link>
        <button
          type="button"
          className="menu-toggle"
          aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={mobileMenuOpen}
          aria-controls="primary-navigation"
          onClick={() => setMobileMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>
      </header>

      {mobileMenuOpen && (
        <button
          type="button"
          className="navigation-backdrop"
          aria-label="Close navigation menu"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      <aside
        className={`app-sidebar${mobileMenuOpen ? ' is-open' : ''}`}
        id="primary-navigation"
      >
        <Link className="brand" to="/" aria-label="Knee Osteoporosis AI home">
          <span className="brand-mark">K</span>
          <span className="brand-name">Knee Osteoporosis AI</span>
        </Link>

        <nav className="primary-navigation" aria-label="Main navigation">
          <NavLink to="/" end onClick={() => setMobileMenuOpen(false)} className={({ isActive }) => `navigation-link${isActive ? ' is-active' : ''}`}>
            <NavigationIcon name="home" />
            <span>Home</span>
          </NavLink>
          <NavLink
            to="/patients"
            onClick={() => setMobileMenuOpen(false)}
            className={({ isActive }) => `navigation-link${isActive && !location.pathname.includes('/analysis/new') ? ' is-active' : ''}`}
          >
            <NavigationIcon name="patients" />
            <span>Patients</span>
          </NavLink>
          <button
            type="button"
            className={`navigation-link${location.pathname.includes('/analysis/new') ? ' is-active' : ''}`}
            onClick={startAnalysis}
            title="Choose a patient before starting an analysis"
          >
            <NavigationIcon name="analysis" />
            <span>New Analysis</span>
          </button>
        </nav>
      </aside>

      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
};

export default AppShell;
