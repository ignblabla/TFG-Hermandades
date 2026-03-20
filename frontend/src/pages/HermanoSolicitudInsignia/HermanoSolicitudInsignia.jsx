import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import '../HermanoSolicitudInsignia/HermanoSolicitudInsignia.css';
import { Save, FileText, Settings, ShieldAlert, CheckCircle, Clock, AlertCircle, Lock, ArrowUp, ArrowDown, X, Send, ChevronDown, ChevronRight } from "lucide-react";

function HermanoSolicitudInsignia() {
    const navigate = useNavigate();
    
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false); 
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState(""); 
    
    const [currentUser, setCurrentUser] = useState(null);
    const [actoActivo, setActoActivo] = useState(null);

    const [insigniasSeleccionadas, setInsigniasSeleccionadas] = useState([]);
    const [isDragOver, setIsDragOver] = useState(false);

    // --- NUEVOS ESTADOS PARA COLAPSAR/EXPANDIR ---
    const [mostrarCristo, setMostrarCristo] = useState(true);
    const [mostrarVirgen, setMostrarVirgen] = useState(true);

    useEffect(() => {
        let isMounted = true;
        
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                if (isMounted) setCurrentUser(resUser.data);

                try {
                    const resActo = await api.get("api/actos/activo-insignias/");
                    if (isMounted) setActoActivo(resActo.data);
                } catch (errActo) {
                    if (errActo.response && errActo.response.status === 404) {
                        if (isMounted) setActoActivo(null);
                    } else {
                        console.error("Error obteniendo el acto activo:", errActo);
                    }
                }

            } catch (err) {
                console.error("Error de autenticación o servidor:", err);
                if (isMounted) setError("Error al cargar configuración inicial.");
                if (err.response?.status === 401) {
                    navigate("/login");
                }
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [navigate]);

    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    const handleDragStart = (e, insignia) => {
        e.dataTransfer.setData('insignia', JSON.stringify(insignia));
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragOver(true);
    };

    const handleDragLeave = () => {
        setIsDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragOver(false);
        const insigniaData = e.dataTransfer.getData('insignia');
        
        if (insigniaData) {
            const insignia = JSON.parse(insigniaData);
            if (!insigniasSeleccionadas.some(i => i.id === insignia.id)) {
                setInsigniasSeleccionadas([...insigniasSeleccionadas, insignia]);
            }
        }
    };

    const moverArriba = (index) => {
        if (index === 0) return;
        const nuevas = [...insigniasSeleccionadas];
        const temp = nuevas[index];
        nuevas[index] = nuevas[index - 1];
        nuevas[index - 1] = temp;
        setInsigniasSeleccionadas(nuevas);
    };

    const moverAbajo = (index) => {
        if (index === insigniasSeleccionadas.length - 1) return;
        const nuevas = [...insigniasSeleccionadas];
        const temp = nuevas[index];
        nuevas[index] = nuevas[index + 1];
        nuevas[index + 1] = temp;
        setInsigniasSeleccionadas(nuevas);
    };

    const quitarInsignia = (id) => {
        setInsigniasSeleccionadas(insigniasSeleccionadas.filter(i => i.id !== id));
    };

    const enviarSolicitud = async () => {
        if (insigniasSeleccionadas.length === 0) {
            setError("Debe seleccionar al menos una insignia para enviar la solicitud.");
            return;
        }

        setSaving(true);
        setError("");
        setSuccessMsg("");

        const payload = {
            acto_id: actoActivo.id,
            preferencias: insigniasSeleccionadas.map((insignia, index) => ({
                puesto_solicitado: insignia.id,
                orden_prioridad: index + 1
            }))
        };

        try {
            await api.post("api/papeletas/solicitar-insignia/", payload);
            setSuccessMsg("¡Solicitud enviada correctamente!");
            
            setTimeout(() => {
                navigate("/home");
            }, 2500);

        } catch (err) {
            console.error("Error al enviar solicitud:", err);
            
            if (err.response && err.response.data) {
                const errorData = err.response.data;
                if (errorData.detail) {
                    setError(errorData.detail);
                } 
                else if (typeof errorData === 'object') {
                    const mensajesLimpios = Object.values(errorData).flat().join(" | ");
                    setError(mensajesLimpios || "Error al procesar la solicitud.");
                } else {
                    setError("Error interno del servidor. Por favor, inténtelo de nuevo más tarde.");
                }
            } else {
                setError("Error de conexión. Verifique su internet.");
            }
        } finally {
            setSaving(false);
        }
    };

    const insigniasDisponibles = actoActivo?.puestos_disponibles?.filter(
        p => !insigniasSeleccionadas.some(seleccionada => seleccionada.id === p.id)
    ) || [];

    const insigniasCristo = insigniasDisponibles.filter(p => p.cortejo_cristo);
    const insigniasVirgen = insigniasDisponibles.filter(p => !p.cortejo_cristo);

    const renderInsignias = (insignias) => {
        if (insignias.length === 0) {
            return (
                <p className="solicitud-insignia-empty-msg">
                    No hay insignias disponibles para este cortejo.
                </p>
            );
        }

        return (
            <div className="insignias-grid-container">
                {insignias.map((insignia) => (
                    <div 
                        key={insignia.id} 
                        className="insignia-card"
                        draggable
                        onDragStart={(e) => handleDragStart(e, insignia)}
                    >
                        <h4 className="insignia-card-title">
                            {insignia.nombre}
                        </h4>
                    </div>
                ))}
            </div>
        );
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
                                <div className="name-dashboard">{currentUser ? `${currentUser.nombre} ${currentUser.primer_apellido}` : "Usuario"}</div>
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

            {/* --- CONTENIDO PRINCIPAL --- */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">
                    {actoActivo 
                        ? `Solicitud de insignias para el acto ${actoActivo.nombre}` 
                        : 'Plazo de solicitud de insignias'
                    }
                </div>
                
                <p style={{ padding: '0 20px', color: '#666', fontSize: '15px', marginTop: '0', marginBottom: '20px' }}>
                    En esta pantalla podrá gestionar su solicitud de insignias. Arrastre las opciones de la columna izquierda hacia el recuadro de la derecha y ordénelas verticalmente en función de su prioridad.
                </p>

                <div style={{ padding: '0 20px 40px 20px' }}>
                    
                    {error && (
                        <div className="solicitud-insignia-error-alert" style={{marginBottom: '15px'}}>{error}</div>
                    )}
                    
                    {successMsg && (
                        <div className="solicitud-insignia-success-alert" style={{marginBottom: '15px', color: 'green', fontWeight: 'bold'}}>{successMsg}</div>
                    )}

                    <div className="dashboard-layout-wrapper">
                        {actoActivo ? (
                            <div className="solicitud-insignia-container">
                                <h3 className="solicitud-insignia-title">Acto: {actoActivo.nombre}</h3>
                                <p className="solicitud-insignia-description" style={{ marginBottom: '10px' }}>
                                    Arrastre las insignias que desea solicitar hacia el panel de la derecha.
                                </p>

                                {insigniasDisponibles.length > 0 ? (
                                    <>
                                        {/* WRAPPER COLAPSABLE CRISTO */}
                                        <div 
                                            className="cortejo-subtitle-wrapper" 
                                            onClick={() => setMostrarCristo(!mostrarCristo)}
                                        >
                                            <h4 className="cortejo-subtitle">
                                                Cortejo de Nuestro Padre Jesús en Su Soberano Poder ante Caifás
                                            </h4>
                                            {mostrarCristo ? <ChevronDown size={20} color="var(--burgundy-primary)" /> : <ChevronRight size={20} color="var(--burgundy-primary)" />}
                                        </div>
                                        
                                        {/* RENDER CONDICIONAL CRISTO */}
                                        {mostrarCristo && renderInsignias(insigniasCristo)}


                                        {/* WRAPPER COLAPSABLE VIRGEN */}
                                        <div 
                                            className="cortejo-subtitle-wrapper" 
                                            onClick={() => setMostrarVirgen(!mostrarVirgen)}
                                        >
                                            <h4 className="cortejo-subtitle">
                                                Cortejo de Nuestra Señora de la Salud
                                            </h4>
                                            {mostrarVirgen ? <ChevronDown size={20} color="var(--burgundy-primary)" /> : <ChevronRight size={20} color="var(--burgundy-primary)" />}
                                        </div>
                                        
                                        {/* RENDER CONDICIONAL VIRGEN */}
                                        {mostrarVirgen && renderInsignias(insigniasVirgen)}
                                    </>
                                ) : (
                                    <p className="solicitud-insignia-empty-msg">
                                        Has seleccionado todas las insignias disponibles.
                                    </p>
                                )}
                            </div>
                        ) : (
                            <div className="solicitud-insignia-container">
                                <p className="solicitud-insignia-error-msg">
                                    Actualmente no hay ningún plazo abierto para solicitar insignias.
                                </p>
                            </div>
                        )}

                        {actoActivo && (
                            <div 
                                className={`resumen-solicitud-container ${isDragOver ? 'drag-over-active' : ''}`}
                                onDragOver={handleDragOver}
                                onDragLeave={handleDragLeave}
                                onDrop={handleDrop}
                            >
                                <h3 className="solicitud-insignia-title">Insignias seleccionadas</h3>
                                <p className="solicitud-insignia-description">
                                    Suéltelas aquí. Ordénelas de arriba a abajo en función de su prioridad.
                                </p>

                                <div className="lista-seleccionadas-container">
                                    {insigniasSeleccionadas.length === 0 ? (
                                        <div className="empty-dropzone">
                                            Arrastre aquí una insignia
                                        </div>
                                    ) : (
                                        insigniasSeleccionadas.map((insignia, index) => (
                                            <div key={insignia.id} className="seleccionada-card">
                                                <div className="seleccionada-info">
                                                    <span className="prioridad-badge">{index + 1}º</span>
                                                    <span className="seleccionada-nombre">{insignia.nombre}</span>
                                                </div>
                                                
                                                <div className="seleccionada-acciones">
                                                    <button 
                                                        onClick={() => moverArriba(index)} 
                                                        disabled={index === 0}
                                                        title="Subir prioridad"
                                                    >
                                                        <ArrowUp size={18} />
                                                    </button>
                                                    <button 
                                                        onClick={() => moverAbajo(index)} 
                                                        disabled={index === insigniasSeleccionadas.length - 1}
                                                        title="Bajar prioridad"
                                                    >
                                                        <ArrowDown size={18} />
                                                    </button>
                                                    <button 
                                                        onClick={() => quitarInsignia(insignia.id)} 
                                                        className="btn-quitar"
                                                        title="Quitar de la lista"
                                                    >
                                                        <X size={18} />
                                                    </button>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                                
                                {/* BOTÓN DE ENVIAR */}
                                <div style={{ marginTop: 'auto', paddingTop: '20px' }}>
                                    <button 
                                        className="btn-enviar-solicitud"
                                        onClick={enviarSolicitud}
                                        disabled={saving || insigniasSeleccionadas.length === 0}
                                        style={{
                                            width: '100%',
                                            padding: '12px',
                                            backgroundColor: (saving || insigniasSeleccionadas.length === 0) ? '#ccc' : 'var(--burgundy-primary)',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '8px',
                                            fontWeight: 'bold',
                                            cursor: (saving || insigniasSeleccionadas.length === 0) ? 'not-allowed' : 'pointer',
                                            display: 'flex',
                                            justifyContent: 'center',
                                            alignItems: 'center',
                                            gap: '10px',
                                            transition: 'background-color 0.2s'
                                        }}
                                    >
                                        <Send size={20} />
                                        {saving ? "Procesando..." : "Enviar Solicitud de Insignias"}
                                    </button>
                                </div>

                            </div>
                        )}

                    </div>
                </div>
            </section>
        </div>
    );
}

export default HermanoSolicitudInsignia;