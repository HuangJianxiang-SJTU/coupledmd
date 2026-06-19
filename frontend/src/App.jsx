import { useState } from 'react'
import './index.css'
import Home from './pages/Home'
import Systems from './pages/Systems'
import SystemDetail from './pages/SystemDetail'
import AtlasBrowser from './pages/AtlasBrowser'

function parseRoute() {
  const hash = window.location.hash.replace('#', '') || '/'
  if (hash.startsWith('/systems/')) return { page: 'system', id: hash.split('/')[2] }
  if (hash === '/systems') return { page: 'systems' }
  if (hash === '/atlas') return { page: 'atlas' }
  return { page: 'home' }
}

export default function App() {
  const [route, setRoute] = useState(parseRoute)

  function navigate(path) {
    window.location.hash = path
    if (path.startsWith('/systems/')) setRoute({ page: 'system', id: path.split('/')[2] })
    else if (path === '/systems') setRoute({ page: 'systems' })
    else if (path === '/atlas') setRoute({ page: 'atlas' })
    else setRoute({ page: 'home' })
  }

  return (
    <>
      <div className="topbar">
        <div className="topbar-inner">
          <span className="brand" style={{ cursor: 'pointer' }} onClick={() => navigate('/')}>
            Coupled<span>MD</span>
          </span>
          <nav>
            <a href="#/systems" onClick={e => { e.preventDefault(); navigate('/systems') }}>Systems</a>
            <a href="#/atlas" onClick={e => { e.preventDefault(); navigate('/atlas') }}>Atlas</a>
            <a href="/api/docs" target="_blank" rel="noreferrer">API</a>
          </nav>
        </div>
      </div>

      {route.page === 'home'   && <Home navigate={navigate} />}
      {route.page === 'systems' && <Systems navigate={navigate} />}
      {route.page === 'system'  && <SystemDetail id={route.id} navigate={navigate} />}
      {route.page === 'atlas'   && <AtlasBrowser navigate={navigate} />}
    </>
  )
}
