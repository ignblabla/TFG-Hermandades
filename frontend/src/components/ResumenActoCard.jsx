import React from 'react';
import '../styles/ResumenActoCard.css';
import { MapPin, Clock, Ticket, X } from "lucide-react";

const ResumenActoCard = ({ formData }) => {

    const getMesDia = (fechaStr) => {
        if (!fechaStr) return { mes: '---', dia: '--' };
        const date = new Date(fechaStr);
        if (isNaN(date.getTime())) return { mes: '---', dia: '--' };

        const mes = date.toLocaleString('es-ES', { month: 'short' }).toUpperCase().replace('.', '');
        const dia = date.toLocaleString('es-ES', { day: '2-digit' });
        
        return { mes, dia };
    };

    const getHora = (fechaStr) => {
        if (!fechaStr) return "--:--";
        const date = new Date(fechaStr);
        if (isNaN(date.getTime())) return "--:--";
        
        return date.toLocaleString('es-ES', { hour: '2-digit', minute: '2-digit' });
    };

    const imagenMostrar = formData?.previewUrl || formData?.imagen_portada || '/portada-comunicado.png';
    const { mes, dia } = getMesDia(formData?.fecha);
    const hora = getHora(formData?.fecha);

    return (
        <div className="card-container-resumen-acto">
            <div className="card-header-resumen-acto">
                <img 
                    src={imagenMostrar} 
                    alt="Portada del acto" 
                    className="header-image-resumen-acto"
                />

                <div className="icon-badge-resumen-acto">
                    <span className="badge-month-resumen-acto">{mes}</span>
                    <span className="badge-day-resumen-acto">{dia}</span>
                </div>
            </div>

            <div className="card-body-resumen-acto">
                <h1 className="card-title-resumen-acto">
                    {formData?.nombre || "Título del Acto"}
                </h1>

                <p className="card-description-resumen-acto">
                    {formData?.descripcion || "Añade una descripción para este acto. Aquí se mostrará un breve resumen del mismo para que los hermanos conozcan los detalles."}
                </p>

                <div className="info-list-resumen-acto">
                    <div className="info-item-resumen-acto">
                        <Clock size={18} className="info-icon-resumen-acto" />
                        <span className="info-text-resumen-acto">{hora}</span>
                    </div>
                    
                    <div className="info-item-resumen-acto">
                        <MapPin size={18} className="info-icon-resumen-acto" />
                        <span className="info-text-resumen-acto">{formData?.lugar || "Lugar por definir"}</span>
                    </div>

                    <div className="info-item-resumen-acto">
                        {formData?.requiere_papeleta ? (
                            <>
                                <Ticket size={18} className="info-icon-resumen-acto papeleta-icon-vertical" />
                                <span className="info-text-resumen-acto"><strong>Requiere Papeleta</strong></span>
                            </>
                        ) : (
                            <>
                                <X size={18} className="info-icon-resumen-acto" />
                                <span className="info-text-resumen-acto">No requiere papeleta</span>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ResumenActoCard;