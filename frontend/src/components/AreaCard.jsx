import React from 'react';
import '../styles/AreasInteresCard.css';

const AreaCard = ({ icon, title, desc, isSelected, onClick, isFeatured = false }) => {
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
    );
};

export default AreaCard;