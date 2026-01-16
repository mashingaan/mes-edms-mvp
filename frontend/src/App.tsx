import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/Auth/ProtectedRoute'
import { AppLayout } from './components/Layout/AppLayout'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { ItemDetailPage } from './pages/ItemDetailPage'
import { UsersPage } from './pages/UsersPage'
import { AuditLogPage } from './pages/AuditLogPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { TechPage } from './pages/TechPage'
import { TechProjectSectionsPage } from './pages/TechProjectSectionsPage'
import { TechSectionDocumentsPage } from './pages/TechSectionDocumentsPage'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/projects" element={<ProjectsPage />} />
              <Route path="/projects/:id" element={<ProjectDetailPage />} />
              <Route path="/items/:id" element={<ItemDetailPage />} />
              <Route path="/users" element={<UsersPage />} />
              <Route path="/audit" element={<AuditLogPage />} />
              <Route path="/tech" element={<TechPage />} />
              <Route path="/tech/projects/:projectId/sections" element={<TechProjectSectionsPage />} />
              <Route path="/tech/sections/:sectionId/documents" element={<TechSectionDocumentsPage />} />
              <Route path="/procurement" element={<PlaceholderPage title="Закупка" />} />
              <Route path="/production" element={<PlaceholderPage title="Производство" />} />
              <Route path="/qc" element={<PlaceholderPage title="ОТК" />} />
              <Route path="/shipping" element={<PlaceholderPage title="Отгрузка" />} />
            </Route>
          </Route>
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App

