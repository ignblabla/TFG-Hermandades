import { Navigate } from "react-router-dom";
import { jwtDecode } from "jwt-decode";
import api from "../api";
import { REFRESH_TOKEN, ACCESS_TOKEN } from "../constants";
import { useState, useEffect } from "react";

function ProtectedRoute({ children }) {
    const [isAuthorized, setIsAuthorized] = useState(null);

    useEffect(() => {
        // Añadimos un catch global por si auth() falla inesperadamente
        auth().catch(() => setIsAuthorized(false));
    }, []);

    const refreshUserToken = async () => { // Cambiado nombre para evitar conflicto
        const tokenRefresh = localStorage.getItem(REFRESH_TOKEN);
        if (!tokenRefresh) {
            setIsAuthorized(false);
            return;
        }

        try {
            // Asegúrate de que esta ruta sea correcta en tu backend
            const res = await api.post("/api/token/refresh/", {
                refresh: tokenRefresh,
            });

            if (res.status === 200) {
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                setIsAuthorized(true);
            } else {
                setIsAuthorized(false);
            }
        } catch (error) {
            console.error("Error refrescando token:", error);
            setIsAuthorized(false);
        }
    };

    const auth = async () => {
        const token = localStorage.getItem(ACCESS_TOKEN);
        
        if (!token) {
            setIsAuthorized(false);
            return;
        }

        try {
            const decoded = jwtDecode(token);
            const tokenExpiration = decoded.exp;
            const now = Date.now() / 1000;

            if (tokenExpiration < now) {
                await refreshUserToken();
            } else {
                setIsAuthorized(true);
            }
        } catch (error) {
            // Si el token es inválido (formato erróneo), forzamos logout
            console.error("Token inválido:", error);
            setIsAuthorized(false);
        }
    };

    if (isAuthorized === null) {
        // Sugerencia: Pon una clase para centrar esto o ver si se está renderizando
        return <div style={{color: 'black', padding: '20px'}}>Verificando sesión...</div>;
    }

    return isAuthorized ? children : <Navigate to="/login" replace />;
}

export default ProtectedRoute;