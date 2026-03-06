import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/NewsCardHome.css';

const NewsCardHome = ({ imagen, titulo, fecha, contenido, enlace }) => {
    const extracto = contenido?.length > 50 
        ? contenido.substring(0, 50) + "..." 
        : contenido;

    return (
        <div className="news-card">
            <img src={imagen} alt={titulo} className="news-image" />
            
            <div className="news-content">
                <span className="news-date">{fecha}</span>
                <h4 className="news-title">{titulo}</h4>
                
                <p className="news-excerpt">
                    {extracto}
                    <Link to={enlace} className="news-link"> Leer más</Link>
                </p>
            </div>
        </div>
    );
};

export default NewsCardHome;