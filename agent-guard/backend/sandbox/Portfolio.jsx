import React, { useState } from 'react';
import Navbar from './Navbar';

/**
 * Portfolio Main Component.
 * Fullstack & Frontend Developer showcase with interactive dark mode UI.
 */
export default function Portfolio() {
  const [activeSection, setActiveSection] = useState('hero');
  const [filter, setFilter] = useState('all');

  const projects = [
    {
      id: 1,
      title: 'Agent Guard Security Gateway',
      category: 'security',
      description: 'Pre-execution runtime security layer intercepting autonomous AI agent tool calls with dynamic goal alignment.',
      tags: ['React', 'FastAPI', 'MongoDB', 'TailwindCSS'],
      link: '#'
    },
    {
      id: 2,
      title: 'Real-Time Telemetry SOC Dashboard',
      category: 'frontend',
      description: 'Glassmorphism operations dashboard visualizing continuous goal drift and automated interventions.',
      tags: ['React', 'Vite', 'Lucide Icons', 'Recharts'],
      link: '#'
    },
    {
      id: 3,
      title: 'Cloud Distributed Task Pipeline',
      category: 'cloud',
      description: 'High-throughput async job processor with dynamic worker pools and circuit breaker recovery.',
      tags: ['Python', 'Docker', 'Redis', 'WebSockets'],
      link: '#'
    }
  ];

  const filteredProjects = filter === 'all' 
    ? projects 
    : projects.filter(p => p.category === filter);

  return (
    <div className="portfolio-app dark-theme">
      <Navbar activeSection={activeSection} onNavigate={setActiveSection} />

      {/* Hero Section */}
      <header id="hero" className="hero-section">
        <div className="hero-content">
          <div className="badge">Available for New Projects</div>
          <h1 className="hero-title">
            Crafting Secure, High-Performance <span className="gradient-text">Web Applications</span>
          </h1>
          <p className="hero-subtitle">
            Full-stack engineer specializing in modern React frontends, robust distributed backends, and AI agent runtime governance.
          </p>
          <div className="hero-actions">
            <a href="#projects" className="btn-primary">View Featured Projects</a>
            <a href="#contact" className="btn-secondary">Contact Me</a>
          </div>
        </div>
      </header>

      {/* Projects Section */}
      <section id="projects" className="projects-section">
        <div className="section-header">
          <h2>Featured Projects</h2>
          <div className="filter-tabs">
            {['all', 'frontend', 'security', 'cloud'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`filter-btn ${filter === tab ? 'active' : ''}`}
              >
                {tab.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div className="projects-grid">
          {filteredProjects.map((project) => (
            <article key={project.id} className="project-card">
              <div className="project-card-body">
                <h3>{project.title}</h3>
                <p>{project.description}</p>
                <div className="project-tags">
                  {project.tags.map((tag, idx) => (
                    <span key={idx} className="tag">{tag}</span>
                  ))}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
