import react from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Login from "./pages/Login"
import Register from "./pages/Register"
import Home from "./pages/Home"
import Index from "./pages/Index"
import NotFound from "./pages/NotFound"
import EditMe from "./pages/EditMe"
import AreaInteres from "./pages/AreasInteres"
import CrearActo from "./pages/CrearActo"
import CrearPuesto from "./pages/CrearPuesto"
import EditarActo from "./pages/EditarActo"
import EditarPuesto from "./pages/EditarPuesto"
import HazteHermano from "./pages/HazteHermano"
import GestionReparto from "./pages/GestionReparto"
import CrearSolicitudInsignia from "./pages/CrearSolicitudInsignia"
import SolicitarCirio from "./pages/SolicitarCirio"
import GestionRepartoCirios from "./pages/GestiónRepartoCirios"
import AdminDashboard from "./pages/Admin/Dashboard"
import MisPapeletas from "./pages/MisPapeletas"
import ValidarAcceso from "./pages/ValidarAcceso";
import ProtectedRoute from "./components/ProtectedRoute"

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
          path="/editar-perfil"
          element={
            <ProtectedRoute>
              <EditMe />
            </ProtectedRoute>
          }
        />
        <Route
          path="/areas-interes"
          element={
            <ProtectedRoute>
              <AreaInteres />
            </ProtectedRoute>
          }
        />
        <Route
          path="/crear-acto"
          element={
            <ProtectedRoute>
              <CrearActo />
            </ProtectedRoute>
          }
        />
        <Route path="/validar-acceso/:id/:codigo" element={<ValidarAcceso />} />
        <Route
          path="/mis-papeletas"
          element={
            <ProtectedRoute>
              <MisPapeletas />
            </ProtectedRoute>
          }
        />
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
          path="/solicitar-insignia"
          element={
            <ProtectedRoute>
              <CrearSolicitudInsignia />
            </ProtectedRoute>
          }
        />
        <Route
          path="/solicitar-cirio" 
          element={
            <ProtectedRoute>
              <SolicitarCirio />
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
          path="/editar-acto/:id"
          element={
            <ProtectedRoute>
              <EditarActo />
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
        <Route path="/login" element={<Login />} />
        <Route path="/logout" element={<Logout />} />
        <Route path="/register" element={<RegisterAndLogout />} />
        <Route path="*" element={<NotFound />}></Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
