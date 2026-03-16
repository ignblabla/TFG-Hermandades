import React from 'react';
import { Users, Heart, Hammer, Church, Sun, BookOpen, Crown, Landmark, Bell } from "lucide-react";
import '../areas_asociadas/AreasAsociadas.css'

const AreasAsociadas = ({ areas }) => {
    const areaInfoEstatica = {
        'TODOS_HERMANOS': { icon: <Bell size={18} />, title: 'Todos los Hermanos' },
        'COSTALEROS': { icon: <Users size={18} />, title: 'Costaleros' },
        'CARIDAD': { icon: <Heart size={18} />, title: 'Diputación de Caridad' },
        'JUVENTUD': { icon: <Sun size={18} />, title: 'Juventud' },
        'PRIOSTIA': { icon: <Hammer size={18} />, title: 'Priostía' },
        'CULTOS_FORMACION': { icon: <BookOpen size={18} />, title: 'Cultos y Formación' },
        'PATRIMONIO': { icon: <Landmark size={18} />, title: 'Patrimonio' },
        'ACOLITOS': { icon: <Church size={18} />, title: 'Acólitos' },
        'DIPUTACION_MAYOR_GOBIERNO': { icon: <Crown size={18} />, title: 'Diputación Mayor de Gobierno' },
    };

    return (
        <aside className="noticia-area-interes" style={{ flex: '1 1 25%', minWidth: '250px' }}>
            <h3>Áreas asociadas:</h3>
            
            {areas && areas.length > 0 ? (
                <ul className="lista-areas-interes">
                    {[...areas]
                        .sort((a, b) => {
                            const keyA = typeof a === 'object' ? (a.nombre_area || a.nombre) : a;
                            const keyB = typeof b === 'object' ? (b.nombre_area || b.nombre) : b;

                            if (keyA === 'TODOS_HERMANOS' || keyA === 'Todos los Hermanos') return -1;
                            if (keyB === 'TODOS_HERMANOS' || keyB === 'Todos los Hermanos') return 1;
                            return 0; 
                        })
                        .map((areaItem, index) => {
                            const areaKey = typeof areaItem === 'object' ? (areaItem.nombre_area || areaItem.nombre) : areaItem;

                            let visualInfo = areaInfoEstatica[areaKey];

                            if (!visualInfo) {
                                const foundKey = Object.keys(areaInfoEstatica).find(
                                    key => areaInfoEstatica[key].title === areaKey
                                );
                                if (foundKey) {
                                    visualInfo = areaInfoEstatica[foundKey];
                                }
                            }

                            if (!visualInfo) {
                                visualInfo = { icon: <Bell size={18} />, title: areaKey };
                            }

                            return (
                                <li key={index} className="item-area-interes">
                                    <span className="icono-area">{visualInfo.icon}</span>
                                    <span className="titulo-area">{visualInfo.title}</span>
                                </li>
                            );
                        })}
                </ul>
            ) : (
                <p style={{ color: '#666', fontStyle: 'italic', fontSize: '14px' }}>
                    Este comunicado es de ámbito general.
                </p> 
            )}
        </aside>
    );
};

export default AreasAsociadas;