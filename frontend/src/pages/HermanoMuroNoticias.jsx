import React, { useState, useEffect } from 'react';
import api from '../api';
import { 
    Calendar, 
    User, 
    Tag, 
    MessageCircle,
    Info
} from "lucide-react";

// Estilos inline básicos para las tarjetas (puedes moverlos a un CSS)
const styles = {
    container: {
        padding: '20px',
        maxWidth: '800px',
        margin: '0 auto',
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    },
    header: {
        marginBottom: '30px',
        borderBottom: '2px solid #eee',
        paddingBottom: '10px'
    },
    title: {
        color: '#111827',
        fontSize: '1.8rem',
        fontWeight: '700'
    },
    grid: {
        display: 'flex',
        flexDirection: 'column',
        gap: '20px'
    },
    card: {
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        padding: '24px',
        border: '1px solid #f3f4f6',
        transition: 'transform 0.2s',
    },
    metaRow: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '12px',
        fontSize: '0.85rem',
        color: '#6b7280'
    },
    badge: {
        padding: '4px 10px',
        borderRadius: '20px',
        fontSize: '0.75rem',
        fontWeight: '600',
        textTransform: 'uppercase'
    },
    cardTitle: {
        fontSize: '1.25rem',
        fontWeight: '700',
        color: '#1f2937',
        margin: '0 0 12px 0'
    },
    content: {
        color: '#4b5563',
        lineHeight: '1.6',
        marginBottom: '16px',
        whiteSpace: 'pre-line' // Respeta los saltos de línea de la BBDD
    },
    footer: {
        display: 'flex',
        alignItems: 'center',
        gap: '15px',
        marginTop: '15px',
        paddingTop: '15px',
        borderTop: '1px solid #f3f4f6',
        fontSize: '0.85rem',
        color: '#9ca3af'
    },
    emptyState: {
        textAlign: 'center',
        padding: '40px',
        color: '#6b7280',
        backgroundColor: '#f9fafb',
        borderRadius: '12px'
    }
};

// Helper para colores según tipo
const getBadgeColor = (tipo) => {
    switch(tipo) {
        case 'URGENTE': return { bg: '#fee2e2', text: '#991b1b' };
        case 'CULTOS': return { bg: '#f3e8ff', text: '#6b21a8' };
        case 'INFORMATIVO': return { bg: '#dbeafe', text: '#1e40af' };
        default: return { bg: '#f3f4f6', text: '#374151' };
    }
};

function HermanoMuroNoticias() {
    const [noticias, setNoticias] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchNoticias = async () => {
            try {
                // Llamamos al endpoint filtrado
                const response = await api.get('api/comunicados/mis-noticias/');
                setNoticias(response.data);
            } catch (err) {
                console.error(err);
                setError("No se pudieron cargar las noticias.");
            } finally {
                setLoading(false);
            }
        };

        fetchNoticias();
    }, []);

    // Formateador de fecha amigable
    const formatDate = (isoString) => {
        return new Date(isoString).toLocaleDateString('es-ES', {
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        });
    };

    if (loading) return <div style={{textAlign: 'center', padding: '50px'}}>Cargando actualidad de la Hermandad...</div>;

    return (
        <div style={styles.container}>
            <div style={styles.header}>
                <h1 style={styles.title}>Mi Tablón de Hermandad</h1>
                <p style={{color: '#6b7280'}}>Noticias seleccionadas según tus áreas de interés.</p>
            </div>

            {error && (
                <div style={{ padding: '15px', backgroundColor: '#fee2e2', color: '#b91c1c', borderRadius: '8px', marginBottom: '20px' }}>
                    {error}
                </div>
            )}

            <div style={styles.grid}>
                {noticias.length === 0 ? (
                    <div style={styles.emptyState}>
                        <Info size={48} style={{ marginBottom: '15px', opacity: 0.5 }} />
                        <h3>No hay noticias recientes para ti</h3>
                        <p>Asegúrate de tener configuradas tus <strong>Áreas de Interés</strong> en tu perfil.</p>
                    </div>
                ) : (
                    noticias.map(noticia => {
                        const colors = getBadgeColor(noticia.tipo_comunicacion);
                        return (
                            <article key={noticia.id} style={styles.card}>
                                {/* Cabecera de la tarjeta: Fecha y Tipo */}
                                <div style={styles.metaRow}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <Calendar size={14} />
                                        <span>{formatDate(noticia.fecha_emision)}</span>
                                    </div>
                                    <span style={{ 
                                        ...styles.badge, 
                                        backgroundColor: colors.bg, 
                                        color: colors.text 
                                    }}>
                                        {noticia.tipo_display || noticia.tipo_comunicacion}
                                    </span>
                                </div>

                                {/* Título y Contenido */}
                                <h2 style={styles.cardTitle}>{noticia.titulo}</h2>
                                <p style={styles.content}>{noticia.contenido}</p>

                                {/* Footer de la tarjeta: Autor y Áreas */}
                                <div style={styles.footer}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <User size={14} />
                                        <span>{noticia.autor_nombre}</span>
                                    </div>
                                    
                                    {/* Mostrar etiquetas de las áreas a las que iba dirigido */}
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: 'auto' }}>
                                        <Tag size={14} />
                                        <div style={{ display: 'flex', gap: '5px' }}>
                                            {noticia.areas_interes.map((area, idx) => (
                                                <span key={idx} style={{ fontSize: '0.75rem', fontWeight: '500' }}>
                                                    {area}{idx < noticia.areas_interes.length - 1 ? ',' : ''}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </article>
                        );
                    })
                )}
            </div>
        </div>
    );
}

export default HermanoMuroNoticias;