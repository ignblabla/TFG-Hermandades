import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import "../styles/HermanoAreaInteres.css";
import AreaCard from "../components/AreaCard"
import { Users, Heart, Hammer, Church, Sun, BookOpen, Save, Crown, Landmark } from "lucide-react";

function HermanoAreaInteres() {

    const [isOpen, setIsOpen] = useState(false); 
    const [user, setUser] = useState({});
    const [selectedAreas, setSelectedAreas] = useState([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const areas = [
        { id: 'COSTALEROS', icon: <Users />, title: 'Costaleros', desc: 'Cuadrillas de hermanos costaleros de Nuestro Padre Jesús en Su Soberano Poder ante Caifás y Nuestra Señora de la Salud Coronada.' },
        { id: 'CARIDAD', icon: <Heart />, title: 'Diputación de Caridad', desc: 'Acción social y ayuda al prójimo' },
        { id: 'JUVENTUD', icon: <Sun />, title: 'Juventud', desc: 'Grupo joven y actividades formativas' },
        { id: 'PRIOSTIA', icon: <Hammer />, title: 'Priostía', desc: 'Mantenimiento y montaje de altares' },
        { id: 'CULTOS_FORMACION', icon: <BookOpen />, title: 'Cultos y Formación', desc: 'Liturgia, charlas y crecimiento espiritual' },
        { id: 'PATRIMONIO', icon: <Landmark />, title: 'Patrimonio', desc: 'Conservación artística de la Hermandad' },
        { id: 'ACOLITOS', icon: <Church />, title: 'Acólitos', desc: 'Cuerpo de acólitos y monaguillos' },
        { id: 'DIPUTACION_MAYOR_GOBIERNO', icon: <Crown />, title: 'Diputación Mayor de Gobierno', desc: 'Organización de la Cofradía' },
    ]

    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");
        if (usuarioGuardado) {
            try {
                const parsedUser = JSON.parse(usuarioGuardado);
                setUser(parsedUser);
                if (parsedUser.areas_interes) {
                    setSelectedAreas(parsedUser.areas_interes);
                }
            } catch (e) {
                console.error("Error al leer user_data", e);
            }
        }

        api.get("/api/me/")
            .then(response => {
                const data = response.data;
                setUser(data);
                setSelectedAreas(data.areas_interes || []);
                localStorage.setItem("user_data", JSON.stringify(data));
            })
            .catch(error => {
                console.error("Error cargando perfil:", error);
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

    const handleCheckboxChange = (areaId) => {
        setSelectedAreas(prevAreas => {
            if (prevAreas.includes(areaId)) {
                return prevAreas.filter(id => id !== areaId);
            } else {
                return [...prevAreas, areaId];
            }
        });
    };

    const handleSave = async () => {
        setLoading(true);
        try {
            const response = await api.patch("/api/me/", {
                areas_interes: selectedAreas
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
                    <div className="full-grid-layout">
                        {areas.map(area => (
                            <AreaCard 
                                key={area.id}
                                {...area}
                                isFeatured={true}
                                isSelected={selectedAreas.includes(area.id)}
                                onClick={() => handleCheckboxChange(area.id)}
                            />
                        ))}
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