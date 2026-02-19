import React from 'react';
import '../styles/AreasInteresCard.css';

const AreaCard = ({ icon, title, desc, telegramLink, isSelected, onClick, isFeatured = false }) => {
    return (
        <div 
            className={`interest-card-area-interes ${isFeatured ? 'card-featured' : ''} ${isSelected ? 'active' : ''}`}
            onClick={onClick}
        >
            <div className="interest-icon-box-area-interes">
                {icon}
            </div>

            <div className="interest-info-area-interes">
                <h3>{title}</h3>
                <p>{desc}</p>
            </div>

            {/* NUEVO CONTENEDOR: Agrupa el enlace y el checkbox a la derecha */}
            <div className="interest-actions-area-interes">
                {isSelected && telegramLink && (
                    <div className="telegram-link-container">
                        <a 
                            href={telegramLink} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="telegram-link"
                            onClick={(e) => e.stopPropagation()}
                        >
                            📲 Canal de Telegram
                        </a>
                    </div>
                )}

                <div className="checkbox-wrapper-area-interes">
                    <input 
                        type="checkbox" 
                        checked={isSelected} 
                        onChange={() => {}}
                        readOnly 
                    />
                    <span className="checkmark-area-interes"></span>
                </div>
            </div>
        </div>
    );
};

export default AreaCard;