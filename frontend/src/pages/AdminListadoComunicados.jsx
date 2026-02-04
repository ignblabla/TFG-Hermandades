import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api'; 
import '../styles/AdminEdicionHermano.css'; 
import { 
    Plus, 
    FileText, 
    Calendar, 
    User, 
    Megaphone,
    Eye,
    Image as ImageIcon 
} from "lucide-react";

// --- USAMOS LA VARIABLE DE ENTORNO ---
// Vite expone las variables del .env en import.meta.env
const API_BASE_URL = import.meta.env.VITE_API_URL;

function AdminListadoComunicados() {
    const navigate = useNavigate();
    const [comunicados, setComunicados] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    // --- CARGA DE DATOS ---
    useEffect(() => {
        const fetchComunicados = async () => {
            try {
                const response = await api.get('api/comunicados/');
                setComunicados(response.data);
            } catch (err) {
                console.error(err);
                setError("Error al cargar los comunicados.");
            } finally {
                setLoading(false);
            }
        };

        fetchComunicados();
    }, []);

    // --- HELPER: CONSTRUIR URL DE IMAGEN ---
    const getFullImageUrl = (imagePath) => {
        if (!imagePath) return null;
        
        // Si ya es absoluta (ej: Amazon S3 o cloudinary), la dejamos igual
        if (imagePath.startsWith('http')) return imagePath;
        
        // Si es relativa (ej: /media/...), le pegamos el dominio de la API
        // Quitamos la barra final a la base si la tuviera para evitar dobles //
        const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
        
        // Nos aseguramos de que imagePath empiece por /
        const path = imagePath.startsWith('/') ? imagePath : `/${imagePath}`;
        
        return `${baseUrl}${path}`;
    };

    // --- HELPER: FORMATO DE FECHA ---
    const formatFecha = (fechaISO) => {
        if (!fechaISO) return "-";
        const date = new Date(fechaISO);
        return date.toLocaleDateString('es-ES', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // --- HELPER: ESTILOS SEGÚN TIPO ---
    const getTipoBadgeStyle = (tipo) => {
        switch (tipo) {
            case 'URGENTE': return { backgroundColor: '#fee2e2', color: '#991b1b', border: '1px solid #fecaca' };
            case 'CULTOS': return { backgroundColor: '#f3e8ff', color: '#6b21a8', border: '1px solid #e9d5ff' };
            case 'GENERAL': return { backgroundColor: '#eff6ff', color: '#1e40af', border: '1px solid #dbeafe' };
            default: return { backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #e5e7eb' };
        }
    };

    if (loading) return <div className="loading-screen">Cargando noticias...</div>;

    return (
        <div className="admin-container">
            {/* TÍTULO Y BOTÓN DE CREAR */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', padding: '20px' }}>
                <h2 className="admin-page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Megaphone size={28} />
                    Gestión de Comunicados
                </h2>
                <button 
                    className="btn-save-edicion" 
                    onClick={() => navigate('/admin/crear-comunicado')}
                    style={{ padding: '10px 20px', display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                    <Plus size={18} />
                    Nuevo Comunicado
                </button>
            </div>

            {/* TABLA DE LISTADO */}
            <div style={{ padding: '0 20px' }}>
                {error && <div className="alert-banner-edicion error-edicion">{error}</div>}

                <div className="card-container-listado" style={{ maxWidth: '100%', overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '800px' }}>
                        <thead>
                            <tr style={{ backgroundColor: '#f9fafb', borderBottom: '2px solid #e5e7eb' }}>
                                {/* COLUMNA PORTADA */}
                                <th style={{...thStyle, width: '60px', textAlign: 'center'}}><ImageIcon size={16} /></th>
                                
                                <th style={thStyle}><Calendar size={16} style={{marginBottom: '-2px'}}/> Fecha</th>
                                <th style={thStyle}><FileText size={16} style={{marginBottom: '-2px'}}/> Título</th>
                                <th style={thStyle}>Tipo</th>
                                <th style={thStyle}>Destinatarios (Áreas)</th>
                                <th style={thStyle}><User size={16} style={{marginBottom: '-2px'}}/> Autor</th>
                                <th style={thStyle}>Acciones</th>
                            </tr>
                        </thead>
                        <tbody>
                            {comunicados.length === 0 ? (
                                <tr>
                                    <td colSpan="7" style={{ padding: '30px', textAlign: 'center', color: '#6b7280' }}>
                                        No hay comunicados registrados.
                                    </td>
                                </tr>
                            ) : (
                                comunicados.map((comunicado) => (
                                    <tr key={comunicado.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                                        
                                        {/* CELDA DE IMAGEN CON URL CORREGIDA */}
                                        <td style={{...tdStyle, padding: '8px', textAlign: 'center'}}>
                                            {comunicado.imagen_portada ? (
                                                <img 
                                                    src={getFullImageUrl(comunicado.imagen_portada)} 
                                                    alt="Portada" 
                                                    style={{ 
                                                        width: '40px', 
                                                        height: '40px', 
                                                        objectFit: 'cover', 
                                                        borderRadius: '6px',
                                                        border: '1px solid #e5e7eb',
                                                        display: 'block',
                                                        margin: '0 auto'
                                                    }}
                                                    onError={(e) => {
                                                        e.target.onerror = null; 
                                                        e.target.style.display = 'none';
                                                        // Mostramos el div hermano (fallback)
                                                        e.target.nextSibling.style.display = 'flex';
                                                    }}
                                                />
                                            ) : (
                                                /* Fallback por si no hay imagen (null) */
                                                <div style={{
                                                    width: '40px', 
                                                    height: '40px', 
                                                    backgroundColor: '#f3f4f6', 
                                                    borderRadius: '6px',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    margin: '0 auto',
                                                    color: '#d1d5db'
                                                }}>
                                                    <ImageIcon size={20} />
                                                </div>
                                            )}
                                            {/* Fallback oculto por defecto (se muestra si falla la carga de img) */}
                                            <div style={{
                                                display: 'none',
                                                width: '40px', 
                                                height: '40px', 
                                                backgroundColor: '#fee2e2', 
                                                borderRadius: '6px',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                margin: '0 auto',
                                                color: '#ef4444'
                                            }}>
                                                <ImageIcon size={20} />
                                            </div>
                                        </td>

                                        <td style={tdStyle}>{formatFecha(comunicado.fecha_emision)}</td>
                                        <td style={{...tdStyle, fontWeight: '600', color: '#111827'}}>
                                            {comunicado.titulo}
                                        </td>
                                        <td style={tdStyle}>
                                            <span style={{ 
                                                ...badgeStyle, 
                                                ...getTipoBadgeStyle(comunicado.tipo_comunicacion) 
                                            }}>
                                                {comunicado.tipo_display || comunicado.tipo_comunicacion}
                                            </span>
                                        </td>
                                        <td style={tdStyle}>
                                            {comunicado.areas_interes && comunicado.areas_interes.length > 0 ? (
                                                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                                                    {comunicado.areas_interes.map((area, idx) => (
                                                        <span key={idx} style={{ fontSize: '0.75rem', backgroundColor: '#eef2ff', color: '#4f46e5', padding: '2px 6px', borderRadius: '4px', border: '1px solid #c7d2fe' }}>
                                                            {area}
                                                        </span>
                                                    ))}
                                                </div>
                                            ) : (
                                                <span style={{ fontSize: '0.8rem', color: '#f59e0b', fontStyle: 'italic' }}>Borrador / Sin asignar</span>
                                            )}
                                        </td>
                                        <td style={tdStyle}>{comunicado.autor_nombre}</td>
                                        <td style={tdStyle}>
                                            <button 
                                                onClick={() => navigate(`/admin/comunicados/${comunicado.id}`)}
                                                style={{ border: 'none', background: 'transparent', cursor: 'pointer', color: '#6b7280' }}
                                                title="Ver detalle"
                                            >
                                                <Eye size={20} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}

// Estilos CSS-in-JS simples para la tabla
const thStyle = {
    padding: '12px 15px',
    textAlign: 'left',
    fontSize: '0.85rem',
    fontWeight: '600',
    color: '#374151',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
};

const tdStyle = {
    padding: '12px 15px',
    fontSize: '0.9rem',
    color: '#4b5563',
    verticalAlign: 'middle'
};

const badgeStyle = {
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: '600',
    display: 'inline-block'
};

export default AdminListadoComunicados;