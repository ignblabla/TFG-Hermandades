import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
// Asegúrate de tener los estilos importados, igual que en tu ejemplo
import '../styles/AdminEdicionHermano.css'; 
import { 
    Save, 
    FileText, 
    Users, 
    MessageSquare, 
    AlertCircle, 
    CheckCircle, 
    Info 
} from "lucide-react";

function AdminCreacionComunicado() {
    const navigate = useNavigate();
    
    // --- ESTADOS DE UI ---
    const [isOpen, setIsOpen] = useState(false); // Sidebar
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");

    // --- DATOS DEL USUARIO Y MAESTROS ---
    const [currentUser, setCurrentUser] = useState(null);
    const [areasDisponibles, setAreasDisponibles] = useState([]);

    // --- FORMULARIO ---
    const [formData, setFormData] = useState({
        titulo: '',
        contenido: '',
        tipo_comunicacion: 'GENERAL',
        areas_interes: [] // Array de IDs [1, 2, ...]
    });

    // Opciones estáticas del modelo (Hardcoded para coincidir con TextChoices de Django)
    const tiposComunicacion = [
        { value: 'GENERAL', label: 'General' },
        { value: 'INFORMATIVO', label: 'Informativo' },
        { value: 'CULTOS', label: 'Cultos' },
        { value: 'SECRETARIA', label: 'Secretaría' },
        { value: 'URGENTE', label: 'Urgente' },
        { value: 'EVENTOS', label: 'Eventos y Caridad' },
    ];

    // --- 1. CARGA INICIAL ---
    useEffect(() => {
        let isMounted = true;
        
        const fetchData = async () => {
            try {
                // 1. Obtener usuario actual
                const resUser = await api.get("api/me/");
                if (isMounted) setCurrentUser(resUser.data);

                // 2. Obtener Áreas de Interés para el selector múltiple
                const resAreas = await api.get("api/areas-interes/");
                if (isMounted) setAreasDisponibles(resAreas.data);

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al conectar con el servidor.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, []);

    // --- 2. MANEJO DE MENSAJES ---
    useEffect(() => {
        if (successMsg) {
            const timer = setTimeout(() => setSuccessMsg(""), 3000);
            return () => clearTimeout(timer);
        }
    }, [successMsg]);

    // --- 3. HANDLERS ---
    const toggleSidebar = () => setIsOpen(!isOpen);

    // Manejo de inputs de texto simple
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const toggleArea = (areaId) => {
        setFormData(prev => {
            const currentAreas = prev.areas_interes;
            if (currentAreas.includes(areaId)) {
                return { ...prev, areas_interes: currentAreas.filter(id => id !== areaId) };
            } else {
                return { ...prev, areas_interes: [...currentAreas, areaId] };
            }
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        if (!formData.titulo.trim() || !formData.contenido.trim()) {
            setError("El título y el contenido son obligatorios.");
            setSaving(false);
            window.scrollTo(0, 0);
            return;
        }

        try {
            await api.post('api/comunicados/', formData);
            
            setSuccessMsg("Comunicado emitido correctamente.");

            setTimeout(() => {
                navigate("/home");
            }, 1500);

        } catch (err) {
            console.error(err);
            if (err.response) {
                if (err.response.status === 403) {
                    setError("No tienes permisos (Solo Admins o Junta de Gobierno).");
                } else if (err.response.data) {
                    const errorData = err.response.data;
                    if (errorData.detail) {
                        setError(errorData.detail);
                    } else {
                        const errorMessages = Object.entries(errorData)
                            .map(([key, msg]) => {
                                const fieldName = key === 'non_field_errors' ? 'Error' : key.toUpperCase();
                                return `${fieldName}: ${Array.isArray(msg) ? msg[0] : msg}`;
                            })
                            .join(" | ");
                        setError(errorMessages);
                    }
                }
            } else {
                setError("Error de conexión al enviar el comunicado.");
            }
            window.scrollTo(0, 0);
        } finally {
            setSaving(false);
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    if (loading) return <div className="loading-screen">Cargando panel...</div>;

    return (
        <div>
            {/* --- SIDEBAR (Idéntico a tu ejemplo) --- */}
            <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
                <div className="logo_details-dashboard">
                    <i className="bx bxl-audible icon-dashboard"></i>
                    <div className="logo_name-dashboard">San Gonzalo</div>
                    <i className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} id="btn" onClick={toggleSidebar}></i>
                </div>
                <ul className="nav-list-dashboard">
                    {/* ... (Items del menú igual que tu ejemplo) ... */}
                    <li>
                        <a onClick={() => navigate("/home")} style={{cursor: 'pointer'}}>
                            <i className="bx bx-grid-alt"></i>
                            <span className="link_name-dashboard">Dashboard</span>
                        </a>
                        <span className="tooltip-dashboard">Dashboard</span>
                    </li>
                     {/* ... Resto de items ... */}
                    <li className="profile-dashboard">
                        <div className="profile_details-dashboard">
                            {/* Placeholder imagen */}
                            <img src="https://via.placeholder.com/40" alt="profile" /> 
                            <div className="profile_content-dashboard">
                                <div className="name-dashboard">{currentUser ? `${currentUser.nombre} ${currentUser.primer_apellido}` : "Usuario"}</div>
                                <div className="designation-dashboard">{currentUser?.esAdmin ? "Administrador" : "Hermano"}</div>
                            </div>
                        </div>
                        <i className="bx bx-log-out" id="log_out" onClick={handleLogout} style={{cursor: 'pointer'}}></i>
                    </li>
                </ul>
            </div>

            {/* --- CONTENIDO PRINCIPAL --- */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">Nuevo Comunicado</div>
                
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        
                        {/* BANNER DE ERRORES/ÉXITO */}
                        {error && (
                            <div className="alert-banner-edicion error-edicion">
                                <AlertCircle size={20} />
                                <span>{error}</span>
                            </div>
                        )}
                        {successMsg && (
                            <div className="alert-banner-edicion success-edicion">
                                <CheckCircle size={20} />
                                <span>{successMsg}</span>
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            {/* SECCIÓN 1: DATOS BÁSICOS */}
                            <div className="form-section-edicion">
                                <h3 className="section-title-edicion"><FileText size={18}/> Información del Comunicado</h3>
                                <div className="form-grid-edicion grid-2-edicion">
                                    
                                    {/* Título */}
                                    <div className="form-group-edicion span-2-edicion">
                                        <label>Título *</label>
                                        <input 
                                            type="text" 
                                            name="titulo" 
                                            value={formData.titulo} 
                                            onChange={handleChange} 
                                            placeholder="Ej: Horario de reparto de papeletas"
                                            required 
                                        />
                                    </div>

                                    {/* Tipo de Comunicación */}
                                    <div className="form-group-edicion">
                                        <label>Tipo de Comunicación *</label>
                                        <select 
                                            name="tipo_comunicacion" 
                                            value={formData.tipo_comunicacion} 
                                            onChange={handleChange}
                                            required
                                        >
                                            {tiposComunicacion.map(opt => (
                                                <option key={opt.value} value={opt.value}>
                                                    {opt.label}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    {/* Contenido */}
                                    <div className="form-group-edicion span-2-edicion">
                                        <label>Contenido del Mensaje *</label>
                                        <textarea 
                                            name="contenido" 
                                            value={formData.contenido} 
                                            onChange={handleChange}
                                            rows="6"
                                            placeholder="Escriba aquí el cuerpo de la noticia..."
                                            style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #d1d5db', resize: 'vertical' }}
                                            required
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN 2: DESTINATARIOS (Áreas de Interés) */}
                            <div className="form-section-edicion admin-section-edicion">
                                <h3 className="section-title-edicion admin-title-edicion">
                                    <Users size={18}/> Áreas de Interés (Destinatarios)
                                </h3>
                                
                                <div style={{ marginBottom: '15px' }}>
                                    <small style={{ color: '#6b7280' }}>
                                        Selecciona las áreas a las que va dirigido este comunicado. Si no seleccionas ninguna, 
                                        el comunicado se guardará como <strong>Borrador</strong> y no aparecerá en el muro de los hermanos.
                                    </small>
                                </div>

                                {/* Grid de Checkboxes personalizados */}
                                <div className="areas-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '10px' }}>
                                    {areasDisponibles.map(area => {
                                        const isSelected = formData.areas_interes.includes(area.id);
                                        return (
                                            <div 
                                                key={area.id}
                                                onClick={() => toggleArea(area.id)}
                                                style={{
                                                    padding: '10px 15px',
                                                    border: isSelected ? '1px solid #2563eb' : '1px solid #e5e7eb',
                                                    borderRadius: '8px',
                                                    backgroundColor: isSelected ? '#eff6ff' : '#fff',
                                                    color: isSelected ? '#1e40af' : '#374151',
                                                    cursor: 'pointer',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    gap: '10px',
                                                    transition: 'all 0.2s'
                                                }}
                                            >
                                                <input 
                                                    type="checkbox" 
                                                    checked={isSelected} 
                                                    onChange={() => {}} // Controlado por el div padre
                                                    style={{ cursor: 'pointer', accentColor: '#2563eb' }}
                                                />
                                                <span style={{ fontSize: '0.9rem', fontWeight: isSelected ? '600' : '400' }}>
                                                    {area.nombre_area} {/* O area.get_nombre_area_display si viene así del serializador */}
                                                    {/* Nota: En tu serializer AreaInteresSerializer usaste fields=['id', 'nombre_area', 'get_nombre_area_display'] 
                                                        Si el campo raw es 'CARIDAD', usamos el display del backend si está disponible.
                                                        Si usaste source='get_nombre_area_display' en el campo nombre_area del serializer, aquí saldrá bien.
                                                    */}
                                                </span>
                                            </div>
                                        )
                                    })}
                                </div>
                                
                                {/* Aviso visual si está vacío */}
                                {formData.areas_interes.length === 0 && (
                                    <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#fff7ed', borderRadius: '6px', borderLeft: '4px solid #f97316', fontSize: '0.85rem', color: '#9a3412', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Info size={16} />
                                        <span>Este comunicado se guardará en modo <strong>Borrador</strong> (sin destinatarios).</span>
                                    </div>
                                )}
                            </div>

                            {/* BOTONES DE ACCIÓN */}
                            <div className="form-actions-edicion">
                                <button type="button" className="btn-cancel-edicion" onClick={() => navigate("/home")}>
                                    Cancelar
                                </button>
                                <button type="submit" className="btn-save-edicion" disabled={saving}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Save size={18} />
                                        {saving ? "Emitiendo..." : "Emitir Comunicado"}
                                    </div>
                                </button>
                            </div>

                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminCreacionComunicado;