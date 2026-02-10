import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api"; // Asumo que este es tu axios configurado
import "../styles/Home.css";
import logoEscudo from '../assets/escudo.png';

const AREA_NOMBRES = {
    CARIDAD: "Caridad",
    CULTOS_FORMACION: "Cultos y Formación",
    JUVENTUD: "Juventud",
    PATRIMONIO: "Patrimonio",
    PRIOSTIA: "Priostía",
    DIPUTACION_MAYOR_GOBIERNO: "Diputación Mayor de Gobierno",
    COSTALEROS: "Costaleros",
    ACOLITOS: "Acólitos"
};

function Home() {

    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState({});
    const navigate = useNavigate();

    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");

        if (usuarioGuardado) {
            setUser(JSON.parse(usuarioGuardado));
        }
    }, []);

    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");
        if (usuarioGuardado) {
            setUser(JSON.parse(usuarioGuardado));
        }

        const verificarSesion = async () => {
            try {
                const response = await api.get("/api/me/");
                
                setUser(response.data);
                localStorage.setItem("user_data", JSON.stringify(response.data));

            } catch (error) {
                console.error("Error verificando sesión:", error);
                
                if (error.response && error.response.status === 401) {
                    console.log("Sesión caducada");
                    localStorage.removeItem("access");
                    localStorage.removeItem("refresh");
                    localStorage.removeItem("user_data");
                    setUser(null);
                }
            }
        };

        verificarSesion();
    }, []);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        setUser(null);
        window.location.href = "/"; 
    };

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


            <main className="profile-container">
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
                                <span className="badge-profile">Antigüedad: {user.antiguedad || "Consultar"}</span>
                                <span className="badge-profile">Antigüedad: {user.antiguedad || "Consultar"}</span>
                                <span className="badge-status-profile">● Cuotas al día</span>
                            </div>
                        </div>
                    </div>

                    <button className="btn-digital-card-profile">
                        <span className="icon-profile">📇</span> Tarjeta Digital
                    </button>
                </section>

                <div className="dashboard-layout-home">
                    <section className="quick-access-section-home">
                        <h3 className="section-title-home">Accesos rápidos</h3>
                        <div className="quick-access-grid-home">
                            <div className="access-card-home" onClick={() => navigate("/editar-perfil")} style={{ cursor: "pointer" }}>
                                <div className="icon-circle-home purple-bg">👤</div>
                                <div className="card-info-home">
                                    <span className="card-label-home">Mi perfil</span>
                                    <span className="card-sublabel-home">Datos personales</span>
                                </div>
                            </div>

                            <div className="access-card-home">
                                <div className="icon-circle-home purple-bg">💳</div>
                                <div className="card-info-home">
                                    <span className="card-label-home">Cuotas</span>
                                    <span className="card-status-ok-home">● Al día</span>
                                </div>
                            </div>

                            <div className="access-card-home">
                                <div className="icon-circle-home purple-bg">📅</div>
                                <div className="card-info-home">
                                    <span className="card-label-home">Agenda</span>
                                    <span className="card-status-ok-home">Próximos cultos</span>
                                </div>
                            </div>

                            <div className="access-card-home">
                                <div className="icon-circle-home purple-bg">✉️</div>
                                <div className="card-info-home">
                                    <span className="card-label-home">Buzón</span>
                                    <span className="card-status-ok-home">2 nuevos</span>
                                </div>
                            </div>
                        </div>
                    </section>

                    <section className="news-section-home">
                        <div className="news-header-home">
                            <h3 className="section-title-home">Noticias de la Hermandad</h3>
                            <a href="#" className="view-all-home">Ver todas →</a>
                        </div>

                        <article className="news-featured-card-home">
                            <div className="news-image-container-home">
                                <img 
                                    src="https://images.unsplash.com/photo-1548625361-625bc2962639?q=80&w=800&auto=format&fit=crop" 
                                    alt="Restauración" 
                                    className="news-img-home"
                                    srcSet="https://images.unsplash.com/photo-1548625361-625bc2962639?q=80&w=400 480w, https://images.unsplash.com/photo-1548625361-625bc2962639?q=80&w=800 1024w"
                                />
                            </div>
                            <div className="news-content-home">
                                <div className="news-meta-home">
                                    <span className="tag-official-home">Oficial</span>
                                    <span className="news-time-home">• Hace 2 horas</span>
                                </div>

                                <h4 className="news-title-home">Restauración del manto de salida: Informe preliminar y aprobación del Cabildo</h4>
                                <p className="news-excerpt-home">La comisión artística ha presentado los resultados del estudio técnico sobre el estado d...</p>
                                <a href="#" className="read-more-home">Leer más ›</a>
                            </div>
                        </article>
                    </section>
                </div>
            </main>
        </div>
    );
    // const navigate = useNavigate();
    // const [menuOpen, setMenuOpen] = useState(false);
    
    // // Estado del usuario
    // const [hermano, setHermano] = useState(null);
    // const [loading, setLoading] = useState(true);
    // const [error, setError] = useState(null);

    // // Estado para la gestión de áreas
    // const [selectedArea, setSelectedArea] = useState(""); // Valor del dropdown
    // const [updatingAreas, setUpdatingAreas] = useState(false); // Spinner para guardar

    // // 1. Carga inicial del perfil
    // useEffect(() => {
    //     fetchPerfil();
    // }, []);

    // const fetchPerfil = async () => {
    //     try {
    //         const response = await api.get("/api/me/"); 
    //         setHermano(response.data);
    //     } catch (err) {
    //         console.error("Error cargando perfil:", err);
    //         setError("No se pudieron cargar los datos del hermano.");
    //     } finally {
    //         setLoading(false);
    //     }
    // };

    // const handleLogout = () => {
    //     localStorage.clear();
    //     navigate("/login");
    // };

    // // --- LÓGICA DE ÁREAS ---

    // // Función auxiliar para enviar los cambios a la API
    // const updateAreasEnBackend = async (nuevaListaAreas) => {
    //     setUpdatingAreas(true);
    //     try {
    //         // Enviamos PATCH con la nueva lista completa
    //         const response = await api.patch("/api/me/", {
    //             areas_interes: nuevaListaAreas
    //         });
    //         // Actualizamos el estado local con la respuesta del servidor
    //         // (esto asegura que lo que vemos es lo que realmente se guardó)
    //         setHermano(prev => ({
    //             ...prev,
    //             areas_interes: response.data.areas_interes
    //         }));
    //         setSelectedArea(""); // Reseteamos el dropdown
    //     } catch (err) {
    //         console.error("Error actualizando áreas:", err);
    //         alert("Hubo un error al actualizar tus áreas.");
    //     } finally {
    //         setUpdatingAreas(false);
    //     }
    // };

    // // Añadir un área nueva
    // const handleAddArea = () => {
    //     if (!selectedArea) return;
    //     // Creamos una nueva lista con lo que había + la nueva
    //     const currentAreas = hermano?.areas_interes || [];
    //     const nuevaLista = [...currentAreas, selectedArea];
    //     updateAreasEnBackend(nuevaLista);
    // };

    // // Borrar un área específica
    // const handleRemoveArea = (areaKeyToRemove) => {
    //     const currentAreas = hermano?.areas_interes || [];
    //     // Filtramos para quitar la que no queremos
    //     const nuevaLista = currentAreas.filter(area => area !== areaKeyToRemove);
    //     updateAreasEnBackend(nuevaLista);
    // };

    // // Borrar todas
    // const handleRemoveAll = () => {
    //     if(window.confirm("¿Seguro que quieres borrar todas tus áreas de interés?")){
    //         updateAreasEnBackend([]);
    //     }
    // };

    // // Calcular qué áreas NO tiene el usuario para mostrarlas en el dropdown
    // const areasDisponibles = Object.keys(AREA_NOMBRES).filter(key => 
    //     !hermano?.areas_interes?.includes(key)
    // );

    // // -----------------------

    // if (loading) return <div className="loading">Cargando datos de la Hermandad...</div>;
    // if (error) return <div className="error">{error}</div>;

    // return (
    //     <div className="site-wrapper">
    //         <nav className="navbar">
    //             {/* ... (Tu código del Navbar se mantiene igual) ... */}
    //             <div className="logo-container">
    //                 <img src={logoEscudo} alt="Escudo San Gonzalo" className="nav-logo" />
    //                 <div className="logo-text">
    //                     <h4>Hermandad de San Gonzalo</h4>
    //                     <span>SEVILLA</span>
    //                 </div>
    //             </div>
    //             <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
    //             <div className="nav-buttons-desktop">
    //                 <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
    //             </div>
    //         </nav>

    //         <section className="profile-card">
    //              {/* ... (Tu código del Profile Card se mantiene igual) ... */}
    //              <div className="user-meta-profile">
    //                 <h2 className="user-name-profile">
    //                     {hermano?.nombre} {hermano?.primer_apellido}
    //                 </h2>
    //              </div>
    //         </section>

    //         {/* SECCIÓN ÁREAS MODIFICADA */}
    //         <div className="areas-container">
    //             <div className="areas-header">
    //                 <h3>Tus Áreas de Interés</h3>
    //                 {hermano?.areas_interes?.length > 0 && (
    //                     <button 
    //                         className="btn-text-danger" 
    //                         onClick={handleRemoveAll}
    //                         disabled={updatingAreas}
    //                     >
    //                         Vaciar lista
    //                     </button>
    //                 )}
    //             </div>

    //             {/* Selector para añadir */}
    //             <div className="add-area-controls">
    //                 <select 
    //                     value={selectedArea} 
    //                     onChange={(e) => setSelectedArea(e.target.value)}
    //                     className="area-select"
    //                     disabled={updatingAreas || areasDisponibles.length === 0}
    //                 >
    //                     <option value="">-- Selecciona un área para añadir --</option>
    //                     {areasDisponibles.map(key => (
    //                         <option key={key} value={key}>
    //                             {AREA_NOMBRES[key]}
    //                         </option>
    //                     ))}
    //                 </select>
                    
    //                 <button 
    //                     className="btn-add-area" 
    //                     onClick={handleAddArea}
    //                     disabled={!selectedArea || updatingAreas}
    //                 >
    //                     {updatingAreas ? "..." : "Añadir"}
    //                 </button>
    //             </div>
                
    //             {/* Lista de Áreas */}
    //             {hermano?.areas_interes && hermano.areas_interes.length > 0 ? (
    //                 <ul className="lista-areas">
    //                     {hermano.areas_interes.map((codigoArea) => (
    //                         <li key={codigoArea} className="area-item">
    //                             <span className="badge">
    //                                 {AREA_NOMBRES[codigoArea] || codigoArea}
    //                             </span>
    //                             <button 
    //                                 className="btn-remove-item"
    //                                 onClick={() => handleRemoveArea(codigoArea)}
    //                                 title="Eliminar área"
    //                                 disabled={updatingAreas}
    //                             >
    //                                 ✕
    //                             </button>
    //                         </li>
    //                     ))}
    //                 </ul>
    //             ) : (
    //                 <p className="empty-msg">No tienes áreas asignadas. ¡Anímate a participar!</p>
    //             )}
    //         </div>
    //     </div>
    // );
}

export default Home;