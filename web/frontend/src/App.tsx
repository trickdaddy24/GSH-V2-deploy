import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Subscribers from './pages/Subscribers'
import SubscriberDetail from './pages/SubscriberDetail'
import Payments from './pages/Payments'
import Risk from './pages/Risk'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="subscribers" element={<Subscribers />} />
          <Route path="subscribers/:accId" element={<SubscriberDetail />} />
          <Route path="payments" element={<Payments />} />
          <Route path="risk" element={<Risk />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
