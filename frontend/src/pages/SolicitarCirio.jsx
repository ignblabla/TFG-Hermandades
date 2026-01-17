import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import "../styles/CrearActo.css";
import logoEscudo from '../assets/escudo.png'; 
import { ArrowLeft, CheckCircle, AlertCircle } from "lucide-react";

function SolicitarCirio() {
    // --- ESTADOS ---
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [actosDisponibles, setActosDisponibles] = useState([]);
    const [puestosCirio, setPuestosCirio] = useState([]);
    
    // Selección del usuario
    const [selectedActoId, setSelectedActoId] = useState("");
    const [selectedPuestoId, setSelectedPuestoId] = useState("");

    // Estados de formulario
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [successData, setSuccessData] = useState(null);

    const navigate = useNavigate();

    // --- CARGA INICIAL ---
    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Cargar Usuario
                const resUser = await api.get("api/me/");
                setUser(resUser.data);

                // 2. Cargar Actos
                const resActos = await api.get("api/actos/");
                const now = new Date();
                
                // FILTRO: Solo actos que requieran papeleta Y estén en plazo de CIRIOS
                const actosValidos = resActos.data.filter(acto => {
                    if (!acto.requiere_papeleta) return false;
                    
                    // Verificación de fechas nulas y rango
                    if (!acto.inicio_solicitud_cirios || !acto.fin_solicitud_cirios) return false;

                    const inicio = new Date(acto.inicio_solicitud_cirios);
                    const fin = new Date(acto.fin_solicitud_cirios);
                    
                    return now >= inicio && now <= fin;
                });

                setActosDisponibles(actosValidos);
            } catch (err) {
                console.error(err);
                if (err.response && err.response.status === 401) navigate("/login");
                else setError("Error cargando los datos del servidor.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [navigate]);

    // --- MANEJADORES ---

    // 1. Al cambiar de acto, buscamos los puestos tipo CIRIO
    const handleActoChange = async (e) => {
        const actoId = e.target.value;
        setSelectedActoId(actoId);
        setSelectedPuestoId(""); // Reset puesto
        setPuestosCirio([]);
        setError("");
        setSuccess(false);

        if (!actoId) return;

        try {
            setLoading(true);
            const res = await api.get(`api/actos/${actoId}/`);
            
            // LÓGICA DE NEGOCIO FRONTEND:
            // Filtramos los puestos disponibles que sean de tipo "CIRIO"
            // (El backend también valida esto, pero filtramos aquí para UX)
            const ciriosDisponibles = res.data.puestos_disponibles.filter(p => {
                const nombreTipo = p.tipo_puesto.toUpperCase() || "";
                return p.disponible === true && nombreTipo.includes("CIRIO");
            });

            if (ciriosDisponibles.length === 0) {
                setError("No hay cupo de cirios disponible para este acto o no se han configurado puestos de tipo 'Cirio'.");
            }

            setPuestosCirio(ciriosDisponibles);
        } catch (err) {
            setError("Error cargando la configuración del acto.");
        } finally {
            setLoading(false);
        }
    };

    // 2. Enviar Solicitud
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!selectedActoId || !selectedPuestoId) {
            setError("Por favor, seleccione el acto y la modalidad de cirio.");
            return;
        }

        setSubmitting(true);
        setError("");
        setSuccess(false);

        const payload = {
            acto: selectedActoId,
            puesto: selectedPuestoId
        };

        try {
            const res = await api.post("api/papeletas/solicitar-cirio/", payload);
            setSuccess(true);
            setSuccessData(res.data);
            
            // Limpiar formulario pero mantener el éxito visible un momento
            setSelectedActoId("");
            setSelectedPuestoId("");
            setPuestosCirio([]);
            
            // Redirección automática opcional
            setTimeout(() => navigate("/home"), 4000); 

        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                // Manejar errores del backend (ej: "Ya tienes solicitud", "Cuerpo incorrecto")
                if (data.detail) setError(data.detail);
                else if (data.non_field_errors) setError(data.non_field_errors[0]);
                else if (data.acto) setError(`Error en el acto: ${data.acto}`);
                else if (data.puesto) setError(`Error en el puesto: ${data.puesto}`);
                else setError("No se pudo procesar la solicitud. Revise los datos.");
            } else {
                setError("Error de conexión con el servidor.");
            }
        } finally {
            setSubmitting(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("access");
        window.location.href = "/";
    };

    if (loading && !user) return <div className="site-wrapper">Cargando aplicación...</div>;

    return (
        <div className="site-wrapper">
            {/* --- NAVBAR --- */}
            <nav className="navbar">
                <div className="logo-container">
                    <img src={logoEscudo} alt="Escudo" className="nav-logo" />
                    <div className="logo-text">
                        <h4>Hermandad de San Gonzalo</h4>
                        <span>SEVILLA</span>
                    </div>
                </div>
                <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
                <ul className={`nav-links ${menuOpen ? "active" : ""}`}>
                     {/* Links de navegación... */}
                    <div className="nav-buttons-mobile">
                        <button className="btn-outline">Hermano: {user?.dni}</button>
                        <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                    </div>
                </ul>
                <div className="nav-buttons-desktop">
                    <button className="btn-outline">Hermano: {user?.dni}</button>
                    <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                </div>
            </nav>

            <main className="main-container-area">
                <div className="card-container-area">
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Solicitud de Papeleta de Sitio</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Obtenga su papeleta de sitio para portar cirio en la Estación de Penitencia u otros actos de culto externo.
                        </p>
                    </header>

                    {/* --- MENSAJES DE ESTADO --- */}
                    {error && (
                        <div className="alert-box error">
                            <AlertCircle size={20} style={{ marginRight: '10px' }}/>
                            <span>{error}</span>
                        </div>
                    )}
                    
                    {success && (
                        <div className="alert-box success">
                            <CheckCircle size={20} style={{ marginRight: '10px' }}/>
                            <div>
                                <strong>¡Solicitud realizada con éxito!</strong>
                                <p style={{ margin: '5px 0 0 0', fontSize: '0.9em' }}>
                                    {successData?.mensaje}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* --- CONTENIDO PRINCIPAL --- */}
                    {actosDisponibles.length === 0 ? (
                        <div className="info-box">
                            No hay plazos abiertos para la solicitud de cirios en este momento.
                            <br/><small>El plazo de insignias y cirios suele ser diferente.</small>
                        </div>
                    ) : (
                        <section className="form-card-acto">
                            <form className="event-form-acto" onSubmit={handleSubmit}>
                                
                                {/* 1. SELECCIÓN DE ACTO */}
                                <div className="form-group-acto full-width">
                                    <label htmlFor="acto">SELECCIONE EL ACTO</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">📅</span>
                                        <select 
                                            id="acto" 
                                            value={selectedActoId} 
                                            onChange={handleActoChange} 
                                            required
                                            disabled={submitting}
                                        >
                                            <option value="" disabled>-- Seleccione un acto disponible --</option>
                                            {actosDisponibles.map(acto => (
                                                <option key={acto.id} value={acto.id}>
                                                    {acto.nombre} (Cierre Cirios: {new Date(acto.fin_solicitud_cirios).toLocaleDateString()})
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                {/* 2. SELECCIÓN DE PUESTO (CIRIO) */}
                                {selectedActoId && (
                                    <div className="form-group-acto full-width fade-in">
                                        <label htmlFor="puesto">MODALIDAD DE SITIO</label>
                                        <div className="input-with-icon-acto">
                                            <span className="icon-acto">🕯️</span>
                                            <select 
                                                id="puesto" 
                                                value={selectedPuestoId} 
                                                onChange={(e) => setSelectedPuestoId(e.target.value)} 
                                                required
                                                disabled={submitting || puestosCirio.length === 0}
                                            >
                                                <option value="" disabled>-- Seleccione tipo de cirio --</option>
                                                {puestosCirio.map(puesto => (
                                                    <option key={puesto.id} value={puesto.id}>
                                                        {puesto.nombre} 
                                                        {/* Mostramos disponibilidad si no es ilimitada */}
                                                        {puesto.numero_maximo_asignaciones < 9999 
                                                            ? ` (Libres: ${puesto.plazas_disponibles})` 
                                                            : ''}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                        {puestosCirio.length > 0 && (
                                            <small className="field-hint">
                                                Seleccione "Cirio" o la variante específica si pertenece a tramos especiales (ej: Niños, Penitentes).
                                            </small>
                                        )}
                                    </div>
                                )}

                                {/* BOTONES DE ACCIÓN */}
                                <div className="form-actions-acto">
                                    <button 
                                        type="button" 
                                        className="btn-cancel-acto" 
                                        onClick={() => navigate("/home")}
                                        disabled={submitting}
                                    >
                                        Cancelar
                                    </button>
                                    <button 
                                        type="submit" 
                                        className="btn-save-acto" 
                                        disabled={submitting || !selectedPuestoId}
                                    >
                                        <span className="icon-save-acto">✍️</span> 
                                        {submitting ? "Procesando..." : "Solicitar Sitio"}
                                    </button>
                                </div>

                            </form>
                        </section>
                    )}
                </div>
            </main>
        </div>
    );
}

export default SolicitarCirio;