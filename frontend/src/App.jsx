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
import SolicitarPapeleta from "./pages/solicitarPapeleta"
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
        <Route
          path="/solicitar-papeleta"
          element={
            <ProtectedRoute>
              <SolicitarPapeleta />
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
