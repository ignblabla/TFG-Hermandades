import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api";
import "../styles/AreasInteres.css";
import logoEscudo from '../assets/escudo.png';
import { 
    Users, Heart, Hammer, Church, 
    Music, Sun, BookOpen, Save, ArrowLeft, Crown
} from "lucide-react";

function AreaInteres() {

    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState({});
    const [selectedAreas, setSelectedAreas] = useState([]);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const areas = [
        { id: 'COSTALEROS', icon: <Users />, title: 'Costaleros', desc: 'Cuadrillas de hermanos costaleros' },
        { id: 'CARIDAD', icon: <Heart />, title: 'Diputación de Caridad', desc: 'Acción social y ayuda al prójimo' },
        { id: 'JUVENTUD', icon: <Sun />, title: 'Juventud', desc: 'Grupo joven y actividades formativas' },
        { id: 'PRIOSTIA', icon: <Hammer />, title: 'Priostía', desc: 'Mantenimiento y montaje de altares' },
        { id: 'CULTOS_FORMACION', icon: <BookOpen />, title: 'Cultos y Formación', desc: 'Liturgia, charlas y crecimiento espiritual' },
        { id: 'PATRIMONIO', icon: <Church />, title: 'Patrimonio', desc: 'Conservación artística de la Hermandad' },
        { id: 'ACOLITOS', icon: <Church />, title: 'Acólitos', desc: 'Cuerpo de acólitos y monaguillos' },
        { id: 'DIPUTACION_MAYOR_GOBIERNO', icon: <Crown />, title: 'Diputación Mayor de Gobierno', desc: 'Organización de la Cofradía' },
    ]

    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");
        if (usuarioGuardado) {
            const parsedUser = JSON.parse(usuarioGuardado);
            setUser(parsedUser);
            if (parsedUser.areas_interes) {
                setSelectedAreas(parsedUser.areas_interes);
            }
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
                    setSelectedAreas(data.areas_interes || []);
                    
                    localStorage.setItem("user_data", JSON.stringify(data));
                } else {
                    console.log("Token caducado o inválido");
                    handleLogout();
                }
            })
            .catch(error => console.error("Error:", error));
        } else {
            navigate("/login");
        }
    }, [navigate]);

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        setUser(null);
        navigate("/");
    };

    // const areas = [
    //     { id: 'costaleros', icon: <Users />, title: 'Costaleros', desc: 'Cuadrillas de hermanos costaleros' },
    //     { id: 'coro', icon: <Music />, title: 'Coro', desc: 'Participación en el acompañamiento coral' },
    //     { id: 'caridad', icon: <Heart />, title: 'Diputación de Caridad', desc: 'Acción social y ayuda al prójimo' },
    //     { id: 'juventud', icon: <Sun />, title: 'Juventud', desc: 'Grupo joven y actividades formativas' },
    //     { id: 'priostia', icon: <Hammer />, title: 'Priostía', desc: 'Mantenimiento y montaje de altares' },
    //     { id: 'formacion', icon: <BookOpen />, title: 'Formación', desc: 'Charlas, cursos y crecimiento espiritual' },
    //     { id: 'cultos', icon: <Church />, title: 'Cultos y Espiritualidad', desc: 'Organización litúrgica y cultos internos' },
    // ];

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
        const token = localStorage.getItem("access");
        if (!token) return;

        setLoading(true);

        try {
            const response = await fetch("http://127.0.0.1:8000/api/me/", {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    areas_interes: selectedAreas
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                const updatedUser = { ...user, ...data };
                
                setUser(updatedUser);
                localStorage.setItem("user_data", JSON.stringify(updatedUser));
                
                alert("Preferencias guardadas correctamente.");
            } else {
                const errorData = await response.json();
                console.error("Error al guardar:", errorData);
                alert("Hubo un error al guardar las preferencias.");
            }
        } catch (error) {
            console.error("Error de red:", error);
            alert("Error de conexión con el servidor.");
        } finally {
            setLoading(false);
        }
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

            <main className="main-container-area">
                <div className="card-container-area">
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <h1>Mis áreas de interés</h1>
                            <button className="btn-back-area" onClick={() => navigate(-1)}>
                                <ArrowLeft size={16} /> Volver
                            </button>
                        </div>
                        <p className="description-area">
                            Selecciona las áreas en las que te gustaría participar o recibir información.
                        </p>
                    </header>

                    <div className="interests-grid-area">
                        {areas.map((area) => {
                            const isSelected = selectedAreas.includes(area.id);
                            
                            return (
                                <div 
                                    key={area.id} 
                                    className={`interest-card-area ${isSelected ? 'active' : ''}`}
                                    onClick={() => handleCheckboxChange(area.id)}
                                >
                                    <div className="interest-icon-box-area">
                                        {area.icon}
                                    </div>
                                    <div className="interest-info-area">
                                        <h3>{area.title}</h3>
                                        <p>{area.desc}</p>
                                    </div>
                                    <div className="checkbox-wrapper-area">
                                        <input 
                                            type="checkbox" 
                                            checked={isSelected} 
                                            onChange={() => {}}
                                            readOnly
                                        />
                                        <span className="checkmark-area"></span>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <footer className="card-footer-area">
                        <button 
                            className="btn-save-area" 
                            onClick={handleSave}
                            disabled={loading}
                        >
                            <Save size={18} /> {loading ? "Guardando..." : "Guardar Preferencias"}
                        </button>
                    </footer>
                </div>
            </main>
        </div>
    );
}

export default AreaInteres;