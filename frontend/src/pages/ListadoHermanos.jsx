import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../styles/ListadoHermanos.css"; // Asegúrate de crear este archivo CSS
import logoEscudo from '../assets/escudo.png'; // Asegúrate de tener la ruta correcta
import { 
    ArrowLeft, 
    ChevronLeft, 
    ChevronRight, 
    Search,
    UserCheck,
    UserX,
    Users
} from "lucide-react";

function ListadoHermanos() {

    const [menuOpen, setMenuOpen] = useState(false);
    const [user, setUser] = useState({});
    
    // Estados para la gestión de datos
    const [hermanos, setHermanos] = useState([]);
    const [loading, setLoading] = useState(false);
    
    // Estados de paginación
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalRegistros, setTotalRegistros] = useState(0);
    const [nextUrl, setNextUrl] = useState(null);
    const [prevUrl, setPrevUrl] = useState(null);

    const navigate = useNavigate();

    // 1. Cargar datos del usuario logueado (Navbar)
    useEffect(() => {
        const usuarioGuardado = localStorage.getItem("user_data");
        if (usuarioGuardado) {
            setUser(JSON.parse(usuarioGuardado));
        }
    }, []);

    // 2. Cargar listado de hermanos (API)
    useEffect(() => {
        fetchHermanos(page);
    }, [page]); // Se ejecuta cada vez que cambia la página

    const fetchHermanos = async (pageNumber) => {
        const token = localStorage.getItem("access");

        if (!token) {
            navigate("/login");
            return;
        }

        setLoading(true);

        try {
            // Llamada al endpoint que creamos en el backend
            // Nota: backend espera ?page=X
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

    const handleLogout = () => {
        localStorage.removeItem("user_data");
        localStorage.removeItem("access");
        localStorage.removeItem("refresh");
        setUser(null);
        navigate("/");
    };

    const handleNext = () => {
        if (nextUrl) setPage(prev => prev + 1);
    };

    const handlePrev = () => {
        if (prevUrl) setPage(prev => prev - 1);
    };

    return (
        <div className="site-wrapper">
            {/* --- NAVBAR (Idéntica a tu ejemplo) --- */}
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
                    
                    <div className="nav-buttons-mobile">
                        {user ? (
                            <>
                                <button className="btn-outline">Hermano: {user.dni}</button>
                                <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                            </>
                        ) : (
                            <button className="btn-outline" onClick={() => navigate("/login")}>Acceso</button>
                        )}
                    </div>
                </ul>

                <div className="nav-buttons-desktop">
                    {user && (
                        <>
                            <button className="btn-outline">Hermano: {user.dni}</button>
                            <button className="btn-purple" onClick={handleLogout}>Cerrar Sesión</button>
                        </>
                    )}
                </div>
            </nav>

            {/* --- CONTENIDO PRINCIPAL --- */}
            <main className="main-container-area">
                <div className="card-container-listado"> {/* Clase CSS específica para tabla ancha */}
                    
                    <header className="content-header-area">
                        <div className="title-row-area">
                            <div style={{display:'flex', alignItems:'center', gap: '10px'}}>
                                <Users size={28} className="text-purple" />
                                <h1>Censo de Hermanos</h1>
                            </div>
                            <button className="btn-back-area" onClick={() => navigate("/")}>
                                <ArrowLeft size={16} /> Volver al Inicio
                            </button>
                        </div>
                        <p className="description-area">
                            Listado general de hermanos (Solo Administración). Total registros: <strong>{totalRegistros}</strong>
                        </p>
                    </header>

                    {/* --- TABLA DE DATOS --- */}
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
                                        <th>Estado</th>
                                        <th>Perfil</th>
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
                                                <td>
                                                    {hermano.estado_hermano === 'ALTA' ? (
                                                        <span className="status-badge success"><UserCheck size={14}/> Alta</span>
                                                    ) : (
                                                        <span className="status-badge error"><UserX size={14}/> Baja</span>
                                                    )}
                                                </td>
                                                <td>
                                                    {hermano.esAdmin && <span className="admin-tag">ADMIN</span>}
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="6" className="text-center">No se encontraron hermanos.</td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        )}
                    </div>

                    {/* --- PAGINACIÓN --- */}
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
            </main>
        </div>
    );
}

export default ListadoHermanos;