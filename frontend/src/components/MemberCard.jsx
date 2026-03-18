import React from 'react';
import { User, FileText } from 'lucide-react';
import '../styles/MemberCard.css';


const MemberCard = ({ currentUser }) => {
    const data = {
        name: currentUser ? `${currentUser.nombre || ''} ${currentUser.primer_apellido || ''} ${currentUser.segundo_apellido || ''}`.trim() : "Cargando...",
        status: currentUser?.estado_hermano || "---",
        dni: currentUser?.dni || "---",
        registro: currentUser?.numero_registro || "---",
        fechaNacimiento: currentUser?.fecha_nacimiento || "---",
        telefono: currentUser?.telefono || "---",
        fechaIngreso: currentUser?.fecha_ingreso_corporacion || "---",
        alCorriente: currentUser?.esta_al_corriente !== undefined 
            ? (currentUser.esta_al_corriente ? "Sí" : "No") 
            : "---"
    };

    return (
        <div className="member-card">
            {/* Header Section */}
            <div className="member-header">
                <div className="member-avatar-box">
                    <svg viewBox="0 0 24 24" fill="currentColor" className="member-avatar-icon">
                        <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                    </svg>
                </div>
                <div className="member-header-info">
                    <h1 className="member-name">{data.name}</h1>
                    <p className="member-status">{data.status}</p>
                </div>
            </div>

            <div className="member-divider"></div>

            {/* Info Grid Section */}
            <div className="member-info-grid">
                <div className="member-info-item">
                    <label>DNI</label>
                    <span>{data.dni}</span>
                </div>
                <div className="member-info-item">
                    <label>Nº REGISTRO</label>
                    <span>{data.registro}</span>
                </div>
                
                <div className="member-info-item">
                    <label>FECHA NACIMIENTO</label>
                    <span>{data.fechaNacimiento}</span>
                </div>
                <div className="member-info-item">
                    <label>TELÉFONO</label>
                    <span>{data.telefono}</span>
                </div>

                <div className="member-info-item">
                    <label>ESTADO DE HERMANO</label>
                    <span>{data.status}</span>
                </div>

                <div className="member-info-item">
                    <label>FECHA INGRESO</label>
                    <span>{data.fechaIngreso}</span>
                </div>
                
                <div className="member-info-item full-width">
                    <label>AL CORRIENTE DE PAGO</label>
                    <span className={data.alCorriente === "Sí" ? "status-paid" : "status-unpaid"}>
                        {data.alCorriente}
                    </span>
                </div>
            </div>

            {/* Footer Buttons */}
            <div className="member-card-footer">
                <button className="member-action-button">
                    <User size={18} strokeWidth={1.5} />
                    Mis Datos
                </button>
                <button className="member-action-button">
                    <FileText size={18} strokeWidth={1.5} />
                    Certificados
                </button>
            </div>
        </div>
    );
};

export default MemberCard;