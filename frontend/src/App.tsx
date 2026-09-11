import { Routes, Route, Navigate } from 'react-router-dom'

import SiteNav from './components/layout/SiteNav'
import SiteFooter from './components/layout/SiteFooter'
import RacesPage from './pages/RacesPage'
import HowItWorksPage from './pages/HowItWorksPage'
import AboutPage from './pages/AboutPage'

export default function App() {
  return (
    <div className="min-h-screen bg-bg flex flex-col">
      <SiteNav />

      <main className="flex-1">
        <Routes>
          <Route path="/" element={<RacesPage />} />
          <Route path="/how-it-works" element={<HowItWorksPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <SiteFooter />
    </div>
  )
}
