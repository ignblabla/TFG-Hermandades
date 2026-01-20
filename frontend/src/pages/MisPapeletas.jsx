import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api"; // Tu wrapper de axios
import "../styles/MisPapeletas.css"; // Nuevo archivo de estilos sugerido abajo
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, FileText, Calendar, MapPin, CheckCircle, Clock, AlertCircle, Download } from "lucide-react";

function MisPapeletas() {
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [papeletas, setPapeletas] = useState([]);
    const [error, setError] = useState("");

    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Cargar Usuario
                const resUser = await api.get("api/me/");
                setUser(resUser.data);

                // 2. Cargar Historial de Papeletas (Endpoint nuevo)
                const resPapeletas = await api.get("api/papeletas/mis-papeletas/");
                setPapeletas(resPapeletas.data);

            } catch (err) {
                console.error("Error cargando datos:", err);
                if (err.response && err.response.status === 401) {
                    localStorage.removeItem("access");
                    navigate("/login");
                } else {
                    setError("No se pudo cargar el historial de papeletas.");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/";
    };

    // Función auxiliar para formatear fecha
    const formatearFecha = (fechaISO) => {
        if (!fechaISO) return "Fecha por determinar";
        const fecha = new Date(fechaISO);
        return fecha.toLocaleDateString('es-ES', { 
            weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute:'2-digit' 
        });
    };

    // Función para obtener estilos según estado
    const getEstadoBadge = (estado) => {
        switch (estado) {
            case 'SOLICITADA':
                return { class: 'badge-warning', icon: <Clock size={14} />, text: 'Solicitada - Pendiente de Reparto' };
            case 'EMITIDA':
                return { class: 'badge-info', icon: <AlertCircle size={14} />, text: 'Emitida - Pendiente de Pago/Retirada' };
            case 'RECOGIDA':
                return { class: 'badge-success', icon: <CheckCircle size={14} />, text: 'Recogida - Activa' };
            case 'LEIDA':
                return { class: 'badge-success', icon: <CheckCircle size={14} />, text: 'Completada (Leída)' };
            case 'ANULADA':
                return { class: 'badge-danger', icon: <AlertCircle size={14} />, text: 'Anulada' };
            default:
                return { class: 'badge-default', icon: <FileText size={14} />, text: estado };
        }
    };

    if (loading) return <div className="site-wrapper loading-screen">Cargando tus papeletas...</div>;

    return (
        <div className="site-wrapper">
            {/* --- NAVBAR (Reutilizada para consistencia) --- */}
            <nav className="navbar">
                <div className="logo-container">
                    <img src={logoEscudo} alt="Escudo San Gonzalo" className="nav-logo" />
                    <div className="logo-text">
                        <h4>Hermandad de San Gonzalo</h4>
                        <span>SEVILLA</span>
                    </div>
                </div>

                <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>☰</button>

                <ul className={`nav-links ${menuOpen ? "active" : ""}`}>
                    <li><a href="/home">Inicio</a></li>
                    <li><a href="/agenda">Agenda</a></li>
                    <div className="nav-buttons-mobile">
                        {user && (
                            <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                        )}
                    </div>
                </ul>

                <div className="nav-buttons-desktop">
                    {user && (
                        <>
                            <button className="btn-outline" onClick={() => navigate("/perfil")}>
                                Hermano: {user.dni}
                            </button>
                            <button className="btn-purple" onClick={handleLogout}>
                                Cerrar Sesión
                            </button>
                        </>
                    )}
                </div>
            </nav>

            {/* --- MAIN CONTENT --- */}
            <main className="main-container-area">
                <div className="card-container-area full-width-card">
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Mis Papeletas de Sitio</h1>
                            <button className="btn-back-area" onClick={() => navigate("/home")}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Consulta el estado de tus solicitudes y accede a tus papeletas históricas.
                        </p>
                    </header>

                    {error && <div className="alert-box error">{error}</div>}

                    {papeletas.length === 0 && !error ? (
                        <div className="empty-state">
                            <FileText size={48} color="#cbd5e1" />
                            <p>No tienes papeletas de sitio solicitadas ni históricas.</p>
                            <button className="btn-purple mt-4" onClick={() => navigate("/agenda")}>
                                Ver Actos Disponibles
                            </button>
                        </div>
                    ) : (
                        <div className="papeletas-grid">
                            {papeletas.map((papeleta) => {
                                const estadoInfo = getEstadoBadge(papeleta.estado_papeleta);
                                
                                return (
                                    <article key={papeleta.id} className="papeleta-card">
                                        <div className="papeleta-header">
                                            <span className="papeleta-year">{papeleta.anio}</span>
                                            <div className={`status-badge ${estadoInfo.class}`}>
                                                {estadoInfo.icon}
                                                <span>{estadoInfo.text}</span>
                                            </div>
                                        </div>
                                        
                                        <h3 className="acto-title">{papeleta.nombre_acto}</h3>

                                        <div className="papeleta-body">
                                            {/* Si ya tiene sitio asignado (EMITIDA/RECOGIDA) */}
                                            {papeleta.nombre_puesto ? (
                                                <div className="asignacion-box">
                                                    <div className="asignacion-row">
                                                        <span className="label">Puesto:</span>
                                                        <span className="value highlight">{papeleta.nombre_puesto}</span>
                                                    </div>
                                                    {papeleta.tramo_display && (
                                                        <div className="asignacion-row">
                                                            <span className="label">Ubicación:</span>
                                                            <span className="value"><MapPin size={14}/> {papeleta.tramo_display}</span>
                                                        </div>
                                                    )}
                                                    {papeleta.numero_papeleta && (
                                                        <div className="asignacion-row">
                                                            <span className="label">Nº Papeleta:</span>
                                                            <span className="value font-mono">{papeleta.numero_papeleta}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                /* Si aún es SOLICITADA, mostramos lo que pidió */
                                                <div className="preferencias-box">
                                                    <h4>Solicitud registrada:</h4>
                                                    <ul>
                                                        {papeleta.preferencias && papeleta.preferencias.map((pref) => (
                                                            <li key={pref.id}>
                                                                <span className="pref-orden">{pref.orden_prioridad}º</span> 
                                                                {pref.nombre_puesto}
                                                            </li>
                                                        ))}
                                                        {(!papeleta.preferencias || papeleta.preferencias.length === 0) && (
                                                            <li>Solicitud general (Cirio)</li>
                                                        )}
                                                    </ul>
                                                </div>
                                            )}
                                        </div>

                                        <div className="papeleta-footer">
                                            {(papeleta.estado_papeleta === 'EMITIDA' || papeleta.estado_papeleta === 'RECOGIDA') ? (
                                                <button className="btn-action primary">
                                                    <Download size={16} /> Descargar Digital
                                                </button>
                                            ) : (
                                                <button className="btn-action disabled" disabled>
                                                    Pendiente de asignación
                                                </button>
                                            )}
                                        </div>
                                    </article>
                                );
                            })}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}

export default MisPapeletas;