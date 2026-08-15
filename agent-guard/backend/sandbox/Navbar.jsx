import React from 'react';

/**
 * Navbar Component for React Portfolio.
 * Responsive navigation header with dark-theme styling and navigation links.
 */
export default function Navbar({ activeSection, onNavigate }) {
  const navItems = [
    { id: 'hero', label: 'Home' },
    { id: 'projects', label: 'Projects' },
    { id: 'skills', label: 'Skills' },
    { id: 'experience', label: 'Experience' },
    { id: 'contact', label: 'Contact' },
  ];

  return (
    <nav className="portfolio-navbar">
      <div className="navbar-container">
        <div className="navbar-logo">
          <span className="logo-accent">&lt;</span>
          <span className="logo-text">DevPortfolio</span>
          <span className="logo-accent">/&gt;</span>
        </div>

        <ul className="navbar-links">
          {navItems.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onNavigate && onNavigate(item.id)}
                className={`nav-link ${activeSection === item.id ? 'active' : ''}`}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>

        <div className="navbar-cta">
          <a href="#contact" className="btn-primary">
            Get in Touch
          </a>
        </div>
      </div>
    </nav>
  );
}
