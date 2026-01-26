import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import "../styles/CrearActo.css";
import logoEscudo from '../assets/escudo.png'; 
import { ArrowLeft, CheckCircle, AlertCircle, Link as LinkIcon, Info } from "lucide-react";

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
    const [numeroVinculado, setNumeroVinculado] = useState(""); 

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
                const resUser = await api.get("api/me/");
                setUser(resUser.data);

                const resActos = await api.get("api/actos/");
                const now = new Date();
                
                const actosValidos = resActos.data.filter(acto => {
                    if (!acto.requiere_papeleta) return false;
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

    const handleActoChange = async (e) => {
        const actoId = e.target.value;
        setSelectedActoId(actoId);
        setSelectedPuestoId(""); 
        setNumeroVinculado(""); 
        setPuestosCirio([]);
        setError("");
        setSuccess(false);

        if (!actoId) return;

        try {
            setLoading(true);
            const res = await api.get(`api/actos/${actoId}/`);
            
            const ciriosDisponibles = res.data.puestos_disponibles.filter(p => {
                const nombreTipo = p.tipo_puesto.toUpperCase() || "";
                return p.disponible === true && nombreTipo.includes("CIRIO");
            });

            if (ciriosDisponibles.length === 0) {
                setError("No hay cupo de cirios disponible para este acto.");
            }

            setPuestosCirio(ciriosDisponibles);
        } catch (err) {
            setError("Error cargando la configuración del acto.");
        } finally {
            setLoading(false);
        }
    };

    // --- SUBMIT SIMPLIFICADO (UNA SOLA LLAMADA) ---
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!selectedActoId || !selectedPuestoId) {
            setError("Por favor, seleccione el acto y la modalidad de cirio.");
            return;
        }

        setSubmitting(true);
        setError("");
        setSuccess(false);

        // Preparamos el payload unificado
        // Si numeroVinculado está vacío, enviamos null o simplemente no lo enviamos
        const payload = {
            acto: selectedActoId,
            puesto: selectedPuestoId,
            numero_registro_vinculado: numeroVinculado ? parseInt(numeroVinculado) : null
        };

        try {
            // UNA SOLA LLAMADA AL BACKEND
            // El backend se encarga de crear Y vincular en la misma transacción atomic
            const res = await api.post("api/papeletas/solicitar-cirio/", payload);
            
            setSuccess(true);
            setSuccessData(res.data); // El backend ya devuelve el mensaje completo ("...vinculada con éxito")
            
            // Limpiar formulario
            setSelectedActoId("");
            setSelectedPuestoId("");
            setNumeroVinculado("");
            setPuestosCirio([]);
            
            setTimeout(() => navigate("/mis-papeletas-de-sitio"), 4000); 

        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                // Si falla la vinculación, el backend devuelve error 400 y NO crea la papeleta
                // Mostramos el error directamente al usuario
                if (data.detail) setError(data.detail);
                else if (data.non_field_errors) setError(data.non_field_errors[0]);
                else if (data.numero_registro_vinculado) setError(`Error en vinculación: ${data.numero_registro_vinculado[0]}`);
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
                            Obtenga su papeleta de sitio para portar cirio en la Estación de Penitencia.
                        </p>
                    </header>

                    {/* MENSAJES DE ESTADO */}
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

                    {/* FORMULARIO */}
                    {actosDisponibles.length === 0 ? (
                        <div className="info-box">
                            No hay plazos abiertos para la solicitud de cirios en este momento.
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

                                {selectedActoId && (
                                    <>
                                        {/* 2. SELECCIÓN DE PUESTO (CIRIO) */}
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
                                                            {puesto.numero_maximo_asignaciones < 9999 
                                                                ? ` (Libres: ${puesto.plazas_disponibles})` 
                                                                : ''}
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>
                                        </div>

                                        {/* 3. VINCULACIÓN CON OTRO HERMANO (OPCIONAL) */}
                                        <div className="separator-line"></div>
                                        <div className="form-group-acto full-width fade-in">
                                            <label htmlFor="vinculacion" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                VINCULAR CON OTRO HERMANO <span className="badge-optional">Opcional</span>
                                            </label>
                                            
                                            <div className="info-box-small" style={{ marginBottom: '10px', fontSize: '0.85em', color: '#555' }}>
                                                <Info size={14} style={{ marginRight: '5px', verticalAlign: '-2px' }}/>
                                                Solo puedes vincularte si tienes un número de registro <strong>MENOR</strong> (más antiguo) que el hermano al que acompañas. Renunciarás a tu antigüedad para ir con él.
                                            </div>

                                            <div className="input-with-icon-acto">
                                                <span className="icon-acto"><LinkIcon size={18}/></span>
                                                <input 
                                                    type="number" 
                                                    id="vinculacion"
                                                    placeholder="Nº de Registro del hermano (Ej: 1250)"
                                                    value={numeroVinculado}
                                                    onChange={(e) => setNumeroVinculado(e.target.value)}
                                                    disabled={submitting}
                                                    min="1"
                                                />
                                            </div>
                                        </div>
                                    </>
                                )}

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