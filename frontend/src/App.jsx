import { Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom'
import useAuthStore from './store/authStore'

// Layout
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import AdminLayout from './components/layout/AdminLayout'

// Pages — lazy imports keep the initial bundle small
import { lazy, Suspense } from 'react'
import Spinner from './components/ui/Spinner'

const HomePage            = lazy(() => import('./pages/HomePage'))
const ProductListPage     = lazy(() => import('./pages/ProductListPage'))
const ProductDetailPage   = lazy(() => import('./pages/ProductDetailPage'))
const CartPage            = lazy(() => import('./pages/CartPage'))
const CheckoutPage        = lazy(() => import('./pages/CheckoutPage'))
const OrderConfirmPage    = lazy(() => import('./pages/OrderConfirmPage'))
const OrderHistoryPage    = lazy(() => import('./pages/OrderHistoryPage'))
const OrderDetailPage     = lazy(() => import('./pages/OrderDetailPage'))
const LoginPage           = lazy(() => import('./pages/LoginPage'))
const RegisterPage        = lazy(() => import('./pages/RegisterPage'))
const ProfilePage         = lazy(() => import('./pages/ProfilePage'))

const AdminDashboardPage  = lazy(() => import('./pages/admin/AdminDashboardPage'))
const AdminProductsPage   = lazy(() => import('./pages/admin/AdminProductsPage'))
const AdminOrdersPage     = lazy(() => import('./pages/admin/AdminOrdersPage'))
const AdminUsersPage      = lazy(() => import('./pages/admin/AdminUsersPage'))
const AdminReviewsPage    = lazy(() => import('./pages/admin/AdminReviewsPage'))
const AdminBannersPage    = lazy(() => import('./pages/admin/AdminBannersPage'))
const AdminShippingPage   = lazy(() => import('./pages/admin/AdminShippingPage'))

// ── Guards ────────────────────────────────────────────────────────────────────
function PrivateRoute({ children }) {
  const { isLoggedIn } = useAuthStore()
  const location = useLocation()
  if (!isLoggedIn) return <Navigate to="/login" state={{ from: location }} replace />
  return children
}

function AdminRoute({ children }) {
  const { isLoggedIn, user } = useAuthStore()
  const location = useLocation()
  if (!isLoggedIn) return <Navigate to="/login" state={{ from: location }} replace />
  if (!user?.is_admin) return <Navigate to="/" replace />
  return children
}

// ── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center"><Spinner size="lg" /></div>}>
      <Routes>
        {/* Public storefront */}
        <Route element={<><Navbar /><main className="min-h-screen"><Outlet /></main><Footer /></>}>
          <Route path="/"                element={<HomePage />} />
          <Route path="/products"        element={<ProductListPage />} />
          <Route path="/products/:slug"  element={<ProductDetailPage />} />
          <Route path="/cart"            element={<CartPage />} />
          <Route path="/login"           element={<LoginPage />} />
          <Route path="/register"        element={<RegisterPage />} />

          {/* Protected customer routes */}
          <Route path="/checkout"        element={<PrivateRoute><CheckoutPage /></PrivateRoute>} />
          <Route path="/orders"          element={<PrivateRoute><OrderHistoryPage /></PrivateRoute>} />
          <Route path="/orders/:orderNumber" element={<PrivateRoute><OrderDetailPage /></PrivateRoute>} />
          <Route path="/orders/confirm/:orderNumber" element={<PrivateRoute><OrderConfirmPage /></PrivateRoute>} />
          <Route path="/profile"         element={<PrivateRoute><ProfilePage /></PrivateRoute>} />
        </Route>

        {/* Admin panel */}
        <Route path="/admin" element={<AdminRoute><AdminLayout /></AdminRoute>}>
          <Route index                   element={<AdminDashboardPage />} />
          <Route path="products"         element={<AdminProductsPage />} />
          <Route path="orders"           element={<AdminOrdersPage />} />
          <Route path="users"            element={<AdminUsersPage />} />
          <Route path="reviews"          element={<AdminReviewsPage />} />
          <Route path="banners"          element={<AdminBannersPage />} />
          <Route path="shipping"         element={<AdminShippingPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}
