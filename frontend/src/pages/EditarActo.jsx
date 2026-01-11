import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from 'axios';
import api from "../api";
import "../styles/EditarActo.css"
import logoEscudo from '../assets/escudo.png';
import { ArrowLeft } from "lucide-react";


function EditarActo() {
    const { id } = useParams();

    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState(false);
    const [formData, setFormData] = useState({
        nombre: "",
        tipo_acto: "",
        fecha: "",
        descripcion: ""
    });

    const navigate = useNavigate();

    useEffect(() => {
        const fetchData = async () => {
            try {
                // 1. Verifico usuario y permisos
                const userRes = await api.get("api/me/");
                console.log("Datos del usuario:", userRes.data);
                const userData = userRes.data;
                setUser(userData);

                if (!userData.esAdmin) {
                    alert("No tienes permisos de administrador.");
                    navigate("/home");
                    return;
                }

                // 2. Obtengo los datos del acto existente
                const actoRes = await api.get(`api/actos/${id}/`);
                const actoData = actoRes.data;

                // 3. Formateo la fecha para el input datetime-local
                let fechaFormateada = "";
                if (actoData.fecha) {
                    fechaFormateada = actoData.fecha.slice(0, 16); 
                }

                setFormData({
                    nombre: actoData.nombre,
                    tipo_acto: actoData.tipo_acto,
                    fecha: fechaFormateada,
                    descripcion: actoData.descripcion || ""
                });

            } catch (err) {
                console.error("Error cargando datos:", err);
                if (err.response && err.response.status === 401) {
                    localStorage.removeItem("access");
                    navigate("/login");
                } else if (err.response && err.response.status === 404) {
                    setError("El acto que intentas editar no existe.");
                } else {
                    setError("Error al cargar la información.");
                }
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [id, navigate]);


    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: value
        }));
    };


    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);
        setError("");
        setSuccess(false);

        try {
            await api.put(`api/actos/${id}/`, formData);
            setSuccess(true);
            setTimeout(() => navigate("/home"), 2000);
        } catch (err) {
            console.error("Error actualizando:", err);
            
            if (err.response && err.response.data) {
                const errorData = err.response.data;
                
                if (errorData.non_field_errors) {
                    setError(errorData.non_field_errors[0]);
                }
                else if (errorData.nombre) {
                    setError(errorData.nombre[0]);
                }
                else if (errorData.fecha) {
                    setError(errorData.fecha[0]);
                }
                else if (errorData.detail) {
                    setError(errorData.detail);
                }
                else {
                    setError("Error al validar los datos. Revisa el formulario.");
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

    if (loading) return <div className="site-wrapper">Cargando...</div>;
    if (!user) return <div className="site-wrapper">No has iniciado sesión.</div>;

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

            <main className="main-container-area">
                <div className="card-container-area">
                    <header className="content-header-area">
                        <div className="title-row-area">
                            {/* Título cambiado para reflejar que es Edición */}
                            <h1>Editar Acto</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Modifique los detalles del evento. Los cambios se reflejarán inmediatamente en la agenda.
                        </p>
                    </header>

                    {error && <div style={{padding: '10px', backgroundColor: '#fee2e2', color: '#dc2626', marginBottom: '1rem', borderRadius: '4px'}}>{error}</div>}
                    {success && <div style={{padding: '10px', backgroundColor: '#dcfce7', color: '#16a34a', marginBottom: '1rem', borderRadius: '4px'}}>¡Acto actualizado correctamente!</div>}

                    <section className="form-card-acto">
                        <form className="event-form-acto" onSubmit={handleSubmit}>
                            
                            {/* CAMPO NOMBRE */}
                            <div className="form-group-acto full-width">
                                <label htmlFor="nombre">NOMBRE DEL ACTO</label>
                                <div className="input-with-icon-acto">
                                    <span className="icon-acto">📅</span>
                                    <input 
                                        type="text" 
                                        id="nombre"
                                        name="nombre" 
                                        required
                                        value={formData.nombre}
                                        onChange={handleChange}
                                        placeholder="Ej: Solemne Quinario..." 
                                    />
                                </div>
                            </div>

                            <div className="form-row-acto">
                                {/* CAMPO TIPO ACTO */}
                                <div className="form-group-acto">
                                    <label htmlFor="tipo_acto">TIPO DE ACTO</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">▲</span>
                                        <select 
                                            id="tipo_acto" 
                                            name="tipo_acto"
                                            required
                                            value={formData.tipo_acto}
                                            onChange={handleChange}
                                        >
                                            <option value="" disabled>Seleccione categoría</option>
                                            {/* Asegúrate de que los 'value' coincidan con los Slugs del Backend */}
                                            <option value="ESTACION_PENITENCIA">Estación de Penitencia</option>
                                            <option value="VIA_CRUCIS">Vía Crucis</option>
                                            <option value="QUINARIO">Quinario</option>
                                            <option value="TRIDUO">Triduo</option>
                                            <option value="ROSARIO_AURORA">Rosario de la Aurora</option>
                                            <option value="CABILDO_GENERAL">Cabildo General</option>
                                            <option value="CABILDO_EXTRAORDINARIO">Cabildo Extraordinario</option>
                                            <option value="CONVIVENCIA">Convivencia</option>
                                            <option value="PROCESION_EUCARISTICA">Procesión Eucarística</option>
                                        </select>
                                    </div>
                                </div>

                                {/* CAMPO FECHA */}
                                <div className="form-group-acto">
                                    <label htmlFor="fecha">FECHA Y HORA</label>
                                    <div className="input-with-icon-acto">
                                        <span className="icon-acto">🕒</span>
                                        <input 
                                            type="datetime-local" 
                                            id="fecha"
                                            name="fecha"
                                            required
                                            value={formData.fecha}
                                            onChange={handleChange}
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* CAMPO DESCRIPCION */}
                            <div className="form-group-acto full-width">
                                <label htmlFor="descripcion">DESCRIPCIÓN DEL ACTO</label>
                                <textarea 
                                    id="descripcion" 
                                    name="descripcion"
                                    rows="5" 
                                    value={formData.descripcion}
                                    onChange={handleChange}
                                    placeholder="Detalle la información relevante..."
                                ></textarea>
                            </div>

                            <div className="form-actions-acto">
                                {/* Botón cancelar redirige a Home o Agenda */}
                                <button type="button" className="btn-cancel-acto" onClick={() => navigate("/home")}>Cancelar</button>
                                
                                <button type="submit" className="btn-save-acto" disabled={submitting}>
                                    <span className="icon-save-acto">💾</span> {submitting ? "Guardando..." : "Actualizar Acto"}
                                </button>
                            </div>
                        </form>
                    </section>
                </div>
            </main>
        </div>
    );
}

export default EditarActo;