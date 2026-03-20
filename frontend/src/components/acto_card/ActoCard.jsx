import React from 'react';
import '../acto_card/ActoCard.css';

const ActoCard = ({ mes, dia, titulo, hora, lugar, descripcion, modalidad, fechaInicioSolicitud, fechaFinSolicitud, fechaInicioSolicitudCirios, fechaFinSolicitudCirios}) => {
    return (
        <div className="acto-card">
            <div className="acto-date-box">
                <span className="acto-month">{mes}</span>
                <span className="acto-day">{dia}</span>
            </div>

            <div className="acto-info">
                <h4 className="acto-title">{titulo}</h4>
                <p className="acto-time-location">
                    {hora} - {lugar}
                </p>
                
                {descripcion && (
                    <p className="acto-description">{descripcion}</p>
                )}

                <div className="acto-fechas-container">
                    {modalidad === 'UNIFICADO' && (
                        <p className="acto-fecha-item">
                            <strong>Solicitudes:</strong> {fechaInicioSolicitud} al {fechaFinSolicitud}
                        </p>
                    )}

                    {modalidad === 'TRADICIONAL' && (
                        <div className="acto-fechas-row">
                            <p className="acto-fecha-item">
                                <strong>Solicitudes de insignias:</strong> {fechaInicioSolicitud} al {fechaFinSolicitud}
                            </p>
                            <p className="acto-fecha-item">
                                <strong>Solicitud de cirios:</strong> {fechaInicioSolicitudCirios} al {fechaFinSolicitudCirios}
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ActoCard;