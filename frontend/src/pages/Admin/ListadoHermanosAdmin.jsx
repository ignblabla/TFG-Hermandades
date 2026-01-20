import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../../styles/ListadoHermanos.css";
import SideBarMenu from "../../components/SideBarMenu";

import { 
    ChevronLeft, 
    ChevronRight, 
    UserCheck,
    UserX,
    Users
} from "lucide-react";

function ListadoHermanos() {

    // --- ESTADOS DEL LAYOUT (SIDEBAR) ---
    const [isOpen, setIsOpen] = useState(false);
    const [user, setUser] = useState({});

    // --- ESTADOS DE DATOS (TABLA) ---
    const [hermanos, setHermanos] = useState([]);
    const [loading, setLoading] = useState(false);
    
    // --- ESTADOS DE PAGINACIÓN ---
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalRegistros, setTotalRegistros] = useState(0);
    const [nextUrl, setNextUrl] = useState(null);
    const [prevUrl, setPrevUrl] = useState(null);

    const navigate = useNavigate();

    // 1. Cargar Usuario (Misma lógica que Dashboard)
    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");
        if (usuarioGuardado) {
            setUser(JSON.parse(usuarioGuardado));
        } else {
            navigate("/login");
        }
    }, [navigate]);

    // 2. Cargar Datos de la API
    useEffect(() => {
        fetchHermanos(page);
    }, [page]);

    const fetchHermanos = async (pageNumber) => {
        const token = localStorage.getItem("access");

        if (!token) {
            navigate("/login");
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(`http://127.0.0.1:8000/api/hermanos/listado/?page=${pageNumber}`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                
                setHermanos(data.results);
                setTotalRegistros(data.count);
                setNextUrl(data.next);
                setPrevUrl(data.previous);

                const pageSize = 20; 
                setTotalPages(Math.ceil(data.count / pageSize));

            } else {
                if (response.status === 403) {
                    alert("No tienes permisos de Administrador para ver esta sección.");
                    navigate("/");
                } else if (response.status === 401) {
                    handleLogout();
                } else {
                    console.error("Error al obtener listado");
                }
            }
        } catch (error) {
            console.error("Error de red:", error);
        } finally {
            setLoading(false);
        }
    };

    // --- MANEJADORES ---
    const toggleSidebar = () => {
        setIsOpen(!isOpen);
    };

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        setUser(null);
        navigate("/login");
    };

    const handleNext = () => {
        if (nextUrl) setPage(prev => prev + 1);
    };

    const handlePrev = () => {
        if (prevUrl) setPage(prev => prev - 1);
    };

    return (
        <div>
            <SideBarMenu isOpen={isOpen} toggleSidebar={toggleSidebar} user={user} handleLogout={handleLogout}/>

            <section className="home-section-dashboard">
                
                <div className="text-dashboard">Gestión de Usuarios</div>

                <div style={{ padding: '0 20px 40px 20px' }}>
                    
                    <div className="card-container-listado" style={{ margin: '0', maxWidth: '100%' }}>
                        
                        <header className="content-header-area">
                            <div className="title-row-area">
                                <div style={{display:'flex', alignItems:'center', gap: '10px'}}>
                                    <Users size={28} className="text-purple" />
                                    <h2>Censo de Hermanos</h2>
                                </div>
                            </div>
                            <p className="description-area">
                                Total registros encontrados: <strong>{totalRegistros}</strong>
                            </p>
                        </header>

                        <div className="table-responsive">
                            {loading ? (
                                <div className="loading-state">Cargando censo...</div>
                            ) : (
                                <table className="hermanos-table">
                                    <thead>
                                        <tr>
                                            <th>Nº Reg.</th>
                                            <th>DNI</th>
                                            <th>Apellidos y Nombre</th>
                                            <th>Teléfono</th>
                                            <th>Dirección</th>
                                            <th>F. Nacimiento</th>
                                            <th>Antigüedad</th> 
                                            <th>Estado</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {hermanos.length > 0 ? (
                                            hermanos.map((hermano) => (
                                                <tr key={hermano.id}>
                                                    <td><span className="badge-reg">{hermano.numero_registro || "-"}</span></td>
                                                    <td>{hermano.dni}</td>
                                                    <td className="fw-bold">
                                                        {hermano.primer_apellido} {hermano.segundo_apellido}, {hermano.nombre}
                                                    </td>
                                                    <td>{hermano.telefono}</td>

                                                    <td>{hermano.direccion || "-"}</td>
                                                    
                                                    <td>
                                                        {hermano.fecha_nacimiento 
                                                            ? new Date(hermano.fecha_nacimiento).toLocaleDateString() 
                                                            : "-"}
                                                    </td>
                                                    <td>
                                                        {hermano.fecha_ingreso_corporacion 
                                                            ? new Date(hermano.fecha_ingreso_corporacion).toLocaleDateString() 
                                                            : "-"}
                                                    </td>

                                                    <td>
                                                        {hermano.estado_hermano === 'ALTA' ? (
                                                            <span className="status-badge success"><UserCheck size={14}/> Alta</span>
                                                        ) : (
                                                            <span className="status-badge error"><UserX size={14}/> Baja</span>
                                                        )}
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan="8" className="text-center">No se encontraron hermanos.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            )}
                        </div>

                        <footer className="pagination-footer">
                            <span className="page-info">
                                Página {page} de {totalPages}
                            </span>
                            <div className="pagination-controls">
                                <button 
                                    className="btn-pagination" 
                                    onClick={handlePrev} 
                                    disabled={!prevUrl || loading}
                                >
                                    <ChevronLeft size={16} /> Anterior
                                </button>
                                
                                <button 
                                    className="btn-pagination" 
                                    onClick={handleNext} 
                                    disabled={!nextUrl || loading}
                                >
                                    Siguiente <ChevronRight size={16} />
                                </button>
                            </div>
                        </footer>

                    </div>
                </div>
            </section>
        </div>
    );
}

export default ListadoHermanos;