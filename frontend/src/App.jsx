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
import GestionReparto from "./pages/GestionReparto"
import HermanoCrearSolicitudInsignia from "./pages/HermanoCrearSolicitudInsignia"
import HermanoCrearSolicitudCirio from "./pages/HermanoCrearSolicitudCirio"
import GestionRepartoCirios from "./pages/GestiónRepartoCirios"
import AdminDashboard from "./pages/Admin/Dashboard"
// import MisPapeletas from "./pages/MisPapeletas"
import ValidarAcceso from "./pages/ValidarAcceso";
import AdminListadoHermanos from "./pages/AdminListadoHermanos"
import AdminEditarHermano from "./pages/AdminEdicionHermano"
import MisPapeletas from "./pages/HermanoMisPapeletasDeSitio"
import AdminCreacionActo from "./pages/AdminCreacionActo"
import AdminEdicionActo from "./pages/AdminEdicionActo"
import HermanoCrearSolicitudUnificada from "./pages/HermanoCrearSolicitudUnificada"
import AdminCreacionComunicado from "./pages/AdminCreacionComunicado"
import AdminListadoComunicados from "./pages/AdminListadoComunicados"
import AdminEdicionComunicado from "./pages/AdminEdicionComunicado";
import HermanoMuroNoticias from "./pages/HermanoMuroNoticias";
import NoticiasHermano from "./pages/NoticiasHermanos"
import HermanoConsultaNoticia from "./pages/HermanoConsultaNoticia"
import HermanoAreaInteres from "./pages/HermanoAreasInteres"
import EditarMiPerfil from "./pages/HermanoEdicionDatos"
import AdminCrearPuesto from "./pages/AdminCrearPuesto"
import AdminEdicionPuesto from "./pages/AdminEdicionPuesto"
import ProtectedRoute from "./components/ProtectedRoute"

// import CrearActo from "./pages/CrearActo"
import EditMe from "./pages/EditMe"


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
        {/* <Route
          path="/editar-perfil"
          element={
            <ProtectedRoute>
              <EditMe />
            </ProtectedRoute>
          }
        /> */}
        <Route
          path="/editar-mi-perfil"
          element={
            <ProtectedRoute>
              <EditarMiPerfil />
            </ProtectedRoute>
          }
        />
        <Route
          path="/interes-hermanos"
          element={
            <ProtectedRoute>
              <HermanoAreaInteres />
            </ProtectedRoute>
          }
        />
        {/* <Route
          path="/crear-acto"
          element={
            <ProtectedRoute>
              <CrearActo />
            </ProtectedRoute>
          }
        /> */}
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
        <Route path="/validar-acceso/:id/:codigo" element={<ValidarAcceso />} />
        {/* <Route
          path="/mis-papeletas"
          element={
            <ProtectedRoute>
              <MisPapeletas />
            </ProtectedRoute>
          }
        /> */}
        <Route
          path="/gestionar-reparto/:id"
          element={
            <ProtectedRoute>
              <GestionReparto />
            </ProtectedRoute>
          }
        />
        <Route
          path="/gestionar-reparto-cirios/:id"
          element={
            <ProtectedRoute>
              <GestionRepartoCirios />
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
          path="/censo"
          element={
            <ProtectedRoute>
              <AdminListadoHermanos />
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
          path="/admin/crear-acto"
          element={
            <ProtectedRoute>
              <AdminCreacionActo />
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
          path="/admin/crear-comunicado"
          element={
            <ProtectedRoute>
              <AdminCreacionComunicado />
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
          path="/admin/comunicados/:id"
          element={
            <ProtectedRoute>
              <AdminEdicionComunicado />
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
          path="/solicitar-insignia"
          element={
            <ProtectedRoute>
              <HermanoCrearSolicitudInsignia />
            </ProtectedRoute>
          }
        />
        <Route
          path="/solicitar-cirio" 
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
        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route path="/register" element={<RegisterAndLogout />} />
        <Route path="*" element={<NotFound />}></Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
