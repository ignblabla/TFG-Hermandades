import React from 'react';
import '../styles/ContadorCard.css';

const ContadorCard = () => {
    const timeUnits = [
        { label: 'MESES', value: '02' },
        { label: 'DÍAS', value: '15' },
        { label: 'HORAS', value: '08' },
        { label: 'MINUTOS', value: '34' },
        { label: 'SEGUNDOS', value: '21' }
    ];

    return (
        <div className="countdown-container card-wrapper">
            <div className="countdown-board">
                <h2 className="countdown-title">Lunes Santo 2026</h2>
                <div className="countdown-timer">
                    {timeUnits.map((unit, index) => (
                        <React.Fragment key={unit.label}>
                            <div className="time-unit">
                                <div className="time-value-box">
                                    {unit.value}
                                </div>
                                <span className="time-label">{unit.label}</span>
                            </div>
                            {index < timeUnits.length - 1 && (
                                <span className="separator">:</span>
                            )}
                        </React.Fragment>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ContadorCard;