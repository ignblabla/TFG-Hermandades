import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api"; // Asegúrate de que tu instancia de Axios esté aquí
import "../styles/CrearActo.css"; // Reutilizamos tus estilos
import logoEscudo from '../assets/escudo.png'; // Asegúrate de la ruta
import { ArrowLeft, Plus, Trash2, ArrowUp, ArrowDown } from "lucide-react";

function CrearSolicitudInsignia() {
    // --- ESTADOS ---
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [actosDisponibles, setActosDisponibles] = useState([]);
    const [insigniasDisponibles, setInsigniasDisponibles] = useState([]);
    
    // Selección del usuario
    const [selectedActoId, setSelectedActoId] = useState("");
    const [selectedInsigniaToAdd, setSelectedInsigniaToAdd] = useState("");
    const [preferencias, setPreferencias] = useState([]); // Array de objetos Puesto

    // Estados de formulario
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    const navigate = useNavigate();

    // --- CARGA INICIAL ---
    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Cargar Usuario
                const resUser = await api.get("api/me/");
                setUser(resUser.data);

                // 2. Cargar Actos
                // Filtramos en el frontend para mostrar solo los vigentes y que requieren papeleta
                const resActos = await api.get("api/actos/");
                const now = new Date();
                
                const actosValidos = resActos.data.filter(acto => {
                    if (!acto.requiere_papeleta) return false;
                    const inicio = new Date(acto.inicio_solicitud);
                    const fin = new Date(acto.fin_solicitud);
                    return now >= inicio && now <= fin;
                });

                setActosDisponibles(actosValidos);
            } catch (err) {
                console.error(err);
                if (err.response && err.response.status === 401) navigate("/login");
                else setError("Error cargando datos iniciales.");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [navigate]);

    // --- MANEJADORES ---

    // 1. Al cambiar de acto, cargamos sus puestos y filtramos insignias
    const handleActoChange = async (e) => {
        const actoId = e.target.value;
        setSelectedActoId(actoId);
        setPreferencias([]); // Resetear preferencias al cambiar acto
        setInsigniasDisponibles([]);
        setError("");

        if (!actoId) return;

        try {
            setLoading(true);
            const res = await api.get(`api/actos/${actoId}/`);
            // Filtramos: Solo disponibles Y que sean insignias (según backend)
            const soloInsignias = res.data.puestos_disponibles.filter(
                p => p.es_insignia === true && p.disponible === true
            );
            setInsigniasDisponibles(soloInsignias);
        } catch (err) {
            setError("Error cargando las insignias del acto.");
        } finally {
            setLoading(false);
        }
    };

    // 2. Añadir una insignia a la lista de preferencias
    const handleAddInsignia = () => {
        if (!selectedInsigniaToAdd) return;

        const insignia = insigniasDisponibles.find(i => i.id === parseInt(selectedInsigniaToAdd));
        
        // Validación: No duplicados
        if (preferencias.some(p => p.id === insignia.id)) {
            setError("Esa insignia ya está en tu lista de preferencias.");
            return;
        }

        setPreferencias([...preferencias, insignia]);
        setSelectedInsigniaToAdd(""); // Reset select
        setError("");
    };

    // 3. Quitar insignia de la lista
    const handleRemoveInsignia = (index) => {
        const nuevasPrefs = [...preferencias];
        nuevasPrefs.splice(index, 1);
        setPreferencias(nuevasPrefs);
    };

    // 4. Mover prioridad (Subir/Bajar)
    const moveInsignia = (index, direction) => {
        const nuevasPrefs = [...preferencias];
        const item = nuevasPrefs[index];
        nuevasPrefs.splice(index, 1);
        nuevasPrefs.splice(index + direction, 0, item);
        setPreferencias(nuevasPrefs);
    };

    // 5. Enviar Solicitud (Submit Transaccional)
    const handleSubmit = async (e) => {
        e.preventDefault();
        if (preferencias.length === 0) {
            setError("Debe seleccionar al menos una insignia.");
            return;
        }

        setSubmitting(true);
        setError("");
        setSuccess(false);

        // Construir Payload según espera el Serializer
        const payload = {
            acto_id: selectedActoId,
            preferencias: preferencias.map((p, index) => ({
                puesto_id: p.id,
                orden_prioridad: index + 1 // El orden es su posición en el array + 1
            }))
        };

        try {
            await api.post("api/papeletas/solicitar-insignia/", payload);
            setSuccess(true);
            setPreferencias([]);
            setSelectedActoId("");
            setTimeout(() => navigate("/home"), 3000); // Redirigir al perfil/home
        } catch (err) {
            if (err.response && err.response.data) {
                // Manejo de errores anidados del serializer
                const data = err.response.data;
                if (data.detail) setError(data.detail);
                else if (data.preferencias) setError(JSON.stringify(data.preferencias));
                else if (data.non_field_errors) setError(data.non_field_errors[0]);
                else setError("Error al procesar la solicitud. Revise los requisitos.");
            } else {
                setError("Error de conexión.");
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
            {/* --- NAVBAR (Reutilizada de tu ejemplo) --- */}
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
                     {/* ... tus links ... */}
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
                            <h1>Solicitud de Insignias</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Seleccione el acto y elabore su lista de preferencias de insignias por orden de prioridad.
                        </p>
                    </header>

                    {error && <div className="alert-box error">{error}</div>}
                    {success && <div className="alert-box success">¡Solicitud registrada correctamente! Recibirá su comprobante en breve.</div>}

                    {actosDisponibles.length === 0 ? (
                        <div className="info-box">
                            No hay actos disponibles para solicitud de insignias en este momento.
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
                                            <option value="" disabled>-- Seleccione un acto vigente --</option>
                                            {actosDisponibles.map(acto => (
                                                <option key={acto.id} value={acto.id}>
                                                    {acto.nombre} (Cierre: {new Date(acto.fin_solicitud).toLocaleDateString()})
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                {/* 2. ZONA DE SELECCIÓN DE INSIGNIAS (Solo visible si hay acto) */}
                                {selectedActoId && (
                                    <>
                                        <div className="separator-line"></div>
                                        
                                        <div className="preference-selector-container">
                                            <label>AÑADIR INSIGNIA A LA LISTA</label>
                                            <div className="add-insignia-row">
                                                <div className="input-with-icon-acto flex-grow">
                                                    <span className="icon-acto">🕯️</span>
                                                    <select 
                                                        value={selectedInsigniaToAdd}
                                                        onChange={(e) => setSelectedInsigniaToAdd(e.target.value)}
                                                        disabled={submitting}
                                                    >
                                                        <option value="" disabled>Seleccione insignia...</option>
                                                        {insigniasDisponibles.map(p => (
                                                            <option 
                                                                key={p.id} 
                                                                value={p.id}
                                                                // Deshabilitar si ya está en la lista de preferencias
                                                                disabled={preferencias.some(pref => pref.id === p.id)}
                                                            >
                                                                {p.nombre} ({p.tipo_puesto}) {preferencias.some(pref => pref.id === p.id) ? '- Añadido' : ''}
                                                            </option>
                                                        ))}
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

                                        {/* 3. LISTA DE PREFERENCIAS */}
                                        <div className="preferences-list-container">
                                            <label>MIS PREFERENCIAS (Orden de prioridad)</label>
                                            {preferencias.length === 0 ? (
                                                <p className="empty-list-text">No ha seleccionado ninguna insignia aún.</p>
                                            ) : (
                                                <ul className="preference-list">
                                                    {preferencias.map((puesto, index) => (
                                                        <li key={puesto.id} className="preference-item">
                                                            <div className="pref-order">
                                                                <span className="order-badge">{index + 1}º</span>
                                                            </div>
                                                            <div className="pref-info">
                                                                <strong>{puesto.nombre}</strong>
                                                                <span>{puesto.tipo_puesto}</span>
                                                            </div>
                                                            <div className="pref-actions">
                                                                <button 
                                                                    type="button" 
                                                                    className="btn-icon-small"
                                                                    onClick={() => moveInsignia(index, -1)}
                                                                    disabled={index === 0 || submitting}
                                                                    title="Subir prioridad"
                                                                >
                                                                    <ArrowUp size={16} />
                                                                </button>
                                                                <button 
                                                                    type="button" 
                                                                    className="btn-icon-small"
                                                                    onClick={() => moveInsignia(index, 1)}
                                                                    disabled={index === preferencias.length - 1 || submitting}
                                                                    title="Bajar prioridad"
                                                                >
                                                                    <ArrowDown size={16} />
                                                                </button>
                                                                <button 
                                                                    type="button" 
                                                                    className="btn-icon-small delete"
                                                                    onClick={() => handleRemoveInsignia(index)}
                                                                    disabled={submitting}
                                                                    title="Eliminar"
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
                                        disabled={submitting || preferencias.length === 0}
                                    >
                                        <span className="icon-save-acto">📩</span> 
                                        {submitting ? "Enviando..." : "Solicitar Insignias"}
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

export default CrearSolicitudInsignia;