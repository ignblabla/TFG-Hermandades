import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../api';
import '../styles/AdminEdicionActo.css'; // Usamos los mismos estilos para consistencia
import { 
    Save, 
    FileText, 
    Users, 
    Trash2, 
    ArrowLeft, 
    AlertCircle, 
    CheckCircle, 
    Info 
} from "lucide-react";

function AdminEdicionComunicado() {
    const navigate = useNavigate();
    const { id } = useParams(); // Obtenemos el ID de la URL

    // --- ESTADOS ---
    const [isOpen, setIsOpen] = useState(false); // Sidebar
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [error, setError] = useState("");
    const [successMsg, setSuccessMsg] = useState("");

    const [currentUser, setCurrentUser] = useState(null);
    const [areasDisponibles, setAreasDisponibles] = useState([]);

    const [formData, setFormData] = useState({
        titulo: '',
        contenido: '',
        tipo_comunicacion: '',
        areas_interes: [] // Array de IDs (ej: [1, 3])
    });

    // Opciones estáticas (Deben coincidir con models.py)
    const tiposComunicacion = [
        { value: 'GENERAL', label: 'General' },
        { value: 'INFORMATIVO', label: 'Informativo' },
        { value: 'CULTOS', label: 'Cultos' },
        { value: 'SECRETARIA', label: 'Secretaría' },
        { value: 'URGENTE', label: 'Urgente' },
        { value: 'EVENTOS', label: 'Eventos y Caridad' },
    ];

    // --- CARGA INICIAL DE DATOS ---
    useEffect(() => {
        let isMounted = true;

        const fetchData = async () => {
            try {
                // 1. Validar Usuario
                const resUser = await api.get("api/me/");
                if (isMounted) setCurrentUser(resUser.data);

                // 2. Obtener todas las Áreas disponibles (para pintar los checkboxes)
                const resAreas = await api.get("api/areas-interes/");
                if (isMounted) setAreasDisponibles(resAreas.data);

                // 3. Obtener Datos del Comunicado a editar
                // NOTA: Gracias a que en la View usamos ComunicadoFormSerializer en el GET,
                // 'areas_interes' vendrá como una lista de IDs: [1, 2], perfecto para React.
                const resComunicado = await api.get(`api/comunicados/${id}/`);
                const data = resComunicado.data;

                if (isMounted) {
                    setFormData({
                        titulo: data.titulo,
                        contenido: data.contenido,
                        tipo_comunicacion: data.tipo_comunicacion,
                        areas_interes: data.areas_interes || [] 
                    });
                }

            } catch (err) {
                console.error(err);
                if (isMounted) setError("Error al cargar los datos del comunicado.");
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData();
        return () => { isMounted = false; };
    }, [id]);

    // --- HANDLERS ---
    const toggleSidebar = () => setIsOpen(!isOpen);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    // Lógica para marcar/desmarcar áreas
    const toggleArea = (areaId) => {
        setFormData(prev => {
            const current = prev.areas_interes;
            if (current.includes(areaId)) {
                // Si ya existe, lo sacamos del array
                return { ...prev, areas_interes: current.filter(id => id !== areaId) };
            } else {
                // Si no existe, lo agregamos
                return { ...prev, areas_interes: [...current, areaId] };
            }
        });
    };

    // --- ACTUALIZAR (PUT) ---
    const handleSubmit = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError("");
        setSuccessMsg("");

        try {
            await api.put(`api/comunicados/${id}/`, formData);
            setSuccessMsg("Comunicado actualizado correctamente.");
            
            // Redirigir al listado después de 1.5 segundos
            setTimeout(() => navigate("/admin/comunicados"), 1500); 
        } catch (err) {
            if (err.response && err.response.data) {
                setError(JSON.stringify(err.response.data));
            } else {
                setError("Error al guardar los cambios.");
            }
        } finally {
            setSaving(false);
        }
    };

    // --- ELIMINAR (DELETE) ---
    const handleDelete = async () => {
        if (!window.confirm("¿Estás seguro de que deseas eliminar este comunicado? Esta acción es irreversible.")) {
            return;
        }

        setDeleting(true);
        try {
            await api.delete(`api/comunicados/${id}/`);
            // Redirección inmediata tras borrado exitoso
            navigate("/admin/comunicados");
        } catch (err) {
            console.error(err);
            setError("Error al eliminar el comunicado. Verifica tus permisos.");
            setDeleting(false);
        }
    };

    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    if (loading) return <div className="loading-screen">Cargando datos...</div>;

    return (
        <div>
            {/* SIDEBAR */}
            <div className={`sidebar-dashboard ${isOpen ? 'open' : ''}`}>
                <div className="logo_details-dashboard">
                    <i className="bx bxl-audible icon-dashboard"></i>
                    <div className="logo_name-dashboard">San Gonzalo</div>
                    <i className={`bx ${isOpen ? 'bx-menu-alt-right' : 'bx-menu'}`} id="btn" onClick={toggleSidebar}></i>
                </div>
                <ul className="nav-list-dashboard">
                    <li onClick={() => navigate("/admin/comunicados")} style={{cursor: 'pointer'}}>
                        <a href="#">
                            <i className='bx bx-arrow-back'></i>
                            <span className="link_name-dashboard">Volver</span>
                        </a>
                        <span className="tooltip-dashboard">Volver</span>
                    </li>
                    <li className="profile-dashboard">
                        <div className="profile_details-dashboard">
                            <img src="/profile.jpeg" alt="profile" />
                            <div className="profile_content-dashboard">
                                <div className="name-dashboard">{currentUser ? `${currentUser.nombre}` : "Usuario"}</div>
                                <div className="designation-dashboard">Admin</div>
                            </div>
                        </div>
                        <i className="bx bx-log-out" id="log_out" onClick={handleLogout} style={{cursor: 'pointer'}}></i>
                    </li>
                </ul>
            </div>

            {/* CONTENIDO PRINCIPAL */}
            <section className="home-section-dashboard">
                <div className="text-dashboard">
                    <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', marginRight: '10px' }}>
                        <ArrowLeft size={24} color="#11101d"/>
                    </button>
                    Editar Comunicado
                </div>
                
                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        
                        {/* ALERTAS */}
                        {error && (
                            <div className="alert-banner-edicion error-edicion">
                                <AlertCircle size={20} /> <span>{error}</span>
                            </div>
                        )}
                        {successMsg && (
                            <div className="alert-banner-edicion success-edicion">
                                <CheckCircle size={20} /> <span>{successMsg}</span>
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            {/* SECCIÓN 1: DATOS */}
                            <div className="form-section-edicion">
                                <h3 className="section-title-edicion"><FileText size={18}/> Datos del Comunicado</h3>
                                <div className="form-grid-edicion grid-2-edicion">
                                    
                                    <div className="form-group-edicion span-2-edicion">
                                        <label>Título *</label>
                                        <input 
                                            type="text" 
                                            name="titulo" 
                                            value={formData.titulo} 
                                            onChange={handleChange} 
                                            required 
                                        />
                                    </div>

                                    <div className="form-group-edicion">
                                        <label>Tipo de Comunicación *</label>
                                        <select 
                                            name="tipo_comunicacion" 
                                            value={formData.tipo_comunicacion} 
                                            onChange={handleChange} 
                                            required
                                        >
                                            <option value="">-- Seleccionar --</option>
                                            {tiposComunicacion.map(opt => (
                                                <option key={opt.value} value={opt.value}>{opt.label}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="form-group-edicion span-2-edicion">
                                        <label>Contenido *</label>
                                        <textarea 
                                            name="contenido" 
                                            value={formData.contenido} 
                                            onChange={handleChange} 
                                            rows="6"
                                            className="textarea-standard"
                                            style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #d1d5db' }}
                                            required
                                        />
                                    </div>
                                </div>
                            </div>

                            {/* SECCIÓN 2: ÁREAS DE INTERÉS (M2M) */}
                            <div className="form-section-edicion admin-section-edicion">
                                <h3 className="section-title-edicion admin-title-edicion">
                                    <Users size={18}/> Destinatarios (Áreas)
                                </h3>
                                
                                <div className="areas-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '10px', marginTop: '15px' }}>
                                    {areasDisponibles.map(area => {
                                        // Verificamos si el ID del área está en nuestro array de IDs seleccionados
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
                                                    {area.get_nombre_area_display || area.nombre_area}
                                                </span>
                                            </div>
                                        )
                                    })}
                                </div>
                                {formData.areas_interes.length === 0 && (
                                    <div style={{ marginTop: '15px', padding: '10px', backgroundColor: '#fff7ed', borderRadius: '6px', borderLeft: '4px solid #f97316', fontSize: '0.85rem', color: '#9a3412', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <Info size={16} />
                                        <span>Sin áreas seleccionadas: este comunicado pasará a estado <strong>Borrador</strong>.</span>
                                    </div>
                                )}
                            </div>

                            {/* ACCIONES DEL FORMULARIO */}
                            <div className="form-actions-edicion" style={{ justifyContent: 'space-between', marginTop: '30px' }}>
                                
                                {/* Botón Borrar (Izquierda) */}
                                <button 
                                    type="button" 
                                    onClick={handleDelete} 
                                    disabled={deleting}
                                    style={{ 
                                        backgroundColor: '#fee2e2', 
                                        color: '#991b1b', 
                                        border: '1px solid #fca5a5', 
                                        padding: '10px 20px', 
                                        borderRadius: '6px', 
                                        cursor: 'pointer', 
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        gap: '8px',
                                        fontSize: '0.9rem',
                                        fontWeight: '500'
                                    }} 
                                >
                                    <Trash2 size={18} />
                                    {deleting ? "Eliminando..." : "Eliminar Comunicado"}
                                </button>

                                {/* Botones Guardar/Cancelar (Derecha) */}
                                <div style={{ display: 'flex', gap: '10px' }}>
                                    <button type="button" className="btn-cancel-edicion" onClick={() => navigate("/admin/comunicados")}>
                                        Cancelar
                                    </button>
                                    <button type="submit" className="btn-save-edicion" disabled={saving}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <Save size={18} />
                                            {saving ? "Guardando..." : "Guardar Cambios"}
                                        </div>
                                    </button>
                                </div>
                            </div>

                        </form>
                    </div>
                </div>
            </section>
        </div>
    );
}

export default AdminEdicionComunicado;