import React from 'react';
import '../styles/HomeCard.css';

const HomeCard = ({ title, value, icon: Icon }) => {
    return (
        <div className="home-card">
            {Icon && (
                <div className="home-card-icon-container">
                    <Icon className="lucide-icon" />
                </div>
            )}
            
            <div className="home-card-info">
                <h3 className="home-card-title">{title}</h3>
                <p className="home-card-value">{value}</p>
            </div>
        </div>
    );
};

export default HomeCard;