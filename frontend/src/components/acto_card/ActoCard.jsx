import React from 'react';
import '../acto_card/ActoCard.css';
import { MapPin, Clock, Ticket, X } from "lucide-react";

const ActoCard = ({ 
    mes, 
    dia, 
    titulo, 
    hora, 
    lugar, 
    descripcion, 
    requierePapeleta, 
    imagenPortada, 
    onVerDetalles 
}) => {

    const imagenMostrar = imagenPortada || '/portada-comunicado.png';

    return (
        <div className="card-container-acto">

            <div className="card-header-acto">
                <img 
                    src={imagenMostrar} 
                    alt={`Portada de ${titulo}`} 
                    className="header-image-acto"
                />

                <div className="icon-badge-acto">
                    <span className="badge-day-acto">{dia}</span>
                    <span className="badge-month-acto">{mes}</span>
                </div>
            </div>

            <div className="card-body-acto">
                <h1 className="card-title-acto">
                    {titulo || "Título del Acto"}
                </h1>

                <p className="card-description-acto">
                    {descripcion || "Sin descripción disponible."}
                </p>

                <div className="info-list-acto">
                    <div className="info-item-acto">
                        <Clock size={18} className="info-icon-acto" />
                        <span className="info-text-acto">{hora}</span>
                    </div>
                    
                    <div className="info-item-acto">
                        <MapPin size={18} className="info-icon-acto" />
                        <span className="info-text-acto">{lugar || "Lugar por definir"}</span>
                    </div>

                    <div className="info-item-acto">
                        {requierePapeleta ? (
                            <>
                                <Ticket 
                                    size={18} 
                                    className="info-icon-acto papeleta-icon-vertical" 
                                />
                                <span className="info-text-acto"><strong>Requiere Papeleta</strong></span>
                            </>
                        ) : (
                            <>
                                <X size={18} className="info-icon-acto" />
                                <span className="info-text-acto">No requiere papeleta</span>
                            </>
                        )}
                    </div>
                </div>

                <div className="card-actions-acto">
                    <button className="btn-ver-detalles-acto" onClick={onVerDetalles}>
                        Ver detalles
                    </button>
                </div>

            </div>
        </div>
    );
};

export default ActoCard;