import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import SideBarMenu from "../../components/SideBarMenu";
import "../../styles/EditarHermanoAdmin.css";
import { ArrowLeft, Save, AlertTriangle } from "lucide-react";

function EditarHermanoAdmin() {
    const { id } = useParams();
    const navigate = useNavigate();

    // Estados de Layout
    const [isOpen, setIsOpen] = useState(false);
    const [currentUser, setCurrentUser] = useState({});

    // Estados del Formulario
    const [hermano, setHermano] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);

    // --- OPCIONES PARA SELECTS ---
    const estadosHermano = [
        { value: 'ALTA', label: 'Alta' },
        { value: 'BAJA', label: 'Baja' },
        { value: 'PENDIENTE_INGRESO', label: 'Pendiente de Ingreso' }
    ];

    const opcionesGenero = [
        { value: 'MASCULINO', label: 'Masculino' },
        { value: 'FEMENINO', label: 'Femenino' }
    ];

    const opcionesEstadoCivil = [
        { value: 'SOLTERO', label: 'Soltero/a' },
        { value: 'CASADO', label: 'Casado/a' },
        { value: 'SEPARADO', label: 'Separado/a' },
        { value: 'VIUDO', label: 'Viudo/a' }
    ];

    // --- CARGA INICIAL ---
    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");
        if (usuarioGuardado) {
            setCurrentUser(JSON.parse(usuarioGuardado));
        } else {
            navigate("/login");
        }
    }, [navigate]);

    // --- CARGAR DATOS DEL HERMANO ---
    useEffect(() => {
        const fetchHermano = async () => {
            const token = localStorage.getItem("access");
            try {
                const response = await fetch(`http://127.0.0.1:8000/api/hermanos/${id}/gestion/`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });

                if (response.ok) {
                    const data = await response.json();
                    setHermano(data);
                } else {
                    const err = await response.json();
                    setError(err.detail || "Error al cargar los datos. Verifica permisos.");
                }
            } catch (err) {
                setError("Error de conexión con el servidor.");
            } finally {
                setLoading(false);
            }
        };

        if (id) fetchHermano();
    }, [id]);

    // --- MANEJADORES ---
    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setHermano(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError(null);
        
        const token = localStorage.getItem("access");

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/hermanos/${id}/gestion/`, {
                method: "PATCH", 
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(hermano)
            });

            if (response.ok) {
                alert("Datos actualizados correctamente.");
                navigate("/admin/censo");
            } else {
                const errData = await response.json();
                const errorMsg = errData.non_field_errors?.[0] || JSON.stringify(errData);
                setError(errorMsg);
            }
        } catch (err) {
            setError("Error al guardar los cambios.");
        } finally {
            setSaving(false);
        }
    };

    const toggleSidebar = () => setIsOpen(!isOpen);
    const handleLogout = () => {
        localStorage.clear();
        navigate("/login");
    };

    if (loading) return <div className="loading-screen">Cargando datos...</div>;

    return (
        <div>
            <SideBarMenu isOpen={isOpen} toggleSidebar={toggleSidebar} user={currentUser} handleLogout={handleLogout}/>

            <section className="home-section-dashboard">
                <div className="text-dashboard">Edición de Hermano</div>

                <div style={{ padding: '0 20px 40px 20px' }}>
                    <div className="form-container-admin">
                        
                        <header className="form-header">
                            <button className="btn-back" onClick={() => navigate("/admin/censo")}>
                                <ArrowLeft size={18} /> Volver
                            </button>
                            <h2>{hermano?.nombre} {hermano?.primer_apellido}</h2>
                            <span className="dni-tag">{hermano?.dni}</span>
                        </header>

                        {error && (
                            <div className="error-banner">
                                <AlertTriangle size={20} />
                                <span>{error}</span>
                            </div>
                        )}

                        {hermano && (
                            <form onSubmit={handleSave} className="admin-form-grid">
                                
                                {/* SECCIÓN 1: Datos Administrativos */}
                                <div className="form-section full-width">
                                    <h3>Datos de Hermandad</h3>
                                    <div className="grid-2"> {/* Cambiado a grid-2 para acomodar mejor 4 campos */}
                                        <div className="form-group">
                                            <label>Nº Registro</label>
                                            <input 
                                                type="number" 
                                                name="numero_registro" 
                                                value={hermano.numero_registro || ''} 
                                                onChange={handleInputChange}
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Estado</label>
                                            <select 
                                                name="estado_hermano" 
                                                value={hermano.estado_hermano} 
                                                onChange={handleInputChange}
                                            >
                                                {estadosHermano.map(est => (
                                                    <option key={est.value} value={est.value}>{est.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label>Fecha Ingreso</label>
                                            <input 
                                                type="date" 
                                                name="fecha_ingreso_corporacion" 
                                                value={hermano.fecha_ingreso_corporacion || ''} 
                                                onChange={handleInputChange}
                                            />
                                        </div>
                                        {/* NUEVO CAMPO: Fecha de Baja */}
                                        <div className="form-group">
                                            <label>Fecha de Baja</label>
                                            <input 
                                                type="date" 
                                                name="fecha_baja_corporacion" 
                                                value={hermano.fecha_baja_corporacion || ''} 
                                                onChange={handleInputChange}
                                            />
                                        </div>
                                    </div>
                                    
                                    <div className="checkbox-group">
                                        <label>
                                            <input 
                                                type="checkbox" 
                                                name="esAdmin" 
                                                checked={hermano.esAdmin} 
                                                onChange={handleInputChange}
                                            />
                                            Conceder permisos de Administrador
                                        </label>
                                    </div>
                                </div>

                                {/* SECCIÓN 2: Datos Personales */}
                                <div className="form-section full-width">
                                    <h3>Datos Personales</h3>
                                    <div className="grid-2">
                                        <div className="form-group">
                                            <label>Nombre</label>
                                            <input type="text" name="nombre" value={hermano.nombre} onChange={handleInputChange} required />
                                        </div>
                                        <div className="form-group">
                                            <label>Apellidos</label>
                                            <div className="sub-grid">
                                                <input type="text" name="primer_apellido" placeholder="1º Apellido" value={hermano.primer_apellido} onChange={handleInputChange} required />
                                                <input type="text" name="segundo_apellido" placeholder="2º Apellido" value={hermano.segundo_apellido} onChange={handleInputChange} />
                                            </div>
                                        </div>
                                        <div className="form-group">
                                            <label>DNI</label>
                                            <input type="text" name="dni" value={hermano.dni} onChange={handleInputChange} required />
                                        </div>
                                        <div className="form-group">
                                            <label>Email</label>
                                            <input type="email" name="email" value={hermano.email} onChange={handleInputChange} />
                                        </div>
                                        <div className="form-group">
                                            <label>Teléfono</label>
                                            <input type="tel" name="telefono" value={hermano.telefono} onChange={handleInputChange} />
                                        </div>
                                        <div className="form-group">
                                            <label>Fecha Nacimiento</label>
                                            <input type="date" name="fecha_nacimiento" value={hermano.fecha_nacimiento || ''} onChange={handleInputChange} />
                                        </div>

                                        {/* NUEVOS CAMPOS: Género y Estado Civil */}
                                        <div className="form-group">
                                            <label>Género</label>
                                            <select name="genero" value={hermano.genero} onChange={handleInputChange}>
                                                {opcionesGenero.map(op => (
                                                    <option key={op.value} value={op.value}>{op.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                        <div className="form-group">
                                            <label>Estado Civil</label>
                                            <select name="estado_civil" value={hermano.estado_civil} onChange={handleInputChange}>
                                                {opcionesEstadoCivil.map(op => (
                                                    <option key={op.value} value={op.value}>{op.label}</option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>
                                </div>

                                {/* SECCIÓN 3: Domicilio */}
                                <div className="form-section full-width">
                                    <h3>Domicilio</h3>
                                    <div className="grid-2">
                                        <div className="form-group span-2">
                                            <label>Dirección</label>
                                            <input type="text" name="direccion" value={hermano.direccion || ''} onChange={handleInputChange} />
                                        </div>
                                        <div className="form-group">
                                            <label>Localidad</label>
                                            <input type="text" name="localidad" value={hermano.localidad || ''} onChange={handleInputChange} />
                                        </div>
                                        <div className="form-group">
                                            <label>Código Postal</label>
                                            <input type="text" name="codigo_postal" value={hermano.codigo_postal || ''} onChange={handleInputChange} />
                                        </div>
                                        <div className="form-group">
                                            <label>Provincia</label>
                                            <input type="text" name="provincia" value={hermano.provincia || ''} onChange={handleInputChange} />
                                        </div>
                                    </div>
                                </div>

                                {/* NUEVA SECCIÓN: Datos de Bautismo */}
                                <div className="form-section full-width">
                                    <h3>Datos Sacramentales (Bautismo)</h3>
                                    <div className="grid-2">
                                        <div className="form-group span-2">
                                            <label>Parroquia de Bautismo</label>
                                            <input 
                                                type="text" 
                                                name="parroquia_bautismo" 
                                                value={hermano.parroquia_bautismo || ''} 
                                                onChange={handleInputChange}
                                                placeholder="Ej: Parroquia de San Gonzalo"
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Lugar de Bautismo (Localidad)</label>
                                            <input 
                                                type="text" 
                                                name="lugar_bautismo" 
                                                value={hermano.lugar_bautismo || ''} 
                                                onChange={handleInputChange} 
                                            />
                                        </div>
                                        <div className="form-group">
                                            <label>Fecha de Bautismo</label>
                                            <input 
                                                type="date" 
                                                name="fecha_bautismo" 
                                                value={hermano.fecha_bautismo || ''} 
                                                onChange={handleInputChange} 
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Botón Guardar */}
                                <div className="form-actions">
                                    <button type="submit" className="btn-save" disabled={saving}>
                                        <Save size={18} /> {saving ? "Guardando..." : "Guardar Cambios"}
                                    </button>
                                </div>

                            </form>
                        )}
                    </div>
                </div>
            </section>
        </div>
    );
}

export default EditarHermanoAdmin;