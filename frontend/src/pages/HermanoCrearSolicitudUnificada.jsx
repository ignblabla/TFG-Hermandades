import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import "../styles/CrearActo.css";
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, Plus, Trash2, ArrowUp, ArrowDown, Info } from "lucide-react";

function HermanoCrearSolicitudUnificada() {
    // --- ESTADOS ---
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [actosDisponibles, setActosDisponibles] = useState([]);
    const [puestosDisponibles, setPuestosDisponibles] = useState([]);
    
    // Selección del usuario
    const [selectedActoId, setSelectedActoId] = useState("");
    const [selectedPuestoToAdd, setSelectedPuestoToAdd] = useState("");
    const [preferencias, setPreferencias] = useState([]); 

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

                // 2. Cargar Actos (DEFINIR LA VARIABLE AQUÍ PRIMERO)
                const resActos = await api.get("api/actos/");

                // 3. Ahora que ya existe 'resActos', podemos usarla
                console.log("--- DEBUG START ---");
                console.log("API Respuesta completa:", resActos);
                
                // Detectar si Django devuelve un array directo o un objeto con paginación
                let listaActos = [];
                if (Array.isArray(resActos.data)) {
                    listaActos = resActos.data;
                } else if (resActos.data && resActos.data.results) {
                    listaActos = resActos.data.results;
                } else {
                    console.error("Formato de respuesta inesperado:", resActos.data);
                }

                console.log("Lista de actos extraída:", listaActos);

                const now = new Date();
                
                // 4. Filtrar
                const actosValidos = listaActos.filter(acto => {
                    console.log(`Analizando acto ID ${acto.id}: ${acto.nombre} | Modalidad: ${acto.modalidad}`);

                    // A. Requiere papeleta
                    if (!acto.requiere_papeleta) return false;
                    
                    // B. Modalidad UNIFICADA (Flexible con mayúsculas/minúsculas)
                    // Asegúrate de que tu modelo devuelve 'UNIFICADO' o 'Unificado'
                    if (String(acto.modalidad).toUpperCase() !== 'UNIFICADO') {
                        console.log(`   -> Rechazado: Modalidad no es UNIFICADO (es ${acto.modalidad})`);
                        return false;
                    }

                    // C. Fechas nulas
                    if (!acto.inicio_solicitud || !acto.fin_solicitud) {
                        console.log("   -> Rechazado: Fechas de solicitud no configuradas (son null).");
                        return false;
                    }

                    // D. Rango de fechas
                    const inicio = new Date(acto.inicio_solicitud);
                    const fin = new Date(acto.fin_solicitud);
                    
                    const estaEnFecha = now >= inicio && now <= fin;

                    if (!estaEnFecha) {
                        console.log(`   -> Rechazado: Fuera de fecha. (Ahora: ${now.toLocaleString()} | Inicio: ${inicio.toLocaleString()} | Fin: ${fin.toLocaleString()})`);
                    } else {
                        console.log("   -> ¡ACEPTADO!");
                    }

                    return estaEnFecha;
                });

                setActosDisponibles(actosValidos);
            } catch (err) {
                console.error("Error en fetchData:", err);
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
        setPreferencias([]); 
        setPuestosDisponibles([]);
        setError("");

        if (!actoId) return;

        try {
            setLoading(true);
            const res = await api.get(`api/actos/${actoId}/`);
            
            // En modalidad UNIFICADA mostramos TODO lo que esté disponible
            // (Tanto insignias como cirios/varas)
            const disponibles = res.data.puestos_disponibles.filter(
                p => p.disponible === true
            );
            setPuestosDisponibles(disponibles);
        } catch (err) {
            setError("Error cargando los puestos del acto.");
        } finally {
            setLoading(false);
        }
    };

    const handleAddPuesto = () => {
        if (!selectedPuestoToAdd) return;

        // Buscamos el objeto completo del puesto seleccionado
        const puesto = puestosDisponibles.find(p => p.id === parseInt(selectedPuestoToAdd));
        if (!puesto) return;

        // 1. Validación: No duplicados exactos (mismo ID)
        if (preferencias.some(p => p.id === puesto.id)) {
            setError("Ese puesto ya está en tu lista de preferencias.");
            return;
        }

        // 2. Validación de Negocio (REGLA UNIFICADA):
        // "Si NO es insignia, no se puede repetir el TIPO de puesto"
        // (Ej: No puedes pedir dos tipos de Cirio distintos, pero sí varias Insignias distintas)
        
        // OJO: Asumo que tu backend devuelve 'es_insignia' y 'tipo_puesto' (nombre del tipo) en el serializer de Puesto
        // Si tu serializer de puestos_disponibles no devuelve 'es_insignia', habría que ajustarlo en el backend.
        
        // Vamos a asumir que 'puesto.tipo_puesto' es el string (Nombre) y necesitamos saber si es insignia.
        // Si tu objeto puesto no tiene 'es_insignia', la lógica visual dependerá de ello. 
        // Suponiendo que viene del serializer:
        
        if (puesto.es_insignia === false) {
             // Buscamos si ya hay un puesto en preferencias con el mismo nombre de tipo y que no sea insignia
            const yaExisteTipo = preferencias.find(p => 
                p.es_insignia === false && p.tipo_puesto === puesto.tipo_puesto
            );

            if (yaExisteTipo) {
                setError(`En la solicitud unificada solo puedes elegir una opción para el tipo '${puesto.tipo_puesto}'. Ya has seleccionado uno.`);
                return;
            }
        }

        setPreferencias([...preferencias, puesto]);
        setSelectedPuestoToAdd(""); 
        setError("");
    };

    const handleRemovePuesto = (index) => {
        const nuevasPrefs = [...preferencias];
        nuevasPrefs.splice(index, 1);
        setPreferencias(nuevasPrefs);
        setError("");
    };

    const movePuesto = (index, direction) => {
        const nuevasPrefs = [...preferencias];
        const item = nuevasPrefs[index];
        nuevasPrefs.splice(index, 1);
        nuevasPrefs.splice(index + direction, 0, item);
        setPreferencias(nuevasPrefs);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (preferencias.length === 0) {
            setError("Debe seleccionar al menos un puesto.");
            return;
        }

        setSubmitting(true);
        setError("");
        setSuccess(false);

        const payload = {
            acto_id: selectedActoId,
            preferencias_solicitadas: preferencias.map((p, index) => ({
                puesto_id: p.id,
                orden: index + 1
            }))
        };

        try {
            await api.post("api/papeletas/solicitar-unificada/", payload);
            setSuccess(true);
            setPreferencias([]);
            setSelectedActoId("");
            setTimeout(() => navigate("/mis-papeletas"), 3000); 
        } catch (err) {
            if (err.response && err.response.data) {
                const data = err.response.data;
                if (data.detail) setError(data.detail);
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
                            <h1>Solicitud Unificada</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Para actos con modalidad unificada. Seleccione puestos (Insignias o Cirios) y ordénelos por prioridad.
                            <br/>
                            <small className="text-muted"><Info size={14} style={{verticalAlign: 'middle'}}/> Solo puede elegir una opción de cada tipo de puesto general (ej: un solo tramo de cirio).</small>
                        </p>
                    </header>

                    {error && <div className="alert-box error">{error}</div>}
                    {success && <div className="alert-box success">¡Solicitud unificada registrada correctamente!</div>}

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
                                                    {acto.nombre} (Cierre: {new Date(acto.fin_solicitud).toLocaleDateString()})
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                {/* 2. ZONA DE SELECCIÓN DE PUESTOS */}
                                {selectedActoId && (
                                    <>
                                        <div className="separator-line"></div>
                                        
                                        <div className="preference-selector-container">
                                            <label>AÑADIR PUESTO (Insignia o Sitio)</label>
                                            <div className="add-insignia-row">
                                                <div className="input-with-icon-acto flex-grow">
                                                    <span className="icon-acto">➕</span>
                                                    <select 
                                                        value={selectedPuestoToAdd}
                                                        onChange={(e) => setSelectedPuestoToAdd(e.target.value)}
                                                        disabled={submitting}
                                                    >
                                                        <option value="" disabled>Seleccione puesto...</option>
                                                        {puestosDisponibles.map(p => {
                                                            // Lógica visual: deshabilitar si ya está seleccionado
                                                            // O si es del mismo tipo (si no es insignia) -> Esto lo validamos al clicar añadir, 
                                                            // pero visualmente podríamos grisearlo aquí si quisieras complicar el render.
                                                            const isSelected = preferencias.some(pref => pref.id === p.id);
                                                            const icon = p.es_insignia ? '🏅' : '🕯️';
                                                            
                                                            return (
                                                                <option 
                                                                    key={p.id} 
                                                                    value={p.id}
                                                                    disabled={isSelected}
                                                                >
                                                                    {icon} {p.nombre} ({p.tipo_puesto}) {isSelected ? '- Añadido' : ''}
                                                                </option>
                                                            );
                                                        })}
                                                    </select>
                                                </div>
                                                <button 
                                                    type="button" 
                                                    className="btn-add-pref" 
                                                    onClick={handleAddPuesto}
                                                    disabled={!selectedPuestoToAdd || submitting}
                                                >
                                                    <Plus size={18} /> Añadir
                                                </button>
                                            </div>
                                        </div>

                                        {/* 3. LISTA DE PREFERENCIAS */}
                                        <div className="preferences-list-container">
                                            <label>MIS PREFERENCIAS (Prioridad: 1º es la más deseada)</label>
                                            {preferencias.length === 0 ? (
                                                <p className="empty-list-text">No ha seleccionado ningún puesto aún.</p>
                                            ) : (
                                                <ul className="preference-list">
                                                    {preferencias.map((puesto, index) => (
                                                        <li key={puesto.id} className="preference-item">
                                                            <div className="pref-order">
                                                                <span className="order-badge">{index + 1}º</span>
                                                            </div>
                                                            <div className="pref-info">
                                                                <strong>
                                                                    {puesto.es_insignia ? '🏅 ' : '🕯️ '}
                                                                    {puesto.nombre}
                                                                </strong>
                                                                <span>{puesto.tipo_puesto}</span>
                                                            </div>
                                                            <div className="pref-actions">
                                                                <button 
                                                                    type="button" 
                                                                    className="btn-icon-small"
                                                                    onClick={() => movePuesto(index, -1)}
                                                                    disabled={index === 0 || submitting}
                                                                    title="Subir prioridad"
                                                                >
                                                                    <ArrowUp size={16} />
                                                                </button>
                                                                <button 
                                                                    type="button" 
                                                                    className="btn-icon-small"
                                                                    onClick={() => movePuesto(index, 1)}
                                                                    disabled={index === preferencias.length - 1 || submitting}
                                                                    title="Bajar prioridad"
                                                                >
                                                                    <ArrowDown size={16} />
                                                                </button>
                                                                <button 
                                                                    type="button" 
                                                                    className="btn-icon-small delete"
                                                                    onClick={() => handleRemovePuesto(index)}
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
                                        {submitting ? "Procesando..." : "Enviar Solicitud Unificada"}
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