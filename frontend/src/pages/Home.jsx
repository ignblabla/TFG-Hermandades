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
    const navigate = useNavigate();
    const [menuOpen, setMenuOpen] = useState(false);
    
    // Estado del usuario
    const [hermano, setHermano] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Estado para la gestión de áreas
    const [selectedArea, setSelectedArea] = useState(""); // Valor del dropdown
    const [updatingAreas, setUpdatingAreas] = useState(false); // Spinner para guardar

    // 1. Carga inicial del perfil
    useEffect(() => {
        fetchPerfil();
    }, []);

    const fetchPerfil = async () => {
        try {
            const response = await api.get("/api/me/"); 
            setHermano(response.data);
        } catch (err) {
            console.error("Error cargando perfil:", err);
            setError("No se pudieron cargar los datos del hermano.");
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    // --- LÓGICA DE ÁREAS ---

    // Función auxiliar para enviar los cambios a la API
    const updateAreasEnBackend = async (nuevaListaAreas) => {
        setUpdatingAreas(true);
        try {
            // Enviamos PATCH con la nueva lista completa
            const response = await api.patch("/api/me/", {
                areas_interes: nuevaListaAreas
            });
            // Actualizamos el estado local con la respuesta del servidor
            // (esto asegura que lo que vemos es lo que realmente se guardó)
            setHermano(prev => ({
                ...prev,
                areas_interes: response.data.areas_interes
            }));
            setSelectedArea(""); // Reseteamos el dropdown
        } catch (err) {
            console.error("Error actualizando áreas:", err);
            alert("Hubo un error al actualizar tus áreas.");
        } finally {
            setUpdatingAreas(false);
        }
    };

    // Añadir un área nueva
    const handleAddArea = () => {
        if (!selectedArea) return;
        // Creamos una nueva lista con lo que había + la nueva
        const currentAreas = hermano?.areas_interes || [];
        const nuevaLista = [...currentAreas, selectedArea];
        updateAreasEnBackend(nuevaLista);
    };

    // Borrar un área específica
    const handleRemoveArea = (areaKeyToRemove) => {
        const currentAreas = hermano?.areas_interes || [];
        // Filtramos para quitar la que no queremos
        const nuevaLista = currentAreas.filter(area => area !== areaKeyToRemove);
        updateAreasEnBackend(nuevaLista);
    };

    // Borrar todas
    const handleRemoveAll = () => {
        if(window.confirm("¿Seguro que quieres borrar todas tus áreas de interés?")){
            updateAreasEnBackend([]);
        }
    };

    // Calcular qué áreas NO tiene el usuario para mostrarlas en el dropdown
    const areasDisponibles = Object.keys(AREA_NOMBRES).filter(key => 
        !hermano?.areas_interes?.includes(key)
    );

    // -----------------------

    if (loading) return <div className="loading">Cargando datos de la Hermandad...</div>;
    if (error) return <div className="error">{error}</div>;

    return (
        <div className="site-wrapper">
            <nav className="navbar">
                {/* ... (Tu código del Navbar se mantiene igual) ... */}
                <div className="logo-container">
                    <img src={logoEscudo} alt="Escudo San Gonzalo" className="nav-logo" />
                    <div className="logo-text">
                        <h4>Hermandad de San Gonzalo</h4>
                        <span>SEVILLA</span>
                    </div>
                </div>
                <button className="menu-toggle" onClick={() => setMenuOpen(!menuOpen)}>☰</button>
                <div className="nav-buttons-desktop">
                    <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                </div>
            </nav>

            <section className="profile-card">
                 {/* ... (Tu código del Profile Card se mantiene igual) ... */}
                 <div className="user-meta-profile">
                    <h2 className="user-name-profile">
                        {hermano?.nombre} {hermano?.primer_apellido}
                    </h2>
                 </div>
            </section>

            {/* SECCIÓN ÁREAS MODIFICADA */}
            <div className="areas-container">
                <div className="areas-header">
                    <h3>Tus Áreas de Interés</h3>
                    {hermano?.areas_interes?.length > 0 && (
                        <button 
                            className="btn-text-danger" 
                            onClick={handleRemoveAll}
                            disabled={updatingAreas}
                        >
                            Vaciar lista
                        </button>
                    )}
                </div>

                {/* Selector para añadir */}
                <div className="add-area-controls">
                    <select 
                        value={selectedArea} 
                        onChange={(e) => setSelectedArea(e.target.value)}
                        className="area-select"
                        disabled={updatingAreas || areasDisponibles.length === 0}
                    >
                        <option value="">-- Selecciona un área para añadir --</option>
                        {areasDisponibles.map(key => (
                            <option key={key} value={key}>
                                {AREA_NOMBRES[key]}
                            </option>
                        ))}
                    </select>
                    
                    <button 
                        className="btn-add-area" 
                        onClick={handleAddArea}
                        disabled={!selectedArea || updatingAreas}
                    >
                        {updatingAreas ? "..." : "Añadir"}
                    </button>
                </div>
                
                {/* Lista de Áreas */}
                {hermano?.areas_interes && hermano.areas_interes.length > 0 ? (
                    <ul className="lista-areas">
                        {hermano.areas_interes.map((codigoArea) => (
                            <li key={codigoArea} className="area-item">
                                <span className="badge">
                                    {AREA_NOMBRES[codigoArea] || codigoArea}
                                </span>
                                <button 
                                    className="btn-remove-item"
                                    onClick={() => handleRemoveArea(codigoArea)}
                                    title="Eliminar área"
                                    disabled={updatingAreas}
                                >
                                    ✕
                                </button>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="empty-msg">No tienes áreas asignadas. ¡Anímate a participar!</p>
                )}
            </div>
        </div>
    );
}

export default Home;