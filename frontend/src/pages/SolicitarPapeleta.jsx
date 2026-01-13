import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api"; 
import "../styles/CrearActo.css"; 
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, PlusCircle, Trash2 } from "lucide-react";

function SolicitarPapeleta() {
    // --- ESTADOS DE UI Y USUARIO ---
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // --- ESTADOS DE DATOS ---
    const [actosDisponibles, setActosDisponibles] = useState([]);
    const [puestosDelActo, setPuestosDelActo] = useState([]);
    
    // --- ESTADOS DEL FORMULARIO ---
    const [selectedActoId, setSelectedActoId] = useState("");
    const [preferencias, setPreferencias] = useState([]); 
    
    // --- ESTADOS DE RESPUESTA ---
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [successCode, setSuccessCode] = useState("");

    const navigate = useNavigate();

    useEffect(() => {
        // 1. Cargar Usuario y Actos Disponibles al inicio
        const fetchData = async () => {
            try {
                const [resUser, resActos] = await Promise.all([
                    api.get("api/me/"),
                    // CAMBIO: Llamamos al endpoint que ya filtra por fecha y tipo en el servidor
                    api.get("api/actos/vigentes/") 
                ]);

                setUser(resUser.data);

                // CAMBIO: Ya no filtramos en el cliente. Usamos los datos directos del backend.
                // La comprobación siguiente maneja si Django usa paginación (devuelve .results) o no (devuelve array).
                const listaActos = Array.isArray(resActos.data) ? resActos.data : resActos.data.results;
                
                setActosDisponibles(listaActos || []);

            } catch (err) {
                console.error("Error cargando datos iniciales:", err);
                if (err.response && err.response.status === 401) {
                    navigate("/login");
                } else {
                    setError("Error cargando la información. Inténtelo más tarde.");
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
        setPreferencias([]); // Resetear preferencias al cambiar de acto
        setPuestosDelActo([]);
        setError("");

        if (!actoId) return;

        try {
            // Cargar los puestos disponibles para este acto específico
            const res = await api.get(`api/actos/${actoId}/`);
            // Filtramos solo los disponibles
            const puestos = res.data.puestos_disponibles.filter(p => p.disponible);
            setPuestosDelActo(puestos);
        } catch (err) {
            console.error("Error cargando puestos:", err);
            setError("No se pudieron cargar los puestos para este acto.");
        }
    };

    const handleAddPreferencia = () => {
        setPreferencias([...preferencias, { puesto_id: "" }]);
    };

    const handleRemovePreferencia = (index) => {
        const nuevasPreferencias = preferencias.filter((_, i) => i !== index);
        setPreferencias(nuevasPreferencias);
    };

    const handleChangePuesto = (index, nuevoPuestoId) => {
        const nuevasPreferencias = [...preferencias];
        nuevasPreferencias[index].puesto_id = nuevoPuestoId;
        setPreferencias(nuevasPreferencias);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError("");
        setSuccess(false);

        // 1. Validaciones Frontend básicas
        if (!selectedActoId) {
            setError("Debe seleccionar un acto.");
            setSubmitting(false);
            return;
        }
        if (preferencias.length === 0) {
            setError("Debe añadir al menos una preferencia de sitio.");
            setSubmitting(false);
            return;
        }
        if (preferencias.some(p => !p.puesto_id)) {
            setError("Por favor, seleccione un puesto en todas las filas de preferencia.");
            setSubmitting(false);
            return;
        }

        // 2. Construir Payload
        const payload = {
            acto_id: parseInt(selectedActoId),
            preferencias: preferencias.map((pref, index) => ({
                puesto_id: parseInt(pref.puesto_id),
                orden: index + 1
            }))
        };

        try {
            const res = await api.post("api/papeletas/solicitar/", payload);
            setSuccess(true);
            setSuccessCode(res.data.codigo_verificacion || "Registrado");
            setPreferencias([]);
            setSelectedActoId("");
        } catch (err) {
            console.error(err);
            if (err.response && err.response.data) {
                const data = err.response.data;

                if (data.non_field_errors) {
                    setError(Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors);
                }
                else if (data.preferencias) {
                    setError(Array.isArray(data.preferencias) ? data.preferencias[0] : data.preferencias);
                }
                else if (data.detail) {
                    setError(data.detail);
                }
                else {
                    const firstKey = Object.keys(data)[0];
                    const msg = data[firstKey];
                    setError(`${firstKey}: ${Array.isArray(msg) ? msg[0] : msg}`);
                }
            } else {
                setError("Error de conexión con el servidor.");
            }
        } finally {
            setSubmitting(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/"; 
    };

    // --- RENDER ---
    if (loading) return <div className="site-wrapper">Cargando sistema de papeletas...</div>;
    if (!user) return <div className="site-wrapper">Redirigiendo...</div>;

    return (
        <div className="site-wrapper">
             {/* --- NAVBAR --- */}
            <nav className="navbar">
                <div className="logo-container">
                    <img src={logoEscudo} alt="Escudo San Gonzalo" className="nav-logo" />
                    <div className="logo-text">
                        <h4>Hermandad de San Gonzalo</h4>
                        <span>SEVILLA</span>
                    </div>
                </div>
                <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
                <div className="nav-buttons-desktop">
                    <button className="btn-outline">Hermano: {user.dni}</button>
                    <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                </div>
            </nav>

            <main className="main-container-area">
                <div className="card-container-area" style={{maxWidth: '800px'}}>
                    
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Solicitud Papeleta de Sitio</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Seleccione el acto y sus preferencias de puesto por orden de prioridad.
                        </p>
                    </header>

                    {/* MENSAJES DE ESTADO */}
                    {error && (
                        <div style={{padding: '15px', backgroundColor: '#fee2e2', color: '#991b1b', marginBottom: '1rem', borderRadius: '6px', border: '1px solid #fca5a5'}}>
                            <strong>Error:</strong> {error}
                        </div>
                    )}
                    
                    {success && (
                        <div style={{padding: '20px', backgroundColor: '#dcfce7', color: '#166534', marginBottom: '1rem', borderRadius: '6px', border: '1px solid #86efac', textAlign: 'center'}}>
                            <h3>¡Solicitud realizada con éxito!</h3>
                            <p>Su código de verificación es: <strong>{successCode}</strong></p>
                            <button className="btn-purple" onClick={() => navigate("/mis-papeletas")} style={{marginTop: '10px'}}>
                                Ver mis papeletas
                            </button>
                        </div>
                    )}

                    {!success && (
                    <section className="form-card-acto">
                        <form className="event-form-acto" onSubmit={handleSubmit}>
                            
                            {/* 1. SELECCIÓN DE ACTO */}
                            <div className="form-group-acto full-width">
                                <label htmlFor="acto_select">SELECCIONE EL ACTO</label>
                                <div className="input-with-icon-acto">
                                    <span className="icon-acto">📜</span>
                                    <select 
                                        id="acto_select"
                                        value={selectedActoId}
                                        onChange={handleActoChange}
                                        required
                                        className="select-acto"
                                    >
                                        <option value="">-- Seleccione un acto disponible --</option>
                                        {actosDisponibles.length === 0 ? (
                                            <option disabled>No hay actos con plazo abierto</option>
                                        ) : (
                                            actosDisponibles.map(acto => (
                                                <option key={acto.id} value={acto.id}>
                                                    {acto.nombre} (Cierra: {new Date(acto.fin_solicitud).toLocaleDateString()})
                                                </option>
                                            ))
                                        )}
                                    </select>
                                </div>
                            </div>

                            {/* 2. ÁREA DE PREFERENCIAS */}
                            {selectedActoId && (
                                <div style={{marginTop: '20px', borderTop: '1px solid #eee', paddingTop: '20px'}}>
                                    <label style={{display:'block', marginBottom:'10px', color:'#4b5563', fontWeight:'600'}}>
                                        PREFERENCIAS DE PUESTO (Ordenadas por prioridad)
                                    </label>

                                    {preferencias.length === 0 && (
                                        <p style={{fontStyle: 'italic', color: '#9ca3af', fontSize: '0.9rem'}}>
                                            No ha añadido ninguna preferencia. Pulse el botón "+" para comenzar.
                                        </p>
                                    )}

                                    <div className="preferencias-list" style={{display: 'flex', flexDirection: 'column', gap: '10px'}}>
                                        {preferencias.map((pref, index) => (
                                            <div key={index} style={{display: 'flex', gap: '10px', alignItems: 'center'}}>
                                                
                                                {/* Badge de Prioridad */}
                                                <div style={{
                                                    backgroundColor: '#4f46e5', color: 'white', 
                                                    width: '30px', height: '30px', borderRadius: '50%', 
                                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    fontWeight: 'bold', flexShrink: 0
                                                }}>
                                                    {index + 1}
                                                </div>

                                                {/* Select de Puesto */}
                                                <select 
                                                    className="input-with-icon-acto" 
                                                    style={{flexGrow: 1, padding: '10px', borderRadius: '6px', border: '1px solid #d1d5db'}}
                                                    value={pref.puesto_id}
                                                    onChange={(e) => handleChangePuesto(index, e.target.value)}
                                                    required
                                                >
                                                    <option value="">Seleccione Puesto...</option>
                                                    {puestosDelActo.map(puesto => {
                                                        const isSelectedElsewhere = preferencias.some((p, i) => i !== index && p.puesto_id == puesto.id);
                                                        return (
                                                            <option key={puesto.id} value={puesto.id} disabled={isSelectedElsewhere}>
                                                                {puesto.nombre} ({puesto.tipo_puesto}) 
                                                                {puesto.numero_maximo_asignaciones > 1 ? ` - Cupo: ${puesto.numero_maximo_asignaciones}` : ''}
                                                            </option>
                                                        );
                                                    })}
                                                </select>

                                                {/* Botón Eliminar Fila */}
                                                <button 
                                                    type="button" 
                                                    onClick={() => handleRemovePreferencia(index)}
                                                    style={{background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer'}}
                                                    title="Eliminar preferencia"
                                                >
                                                    <Trash2 size={20} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Botón Añadir */}
                                    <button 
                                        type="button" 
                                        onClick={handleAddPreferencia}
                                        style={{
                                            marginTop: '15px', display: 'flex', alignItems: 'center', gap: '5px',
                                            padding: '8px 12px', backgroundColor: '#f3f4f6', color: '#374151',
                                            border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontSize: '0.9rem'
                                        }}
                                    >
                                        <PlusCircle size={16} /> Añadir Preferencia
                                    </button>
                                </div>
                            )}

                            {/* BOTONES DE ACCIÓN */}
                            <div className="form-actions-acto" style={{marginTop: '30px'}}>
                                <button type="button" className="btn-cancel-acto" onClick={() => navigate("/home")}>
                                    Cancelar
                                </button>
                                <button 
                                    type="submit" 
                                    className="btn-save-acto" 
                                    disabled={submitting || !selectedActoId || preferencias.length === 0}
                                >
                                    <span className="icon-save-acto">📩</span> 
                                    {submitting ? "Enviando Solicitud..." : "Enviar Solicitud"}
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

export default SolicitarPapeleta;