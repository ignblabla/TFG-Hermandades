import React from 'react';
import '../styles/ResumenActoCard.css';
import { Calendar, MapPin, CalendarDays } from "lucide-react";

const ResumenActoCard = () => {
    return (
        <div className="card-container-resumen-acto">
            <div className="card-header-resumen-acto">
                <div className="icon-badge-resumen-acto">
                    <Calendar size={32} className="main-icon-resumen-acto" />
                </div>
            </div>

            <div className="card-body-resumen-acto">
                <h1 className="card-title-resumen-acto">Resumen del Acto</h1>
                <p className="card-description-resumen-acto">
                    Esta es una vista previa de cómo se mostrará la información básica a los usuarios.
                </p>

                <div className="info-list-resumen-acto">
                    <div className="info-item-resumen-acto">
                        <div className="item-icon-wrapper-resumen-acto">
                            <MapPin size={18} />
                        </div>
                        <div className="item-content-resumen-acto">
                            <span className="item-label-resumen-acto">UBICACIÓN</span>
                            <span className="item-value-resumen-acto">Pendiente de definir</span>
                        </div>
                    </div>

                    <div className="info-item-resumen-acto">
                        <div className="item-icon-wrapper-resumen-acto">
                            <CalendarDays size={18} />
                        </div>
                        <div className="item-content-resumen-acto">
                            <span className="item-label-resumen-acto">FECHA PROGRAMADA</span>
                            <span className="item-value-resumen-acto">No establecida</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ResumenActoCard;