import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Subscribers from './pages/Subscribers'
import SubscriberDetail from './pages/SubscriberDetail'
import Payments from './pages/Payments'
import Risk from './pages/Risk'
import BulkUpdate from './pages/BulkUpdate'
import Settings from './pages/Settings'
import { useToast } from './lib/ToastContext'
import { registerToast } from './lib/api'

export default function App() {
  const { addToast } = useToast()

  useEffect(() => {
    registerToast(addToast)
  }, [addToast])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="subscribers" element={<Subscribers />} />
            <Route path="subscribers/:accId" element={<SubscriberDetail />} />
            <Route path="payments" element={<Payments />} />
            <Route path="risk" element={<Risk />} />
            <Route path="bulk-update" element={<BulkUpdate />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
