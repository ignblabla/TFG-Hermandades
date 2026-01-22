import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api";
import { CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import "../styles/Home.css";

function ValidarAcceso() {
    const { id, codigo } = useParams();
    const navigate = useNavigate();
    
    const effectCalled = useRef(false); 

    const [estado, setEstado] = useState("cargando");
    const [mensaje, setMensaje] = useState("Verificando credenciales...");
    const [datos, setDatos] = useState(null);

    useEffect(() => {
        if (effectCalled.current) return;

        const validar = async () => {
            try {
                effectCalled.current = true; 

                const response = await api.post("api/control-acceso/validar/", {
                    id: id,
                    codigo: codigo
                });

                setEstado(response.data.resultado);
                setMensaje(response.data.mensaje);
                setDatos(response.data.datos);

            } catch (err) {
                console.error(err);
                
                setEstado("error");
                if (err.response && err.response.status === 401) {
                    setMensaje("Debes iniciar sesión como Diputado/Admin para validar.");
                    setTimeout(() => navigate("/login", { state: { from: `/validar-acceso/${id}/${codigo}` } }), 2000);
                } else {
                    setMensaje(err.response?.data?.error || "Error de conexión o código inválido.");
                }
            }
        };

        validar();

    }, [id, codigo, navigate]);

    return (
        <div className="validacion-container">
            <div className={`card-validacion ${estado}`}>
                
                {estado === "cargando" && <div className="spinner">Validando...</div>}

                {estado === "success" && (
                    <>
                        <CheckCircle size={80} color="white" />
                        <h1>ACCESO PERMITIDO</h1>
                    </>
                )}

                {estado === "warning" && (
                    <>
                        <AlertTriangle size={80} color="white" />
                        <h1>YA LEÍDA</h1>
                    </>
                )}

                {estado === "error" && (
                    <>
                        <XCircle size={80} color="white" />
                        <h1>ACCESO DENEGADO</h1>
                    </>
                )}

                <p className="mensaje-validacion">{mensaje}</p>

                {datos && (
                    <div className="datos-hermano">
                        <h3>{datos.nombre_hermano} {datos.apellidos_hermano}</h3>
                        <p className="puesto-grande">{datos.nombre_puesto}</p>
                        {datos.tramo_display && <p>{datos.tramo_display}</p>}
                        {datos.numero_papeleta && <p className="numero">Nº {datos.numero_papeleta}</p>}
                    </div>
                )}
                
                <button onClick={() => navigate("/home")} className="btn-salir">Salir</button>
            </div>
        </div>
    );
}

export default ValidarAcceso;