import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/CrearActo.css"; // Reutilizamos tus estilos existentes
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft, Trash2, PlusCircle, AlertCircle, CheckCircle } from "lucide-react";

function SolicitarPapeleta() {
    // --- ESTADOS ---
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Datos maestros
    const [listaActos, setListaActos] = useState([]);
    const [puestosDisponibles, setPuestosDisponibles] = useState([]); // Puestos del acto seleccionado

    // Estado del formulario
    const [selectedActoId, setSelectedActoId] = useState("");
    const [selectedPuestoId, setSelectedPuestoId] = useState(""); // El puesto que se está eligiendo en el select
    
    // Aquí guardamos la lista ordenada de deseos: [{puesto_id, nombre_puesto, ...}]
    const [preferencias, setPreferencias] = useState([]); 

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    // NUEVO ESTADO: Para guardar el número devuelto por el backend
    const [numeroAsignado, setNumeroAsignado] = useState(null); 

    const navigate = useNavigate();

    // --- EFECTOS ---

    // 1. Carga inicial de Usuario y Actos
    useEffect(() => {
        const token = localStorage.getItem("access");
        if (!token) {
            navigate("/login");
            return;
        }

        const fetchInicial = async () => {
            try {
                // A. Obtener Usuario
                const userRes = await fetch("http://127.0.0.1:8000/api/me/", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (!userRes.ok) throw new Error("Error de autenticación");
                const userData = await userRes.json();
                setUser(userData);

                // B. Obtener Actos (Solo futuros y que requieran papeleta)
                const actosRes = await fetch("http://127.0.0.1:8000/api/actos/", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (actosRes.ok) {
                    const actosData = await actosRes.json();
                    const now = new Date();
                    const actosFiltrados = actosData.filter(acto => 
                        acto.requiere_papeleta === true && new Date(acto.fecha) > now
                    );
                    setListaActos(actosFiltrados);
                }

            } catch (err) {
                console.error(err);
                navigate("/login");
            } finally {
                setLoading(false);
            }
        };

        fetchInicial();
    }, [navigate]);

    // 2. Cargar puestos cuando cambia el Acto seleccionado
    useEffect(() => {
        if (!selectedActoId) {
            setPuestosDisponibles([]);
            setPreferencias([]); // Limpiar preferencias si cambia el acto
            return;
        }

        const fetchPuestos = async () => {
            const token = localStorage.getItem("access");
            try {
                const res = await fetch(`http://127.0.0.1:8000/api/actos/${selectedActoId}/`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                
                if (res.ok) {
                    const actoData = await res.json();
                    
                    if (actoData.puestos_disponibles) {
                        setPuestosDisponibles(actoData.puestos_disponibles.filter(p => p.disponible));
                    } else {
                        console.warn("Asegúrate de que ActoSerializer devuelva 'puestos_disponibles'");
                    }
                }
            } catch (err) {
                console.error("Error cargando puestos", err);
            }
        };

        fetchPuestos();
    }, [selectedActoId]);


    // --- MANEJADORES ---

    const handleActoChange = (e) => {
        setSelectedActoId(e.target.value);
        setPreferencias([]); // Reiniciar preferencias al cambiar de acto
        setSelectedPuestoId("");
        setError("");
    };

    const handleAddPreferencia = () => {
        if (!selectedPuestoId) return;

        // Verificar duplicados
        if (preferencias.some(p => p.id === parseInt(selectedPuestoId))) {
            setError("Ya has añadido este puesto a tu lista de preferencias.");
            return;
        }
        
        // Encontrar el objeto puesto completo para mostrar el nombre
        const puestoObj = puestosDisponibles.find(p => p.id === parseInt(selectedPuestoId));
        
        if (puestoObj) {
            setPreferencias([...preferencias, puestoObj]);
            setSelectedPuestoId(""); // Reset selector
            setError("");
        }
    };

    const handleRemovePreferencia = (indexToRemove) => {
        setPreferencias(preferencias.filter((_, index) => index !== indexToRemove));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (preferencias.length === 0) {
            setError("Debes seleccionar al menos una preferencia de puesto.");
            return;
        }

        setSubmitting(true);
        setError("");
        setSuccess(false);
        setNumeroAsignado(null);

        const token = localStorage.getItem("access");

        // Construir el Payload para el Backend
        const payload = {
            acto_id: selectedActoId,
            preferencias: preferencias.map((puesto, index) => ({
                puesto_id: puesto.id,
                orden: index + 1 // Prioridad basada en el orden del array
            }))
        };

        try {
            const response = await fetch("http://127.0.0.1:8000/api/papeletas/solicitar/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                // ACTUALIZACIÓN: Capturamos el número devuelto por el Backend
                setNumeroAsignado(data.numero_papeleta);
                setSuccess(true);
                
                // Resetear form visualmente
                setPreferencias([]);
                setSelectedActoId("");
                
                // Redirigir a Home con un poco más de retraso para que lean el número
                setTimeout(() => navigate("/home"), 4000); 
            } else {
                if (data.error) {
                    setError(data.error); 
                } else if (data.detail) {
                    setError(data.detail);
                } else {
                    setError("Error al procesar la solicitud. Revise los datos.");
                }
            }
        } catch (err) {
            setError("Error de conexión con el servidor.");
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

    if (loading) return <div className="site-wrapper">Cargando...</div>;
    if (!user) return null;

    return (
        <div className="site-wrapper">
            <nav className="navbar">
                <div className="logo-container">
                    <img src={logoEscudo} alt="Escudo San Gonzalo" className="nav-logo" />
                    <div className="logo-text">
                        <h4>Hermandad de San Gonzalo</h4>
                        <span>SEVILLA</span>
                    </div>
                </div>

                <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>
                    ☰
                </button>

                <ul className={`nav-links ${menuOpen ? "active" : ""}`}>
                    <li><a href="#hermandad">Hermandad</a></li>
                    
                    <div className="nav-buttons-mobile">
                        <button className="btn-outline">Hermano: {user.dni}</button>
                        <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                    </div>
                </ul>

                <div className="nav-buttons-desktop">
                    <button className="btn-outline" onClick={() => navigate("/editar-perfil")} style={{cursor: 'pointer'}}>
                        Hermano: {user.dni}
                    </button>
                    <button className="btn-purple" onClick={handleLogout}>
                        Cerrar Sesión
                    </button>
                </div>
            </nav>

            {/* --- MAIN CONTENT --- */}
            <main className="main-container-area">
                <div className="card-container-area">
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Solicitud de Sitio</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Seleccione el acto y elija sus preferencias de puesto por orden de prioridad.
                        </p>
                    </header>

                    {/* Feedback Messages */}
                    {error && <div style={{padding: '15px', backgroundColor: '#fee2e2', color: '#b91c1c', marginBottom: '1rem', borderRadius: '6px', border: '1px solid #fca5a5', display: 'flex', alignItems: 'center', gap: '10px'}}>
                        <AlertCircle size={20}/> {error}
                    </div>}
                    
                    {/* MENSAJE DE ÉXITO MEJORADO */}
                    {success && <div style={{
                        padding: '20px', 
                        backgroundColor: '#dcfce7', 
                        color: '#15803d', 
                        marginBottom: '1.5rem', 
                        borderRadius: '8px', 
                        border: '1px solid #86efac',
                        textAlign: 'center'
                    }}>
                        <div style={{display: 'flex', justifyContent: 'center', marginBottom: '10px'}}>
                            <CheckCircle size={48} color="#16a34a" />
                        </div>
                        <h3 style={{fontSize: '1.2rem', marginBottom: '5px', color:'#166534'}}>¡Solicitud realizada con éxito!</h3>
                        
                        {numeroAsignado && (
                            <div style={{margin: '15px 0', fontSize: '1.1rem'}}>
                                Se le ha asignado el número de papeleta: <br/>
                                <span style={{fontSize: '2rem', fontWeight: 'bold', color: '#15803d'}}>#{numeroAsignado}</span>
                            </div>
                        )}
                        
                        <p style={{fontSize: '0.9rem', opacity: 0.9}}>Redirigiendo al inicio...</p>
                    </div>}

                    {/* Ocultamos el formulario si hay éxito para limpiar la vista */}
                    {!success && (
                        <section className="form-card-acto">
                            <form className="event-form-acto" onSubmit={handleSubmit}>
                                
                                {/* PASO 1: SELECCIONAR ACTO */}
                                <div className="form-row-acto">
                                    <div className="form-group-acto full-width">
                                        <label htmlFor="acto">1. SELECCIONA EL ACTO</label>
                                        <div className="input-with-icon-acto">
                                            <span className="icon-acto">📅</span>
                                            <select 
                                                id="acto" 
                                                value={selectedActoId} 
                                                onChange={handleActoChange}
                                                required
                                            >
                                                <option value="" disabled>-- Elige un Acto disponible --</option>
                                                {listaActos.map(acto => (
                                                    <option key={acto.id} value={acto.id}>
                                                        {acto.nombre} ({new Date(acto.fecha).getFullYear()})
                                                    </option>
                                                ))}
                                                {listaActos.length === 0 && <option disabled>No hay actos disponibles</option>}
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                {/* PASO 2: AÑADIR PREFERENCIAS (Solo si hay acto seleccionado) */}
                                {selectedActoId && (
                                    <div style={{marginTop: '20px', padding: '20px', backgroundColor: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0'}}>
                                        <label style={{display:'block', marginBottom:'10px', fontWeight:'600', color:'#334155'}}>
                                            2. AÑADIR PREFERENCIAS DE PUESTO
                                        </label>
                                        
                                        <div style={{display: 'flex', gap: '10px', alignItems: 'flex-end'}}>
                                            <div className="form-group-acto" style={{flex: 1, marginBottom: 0}}>
                                                <div className="input-with-icon-acto">
                                                    <span className="icon-acto">🕯️</span>
                                                    <select 
                                                        value={selectedPuestoId}
                                                        onChange={(e) => setSelectedPuestoId(e.target.value)}
                                                    >
                                                        <option value="" disabled>Seleccionar puesto...</option>
                                                        {puestosDisponibles.map(puesto => (
                                                            <option 
                                                                key={puesto.id} 
                                                                value={puesto.id}
                                                                disabled={preferencias.some(p => p.id === puesto.id)}
                                                            >
                                                                {puesto.nombre} (Libres: {puesto.numero_maximo_asignaciones})
                                                            </option>
                                                        ))}
                                                        {puestosDisponibles.length === 0 && <option disabled>Cargando puestos...</option>}
                                                    </select>
                                                </div>
                                            </div>
                                            <button 
                                                type="button" 
                                                className="btn-purple" 
                                                onClick={handleAddPreferencia}
                                                disabled={!selectedPuestoId}
                                                style={{height: '42px', display: 'flex', alignItems: 'center', gap: '5px'}}
                                            >
                                                <PlusCircle size={18}/> Añadir
                                            </button>
                                        </div>
                                        <small style={{color: '#64748b', marginTop: '5px', display: 'block'}}>
                                            Añada los puestos en orden de preferencia. El primero será su prioridad 1.
                                        </small>
                                    </div>
                                )}

                                {/* PASO 3: LISTA DE PREFERENCIAS */}
                                {preferencias.length > 0 && (
                                    <div style={{marginTop: '20px'}}>
                                        <h3 style={{fontSize: '1rem', color: '#475569', marginBottom: '10px'}}>Tus Preferencias:</h3>
                                        <div style={{display: 'flex', flexDirection: 'column', gap: '8px'}}>
                                            {preferencias.map((puesto, index) => (
                                                <div key={puesto.id} style={{
                                                    display: 'flex', 
                                                    justifyContent: 'space-between', 
                                                    alignItems: 'center',
                                                    padding: '12px 15px',
                                                    backgroundColor: 'white',
                                                    border: '1px solid #cbd5e1',
                                                    borderRadius: '6px',
                                                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
                                                }}>
                                                    <div style={{display: 'flex', alignItems: 'center', gap: '15px'}}>
                                                        <span style={{
                                                            backgroundColor: '#7c3aed', 
                                                            color: 'white', 
                                                            width: '28px', 
                                                            height: '28px', 
                                                            borderRadius: '50%', 
                                                            display: 'flex', 
                                                            justifyContent: 'center', 
                                                            alignItems: 'center',
                                                            fontWeight: 'bold',
                                                            fontSize: '0.9rem'
                                                        }}>
                                                            {index + 1}
                                                        </span>
                                                        <span style={{fontWeight: '500', color: '#1e293b'}}>
                                                            {puesto.nombre}
                                                        </span>
                                                    </div>
                                                    
                                                    <button 
                                                        type="button" 
                                                        onClick={() => handleRemovePreferencia(index)}
                                                        style={{background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444'}}
                                                        title="Eliminar preferencia"
                                                    >
                                                        <Trash2 size={18} />
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <div className="form-actions-acto" style={{marginTop: '30px', borderTop: '1px solid #e2e8f0', paddingTop: '20px'}}>
                                    <button type="button" className="btn-cancel-acto" onClick={() => navigate("/home")}>Cancelar</button>
                                    <button 
                                        type="submit" 
                                        className="btn-save-acto" 
                                        disabled={submitting || preferencias.length === 0}
                                        style={{opacity: (submitting || preferencias.length === 0) ? 0.6 : 1}}
                                    >
                                        <span className="icon-save-acto">📩</span> {submitting ? "Enviando..." : "Solicitar Papeleta"}
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