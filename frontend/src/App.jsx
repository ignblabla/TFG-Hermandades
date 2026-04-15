import react from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Login from "./pages/Login"
import Register from "./pages/Register"
import Home from "./pages/Home"
import Index from "./pages/Index"
import NotFound from "./pages/NotFound"
import CrearPuesto from "./pages/CrearPuesto"
import EditarActo from "./pages/EditarActo"
import EditarPuesto from "./pages/EditarPuesto"
import HazteHermano from "./pages/HazteHermano"
import HermanoCrearSolicitudCirio from "./pages/HermanoSolicitudCirio/HermanoCrearSolicitudCirio"
import AdminDashboard from "./pages/Admin/Dashboard"
import ValidarAcceso from "./pages/ValidarAcceso";
import AdminEditarHermano from "./pages/AdminEdicionHermano"
import MisPapeletas from "./pages/HermanoMisPapeletasDeSitio"
import AdminEdicionActo from "./pages/AdminEdicionActo"
import HermanoCrearSolicitudUnificada from "./pages/HermanoCrearSolicitudUnificada"
import AdminListadoComunicados from "./pages/AdminListadoComunicados"
import HermanoMuroNoticias from "./pages/HermanoMuroNoticias";
import NoticiasHermano from "./pages/NoticiasHermanos"
import HermanoConsultaNoticia from "./pages/HermanoConsultaNoticia"
import HermanoAreaInteres from "./pages/HermanoAreasInteres/HermanoAreasInteres"

import EditarMiPerfil from "./pages/HermanoEdicionDatos/HermanoEdicionDatos"
import AdminCreacionComunicado from "./pages/AdminCreacionComunicado/AdminCreacionComunicado"
import AdminEdicionComunicado from "./pages/AdminEdicionComunicado/AdminEdicionComunicado"
import AdminCrearActo from "./pages/AdminCreacionActo/AdminCrearActo"
import AdminEditarActo from "./pages/AdminEdicionActo/AdminEditarActo"

import AdminCrearPuesto from "./pages/AdminCrearPuesto"
import AdminEdicionPuesto from "./pages/AdminEdicionPuesto"
import ChatAsistente from "./pages/ChatAsistente"
import HermanoNewHome from "./pages/NewHome"
import HermanoListadoCuotas from "./pages/HermanoListadoCuotas"
import AdminCenso from "./pages/AdminCenso"
import HermanoSolicitudInsignia from "./pages/HermanoSolicitudInsignia/HermanoSolicitudInsignia"
import HermanoListadoActos from "./pages/HermanoListadoActos/HermanoListadoActos"
import GestionRepartoInsignias from "./pages/AdminGestionRepartoInsignias/AdminGestionRepartoInsignias"
import AdminListadoSolicitudesInsigniasActoConcreto from "./pages/AdminListadoSolicitudesInsigniasActoConcreto/AdminListadoSolicitudesInsigniasActoConcreto"
import HermanoConsultaActo from "./pages/HermanoConsultaActo/HermanoConsultaActo"
import ProtectedRoute from "./components/ProtectedRoute"

import EditMe from "./pages/EditMe"
import AdminConsultaActo from "./pages/AdminConsultaActo/AdminConsultaActo"
import GestionRepartoCirio from "./pages/AdminGestionRepartoCirios/AdminGestionRepartoCirios"


function Logout() {
  localStorage.clear()
  return <Navigate to="/login" />
}

function RegisterAndLogout() {
  localStorage.clear()
  return <Register />
}

