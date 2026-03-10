import React from 'react';
import '../styles/SolicitudPapeletaCard.css';

const SolicitudPapeletaCard = () => {
    return (
        <div className="card-container">
        <div className="content-side">
            <div className="status-badge">
            <span className="dot"></span>
            PLAZO ABIERTO
            </div>
            
            <h2 className="title">Papeletas de Sitio 2024</h2>
            
            <p className="description">
            Ya está disponible la reserva online de túnicas y papeletas para la próxima 
            Estación de Penitencia. Asegura tu sitio en el cortejo.
            </p>
            
            <button className="cta-button">
            Solicitar Papeleta
            </button>
        </div>

        <div className="icon-side">
            <div className="ticket-icon">
            <svg width="64" height="90" viewBox="0 0 64 90" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M0 10C0 4.47715 4.47715 0 10 0H54C59.5228 0 64 4.47715 64 10V34C59.5817 34 56 37.5817 56 42C56 46.4183 59.5817 50 64 50V80C64 85.5228 59.5228 90 54 90H10C4.47715 90 0 85.5228 0 80V50C4.41828 50 8 46.4183 8 42C8 37.5817 4.41828 34 0 34V10Z" fill="#5c0a16"/>
                <circle cx="32" cy="26" r="4" fill="#000" fillOpacity="0.4" />
                <circle cx="32" cy="42" r="4" fill="#000" fillOpacity="0.4" />
                <circle cx="32" cy="58" r="4" fill="#000" fillOpacity="0.4" />
            </svg>
            </div>
        </div>
        </div>
    );
};

export default SolicitudPapeletaCard;