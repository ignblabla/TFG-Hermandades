import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import "../styles/CrearActo.css"; // Asegúrate de mantener tus estilos
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, Plus, Trash2, ArrowUp, ArrowDown, Info, AlertCircle } from "lucide-react";

function HermanoCrearSolicitudUnificada() {
    // --- ESTADOS ---
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [actosDisponibles, setActosDisponibles] = useState([]);
    
    // Arrays separados para la lógica de interfaz
    const [insigniasDisponibles, setInsigniasDisponibles] = useState([]);
    const [generalesDisponibles, setGeneralesDisponibles] = useState([]); // Cirios, Diputados, etc.
    
    // Selección del usuario
    const [selectedActoId, setSelectedActoId] = useState("");
    
    // 1. Estado para el puesto único (NO insignia)
    const [selectedPuestoGeneralId, setSelectedPuestoGeneralId] = useState("");
    
    // 2. Estado para la lista de insignias
    const [selectedInsigniaToAdd, setSelectedInsigniaToAdd] = useState("");
    const [preferenciasInsignias, setPreferenciasInsignias] = useState([]); 

    // Estados de formulario
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const navigate = useNavigate();

    // --- CARGA INICIAL ---
    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);

                // 1. Cargar Usuario
                const resUser = await api.get("api/me/");
                setUser(resUser.data);

                // 2. Cargar Actos
                const resActos = await api.get("api/actos/");
                
                let listaActos = [];
                if (Array.isArray(resActos.data)) {
                    listaActos = resActos.data;
                } else if (resActos.data && resActos.data.results) {
                    listaActos = resActos.data.results;
                }

                const now = new Date();
                
                // 3. Filtrar Actos válidos (Unificados y en fecha)
                const actosValidos = listaActos.filter(acto => {
                    if (!acto.requiere_papeleta) return false;
                    
                    // Comprobación flexible de modalidad
                    if (String(acto.modalidad).toUpperCase() !== 'UNIFICADO') return false;

                    if (!acto.inicio_solicitud || !acto.fin_solicitud) return false;

                    const inicio = new Date(acto.inicio_solicitud);
                    const fin = new Date(acto.fin_solicitud);
                    
                    return now >= inicio && now <= fin;
                });

                setActosDisponibles(actosValidos);
            } catch (err) {
                console.error("Error cargando datos:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                } else {
                    setError("Error cargando datos iniciales.");
                }
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
        
        // Resetear selecciones
        setPreferenciasInsignias([]); 
        setSelectedPuestoGeneralId("");
        setInsigniasDisponibles([]);
        setGeneralesDisponibles([]);
        setError("");

        if (!actoId) return;

        try {
            setLoading(true);
            const res = await api.get(`api/actos/${actoId}/`);
            
            // Separar los puestos disponibles en dos grupos
            const todosLosPuestos = res.data.puestos_disponibles || [];
            
            // Filtramos solo los disponibles
            const disponibles = todosLosPuestos.filter(p => p.disponible === true);

            // Grupo A: Insignias (Para la lista de preferencias)
            const soloInsignias = disponibles.filter(p => p.es_insignia === true);
            
            // Grupo B: Generales (Para el select único)
            const soloGenerales = disponibles.filter(p => p.es_insignia === false);

            setInsigniasDisponibles(soloInsignias);
            setGeneralesDisponibles(soloGenerales);

        } catch (err) {
            setError("Error cargando los puestos del acto.");
        } finally {
            setLoading(false);
        }
    };

    const handleAddInsignia = () => {
        if (!selectedInsigniaToAdd) return;

        const puesto = insigniasDisponibles.find(p => p.id === parseInt(selectedInsigniaToAdd));
        if (!puesto) return;

        // Validación: No duplicados
        if (preferenciasInsignias.some(p => p.id === puesto.id)) {
            setError("Esa insignia ya está en tu lista de preferencias.");
            return;
        }

        // Validación: Máximo 20 (según tu servicio)
        if (preferenciasInsignias.length >= 20) {
            setError("Ha alcanzado el número máximo de preferencias.");
            return;
        }

        setPreferenciasInsignias([...preferenciasInsignias, puesto]);
        setSelectedInsigniaToAdd(""); 
        setError("");
    };

    const handleRemoveInsignia = (index) => {
        const nuevasPrefs = [...preferenciasInsignias];
        nuevasPrefs.splice(index, 1);
        setPreferenciasInsignias(nuevasPrefs);
        setError("");
    };

    const moveInsignia = (index, direction) => {
        const nuevasPrefs = [...preferenciasInsignias];
        const item = nuevasPrefs[index];
        nuevasPrefs.splice(index, 1);
        nuevasPrefs.splice(index + direction, 0, item);
        setPreferenciasInsignias(nuevasPrefs);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Validación final
        if (preferenciasInsignias.length === 0 && !selectedPuestoGeneralId) {
            setError("Debe solicitar al menos una Insignia o un Sitio General (Cirio/Diputado, etc).");
            return;
        }

        setSubmitting(true);
        setError("");
        setSuccess(false);

        // --- CORRECCIÓN DEL PAYLOAD ---
        const payload = {
            acto_id: selectedActoId,
            
            // Enviamos el ID del puesto general o null si está vacío
            puesto_general_id: selectedPuestoGeneralId ? parseInt(selectedPuestoGeneralId) : null,
            
            // CORREGIDO AQUÍ:
            // El Serializer 'PreferenciaSolicitudDTO' espera las claves 'puesto_id' y 'orden'.
            preferencias_solicitadas: preferenciasInsignias.map((p, index) => ({
                puesto_id: p.id,       // Antes enviabas: puesto_solicitado
                orden: index + 1       // Antes enviabas: orden_prioridad
            }))
        };

        try {
            await api.post("api/papeletas/solicitar-unificada/", payload);
            setSuccess(true);
            
            // Limpieza
            setPreferenciasInsignias([]);
            setSelectedPuestoGeneralId("");
            setSelectedActoId("");
            
            setTimeout(() => navigate("/mis-papeletas"), 3000); 
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                const data = err.response.data;
                // Manejo de errores detallado
                if (data.detail) setError(data.detail);
                else if (typeof data === 'string') setError(data); 
                // Errores de validación por campo
                else if (data.puesto_general_id) setError(`Error en puesto general: ${data.puesto_general_id}`);
                // Ahora atrapamos errores específicos del array de preferencias
                else if (data.preferencias_solicitadas) {
                     // A veces DRF devuelve un array de errores si falla un item específico
                    const msg = Array.isArray(data.preferencias_solicitadas) 
                        ? "Error en los datos de las insignias seleccionadas." 
                        : data.preferencias_solicitadas;
                    setError(msg);
                }
                else setError("Error al procesar la solicitud. Revise los datos.");
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

    if (loading && !user) return <div className="site-wrapper">Cargando...</div>;

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
                <div className="nav-buttons-desktop">
                    <button className="btn-outline">Hermano: {user?.dni}</button>
                    <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                </div>
            </nav>

            <main className="main-container-area">
                <div className="card-container-area" style={{maxWidth: '800px'}}>
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Solicitud Unificada</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Solicitud combinada de sitio. Puede solicitar sitio general (ej: Cirio) y/o participar en el concurso de insignias.
                            <br/>
                            <small className="text-muted"><Info size={14} style={{verticalAlign: 'middle'}}/> Si solicita insignias, el puesto general actuará como reserva si no se le asigna ninguna vara.</small>
                        </p>
                    </header>

                    {error && <div className="alert-box error"><AlertCircle size={16}/> {error}</div>}
                    {success && <div className="alert-box success">¡Solicitud registrada correctamente!</div>}

                    {actosDisponibles.length === 0 ? (
                        <div className="info-box">
                            No hay actos de modalidad unificada disponibles en este momento.
                        </div>
                    ) : (
                        <section className="form-card-acto">
                            <form className="event-form-acto" onSubmit={handleSubmit}>
                                
                                {/* 1. SELECCIÓN DE ACTO */}
                                <div className="form-group-acto full-width">
                                    <label htmlFor="acto">SELECCIONE EL ACTO</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">📜</span>
                                        <select 
                                            id="acto" 
                                            value={selectedActoId} 
                                            onChange={handleActoChange} 
                                            required
                                            disabled={submitting}
                                        >
                                            <option value="" disabled>-- Seleccione un acto --</option>
                                            {actosDisponibles.map(acto => (
                                                <option key={acto.id} value={acto.id}>
                                                    {acto.nombre}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                {selectedActoId && (
                                    <>
                                        {/* 2. SITIO GENERAL (Cirios, Cruz, Diputados...) */}
                                        <div className="separator-line"></div>
                                        <h3 className="section-title">1. Sitio General (Reserva o Puesto Fijo)</h3>
                                        <p className="section-desc">Seleccione el puesto que ocupará si no solicita insignias o si no se le asignan.</p>
                                        
                                        <div className="form-group-acto full-width">
                                            <div className="input-with-icon-acto">
                                                <span className="icon-acto">🕯️</span>
                                                <select 
                                                    value={selectedPuestoGeneralId}
                                                    onChange={(e) => setSelectedPuestoGeneralId(e.target.value)}
                                                    disabled={submitting}
                                                    className={!selectedPuestoGeneralId ? "select-placeholder" : ""}
                                                >
                                                    <option value="">-- No solicitar sitio general --</option>
                                                    {generalesDisponibles.map(p => (
                                                        <option key={p.id} value={p.id}>
                                                            {p.nombre} ({p.tipo_puesto.nombre_tipo || p.tipo_puesto})
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>
                                            {generalesDisponibles.length === 0 && (
                                                <small className="text-warning">No hay sitios generales disponibles.</small>
                                            )}
                                        </div>

                                        {/* 3. INSIGNIAS (Preferencias) */}
                                        <div className="separator-line"></div>
                                        <h3 className="section-title">2. Solicitud de Insignias (Opcional)</h3>
                                        <p className="section-desc">Añada las insignias a las que desea optar, ordenadas por preferencia.</p>

                                        <div className="preference-selector-container">
                                            <div className="add-insignia-row">
                                                <div className="input-with-icon-acto flex-grow">
                                                    <span className="icon-acto">🏅</span>
                                                    <select 
                                                        value={selectedInsigniaToAdd}
                                                        onChange={(e) => setSelectedInsigniaToAdd(e.target.value)}
                                                        disabled={submitting}
                                                    >
                                                        <option value="" disabled>Seleccione una insignia...</option>
                                                        {insigniasDisponibles.map(p => {
                                                            const isSelected = preferenciasInsignias.some(pref => pref.id === p.id);
                                                            return (
                                                                <option key={p.id} value={p.id} disabled={isSelected}>
                                                                    {p.nombre} {isSelected ? '(Añadida)' : ''}
                                                                </option>
                                                            );
                                                        })}
                                                    </select>
                                                </div>
                                                <button 
                                                    type="button" 
                                                    className="btn-add-pref" 
                                                    onClick={handleAddInsignia}
                                                    disabled={!selectedInsigniaToAdd || submitting}
                                                >
                                                    <Plus size={18} /> Añadir
                                                </button>
                                            </div>
                                        </div>

                                        <div className="preferences-list-container">
                                            {preferenciasInsignias.length === 0 ? (
                                                <p className="empty-list-text">No ha seleccionado ninguna insignia.</p>
                                            ) : (
                                                <ul className="preference-list">
                                                    {preferenciasInsignias.map((puesto, index) => (
                                                        <li key={puesto.id} className="preference-item">
                                                            <div className="pref-order">
                                                                <span className="order-badge">{index + 1}º</span>
                                                            </div>
                                                            <div className="pref-info">
                                                                <strong>{puesto.nombre}</strong>
                                                                <span>{puesto.tipo_puesto.nombre_tipo || puesto.tipo_puesto}</span>
                                                            </div>
                                                            <div className="pref-actions">
                                                                <button 
                                                                    type="button" 
                                                                    className="btn-icon-small"
                                                                    onClick={() => moveInsignia(index, -1)}
                                                                    disabled={index === 0 || submitting}
                                                                >
                                                                    <ArrowUp size={16} />
                                                                </button>
                                                                <button 
                                                                    type="button" 
                                                                    className="btn-icon-small"
                                                                    onClick={() => moveInsignia(index, 1)}
                                                                    disabled={index === preferenciasInsignias.length - 1 || submitting}
                                                                >
                                                                    <ArrowDown size={16} />
                                                                </button>
                                                                <button 
                                                                    type="button" 
                                                                    className="btn-icon-small delete"
                                                                    onClick={() => handleRemoveInsignia(index)}
                                                                    disabled={submitting}
                                                                >
                                                                    <Trash2 size={16} />
                                                                </button>
                                                            </div>
                                                        </li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                    </>
                                )}

                                <div className="form-actions-acto">
                                    <button type="button" className="btn-cancel-acto" onClick={() => navigate("/home")}>Cancelar</button>
                                    <button 
                                        type="submit" 
                                        className="btn-save-acto" 
                                        disabled={submitting || (preferenciasInsignias.length === 0 && !selectedPuestoGeneralId)}
                                    >
                                        <span className="icon-save-acto">📩</span> 
                                        {submitting ? "Enviando..." : "Registrar Solicitud"}
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

export default HermanoCrearSolicitudUnificada;