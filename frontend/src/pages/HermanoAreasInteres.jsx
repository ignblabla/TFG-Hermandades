import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import "../styles/HermanoAreaInteres.css";
import AreaCard from "../components/AreaCard"
import { Users, Heart, Hammer, Church, Sun, BookOpen, Save, Crown, Landmark, Bell } from "lucide-react";

function HermanoAreaInteres() {

    const [isOpen, setIsOpen] = useState(false); 
    const [user, setUser] = useState({});
    const [selectedAreas, setSelectedAreas] = useState([]);
    const [areasDB, setAreasDB] = useState([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const areaInfoEstatica = {
        'TODOS_HERMANOS': { icon: <Bell />, title: 'Todos los Hermanos', desc: 'Comunicados generales de la Hermandad (Suscripción obligatoria)' },
        'COSTALEROS': { icon: <Users />, title: 'Costaleros', desc: 'Cuadrillas de hermanos costaleros de Nuestro Padre Jesús en Su Soberano Poder ante Caifás y Nuestra Señora de la Salud Coronada.' },
        'CARIDAD': { icon: <Heart />, title: 'Diputación de Caridad', desc: 'Acción social y ayuda al prójimo' },
        'JUVENTUD': { icon: <Sun />, title: 'Juventud', desc: 'Grupo joven y actividades formativas' },
        'PRIOSTIA': { icon: <Hammer />, title: 'Priostía', desc: 'Mantenimiento y montaje de altares' },
        'CULTOS_FORMACION': { icon: <BookOpen />, title: 'Cultos y Formación', desc: 'Liturgia, charlas y crecimiento espiritual' },
        'PATRIMONIO': { icon: <Landmark />, title: 'Patrimonio', desc: 'Conservación artística de la Hermandad' },
        'ACOLITOS': { icon: <Church />, title: 'Acólitos', desc: 'Cuerpo de acólitos y monaguillos' },
        'DIPUTACION_MAYOR_GOBIERNO': { icon: <Crown />, title: 'Diputación Mayor de Gobierno', desc: 'Organización de la Cofradía' },
    };

    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");
        if (usuarioGuardado) {
            try {
                const parsedUser = JSON.parse(usuarioGuardado);
                setUser(parsedUser);
                if (parsedUser.areas_interes) {
                    const areasLocal = parsedUser.areas_interes;
                    if (!areasLocal.includes('TODOS_HERMANOS')) areasLocal.push('TODOS_HERMANOS');
                    setSelectedAreas(areasLocal);
                }
            } catch (e) {
                console.error("Error al leer user_data", e);
            }
        }

        api.get("/api/me/")
            .then(response => {
                const data = response.data;
                setUser(data);
                
                const areasBackend = data.areas_interes || [];
                if (!areasBackend.includes('TODOS_HERMANOS')) areasBackend.push('TODOS_HERMANOS');
                
                setSelectedAreas(areasBackend);
                localStorage.setItem("user_data", JSON.stringify(data));
            })
            .catch(error => {
                console.error("Error cargando perfil:", error);
            });

        api.get("/api/areas-interes/")
            .then(response => {
                setAreasDB(response.data);
            })
            .catch(error => {
                console.error("Error cargando las áreas de interés:", error);
            });
    }, []);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        setUser(null);
        navigate("/");
    };

    const handleCheckboxChange = (areaNombre) => {
        if (areaNombre === 'TODOS_HERMANOS') {
            return;
        }

        setSelectedAreas(prevAreas => {
            if (prevAreas.includes(areaNombre)) {
                return prevAreas.filter(nombre => nombre !== areaNombre);
            } else {
                return [...prevAreas, areaNombre];
            }
        });
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            const areasToSave = selectedAreas.includes('TODOS_HERMANOS') 
                ? selectedAreas 
                : [...selectedAreas, 'TODOS_HERMANOS'];

            const response = await api.patch("/api/me/", {
                areas_interes: areasToSave
            });
            const data = response.data;
            const updatedUser = { ...user, ...data };
            setUser(updatedUser);
            localStorage.setItem("user_data", JSON.stringify(updatedUser));
            alert("Preferencias guardadas correctamente.");

        } catch (error) {
            console.error("Error al guardar:", error);

            if (error.response) {
                alert(`Error al guardar: ${JSON.stringify(error.response.data)}`);
            } else if (error.request) {
                alert("Error de conexión con el servidor.");
            } else {
                alert("Ocurrió un error inesperado.");
            }
        } finally {
            setLoading(false);
        }
    };

    const sortedAreasDB = [...areasDB].sort((a, b) => {
        if (a.nombre_area === 'TODOS_HERMANOS') return -1;
        if (b.nombre_area === 'TODOS_HERMANOS') return 1;
        return a.nombre_area.localeCompare(b.nombre_area); 
    });

    return (
        <div>
            <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
                <div className="logo_details-dashboard">
                    <i className="bx bxl-audible icon-dashboard"></i>
                    <div className="logo_name-dashboard">San Gonzalo</div>
                    <i 
                        className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} 
                        id="btn" 
                        onClick={toggleSidebar}
                    ></i>
                </div>
                <ul className="nav-list-dashboard">
                    <li>
                        <i className="bx bx-search" onClick={toggleSidebar}></i>
                        <input type="text" placeholder="Search..." />
                        <span className="tooltip-dashboard">Search</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-grid-alt"></i>
                            <span className="link_name-dashboard">Dashboard</span>
                        </a>
                        <span className="tooltip-dashboard">Dashboard</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-user"></i>
                            <span className="link_name-dashboard">User</span>
                        </a>
                        <span className="tooltip-dashboard">User</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-chat"></i>
                            <span className="link_name-dashboard">Message</span>
                        </a>
                        <span className="tooltip-dashboard">Message</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-pie-chart-alt-2"></i>
                            <span className="link_name-dashboard">Analytics</span>
                        </a>
                        <span className="tooltip-dashboard">Analytics</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-folder"></i>
                            <span className="link_name-dashboard">File Manager</span>
                        </a>
                        <span className="tooltip-dashboard">File Manager</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-cart-alt"></i>
                            <span className="link_name-dashboard">Order</span>
                        </a>
                        <span className="tooltip-dashboard">Order</span>
                    </li>
                    <li>
                        <a href="#">
                            <i className="bx bx-cog"></i>
                            <span className="link_name-dashboard">Settings</span>
                        </a>
                        <span className="tooltip-dashboard">Settings</span>
                    </li>
                    
                    <li className="profile-dashboard">
                        <div className="profile_details-dashboard">
                            <img src="profile.jpeg" alt="profile image" />
                            <div className="profile_content-dashboard">
                                <div className="name-dashboard">{user ? `${user.nombre} ${user.primer_apellido}` : "Usuario"}</div>
                                <div className="designation-dashboard">Administrador</div>
                            </div>
                        </div>
                        <i 
                            className="bx bx-log-out" 
                            id="log_out" 
                            onClick={handleLogout}
                            style={{cursor: 'pointer'}} 
                        ></i>
                    </li>
                </ul>
            </div>

            <section className="home-section-dashboard">
                <div className="text-dashboard">Áreas de interés</div>
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <p style={{ marginBottom: '20px', color: 'var(--text-muted)' }}>
                        Gestiona tus preferencias de comunicación. El canal general de <strong>Todos los Hermanos</strong> es obligatorio para mantenerte informado de la actualidad de la Hermandad.
                    </p>
                    <div className="full-grid-layout">
                        {sortedAreasDB.map(area => {
                            const visualInfo = areaInfoEstatica[area.nombre_area] || {};
                            const isMandatory = area.nombre_area === 'TODOS_HERMANOS';
                            
                            return (
                                <AreaCard 
                                    key={area.id}
                                    icon={visualInfo.icon}
                                    title={visualInfo.title || area.nombre_area}
                                    desc={visualInfo.desc || ''}
                                    telegramLink={area.telegram_invite_link}
                                    isFeatured={true}
                                    isSelected={isMandatory ? true : selectedAreas.includes(area.nombre_area)}
                                    onClick={() => handleCheckboxChange(area.nombre_area)}

                                    isLocked={isMandatory} 
                                />
                            );
                        })}
                    </div>

                    <footer className="card-footer-area-interes">
                        <button className="btn-save-area-interes" onClick={handleSave} disabled={loading}>
                            <Save size={18} /> {loading ? "Guardando..." : "Guardar Preferencias"}
                        </button>
                    </footer>
                </div>
            </section>
        </div>
    );
}

export default HermanoAreaInteres;