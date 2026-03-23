import React from 'react';
import '../acto_card_solicitud/ActoCardSolicitud.css';
import { MapPin, Clock, Ticket, X } from "lucide-react";

const ActoCardSolicitud = ({ mes, dia, titulo, hora, lugar, descripcion, requierePapeleta, imagenPortada, onVerDetalles }) => {
    const imagenMostrar = imagenPortada || '/portada-comunicado.png';
    return (
        <div className="solicitar-card-container-acto">
            <div className="solicitar-card-header-acto">
                <img 
                    src={imagenMostrar} 
                    alt={`Portada de ${titulo}`} 
                    className="solicitar-header-image-acto"
                />

                <div className="solicitar-icon-badge-acto">
                    <span className="solicitar-badge-day-acto">{dia}</span>
                    <span className="solicitar-badge-month-acto">{mes}</span>
                </div>
            </div>

            <div className="solicitar-card-body-acto">
                <h1 className="solicitar-card-title-acto">
                    {titulo || "Título del Acto"}
                </h1>

                <p className="solicitar-card-description-acto">
                    {descripcion || "Sin descripción disponible."}
                </p>

                <div className="solicitar-info-list-acto">
                    <div className="solicitar-info-item-acto">
                        <Clock size={18} className="solicitar-info-icon-acto" />
                        <span className="solicitar-info-text-acto">{hora}</span>
                    </div>
                    
                    <div className="solicitar-info-item-acto">
                        <MapPin size={18} className="solicitar-info-icon-acto" />
                        <span className="solicitar-info-text-acto">{lugar || "Lugar por definir"}</span>
                    </div>

                    <div className="solicitar-info-item-acto">
                        {requierePapeleta ? (
                            <>
                                <Ticket 
                                    size={18} 
                                    className="solicitar-info-icon-acto solicitar-papeleta-icon-vertical" 
                                />
                                <span className="solicitar-info-text-acto"><strong>Requiere Papeleta</strong></span>
                            </>
                        ) : (
                            <>
                                <X size={18} className="solicitar-info-icon-acto" />
                                <span className="solicitar-info-text-acto">No requiere papeleta</span>
                            </>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
};

export default ActoCardSolicitud;