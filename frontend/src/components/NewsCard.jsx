/* Cada prueba debe tener un comentario como el que te pasé antes. */
import React from "react";
import { Link } from "react-router-dom"; // Importamos Link de React Router
import '../styles/NewsCard.css'; 

const NewsCard = ({ item }) => {
    return (
        <div className="card-noticias">
            <div className="card-header-noticias">
                <img src={item.image} alt={item.title} className="card-image-noticias" />
                <span className="category-tag-noticias" style={{ backgroundColor: item.categoryColor }}>
                {item.category}
                </span>
            </div>
            
            <div className="card-content-noticias">
                <div className="card-meta-noticias">
                {item.time} • {item.readTime}
                </div>
                <h3 className="card-title-noticias">{item.title}</h3>
                <p className="card-description-noticias">{item.description}</p>
                
                <div className="card-footer-noticias">
                    <Link to={`/comunicados/${item.id}`} className="read-link-noticias">
                        Leer noticia
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default NewsCard;