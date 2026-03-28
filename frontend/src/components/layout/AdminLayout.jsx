import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Package,
  ShoppingBag,
  Users,
  Star,
  Image,
  Truck,
  LogOut,
} from 'lucide-react'
import useAuthStore from '../../store/authStore'

const nav = [
  { to: '/admin',          label: 'Dashboard',  icon: LayoutDashboard, end: true },
  { to: '/admin/products', label: 'Products',   icon: Package },
  { to: '/admin/orders',   label: 'Orders',     icon: ShoppingBag },
  { to: '/admin/users',    label: 'Users',      icon: Users },
  { to: '/admin/reviews',  label: 'Reviews',    icon: Star },
  { to: '/admin/banners',  label: 'Banners',    icon: Image },
  { to: '/admin/shipping', label: 'Shipping',   icon: Truck },
]

export default function AdminLayout() {
  const { logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 border-r border-gray-200 bg-white">
        <div className="flex h-14 items-center px-5 border-b border-gray-100">
          <span className="font-bold text-brand-600">KYFF Admin</span>
        </div>

        <nav className="flex flex-col gap-0.5 p-3">
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition ${
                  isActive
                    ? 'bg-brand-50 text-brand-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-4 left-0 w-56 px-3">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-gray-500 transition hover:bg-red-50 hover:text-red-600"
          >
            <LogOut size={16} /> Log out
          </button>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
