import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom"; // Añadido useParams para obtener el ID del acto
import api from "../api"; // Tu instancia de axios
import "../styles/CrearActo.css"; // Reutilizamos los mismos estilos
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, AlertTriangle, CheckCircle, Clock } from "lucide-react";

function GestionReparto() {
    // 1. Estados de UI y Usuario (Idéntico a CrearActo)
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // 2. Estados específicos para la lógica de Reparto
    const [acto, setActo] = useState(null);
    const [processing, setProcessing] = useState(false); // Estado de carga del botón
    const [error, setError] = useState("");
    const [successData, setSuccessData] = useState(null); // Para mostrar resultados del reparto

    const navigate = useNavigate();
    const { id } = useParams(); // Obtenemos el ID del acto de la URL

    useEffect(() => {
        // Carga inicial de datos
        const fetchData = async () => {
            try {
                // 1. Cargar Usuario
                const resUser = await api.get("api/me/");
                const userData = resUser.data;
                setUser(userData);

                // Validación de seguridad frontend
                if (!userData.esAdmin) {
                    alert("Acceso denegado. Se requieren permisos de administrador.");
                    navigate("/home");
                    return;
                }

                // 2. Cargar Datos del Acto específico
                // Asumimos que tienes un endpoint GET /api/actos/{id}/
                const resActo = await api.get(`api/actos/${id}/`);
                setActo(resActo.data);

            } catch (err) {
                console.error("Error cargando datos:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                } else if (err.response && err.response.status === 404) {
                    setError("El acto solicitado no existe.");
                } else {
                    setError("Error de conexión. Por favor, recargue la página.");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [navigate, id]);

    // Lógica para verificar fechas
    const verificarDisponibilidad = () => {
        if (!acto || !acto.fin_solicitud) return false;
        const ahora = new Date();
        const finSolicitud = new Date(acto.fin_solicitud);
        return ahora > finSolicitud;
    };

    const handleReparto = async () => {
        if (!window.confirm(`¿Estás seguro de generar el reparto para "${acto.nombre}"?\n\nEsta acción asignará los puestos disponibles a los hermanos según su antigüedad.`)) {
            return;
        }

        setProcessing(true);
        setError("");
        setSuccessData(null);

        try {
            // Llamada al endpoint POST que definimos en Django
            const response = await api.post(`api/actos/${id}/reparto-automatico/`);
            
            setSuccessData(response.data); // Guardamos el resultado { asignaciones: X, sin_asignar: Y ... }
            
        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                // Manejo de errores que vienen del backend (ValidationError)
                setError(data.error || data.detail || "Error al procesar el reparto.");
            } else {
                setError("Error de red al intentar conectar con el servidor.");
            }
        } finally {
            setProcessing(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/";
    };

    if (loading) return <div className="site-wrapper"><div className="loading-spinner">Cargando datos...</div></div>;
    if (!user) return <div className="site-wrapper">Redirigiendo...</div>;

    const fechaValida = verificarDisponibilidad();

    return (
        <div className="site-wrapper">
            {/* --- NAVBAR (IDÉNTICO A TU CÓDIGO) --- */}
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
                    <li><a href="#hermandad">Hermandad</a></li>
                    <li><a href="#titulares">Titulares</a></li>
                    
                    <div className="nav-buttons-mobile">
                        {user && (
                            <>
                                <button className="btn-outline">Hermano: {user.dni}</button>
                                <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                            </>
                        )}
                    </div>
                </ul>

                <div className="nav-buttons-desktop">
                    {user && (
                        <>
                            <button className="btn-outline" onClick={() => navigate("/editar-perfil")} style={{cursor: 'pointer'}}>
                                Hermano: {user.dni}
                            </button>
                            <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                        </>
                    )}
                </div>
            </nav>

            {/* --- MAIN CONTENT --- */}
            <main className="main-container-area">
                <div className="card-container-area">
                    
                    {/* HEADER DE LA TARJETA */}
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Gestión de Reparto</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Asignación automática de insignias y puestos basada en antigüedad y preferencias.
                        </p>
                    </header>

                    {/* MENSAJES DE ESTADO */}
                    {error && (
                        <div style={{padding: '15px', backgroundColor: '#fee2e2', color: '#b91c1c', marginBottom: '1.5rem', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '10px'}}>
                            <AlertTriangle size={20}/> 
                            <span>{error}</span>
                        </div>
                    )}

                    {successData && (
                        <div style={{padding: '15px', backgroundColor: '#dcfce7', color: '#15803d', marginBottom: '1.5rem', borderRadius: '6px', border: '1px solid #86efac'}}>
                            <div style={{display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 'bold', marginBottom: '10px'}}>
                                <CheckCircle size={20}/> 
                                <span>{successData.mensaje}</span>
                            </div>
                            <ul style={{marginLeft: '30px', listStyleType: 'disc'}}>
                                <li>Puestos asignados correctamente: <strong>{successData.asignaciones}</strong></li>
                                <li>Hermanos en lista de espera (sin cupo): <strong>{successData.sin_asignar_count}</strong></li>
                            </ul>
                        </div>
                    )}

                    {/* CUERPO DE LA TARJETA */}
                    <section className="form-card-acto">
                        {acto ? (
                            <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
                                
                                {/* 1. INFORMACIÓN DEL ACTO */}
                                <div style={{backgroundColor: '#f8fafc', padding: '20px', borderRadius: '8px', border: '1px solid #e2e8f0'}}>
                                    <h3 style={{marginTop: 0, color: '#334155', borderBottom: '1px solid #cbd5e1', paddingBottom: '10px'}}>
                                        {acto.nombre}
                                    </h3>
                                    <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginTop: '15px'}}>
                                        <div>
                                            <span style={{fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 'bold'}}>Fecha del Acto</span>
                                            <div style={{color: '#1e293b', fontWeight: '500'}}>{new Date(acto.fecha).toLocaleString()}</div>
                                        </div>
                                        <div>
                                            <span style={{fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 'bold'}}>Cierre de Solicitudes</span>
                                            <div style={{color: '#1e293b', fontWeight: '500'}}>
                                                {acto.fin_solicitud ? new Date(acto.fin_solicitud).toLocaleString() : "No definido"}
                                            </div>
                                        </div>
                                        <div>
                                            <span style={{fontSize: '0.8rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 'bold'}}>Estado Plazo</span>
                                            <div style={{display: 'flex', alignItems: 'center', gap: '5px', fontWeight: 'bold', color: fechaValida ? '#16a34a' : '#ea580c'}}>
                                                {fechaValida ? (
                                                    <> <CheckCircle size={14}/> Plazo Finalizado (Listo)</>
                                                ) : (
                                                    <> <Clock size={14}/> Plazo Abierto (Esperar)</>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* 2. ZONA DE ACCIÓN */}
                                <div className="form-actions-acto" style={{flexDirection: 'column', alignItems: 'center', gap: '15px', borderTop: '2px dashed #e2e8f0', paddingTop: '20px'}}>
                                    {!fechaValida ? (
                                        <p style={{color: '#64748b', textAlign: 'center', fontStyle: 'italic'}}>
                                            El botón de reparto se habilitará automáticamente cuando pase la fecha de fin de solicitudes.
                                        </p>
                                    ) : (
                                        <p style={{color: '#334155', textAlign: 'center'}}>
                                            Al pulsar el botón, el sistema calculará la antigüedad de los solicitantes y asignará los puestos disponibles.
                                        </p>
                                    )}

                                    <button 
                                        type="button" 
                                        className="btn-save-acto" 
                                        onClick={handleReparto}
                                        disabled={!fechaValida || processing}
                                        style={{
                                            width: '100%', 
                                            maxWidth: '400px', 
                                            height: '50px', 
                                            fontSize: '1.1rem',
                                            backgroundColor: !fechaValida ? '#94a3b8' : undefined,
                                            cursor: !fechaValida ? 'not-allowed' : 'pointer'
                                        }}
                                    >
                                        {processing ? (
                                            "Procesando algoritmos..."
                                        ) : (
                                            <><span className="icon-save-acto">⚙️</span> Ejecutar Asignación Automática</>
                                        )}
                                    </button>
                                </div>

                            </div>
                        ) : (
                            <div style={{textAlign: 'center', padding: '20px'}}>No se ha cargado la información del acto.</div>
                        )}
                    </section>
                </div>
            </main>
        </div>
    );
}

export default GestionReparto;