import React from "react";
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
                    <div className="author-info-noticias">
                        <div className="author-icon-noticias">
                        <svg viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                        </svg>
                        </div>
                        <span className="author-name-noticias">{item.author}</span>
                    </div>
                    <a href="#" className="read-link-noticias">Read</a>
                    </div>
                </div>
            </div>
        );
    };

export default NewsCard;