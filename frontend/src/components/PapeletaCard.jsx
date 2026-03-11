import React from 'react';
import '../styles//PapeletaCard.css';

const PapeletaCard = () => {
    return (
        <div className="papeleta-card">
            <div className="top-accent"></div>
            
            <div className="card-content">
                <div className="icon-container">
                <div className="icon-circle">
                    <svg 
                    viewBox="0 0 24 24" 
                    className="ticket-icon"
                    fill="currentColor"
                    >
                    <path d="M20,12V10a2,2,0,0,0,0-4V4H4V6A2,2,0,0,0,4,10v2a2,2,0,0,0,0,4v2H20V16a2,2,0,0,0,0-4Z" />
                    </svg>
                </div>
                </div>

                <h2 className="card-title">Papeleta de Sitio</h2>
                <p className="card-description">
                Ya está abierto el plazo para solicitar su papeleta de sitio 
                para la próxima estación de penitencia.
                </p>

                <button className="cta-button">
                Solicitar ahora 
                <span className="arrow">→</span>
                </button>

                <p className="deadline-text">
                PLAZO DISPONIBLE HASTA EL 15 DE MARZO
                </p>
            </div>
        </div>
    );
};

export default PapeletaCard;