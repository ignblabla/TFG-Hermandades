import React from 'react';
import '../styles/ResumenActoCard.css';
import { Calendar, MapPin, CalendarDays } from "lucide-react";

const ResumenActoCard = ({ formData }) => {

    const formatFecha = (fechaStr) => {
        if (!fechaStr) return "No establecida";
        const date = new Date(fechaStr);
        return date.toLocaleString('es-ES', { 
            day: '2-digit', 
            month: 'short', 
            year: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    };

    return (
        <div className="card-container-resumen-acto">
            <div className="card-header-resumen-acto">
                <div className="icon-badge-resumen-acto">
                    <Calendar size={32} className="main-icon-resumen-acto" />
                </div>
            </div>

            <div className="card-body-resumen-acto">
                <h1 className="card-title-resumen-acto">
                    {formData?.nombre || "Resumen del Acto"}
                </h1>

                <p className="card-description-resumen-acto">
                    {formData?.descripcion || "Esta es una vista previa de cómo se mostrará la información básica a los usuarios."}
                </p>

                <div className="info-list-resumen-acto">
                    <div className="info-item-resumen-acto">
                        <div className="item-icon-wrapper-resumen-acto">
                            <MapPin size={18} />
                        </div>
                        <div className="item-content-resumen-acto">
                            <span className="item-label-resumen-acto">UBICACIÓN</span>
                            <span className="item-value-resumen-acto">
                                {formData?.lugar || "Pendiente de definir"}
                            </span>
                        </div>
                    </div>

                    {/* Fecha */}
                    <div className="info-item-resumen-acto">
                        <div className="item-icon-wrapper-resumen-acto">
                            <CalendarDays size={18} />
                        </div>
                        <div className="item-content-resumen-acto">
                            <span className="item-label-resumen-acto">FECHA PROGRAMADA</span>
                            <span className="item-value-resumen-acto">
                                {formatFecha(formData?.fecha)}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ResumenActoCard;