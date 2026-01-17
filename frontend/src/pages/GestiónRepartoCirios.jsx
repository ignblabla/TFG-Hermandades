import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api from "../api"; // Tu instancia de axios configurada
import "../styles/CrearActo.css"; // Reutilizamos estilos
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, AlertTriangle, CheckCircle, Clock, Calendar, Users } from "lucide-react";

function GestionRepartoCirios() {
    // --- 1. Estados ---
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [acto, setActo] = useState(null);
    const [processing, setProcessing] = useState(false);
    const [error, setError] = useState("");
    const [successData, setSuccessData] = useState(null);

    const navigate = useNavigate();
    const { id } = useParams();

    // --- 2. Carga de Datos ---
    useEffect(() => {
        const fetchData = async () => {
            try {
                // A. Usuario
                const resUser = await api.get("api/me/");
                const userData = resUser.data;
                setUser(userData);

                if (!userData.esAdmin) {
                    alert("Acceso denegado. Solo administradores pueden realizar el reparto.");
                    navigate("/home");
                    return;
                }

                // B. Acto
                const resActo = await api.get(`api/actos/${id}/`);
                setActo(resActo.data);

            } catch (err) {
                console.error("Error cargando datos:", err);
                if (err.response?.status === 401) navigate("/login");
                else if (err.response?.status === 404) setError("El acto no existe.");
                else setError("Error de conexión.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [navigate, id]);

    // --- 3. Lógica de Fechas (Ajustada a Cirios) ---
    const verificarDisponibilidad = () => {
        // Usamos fin_solicitud_cirios, que es el campo específico del modelo para este proceso
        if (!acto || !acto.fin_solicitud_cirios) return false;
        
        const ahora = new Date();
        const finSolicitud = new Date(acto.fin_solicitud_cirios);
        
        // El reparto solo se puede hacer si YA pasó la fecha de fin
        return ahora > finSolicitud;
    };

    // --- 4. Ejecución del Reparto ---
    const handleReparto = async () => {
        if (!window.confirm(`⚠️ CONFIRMACIÓN REQUERIDA\n\n¿Estás seguro de ejecutar el algoritmo de asignación para "${acto.nombre}"?\n\nEsto borrará asignaciones de cirios previas y recalculará los tramos basándose en la antigüedad.`)) {
            return;
        }

        setProcessing(true);
        setError("");
        setSuccessData(null);

        try {
            // Ajustamos la URL al endpoint definido en Django: 'reparto-cirios'
            const response = await api.post(`api/actos/${id}/reparto-cirios/`);
            
            setSuccessData(response.data);
            
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                // Captura el ValidationError de Python
                setError(err.response.data.error || "Error al procesar el reparto.");
            } else {
                setError("Error de red. Verifique su conexión.");
            }
        } finally {
            setProcessing(false);
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        window.location.href = "/login";
    };

    // --- 5. Renderizado ---
    if (loading) return <div className="site-wrapper"><div className="loading-spinner">Cargando...</div></div>;
    if (!user) return null;

    const fechaValida = verificarDisponibilidad();
    // Formateador de fecha simple
    const formatDate = (dateString) => dateString ? new Date(dateString).toLocaleString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute:'2-digit'}) : "No definido";

    return (
        <div className="site-wrapper">
            {/* NAVBAR (Reutilizada) */}
            <nav className="navbar">
                <div className="logo-container">
                    <img src={logoEscudo} alt="Escudo" className="nav-logo" />
                    <div className="logo-text">
                        <h4>Hermandad de San Gonzalo</h4>
                        <span>SECRETARÍA</span>
                    </div>
                </div>
                <div className="nav-buttons-desktop">
                    <button className="btn-outline" style={{cursor: 'default'}}>Admin: {user.nombre}</button>
                    <button className="btn-purple" onClick={handleLogout}>Salir</button>
                </div>
            </nav>

            <main className="main-container-area">
                <div className="card-container-area" style={{maxWidth: '800px'}}>
                    
                    {/* Header */}
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1><Users size={28} style={{marginRight: '10px'}}/>Gestión de Reparto de Cirios</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Algoritmo de asignación automática de tramos por antigüedad.
                        </p>
                    </header>

                    {/* Alertas */}
                    {error && (
                        <div style={{padding: '15px', backgroundColor: '#fee2e2', color: '#b91c1c', marginBottom: '1.5rem', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '10px', border: '1px solid #fca5a5'}}>
                            <AlertTriangle size={24}/> 
                            <div>
                                <strong>Error en el proceso:</strong><br/>
                                <span>{error}</span>
                            </div>
                        </div>
                    )}

                    {successData && (
                        <div style={{padding: '20px', backgroundColor: '#dcfce7', color: '#15803d', marginBottom: '1.5rem', borderRadius: '8px', border: '1px solid #86efac'}}>
                            <div style={{display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '10px'}}>
                                <CheckCircle size={28}/> 
                                <span>Reparto Completado con Éxito</span>
                            </div>
                            <p>{successData.mensaje}</p>
                            {/* Si decidimos enviar estadísticas desde el backend en el futuro, se mostrarían aquí */}
                        </div>
                    )}

                    {/* Información del Acto */}
                    <section className="form-card-acto">
                        {acto ? (
                            <div style={{display: 'flex', flexDirection: 'column', gap: '25px'}}>
                                
                                <div style={{backgroundColor: '#f1f5f9', padding: '20px', borderRadius: '12px', border: '1px solid #cbd5e1'}}>
                                    <h2 style={{marginTop: 0, fontSize: '1.4rem', color: '#334155', marginBottom: '15px'}}>{acto.nombre}</h2>
                                    
                                    <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px'}}>
                                        {/* Dato 1: Cierre de Insignias (Informativo) */}
                                        <div>
                                            <span style={{fontSize: '0.75rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>
                                                Fin Solicitud Insignias
                                            </span>
                                            <div style={{display: 'flex', alignItems: 'center', gap: '8px', color: '#64748b'}}>
                                                <Calendar size={16}/>
                                                <span>{formatDate(acto.fin_solicitud)}</span>
                                            </div>
                                        </div>

                                        {/* Dato 2: Cierre de Cirios (CRÍTICO) */}
                                        <div style={{position: 'relative'}}>
                                            <span style={{fontSize: '0.75rem', color: '#475569', textTransform: 'uppercase', fontWeight: 'bold', display: 'block', marginBottom: '5px'}}>
                                                Fin Solicitud Cirios (General)
                                            </span>
                                            <div style={{display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a', fontWeight: '600', fontSize: '1.1rem'}}>
                                                <Clock size={20} color={fechaValida ? "#16a34a" : "#ea580c"}/>
                                                <span>{formatDate(acto.fin_solicitud_cirios)}</span>
                                            </div>
                                            {/* Badge de estado */}
                                            <span style={{
                                                marginTop: '8px', display: 'inline-block', padding: '4px 12px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: 'bold',
                                                backgroundColor: fechaValida ? '#dcfce7' : '#fff7ed',
                                                color: fechaValida ? '#166534' : '#c2410c',
                                                border: `1px solid ${fechaValida ? '#86efac' : '#fdba74'}`
                                            }}>
                                                {fechaValida ? "PLAZO CERRADO - REPARTO DISPONIBLE" : "PLAZO ABIERTO - ESPERAR"}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Botón de Acción */}
                                <div style={{borderTop: '2px dashed #e2e8f0', paddingTop: '25px', display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
                                    
                                    {!fechaValida && (
                                        <div style={{marginBottom: '15px', display: 'flex', gap: '10px', color: '#d97706', backgroundColor: '#fffbeb', padding: '10px 15px', borderRadius: '6px', fontSize: '0.9rem', maxWidth: '600px'}}>
                                            <AlertTriangle size={20} style={{minWidth: '20px'}}/>
                                            <p style={{margin: 0}}>
                                                No es posible realizar el reparto automático mientras el plazo de solicitud de cirios siga abierto. Espere a que finalice la fecha indicada arriba.
                                            </p>
                                        </div>
                                    )}

                                    <button 
                                        type="button" 
                                        className="btn-save-acto" 
                                        onClick={handleReparto}
                                        disabled={!fechaValida || processing}
                                        style={{
                                            width: '100%', 
                                            maxWidth: '500px', 
                                            height: '60px', 
                                            fontSize: '1.2rem',
                                            display: 'flex',
                                            justifyContent: 'center',
                                            alignItems: 'center',
                                            gap: '15px',
                                            backgroundColor: (!fechaValida || processing) ? '#94a3b8' : '#4f46e5',
                                            cursor: (!fechaValida || processing) ? 'not-allowed' : 'pointer',
                                            transition: 'all 0.3s ease',
                                            boxShadow: (!fechaValida || processing) ? 'none' : '0 4px 6px -1px rgba(79, 70, 229, 0.3)'
                                        }}
                                    >
                                        {processing ? (
                                            <>
                                                <div className="spinner-mini"></div>
                                                Calculando Antigüedad...
                                            </>
                                        ) : (
                                            <>
                                                <Users size={24} />
                                                EJECUTAR ALGORITMO DE REPARTO
                                            </>
                                        )}
                                    </button>

                                    {fechaValida && !processing && (
                                        <p style={{marginTop: '15px', color: '#64748b', fontSize: '0.9rem', fontStyle: 'italic'}}>
                                            Esta acción puede tardar unos segundos dependiendo del número de hermanos.
                                        </p>
                                    )}
                                </div>

                            </div>
                        ) : (
                            <div style={{textAlign: 'center', padding: '40px', color: '#94a3b8'}}>No se ha podido cargar la información del acto.</div>
                        )}
                    </section>
                </div>
            </main>
        </div>
    );
}

export default GestionRepartoCirios;