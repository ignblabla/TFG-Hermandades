import React from 'react';
import { User, Pencil, CreditCard, Mail, Phone, MapPin } from 'lucide-react';
import '../styles/ProfileCard.css';

const ProfileCard = ({ hermano }) => {
    const nombre = hermano?.nombre || 'Usuario';
    const primerApellido = hermano?.primer_apellido || '';
    const segundoApellido = hermano?.segundo_apellido || '';
    
    const dni = hermano?.dni || 'Sin DNI';
    const email = hermano?.email || 'Sin email';
    const telefono = hermano?.telefono || 'Sin teléfono';

    const direccion = hermano?.direccion || 'Sin dirección';
    const codigoPostal = hermano?.codigo_postal || '';

    const direccionCompleta = codigoPostal ? `${direccion}, ${codigoPostal}` : direccion;

    return (
        <div className="card-container">
            <div className="card-icon-container">
                <User className="lucide-icon" />
            </div>
            
            <div className="card-info">
                <h3 className="card-user-name">
                    {`${nombre} ${primerApellido} ${segundoApellido}`.trim()}
                </h3>

                <div className="card-contact-info">
                    <span className="contact-item">
                        <CreditCard size={14} />
                        {dni}
                    </span>
                    <span className="contact-item">
                        <Mail size={14} />
                        {email}
                    </span>
                    <span className="contact-item">
                        <Phone size={14} />
                        {telefono}
                    </span>
                    <span className="contact-item">
                        <MapPin size={14} />
                        {direccionCompleta}
                    </span>
                </div>
            </div>

            <button className="edit-profile-btn">
                <Pencil className="edit-icon" size={16} />
                <span className="edit-text">Editar perfil</span>
            </button>
        </div>
    );
};

export default ProfileCard;