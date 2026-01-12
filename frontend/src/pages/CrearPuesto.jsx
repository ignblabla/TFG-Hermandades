import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/CrearActo.css"; // Reutilizamos estilos para consistencia
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft } from "lucide-react";

function CrearPuesto() {
    // --- ESTADOS ---
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Estados para los selectores (Foreign Keys)
    const [listaActos, setListaActos] = useState([]);
    const [listaTiposPuesto, setListaTiposPuesto] = useState([]);

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);

    // Form Data inicial
    const [formData, setFormData] = useState({
        nombre: "",
        numero_maximo_asignaciones: 1,
        acto: "",
        tipo_puesto: "",
        lugar_citacion: "",
        hora_citacion: "",
        disponible: true
    });

    const navigate = useNavigate();

    useEffect(() => {
        const token = localStorage.getItem("access");

        if (!token) {
            setLoading(false);
            navigate("/login");
            return;
        }

        const fetchData = async () => {
            try {
                const userRes = await fetch("http://127.0.0.1:8000/api/me/", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                
                if (!userRes.ok) throw new Error("Auth Failed");
                const userData = await userRes.json();
                
                if (!userData.esAdmin) {
                    alert("No tienes permisos de administrador para gestionar puestos.");
                    navigate("/");
                    return;
                }
                setUser(userData);

                const actosRes = await fetch("http://127.0.0.1:8000/api/actos/", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (actosRes.ok) {
                    const actosData = await actosRes.json();
                    const actosFiltrados = actosData.filter(acto => acto.requiere_papeleta === true);
                    setListaActos(actosFiltrados);
                }

                const tiposRes = await fetch("http://127.0.0.1:8000/api/tipos-puesto/", {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (tiposRes.ok) {
                    const tiposData = await tiposRes.json();
                    setListaTiposPuesto(tiposData);
                }

            } catch (err) {
                console.error("Error cargando datos:", err);
                localStorage.removeItem("access");
                navigate("/login");
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [navigate]);

    // --- MANEJADORES ---

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError("");
        setSuccess(false);

        const token = localStorage.getItem("access");

        try {
            const response = await fetch("http://127.0.0.1:8000/api/puestos/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess(true);
                setTimeout(() => navigate("/home"), 2000); 
            } else {
                // --- AQUÍ ESTÁ LA LÓGICA PERSONALIZADA ---
                
                // CASO 1: Error de Negocio (El acto no lleva papeleta)
                if (data.acto) {
                    // Django devuelve array: ["Mensaje..."], extraemos el texto
                    const msg = Array.isArray(data.acto) ? data.acto[0] : data.acto;
                    // Lo guardamos tal cual, o le añadimos un prefijo si quieres
                    setError(`⚠️ ${msg}`); 
                } 
                else if (data.detail) {
                    setError(data.detail);
                }
                // CASO 3: Errores en otros campos (ej. validación nombre)
                else if (data.non_field_errors) {
                    setError(data.non_field_errors[0]);
                }
                // CASO 4: Fallback genérico
                else {
                    // Buscamos el primer error que encontremos en el objeto
                    const firstKey = Object.keys(data)[0];
                    const firstMsg = data[firstKey];
                    const msgTexto = Array.isArray(firstMsg) ? firstMsg[0] : firstMsg;
                    setError(`Error en ${firstKey}: ${msgTexto}`);
                }
            }
        } catch (err) {
            console.error(err);
            setError("Error de conexión con el servidor. Inténtelo más tarde.");
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
                    <li><a href="#titulares">Titulares</a></li>
                    <li><a href="#agenda">Agenda</a></li>
                    <li><a href="#lunes-santo">Lunes Santo</a></li>
                    <li><a href="#multimedia">Multimedia</a></li>
                    
                    <div className="nav-buttons-mobile">
                        {user ? (
                            <>
                                <button className="btn-outline">
                                    Hermano: {user.dni}
                                </button>
                                <button className="btn-purple" onClick={handleLogout}>
                                    Cerrar Sesión
                                </button>
                            </>
                        ) : (
                            <>
                                <button className="btn-outline" onClick={() => navigate("/login")}>Acceso Hermano</button>
                                <button className="btn-purple">Hazte Hermano</button>
                            </>
                        )}
                    </div>
                </ul>

                <div className="nav-buttons-desktop">
                    {user ? (
                            <>
                            <button className="btn-outline" onClick={() => navigate("/editar-perfil")} style={{cursor: 'pointer'}}>
                                Hermano: {user.dni}
                            </button>
                            <button className="btn-purple" onClick={handleLogout}>
                                Cerrar Sesión
                            </button>
                            </>
                    ) : (
                        <>
                            <button className="btn-outline" onClick={() => navigate("/login")}>Acceso Hermano</button>
                            <button className="btn-purple">Hazte Hermano</button>
                        </>
                    )}
                </div>
            </nav>

            {/* --- MAIN CONTENT --- */}
            <main className="main-container-area">
                <div className="card-container-area">
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Crear Puesto / Papeleta</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Configure un puesto disponible para ser solicitado mediante papeleta de sitio.
                        </p>
                    </header>

                    {/* Feedback Messages */}
                    {error && <div style={{padding: '15px', backgroundColor: '#fee2e2', color: '#b91c1c', marginBottom: '1rem', borderRadius: '6px', border: '1px solid #fca5a5'}}>
                        <strong>Error:</strong> {error}
                    </div>}
                    
                    {success && <div style={{padding: '15px', backgroundColor: '#dcfce7', color: '#15803d', marginBottom: '1rem', borderRadius: '6px', border: '1px solid #86efac'}}>
                        ¡Puesto creado con éxito!
                    </div>}

                    <section className="form-card-acto">
                        <form className="event-form-acto" onSubmit={handleSubmit}>
                            
                            {/* FILA 1: Nombre y Cantidad */}
                            <div className="form-row-acto">
                                <div className="form-group-acto" style={{flex: 2}}>
                                    <label htmlFor="nombre">NOMBRE DEL PUESTO</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">🏷️</span>
                                        <input 
                                            type="text" id="nombre" name="nombre" 
                                            required value={formData.nombre} onChange={handleChange}
                                            placeholder="Ej: Vara de Presidencia, Cirio, Diputado..." 
                                        />
                                    </div>
                                </div>
                                <div className="form-group-acto" style={{flex: 1}}>
                                    <label htmlFor="numero_maximo_asignaciones">CANTIDAD</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">🔢</span>
                                        <input 
                                            type="number" id="numero_maximo_asignaciones" name="numero_maximo_asignaciones" 
                                            required min="1" value={formData.numero_maximo_asignaciones} onChange={handleChange}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* FILA 2: Selectores (Acto y Tipo) */}
                            <div className="form-row-acto">
                                <div className="form-group-acto">
                                    <label htmlFor="acto">ACTO ASOCIADO</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">📅</span>
                                        <select 
                                            id="acto" name="acto" 
                                            required value={formData.acto} onChange={handleChange}
                                        >
                                            <option value="" disabled>Seleccione un acto</option>
                                            {listaActos.map(acto => (
                                                <option key={acto.id} value={acto.id}>
                                                    {acto.nombre} ({new Date(acto.fecha).toLocaleDateString()})
                                                </option>
                                            ))}
                                            {listaActos.length === 0 && (
                                                <option disabled>No hay actos que requieran papeleta.</option>
                                            )}
                                        </select>
                                    </div>
                                    <small style={{color: '#666', fontSize: '0.8rem'}}>Solo actos que requieran papeleta.</small>
                                </div>

                                <div className="form-group-acto">
                                    <label htmlFor="tipo_puesto">TIPO DE PUESTO</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">🗂️</span>
                                        <select 
                                            id="tipo_puesto" name="tipo_puesto" 
                                            required value={formData.tipo_puesto} onChange={handleChange}
                                        >
                                            <option value="" disabled>Seleccione Categoría</option>
                                            {listaTiposPuesto.map(tipo => (
                                                <option key={tipo.id} value={tipo.nombre_tipo}>
                                                    {tipo.nombre_tipo} {tipo.solo_junta_gobierno ? '(Solo Junta)' : ''}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* FILA 3: Citación */}
                            <div className="form-row-acto">
                                <div className="form-group-acto">
                                    <label htmlFor="lugar_citacion">LUGAR CITACIÓN</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">📍</span>
                                        <input 
                                            type="text" id="lugar_citacion" name="lugar_citacion" 
                                            value={formData.lugar_citacion} onChange={handleChange}
                                            placeholder="Ej: Capilla, Casa Hermandad..."
                                        />
                                    </div>
                                </div>
                                <div className="form-group-acto">
                                    <label htmlFor="hora_citacion">HORA CITACIÓN</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">🕒</span>
                                        <input 
                                            type="time" id="hora_citacion" name="hora_citacion" 
                                            value={formData.hora_citacion} onChange={handleChange}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* FILA 4: Checkbox Disponible */}
                            <div className="form-group-acto full-width">
                                <label style={{display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer'}}>
                                    <input 
                                        type="checkbox" 
                                        name="disponible" 
                                        checked={formData.disponible} 
                                        onChange={handleChange}
                                        style={{width: '20px', height: '20px'}}
                                    />
                                    <span>Marcar como <strong>Disponible</strong> para asignación inmediata.</span>
                                </label>
                            </div>

                            <div className="form-actions-acto">
                                <button type="button" className="btn-cancel-acto" onClick={() => navigate("/agenda")}>Cancelar</button>
                                <button type="submit" className="btn-save-acto" disabled={submitting}>
                                    <span className="icon-save-acto">💾</span> {submitting ? "Creando..." : "Crear Puesto"}
                                </button>
                            </div>
                        </form>
                    </section>
                </div>
            </main>
        </div>
    );
}

export default CrearPuesto;