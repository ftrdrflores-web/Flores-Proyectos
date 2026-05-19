import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

const AppLayout = () => {
  return (
    <div className="min-h-screen bg-clan-dark">
      <Sidebar />
      <Topbar />
      <main
        className="pt-[60px] min-h-screen"
        style={{ marginLeft: 240 }}
      >
        <Outlet />
      </main>
    </div>
  )
}

export default AppLayout