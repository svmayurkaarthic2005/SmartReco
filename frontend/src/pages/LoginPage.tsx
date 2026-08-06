/**
 * Login Page — matches app light theme (indigo primary, white cards, gray-50 bg)
 */

import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
// No backend API auth — using Supabase Auth exclusively
import { useAuthStore } from '../store/authStore'
import { supabase } from '../lib/supabase'

// ── Eye toggle icon ──────────────────────────────────────────────────────────
const EyeIcon = ({ open }: { open: boolean }) =>
  open ? (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )

// ── Animated branding side pill ──────────────────────────────────────────────
const PersonaPill = ({ icon, label, delay, indent = 0 }: { icon: string; label: string; delay: string; indent?: number }) => (
  <div
    className="animate-float"
    style={{ animationDelay: delay, marginLeft: `${indent}px`, display: 'inline-block' }}
  >
    <div className="inline-flex items-center gap-3 bg-white/10 backdrop-blur-sm px-5 py-2.5 rounded-full border border-white/20 text-white font-medium text-sm">
      <span className="text-xl">{icon}</span>
      <span>{label}</span>
    </div>
  </div>
)

const LoginPage = () => {
  const navigate = useNavigate()
  const { login: storeLogin, setError } = useAuthStore()

  const [formData, setFormData] = useState({ email: '', password: '' })
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setErrorMessage('')
    try {
      // Supabase Auth — primary and only auth provider
      const { data: supaData, error: supaError } = await supabase.auth.signInWithPassword({
        email: formData.email,
        password: formData.password,
      })

      if (supaError) throw new Error(supaError.message)

      const token = supaData.session?.access_token || supaData.user?.id || 'sb-' + Date.now()
      const user = {
        id: supaData.user?.id || 'usr-' + Date.now(),
        name: supaData.user?.user_metadata?.name || formData.email.split('@')[0],
        email: formData.email,
        role: (supaData.user?.user_metadata?.role as string) || 'user',
      }

      storeLogin(token, user)
      navigate('/dashboard')
    } catch (error: any) {
      const message = error.message || 'Invalid email or password'
      setErrorMessage(message)
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">

      {/* ── Left: Branding panel ── */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-600 via-primary-700 to-indigo-900 relative overflow-hidden">
        {/* Grid overlay */}
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />
        {/* Decorative blobs */}
        <div className="absolute -top-24 -right-24 w-80 h-80 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-32 -left-16 w-96 h-96 bg-indigo-400/10 rounded-full blur-3xl" />

        <div className="relative z-10 flex flex-col justify-center px-14 text-white w-full">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-2xl">🎓</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">SmartReco</h1>
              <p className="text-primary-200 text-sm">AI-powered learning</p>
            </div>
          </div>

          <h2 className="text-4xl font-bold leading-tight mb-4">
            Continue your<br />learning journey
          </h2>
          <p className="text-primary-100 text-base leading-relaxed mb-10 max-w-xs">
            Sign in to access your personalized AI recommendations and pick up right where you left off.
          </p>

          {/* Animated persona pills */}
          <div className="space-y-3 mb-12">
            <PersonaPill icon="🧭" label="Explorer" delay="0s" />
            <div><PersonaPill icon="🎯" label="Focused Builder" delay="1.5s" indent={48} /></div>
            <div><PersonaPill icon="🚀" label="Career Switcher" delay="3s" indent={24} /></div>
            <div><PersonaPill icon="📈" label="Deep Diver" delay="4.5s" /></div>
          </div>

          {/* Feature checklist */}
          <div className="space-y-3">
            {['Personalized learning paths', 'AI-powered recommendations', 'Behavioral insights & analytics'].map(f => (
              <div key={f} className="flex items-center gap-3 text-primary-100 text-sm">
                <svg className="w-4 h-4 text-primary-300 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                {f}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Right: Login form ── */}
      <div className="flex-1 flex items-center justify-center px-6 py-12 bg-gray-50">
        <div className="w-full max-w-md animate-fade-in">

          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
              <span className="text-xl">🎓</span>
            </div>
            <span className="text-2xl font-bold text-gray-900">SmartReco</span>
          </div>

          {/* Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <div className="mb-7">
              <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
              <p className="mt-1.5 text-gray-500 text-sm">Sign in to your SmartReco account</p>
            </div>

            {/* Error */}
            {errorMessage && (
              <div className="mb-5 flex items-start gap-3 p-3.5 bg-red-50 border border-red-200 rounded-lg animate-slide-up">
                <svg className="w-4 h-4 text-red-500 mt-0.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-sm text-red-700">{errorMessage}</p>
              </div>
            )}

            <form id="login-form" onSubmit={handleSubmit} className="space-y-5">
              {/* Email */}
              <div>
                <label htmlFor="login-email" className="block text-sm font-medium text-gray-700 mb-1.5">
                  Email address
                </label>
                <input
                  id="login-email"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 text-sm
                             focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                             transition-all duration-200 bg-white"
                />
              </div>

              {/* Password */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label htmlFor="login-password" className="block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <a href="#" className="text-xs font-medium text-primary-600 hover:text-primary-700">
                    Forgot password?
                  </a>
                </div>
                <div className="relative">
                  <input
                    id="login-password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    autoComplete="current-password"
                    placeholder="Enter your password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-2.5 pr-11 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 text-sm
                               focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                               transition-all duration-200 bg-white"
                  />
                  <button
                    type="button"
                    id="login-toggle-password"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <EyeIcon open={showPassword} />
                  </button>
                </div>
              </div>

              {/* Remember me */}
              <label className="flex items-center gap-2.5 cursor-pointer select-none">
                <input
                  id="login-remember"
                  type="checkbox"
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500 cursor-pointer"
                />
                <span className="text-sm text-gray-600">Remember me for 30 days</span>
              </label>

              {/* Submit */}
              <button
                id="login-submit"
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center items-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm text-white
                           bg-primary-600 hover:bg-primary-700 active:bg-primary-800
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                           disabled:opacity-50 disabled:cursor-not-allowed
                           transition-all duration-200 shadow-sm hover:shadow-md"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Signing in…
                  </>
                ) : 'Sign in'}
              </button>
            </form>

            <p className="mt-6 text-center text-sm text-gray-500">
              Don't have an account?{' '}
              <Link to="/register" className="font-semibold text-primary-600 hover:text-primary-700">
                Create one free
              </Link>
            </p>
          </div>

          {/* Stats strip */}
          <div className="mt-6 flex justify-center gap-8 text-center">
            {[['10K+', 'Learners'], ['500+', 'Courses'], ['4.9★', 'Rating']].map(([n, l]) => (
              <div key={l}>
                <div className="text-base font-bold text-gray-800">{n}</div>
                <div className="text-xs text-gray-400">{l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
