import React from 'react';
import '../styles/CultoCard.css';

const CultoCard = ({ mes, dia, titulo, hora, lugar }) => {
    return (
        <div className="culto-card">
            <div className="culto-date-box">
                <span className="culto-month">{mes}</span>
                <span className="culto-day">{dia}</span>
            </div>

            <div className="culto-info">
                <h4 className="culto-title">{titulo}</h4>
                <p className="culto-time-location">
                    {hora} - {lugar}
                </p>
            </div>
        </div>
    );
};

export default CultoCard;