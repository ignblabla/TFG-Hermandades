import React from 'react';
import '../styles/AreasInteresCard.css';

const AreaCard = ({ icon, title, desc, telegramLink, isSelected, onClick, isFeatured = false, isLocked = false }) => {
    return (
        <div 
            className={`interest-card-area-interes ${isFeatured ? 'card-featured' : ''} ${isSelected ? 'active' : ''} ${isLocked ? 'locked' : ''}`}
            onClick={isLocked ? undefined : onClick}
            style={{ cursor: isLocked ? 'not-allowed' : 'pointer', opacity: isLocked ? 0.9 : 1 }}
        >
            <div className="interest-icon-box-area-interes">
                {icon}
            </div>

            <div className="interest-info-area-interes">
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {title} 
                    {isLocked && <span style={{ fontSize: '0.75rem', fontWeight: 'normal', color: '#6c757d', backgroundColor: '#e9ecef', padding: '2px 8px', borderRadius: '12px' }}>Obligatorio</span>}
                </h3>
                <p>{desc}</p>
            </div>

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
                        disabled={isLocked}
                        onChange={() => {}}
                        readOnly 
                    />
                    <span 
                        className="checkmark-area-interes" 
                        style={{ 
                            cursor: isLocked ? 'not-allowed' : 'pointer',
                            opacity: isLocked ? 0.6 : 1
                        }}
                    ></span>
                </div>
            </div>
        </div>
    );
};

export default AreaCard;