function App() {

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/hazte-hermano" element={<HazteHermano />} />
        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route
          path="/editar-mi-perfil"
          element={
            <ProtectedRoute>
              <EditarMiPerfil />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/crear-comunicado"
          element={
            <ProtectedRoute>
              <AdminCreacionComunicado />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/editar-comunicado/:id"
          element={
            <ProtectedRoute>
              <AdminEdicionComunicado />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/crear-acto"
          element={
            <ProtectedRoute>
              <AdminCrearActo />
            </ProtectedRoute>
          }
        />


        <Route
          path="/areas-de-interes"
          element={
            <ProtectedRoute>
              <HermanoAreaInteres />
            </ProtectedRoute>
          }
        />


        
        <Route
          path="/noticias-hermano"
          element={
            <ProtectedRoute>
              <NoticiasHermano />
            </ProtectedRoute>
          }
        />
        <Route
          path="/comunicados/:id"
          element={
            <ProtectedRoute>
              <HermanoConsultaNoticia />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat-asistente"
          element={
            <ProtectedRoute>
              <ChatAsistente />
            </ProtectedRoute>
          }
        />
        <Route path="/validar-acceso/:id/:codigo" element={<ValidarAcceso />} />
        <Route
          path="admin/gestion-reparto-cirios/:id"
          element={
            <ProtectedRoute>
              <GestionRepartoCirio />
            </ProtectedRoute>
          }
        />
        <Route
          path="/panel-administracion" 
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/crear-puesto"
          element={
            <ProtectedRoute>
              <CrearPuesto />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/crear-puesto"
          element={
            <ProtectedRoute>
              <AdminCrearPuesto />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/editar-puesto/:id"
          element={
            <ProtectedRoute>
              <AdminEdicionPuesto />
            </ProtectedRoute>
          }
        />
        <Route
          path="/editar-puesto/:id"
          element={
            <ProtectedRoute>
              <EditarPuesto />
            </ProtectedRoute>
          }
        />
        <Route 
          path="/gestion/hermanos/:id" 
          element={
            <ProtectedRoute>
              <AdminEditarHermano />
            </ProtectedRoute>
          } 
        />
        <Route
          path="/admin/editar-acto/:id"
          element={
            <ProtectedRoute>
              <AdminEdicionActo />
            </ProtectedRoute>
          }
        />

        <Route
          path="editar-acto/:id"
          element={
            <ProtectedRoute>
              <AdminEditarActo />
            </ProtectedRoute>
          }
        />

        <Route
          path="/hermano/solicitar-insignias/:id"
          element={
            <ProtectedRoute>
              <HermanoSolicitudInsignia />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/comunicados"
          element={
            <ProtectedRoute>
              <AdminListadoComunicados />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mis-noticias"
          element={
            <ProtectedRoute>
              <HermanoMuroNoticias />
            </ProtectedRoute>
          }
        />
        <Route
          path="/solicitar-unificada" 
          element={
            <ProtectedRoute>
              <HermanoCrearSolicitudUnificada />
            </ProtectedRoute>
          }
        />

        <Route
          path="/hermano/solicitar-cirios/:id"
          element={
            <ProtectedRoute>
              <HermanoCrearSolicitudCirio />
            </ProtectedRoute>
          }
        />

        <Route
          path="/mis-papeletas-de-sitio"
          element={
            <ProtectedRoute>
              <MisPapeletas />
            </ProtectedRoute>
          }
        />
        <Route
          path="/new-home"
          element={
            <ProtectedRoute>
              <HermanoNewHome />
            </ProtectedRoute>
          }
        />
        <Route
          path="/listado-cuotas"
          element={
            <ProtectedRoute>
              <HermanoListadoCuotas />
            </ProtectedRoute>
          }
        />

        <Route
          path="/censo-hermanos"
          element={
            <ProtectedRoute>
              <AdminCenso />
            </ProtectedRoute>
          }
        />

        <Route
          path="/listado-actos"
          element={
            <ProtectedRoute>
              <HermanoListadoActos />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/acto/:id"
          element={
            <ProtectedRoute>
              <AdminConsultaActo />
            </ProtectedRoute>
          }
        />
        <Route
          path="/acto/:id"
          element={
            <ProtectedRoute>
              <HermanoConsultaActo />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/gestion-reparto-insignias/:id"
          element={
            <ProtectedRoute>
              <GestionRepartoInsignias />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/listado-solicitudes-insignias/:id"
          element={
            <ProtectedRoute>
              <AdminListadoSolicitudesInsigniasActoConcreto />
            </ProtectedRoute>
          }
        />

        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route path="/register" element={<RegisterAndLogout />} />
        <Route path="*" element={<NotFound />}></Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
