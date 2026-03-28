import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-white mt-16">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          <div className="col-span-2 md:col-span-1">
            <span className="text-lg font-bold text-brand-600">KYFF Store</span>
            <p className="mt-2 text-sm text-gray-500">Fresh organic food, delivered to your door.</p>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Shop</h3>
            <ul className="mt-3 space-y-2 text-sm text-gray-600">
              <li><Link to="/products" className="hover:text-brand-600 transition">All Products</Link></li>
              <li><Link to="/products?category=fruits" className="hover:text-brand-600 transition">Fruits</Link></li>
              <li><Link to="/products?category=vegetables" className="hover:text-brand-600 transition">Vegetables</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Account</h3>
            <ul className="mt-3 space-y-2 text-sm text-gray-600">
              <li><Link to="/login" className="hover:text-brand-600 transition">Log In</Link></li>
              <li><Link to="/register" className="hover:text-brand-600 transition">Sign Up</Link></li>
              <li><Link to="/orders" className="hover:text-brand-600 transition">My Orders</Link></li>
              <li><Link to="/profile" className="hover:text-brand-600 transition">Profile</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500">Help</h3>
            <ul className="mt-3 space-y-2 text-sm text-gray-600">
              <li><span className="cursor-default">FAQ</span></li>
              <li><span className="cursor-default">Shipping Policy</span></li>
              <li><span className="cursor-default">Returns</span></li>
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-gray-100 pt-6 text-center text-xs text-gray-400">
          &copy; {new Date().getFullYear()} KYFF Store. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
