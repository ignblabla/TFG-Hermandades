import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api';
import '../HermanoSolicitudInsignia/HermanoSolicitudInsignia.css';
import { ArrowUp, ArrowDown, X, Send, ChevronDown, ChevronRight, Info } from "lucide-react";
import ActoCardSolicitud from '../../components/acto_card_solicitud/ActoCardSolicitud';

function HermanoSolicitudInsignia() {
    const navigate = useNavigate();
    
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false); 
    const [successMsg, setSuccessMsg] = useState(""); 
    
    const [currentUser, setCurrentUser] = useState(null);
    const [actoActivo, setActoActivo] = useState(null);

    const [insigniasSeleccionadas, setInsigniasSeleccionadas] = useState([]);
    const [isDragOver, setIsDragOver] = useState(false);

    const [mostrarCristo, setMostrarCristo] = useState(true);
    const [mostrarVirgen, setMostrarVirgen] = useState(true);

    const [modalBloqueo, setModalBloqueo] = useState(false);
    const [modalNoActivo, setModalNoActivo] = useState(false);

    const obtenerMes = (fechaString) => {
        if (!fechaString) return "MES";
        const date = new Date(fechaString);
        return date.toLocaleString('es-ES', { month: 'short' }).toUpperCase();
    };

    const obtenerDia = (fechaString) => {
        if (!fechaString) return "00";
        const date = new Date(fechaString);
        return date.getDate().toString().padStart(2, '0');
    };
    
    const obtenerHora = (fechaString) => {
        if (!fechaString) return "Por definir";
        const date = new Date(fechaString);
        return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' }) + " h";
    };

    useEffect(() => {
        let isMounted = true;
        
        const fetchData = async () => {
            try {
                const resUser = await api.get("api/me/");
                if (isMounted) setCurrentUser(resUser.data);

                try {
                    const resActo = await api.get("api/actos/activo-insignias/");
                    if (isMounted) {
                        setActoActivo(resActo.data);

                        try {
                            const resPapeletas = await api.get("api/papeletas/mis-papeletas/");
                            const misPapeletas = resPapeletas.data.results || resPapeletas.data;
                            
                            const yaSolicitado = misPapeletas.some(p => {
                                const coincideActo = Number(p.acto) === Number(resActo.data.id);
                                const estado = String(p.estado_papeleta || '').toUpperCase();
                                const estaActiva = estado !== 'ANULADA' && estado !== 'NO_ASIGNADA';

                                return coincideActo && estaActiva;
                            });

                            if (yaSolicitado) {
                                setModalBloqueo(true);
                            }
                        } catch (errPapeletas) {
                            console.error("Error verificando papeletas previas:", errPapeletas);
                        }
                    }
                } catch (errActo) {
                    if (errActo.response && errActo.response.status === 404) {
                        if (isMounted) {
                            setActoActivo(null);
                            setModalNoActivo(true);
                        }
                    } else {
                        console.error("Error obteniendo el acto activo:", errActo);
                    }
                }

            } catch (err) {
                console.error("Error de autenticación o servidor:", err);
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
        setSaving(true);
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
            alert("Ocurrió un problema de conexión con el servidor. Por favor, inténtelo de nuevo.");
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
            {modalBloqueo && (
                <div className="modal-overlay-bloqueo">
                    <div className="modal-content-bloqueo">
                        <div className="modal-header-bloqueo">
                            <Info className="modal-icon-info" size={28} />
                            <h3>Solicitud ya realizada</h3>
                        </div>
                        <div className="modal-body-bloqueo">
                            <p>
                                Ya consta una solicitud activa de papeleta de sitio para el acto <strong>{actoActivo?.nombre}</strong>.
                                <br/><br/>
                                Le recordamos que <strong>no es posible realizar múltiples solicitudes de insignias para un mismo acto</strong>. Si desea hacer cambios, por favor contacte con secretaría.
                            </p>
                            <button 
                                className="btn-volver-inicio" 
                                onClick={() => navigate('/new-home')}
                            >
                                Volver al inicio
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {modalNoActivo && (
                <div className="modal-overlay-bloqueo">
                    <div className="modal-content-bloqueo">
                        <div className="modal-header-bloqueo">
                            <Info className="modal-icon-info" size={28} />
                            <h3>Plazo cerrado</h3>
                        </div>
                        <div className="modal-body-bloqueo">
                            <p>
                                Actualmente no hay ningún plazo abierto para solicitar insignias. Por favor, manténgase atento a los comunicados oficiales de la Hermandad.
                            </p>
                            <button 
                                className="btn-volver-inicio" 
                                onClick={() => navigate('/new-home')}
                            >
                                Volver al inicio
                            </button>
                        </div>
                    </div>
                </div>
            )}

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
                        ? `Solicitud de insignias - ${actoActivo.nombre}` 
                        : 'Plazo de solicitud de insignias'
                    }
                </div>
                
                <p className="solicitud-insignia-instrucciones">
                    En esta pantalla podrá gestionar su solicitud de insignias. Arrastre las opciones de la columna izquierda hacia el recuadro de la derecha y ordénelas verticalmente en función de su prioridad.
                </p>

                <div className="solicitud-insignia-main-container">
                    
                    {successMsg && (
                        <div className="solicitud-insignia-success-alert">{successMsg}</div>
                    )}

                    <div className="dashboard-layout-wrapper">
                        {actoActivo ? (
                            <>
                                <div className="solicitud-insignia-container">
                                    <h3 className="solicitud-insignia-title">Acto: {actoActivo.nombre}</h3>
                                    <p className="solicitud-insignia-description mb-10">
                                        Arrastre las insignias que desea solicitar hacia el panel de la derecha.
                                    </p>

                                    {insigniasDisponibles.length > 0 ? (
                                        <>
                                            <div 
                                                className="cortejo-subtitle-wrapper" 
                                                onClick={() => setMostrarCristo(!mostrarCristo)}
                                            >
                                                <h4 className="cortejo-subtitle">
                                                    Cortejo de Nuestro Padre Jesús en Su Soberano Poder ante Caifás
                                                </h4>
                                                {mostrarCristo ? <ChevronDown size={20} color="var(--burgundy-primary)" /> : <ChevronRight size={20} color="var(--burgundy-primary)" />}
                                            </div>

                                            {mostrarCristo && renderInsignias(insigniasCristo)}

                                            <div 
                                                className="cortejo-subtitle-wrapper" 
                                                onClick={() => setMostrarVirgen(!mostrarVirgen)}
                                            >
                                                <h4 className="cortejo-subtitle">
                                                    Cortejo de Nuestra Señora de la Salud
                                                </h4>
                                                {mostrarVirgen ? <ChevronDown size={20} color="var(--burgundy-primary)" /> : <ChevronRight size={20} color="var(--burgundy-primary)" />}
                                            </div>

                                            {mostrarVirgen && renderInsignias(insigniasVirgen)}
                                        </>
                                    ) : (
                                        <p className="solicitud-insignia-empty-msg">
                                            Has seleccionado todas las insignias disponibles.
                                        </p>
                                    )}
                                </div>

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

                                    <div className="btn-enviar-wrapper">
                                        <button 
                                            className="btn-enviar-solicitud-final"
                                            onClick={enviarSolicitud}
                                            disabled={saving || insigniasSeleccionadas.length === 0}
                                        >
                                            <Send size={20} />
                                            {saving ? "Procesando..." : "Enviar Solicitud de Insignias"}
                                        </button>
                                    </div>
                                </div>

                                <div className="acto-card-lateral-wrapper">
                                    <ActoCardSolicitud
                                        mes={obtenerMes(actoActivo.fecha)}
                                        dia={obtenerDia(actoActivo.fecha)}
                                        titulo={actoActivo.nombre}
                                        hora={obtenerHora(actoActivo.fecha)}
                                        lugar={actoActivo.lugar || "Parroquia de San Gonzalo"}
                                        descripcion={actoActivo.descripcion || "Solicitud de insignias para el cortejo."}
                                        requierePapeleta={true} 
                                        imagenPortada={actoActivo.imagen || null}
                                        onVerDetalles={() => alert("Mostrando detalles del acto...")}
                                    />
                                </div>
                            </>
                        ) : (
                            <div className="solicitud-insignia-container" style={{width: '100%'}}>
                                <p className="solicitud-insignia-error-msg">
                                    Actualmente no hay ningún plazo abierto para solicitar insignias.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default HermanoSolicitudInsignia;