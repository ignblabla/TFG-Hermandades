import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from 'axios';
import api from "../api";
import Note from "../components/Note"
import "../styles/Home.css"
import logoEscudo from '../assets/escudo.png';

function Home() {
    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const [editMode, setEditMode] = useState(false);
    const [formData, setFormData] = useState({
        telefono: "",
        direccion: "",
        codigo_postal: "",
        localidad: "",
        provincia: "",
        comunidad_autonoma: ""
    });

    const [mensaje, setMensaje] = useState({ texto: "", tipo: "" });

    const navigate = useNavigate();

    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");
        if (usuarioGuardado) {
            const parsedUser = JSON.parse(usuarioGuardado);
            setUser(parsedUser);
            // Inicializamos el formulario con los datos guardados
            inicializarFormulario(parsedUser);
        }
    }, []);

    useEffect(() => {
        const token = localStorage.getItem("access");

        if (token) {
            fetch("http://127.0.0.1:8000/api/me/", {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                }
            })
            .then(async response => {
                if (response.ok) {
                    const data = await response.json();
                    setUser(data);
                    inicializarFormulario(data); // Actualizamos form con datos frescos
                } else {
                    console.log("Token caducado o inválido");
                    localStorage.removeItem("access"); 
                    setUser(null);
                }
            })
            .catch(error => console.error("Error:", error))
            .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const inicializarFormulario = (datosUsuario) => {
        setFormData({
            telefono: datosUsuario.telefono || "",
            direccion: datosUsuario.direccion || "",
            codigo_postal: datosUsuario.codigo_postal || "",
            localidad: datosUsuario.localidad || "",
            provincia: datosUsuario.provincia || "",
            comunidad_autonoma: datosUsuario.comunidad_autonoma || ""
        });
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/"; 
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSave = () => {
        const token = localStorage.getItem("access");
        setMensaje({ texto: "Guardando...", tipo: "info" });

        fetch("http://127.0.0.1:8000/api/me/", {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        })
        .then(async response => {
            if (response.ok) {
                const data = await response.json();
                
                // --- CORRECCIÓN AQUÍ ---
                // No reemplazamos 'user' directamente.
                // Creamos un nuevo objeto manteniendo lo que ya teníamos (...user)
                // y sobrescribiendo solo lo que viene nuevo (...data).
                const usuarioActualizado = { ...user, ...data };

                setUser(usuarioActualizado); 
                setEditMode(false);
                setMensaje({ texto: "Datos actualizados correctamente.", tipo: "success" });
                
                // Guardamos el objeto COMPLETO y fusionado en localStorage
                localStorage.setItem("user_data", JSON.stringify(usuarioActualizado));
                
                setTimeout(() => setMensaje({ texto: "", tipo: "" }), 3000);
            } else {
                const errorData = await response.json();
                console.error("Errores:", errorData);
                setMensaje({ texto: "Error al actualizar. Revise los campos.", tipo: "error" });
            }
        })
        .catch(error => {
            console.error("Error de red:", error);
            setMensaje({ texto: "Error de conexión.", tipo: "error" });
        });
    };

    const handleCancel = () => {
        setEditMode(false);
        if (user) inicializarFormulario(user); // Revertir cambios
        setMensaje({ texto: "", tipo: "" });
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
                            <button className="btn-outline" style={{cursor: 'default'}}>
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

            <main className="profile-container">
                <header className="profile-header">
                    <nav className="breadcrumbs-profile">
                        <a href="#inicio">Inicio</a> <span>&gt;</span> <a href="#perfil" className="active">Mi Perfil</a>
                    </nav>
                    <h1 className="main-title-profile">Mi perfil de Hermano</h1>
                    <p className="subtitle-profile">Gestione su información personal y vinculación con la Hermandad.</p>
                </header>

                <section className="profile-card">
                    <div className="profile-info-main">
                        <div className="avatar-wrapper-profile">
                            <img 
                                src="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=200&auto=format&fit=crop" 
                                alt="Francisco Javier Pérez" 
                                className="avatar-img-profile"
                                srcSet="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=200 1x, https://images.unsplash.com/photo-1500648767791-00dcc994a43e?q=80&w=400 2x"
                            />
                            <button className="edit-avatar-profile" aria-label="Editar foto de perfil">✎</button>
                        </div>

                        <div className="user-meta-profile">
                            <h2 className="user-name-profile">{user.nombre} {user.primer_apellido} {user.segundo_apellido}</h2>
                            <div className="badges-group-profile">
                                <span className="badge-profile">Número de registro: {user.id || "---"}</span>
                                <span className="badge-profile">Antigüedad: {user.antiguedad || "Consultar"}</span>
                                <span className="badge-status-profile">● Cuotas al día</span>
                            </div>
                        </div>
                    </div>

                    <button className="btn-digital-card-profile">
                        <span className="icon-profile">📇</span> Tarjeta Digital
                    </button>
                </section>

                <nav className="profile-tabs">
                    <button className="tab-item-profile active">
                        <span className="tab-icon-profile">👤</span> Datos Personales
                    </button>
                    <button className="tab-item-profile">
                        <span className="tab-icon-profile">📧</span> Contacto
                    </button>
                    <button className="tab-item-profile">
                        <span className="tab-icon-profile">⛪</span> Datos religiosos
                    </button>
                    <button className="tab-item-profile">
                        <span className="tab-icon-profile">💳</span> Estado de cuotas
                    </button>
                </nav>

                <div className="details-grid-profile">
                    <section className="info-box-profile">
                        <div className="box-header-profile">
                            <h3><span className="icon-profile">👤</span>Información Personal</h3>
                        </div>

                        <div className="form-row-profile">
                            <div className="form-group-profile">
                                <label>NOMBRE</label>
                                <div className="read-only-field-profile">{user.nombre}</div>
                            </div>
                            <div className="form-group-profile">
                                <label>PRIMER APELLIDO</label>
                                <div className="read-only-field-profile">{user.primer_apellido}</div>
                            </div>
                        </div>

                        <div className="form-row-profile">
                            <div className="form-group-profile">
                                <label>SEGUNDO APELLIDO</label>
                                <div className="read-only-field-profile">{user.segundo_apellido}</div>
                            </div>
                            <div className="form-group-profile">
                                <label>DNI / NIF</label>
                                <div className="read-only-field-profile">{user.dni}</div>
                            </div>
                        </div>

                        <div className="form-row-profile">
                            <div className="form-group-profile">
                                <label>FECHA DE NACIMIENTO</label>
                                <div className="read-only-field-profile">{user.fecha_nacimiento || "--/--/----"}</div>
                            </div>
                            <div className="form-group-profile">
                                <label>GÉNERO</label>
                                <div className="read-only-field-profile select-mock">{user.genero || "-"}</div>
                            </div>
                        </div>

                        <div className="form-group-profile">
                            <label>ESTADO CIVIL</label>
                            <div className="read-only-field-profile select-mock">{user.estado_civil || "-"}</div>
                        </div>
                    </section>

                    <section className="info-box-profile">
                        <div className="box-header-profile">
                            <h3><span className="icon-profile">📍</span>Datos de contacto</h3>
                            {!editMode ? (
                                <button className="btn-edit-inline-profile" onClick={() => setEditMode(true)}>
                                    Editar
                                </button>
                            ) : (
                                <div style={{ display: 'flex', gap: '10px' }}>
                                    <button className="btn-save-profile" onClick={handleSave} style={{cursor: 'pointer', fontWeight: 'bold', color: '#6a1b9a', background: 'transparent', border: 'none'}}>
                                        Guardar
                                    </button>
                                    <button className="btn-cancel-profile" onClick={handleCancel} style={{cursor: 'pointer', color: '#666', background: 'transparent', border: 'none'}}>
                                        Cancelar
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="form-group-profile">
                            <label>DIRECCIÓN POSTAL</label>
                            {editMode ? (
                                <input 
                                    type="text" 
                                    name="direccion" 
                                    className="input-field-profile" // Asegúrate de tener estilo para esto en CSS
                                    value={formData.direccion} 
                                    onChange={handleChange} 
                                />
                            ) : (
                                <div className="read-only-field-profile">{user.direccion}</div>
                            )}
                        </div>

                        <div className="form-row-profile">
                            <div className="form-group-profile">
                                <label>CÓDIGO POSTAL</label>
                                {editMode ? (
                                    <input 
                                        type="text" 
                                        name="codigo_postal" 
                                        className="input-field-profile"
                                        value={formData.codigo_postal} 
                                        onChange={handleChange} 
                                    />
                                ) : (
                                    <div className="read-only-field-profile">{user.codigo_postal}</div>
                                )}
                            </div>
                            <div className="form-group-profile">
                                <label>LOCALIDAD</label>
                                {editMode ? (
                                    <input 
                                        type="text" 
                                        name="localidad" 
                                        className="input-field-profile"
                                        value={formData.localidad} 
                                        onChange={handleChange} 
                                    />
                                ) : (
                                    <div className="read-only-field-profile">{user.localidad}</div>
                                )}
                            </div>
                        </div>

                        <div className="form-row-profile">
                            <div className="form-group-profile">
                                <label>PROVINCIA</label>
                                {editMode ? (
                                    <input 
                                        type="text" 
                                        name="provincia" 
                                        className="input-field-profile"
                                        value={formData.provincia} 
                                        onChange={handleChange} 
                                    />
                                ) : (
                                    <div className="read-only-field-profile">{user.provincia}</div>
                                )}
                            </div>
                             {/* Agrego Comunidad Autónoma ya que estaba en tu formData */}
                            <div className="form-group-profile">
                                <label>COMUNIDAD</label>
                                {editMode ? (
                                    <input 
                                        type="text" 
                                        name="comunidad_autonoma" 
                                        className="input-field-profile"
                                        value={formData.comunidad_autonoma} 
                                        onChange={handleChange} 
                                    />
                                ) : (
                                    <div className="read-only-field-profile">{user.comunidad_autonoma}</div>
                                )}
                            </div>
                        </div>

                        <div className="form-row-profile">
                            <div className="form-group-profile">
                                <label>TELÉFONO</label>
                                {editMode ? (
                                    <input 
                                        type="tel" 
                                        name="telefono" 
                                        className="input-field-profile"
                                        value={formData.telefono} 
                                        onChange={handleChange} 
                                    />
                                ) : (
                                    <div className="read-only-field-profile">📞 {user.telefono}</div>
                                )}
                            </div>
                            <div className="form-group-profile">
                                <label>CORREO ELECTRÓNICO</label>
                                <div className="read-only-field-profile">✉️ fran.perez@email.com</div>
                            </div>
                        </div>
                    </section>
                </div>
            </main>
        </div>
    );
}

export default Home;