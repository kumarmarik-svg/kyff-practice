import { Link, useNavigate } from 'react-router-dom'
import { ShoppingCart, User, LogOut, LayoutDashboard, Menu, X } from 'lucide-react'
import { useState } from 'react'
import useAuthStore from '../../store/authStore'
import useCartStore from '../../store/cartStore'

export default function Navbar() {
  const { isLoggedIn, user, logout } = useAuthStore()
  const { itemCount } = useCartStore()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        {/* Brand */}
        <Link to="/" className="text-xl font-bold text-brand-600 tracking-tight">
          KYFF Store
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-6 md:flex">
          <Link to="/products" className="text-sm text-gray-600 hover:text-brand-600 transition">Shop</Link>

          {/* Cart */}
          <Link to="/cart" className="relative text-gray-600 hover:text-brand-600 transition">
            <ShoppingCart size={20} />
            {itemCount > 0 && (
              <span className="absolute -right-2 -top-2 flex h-4 w-4 items-center justify-center rounded-full bg-brand-500 text-[10px] font-bold text-white">
                {itemCount > 99 ? '99+' : itemCount}
              </span>
            )}
          </Link>

          {/* Auth */}
          {isLoggedIn ? (
            <div className="flex items-center gap-3">
              {user?.is_admin && (
                <Link to="/admin" className="flex items-center gap-1 text-sm text-gray-600 hover:text-brand-600 transition">
                  <LayoutDashboard size={16} /> Admin
                </Link>
              )}
              <Link to="/profile" className="flex items-center gap-1 text-sm text-gray-600 hover:text-brand-600 transition">
                <User size={16} /> {user?.first_name ?? 'Account'}
              </Link>
              <button onClick={handleLogout} className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-600 transition">
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login" className="btn-secondary text-xs px-3 py-1.5">Log in</Link>
              <Link to="/register" className="btn-primary text-xs px-3 py-1.5">Sign up</Link>
            </div>
          )}
        </nav>

        {/* Mobile toggle */}
        <button className="md:hidden text-gray-600" onClick={() => setMobileOpen((v) => !v)}>
          {mobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="border-t border-gray-100 bg-white px-4 pb-4 md:hidden">
          <Link to="/products" className="block py-2 text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Shop</Link>
          <Link to="/cart" className="block py-2 text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Cart {itemCount > 0 && `(${itemCount})`}</Link>
          {isLoggedIn ? (
            <>
              {user?.is_admin && <Link to="/admin" className="block py-2 text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Admin</Link>}
              <Link to="/profile" className="block py-2 text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Profile</Link>
              <button onClick={() => { handleLogout(); setMobileOpen(false) }} className="block w-full py-2 text-left text-sm text-red-600">Log out</button>
            </>
          ) : (
            <>
              <Link to="/login" className="block py-2 text-sm text-gray-700" onClick={() => setMobileOpen(false)}>Log in</Link>
              <Link to="/register" className="block py-2 text-sm text-brand-600 font-medium" onClick={() => setMobileOpen(false)}>Sign up</Link>
            </>
          )}
        </div>
      )}
    </header>
  )
}
