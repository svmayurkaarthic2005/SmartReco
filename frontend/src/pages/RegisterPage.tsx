/**
 * Register Page — matches app light theme (indigo primary, white cards, gray-50 bg)
 */

import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
// No backend API auth — using Supabase Auth exclusively
import { useAuthStore } from '../store/authStore'
import { supabase } from '../lib/supabase'

// ── Eye toggle ───────────────────────────────────────────────────────────────
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

// ── Password strength ────────────────────────────────────────────────────────
function getStrength(pw: string) {
  if (!pw) return { score: 0, label: '', color: '' }
  let s = 0
  if (pw.length >= 8) s++
  if (pw.length >= 12) s++
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) s++
  if (/\d/.test(pw)) s++
  if (/[^a-zA-Z\d]/.test(pw)) s++
  if (s <= 2) return { score: 1, label: 'Weak',   color: '#ef4444' }
  if (s <= 3) return { score: 2, label: 'Fair',   color: '#f59e0b' }
  if (s <= 4) return { score: 3, label: 'Good',   color: '#3b82f6' }
  return         { score: 4, label: 'Strong', color: '#22c55e' }
}

// ── Rule chip ────────────────────────────────────────────────────────────────
const RuleChip = ({ met, label }: { met: boolean; label: string }) => (
  <div className={`flex items-center gap-1.5 text-xs transition-colors duration-200 ${met ? 'text-green-600' : 'text-gray-400'}`}>
    <svg className="w-3 h-3 shrink-0" fill="currentColor" viewBox="0 0 20 20">
      {met
        ? <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        : <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm-1-5a1 1 0 112 0v-4a1 1 0 10-2 0v4zm1-8a1 1 0 100 2 1 1 0 000-2z" clipRule="evenodd" />
      }
    </svg>
    {label}
  </div>
)

// ── Stat card (branding panel) ───────────────────────────────────────────────
const StatCard = ({ n, l }: { n: string; l: string }) => (
  <div className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl p-4 text-center flex-1">
    <div className="text-2xl font-bold text-white">{n}</div>
    <div className="text-xs text-primary-200 mt-0.5">{l}</div>
  </div>
)

const RegisterPage = () => {
  const navigate = useNavigate()
  const { login: storeLogin, setError } = useAuthStore()

  const [formData, setFormData] = useState({ name: '', email: '', password: '', confirmPassword: '' })
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const [acceptedTerms, setAcceptedTerms] = useState(false)
  const [success, setSuccess] = useState(false)

  const strength = getStrength(formData.password)
  const rules = [
    { met: formData.password.length >= 8,             label: 'At least 8 characters' },
    { met: /[A-Z]/.test(formData.password),           label: 'One uppercase letter' },
    { met: /\d/.test(formData.password),              label: 'One number' },
    { met: /[^a-zA-Z\d]/.test(formData.password),    label: 'One special character' },
  ]
  const pwMatch = formData.password && formData.confirmPassword && formData.password === formData.confirmPassword

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (formData.password !== formData.confirmPassword) { setErrorMessage('Passwords do not match'); return }
    if (!acceptedTerms) { setErrorMessage('Please accept the Terms of Service to continue'); return }
    setIsLoading(true); setErrorMessage('')
    try {
      // Supabase Auth — primary and only auth provider
      const { data: supaData, error: supaError } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
        options: { data: { name: formData.name } }
      })

      if (supaError) throw new Error(supaError.message)

      const token = supaData.session?.access_token || supaData.user?.id || 'sb-' + Date.now()
      const user = {
        id: supaData.user?.id || 'usr-' + Date.now(),
        name: formData.name,
        email: formData.email,
        role: 'user',
      }

      storeLogin(token, user)
      setSuccess(true)
      setTimeout(() => navigate('/dashboard'), 900)
    } catch (error: any) {
      const message = error.message || 'Registration failed. Please try again.'
      setErrorMessage(message); setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">

      {/* ── Right: Branding panel (flipped: form left, branding right) ── */}
      <div className="hidden lg:flex lg:w-5/12 bg-gradient-to-bl from-primary-600 via-primary-700 to-indigo-900 relative overflow-hidden order-last">
        <div
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: 'linear-gradient(rgba(255,255,255,0.5) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.5) 1px,transparent 1px)',
            backgroundSize: '40px 40px',
          }}
        />
        <div className="absolute -top-20 -left-20 w-72 h-72 bg-white/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-28 -right-12 w-80 h-80 bg-indigo-400/10 rounded-full blur-3xl" />

        <div className="relative z-10 flex flex-col justify-center px-12 text-white w-full">
          <div className="flex items-center gap-3 mb-10">
            <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-2xl">🎓</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">SmartReco</h1>
              <p className="text-primary-200 text-sm">AI-powered learning</p>
            </div>
          </div>

          <h2 className="text-3xl font-bold leading-tight mb-3">
            Start your personalized<br />learning journey today
          </h2>
          <p className="text-primary-100 text-sm leading-relaxed mb-8 max-w-xs">
            Join thousands of learners accelerating their careers with AI-powered recommendations.
          </p>

          {/* Stats */}
          <div className="flex gap-3 mb-10">
            <StatCard n="10K+" l="Active Learners" />
            <StatCard n="500+" l="Courses" />
            <StatCard n="4.9★" l="Rating" />
          </div>

          {/* Feature list */}
          <div className="space-y-3">
            {[
              'Adaptive learning recommendations',
              'Track your learning progress',
              'Discover new learning paths',
              'AI-powered behavioral insights',
            ].map(f => (
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

      {/* ── Left: Registration form ── */}
      <div className="flex-1 flex items-center justify-center px-6 py-10 bg-gray-50 overflow-y-auto">
        <div className="w-full max-w-md animate-fade-in">

          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
              <span className="text-xl">🎓</span>
            </div>
            <span className="text-2xl font-bold text-gray-900">SmartReco</span>
          </div>

          {/* Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100 relative overflow-hidden">

            {/* Success overlay */}
            {success && (
              <div className="absolute inset-0 bg-white/95 flex flex-col items-center justify-center gap-4 z-10 rounded-2xl animate-fade-in">
                <div className="text-5xl animate-bounce">🎉</div>
                <div className="text-xl font-bold text-gray-900">Account created!</div>
                <div className="text-sm text-gray-500">Redirecting to your dashboard…</div>
                <div className="w-32 h-1 bg-primary-100 rounded-full overflow-hidden">
                  <div className="h-full bg-primary-600 rounded-full animate-slide-right" style={{ animation: 'growWidth 1.4s ease forwards' }} />
                </div>
                <style>{`@keyframes growWidth{from{width:0}to{width:100%}}`}</style>
              </div>
            )}

            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900">Create your account</h2>
              <p className="mt-1.5 text-gray-500 text-sm">Free forever · No credit card required</p>
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

            <form id="register-form" onSubmit={handleSubmit} className="space-y-4">

              {/* Full name */}
              <div>
                <label htmlFor="reg-name" className="block text-sm font-medium text-gray-700 mb-1.5">Full name</label>
                <input
                  id="reg-name" type="text" required autoComplete="name"
                  placeholder="Your full name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400
                             focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                             transition-all duration-200 bg-white"
                />
              </div>

              {/* Email */}
              <div>
                <label htmlFor="reg-email" className="block text-sm font-medium text-gray-700 mb-1.5">Email address</label>
                <input
                  id="reg-email" type="email" required autoComplete="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400
                             focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                             transition-all duration-200 bg-white"
                />
              </div>

              {/* Password */}
              <div>
                <label htmlFor="reg-password" className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
                <div className="relative">
                  <input
                    id="reg-password" type={showPassword ? 'text' : 'password'} required autoComplete="new-password"
                    placeholder="Create a strong password"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-2.5 pr-11 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400
                               focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
                               transition-all duration-200 bg-white"
                  />
                  <button type="button" id="reg-toggle-password" onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors">
                    <EyeIcon open={showPassword} />
                  </button>
                </div>

                {/* Strength bar + rules */}
                {formData.password && (
                  <div className="mt-2.5 space-y-2">
                    {/* Bar */}
                    <div className="flex items-center gap-2">
                      <div className="flex gap-1 flex-1">
                        {[1, 2, 3, 4].map(i => (
                          <div key={i} className="h-1.5 flex-1 rounded-full transition-all duration-300"
                            style={{ background: i <= strength.score ? strength.color : '#e5e7eb' }} />
                        ))}
                      </div>
                      <span className="text-xs font-medium w-10 text-right" style={{ color: strength.color }}>
                        {strength.label}
                      </span>
                    </div>
                    {/* Rules grid */}
                    <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                      {rules.map(r => <RuleChip key={r.label} met={r.met} label={r.label} />)}
                    </div>
                  </div>
                )}
              </div>

              {/* Confirm password */}
              <div>
                <label htmlFor="reg-confirm" className="block text-sm font-medium text-gray-700 mb-1.5">Confirm password</label>
                <div className="relative">
                  <input
                    id="reg-confirm" type={showConfirm ? 'text' : 'password'} required autoComplete="new-password"
                    placeholder="Repeat your password"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    className={`w-full px-4 py-2.5 pr-11 border rounded-lg text-sm text-gray-900 placeholder-gray-400
                               focus:outline-none focus:ring-2 focus:border-transparent transition-all duration-200 bg-white
                               ${formData.confirmPassword
                                  ? pwMatch
                                    ? 'border-green-400 focus:ring-green-400'
                                    : 'border-red-300 focus:ring-red-400'
                                  : 'border-gray-300 focus:ring-primary-500'}`}
                  />
                  <button type="button" id="reg-toggle-confirm" onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors">
                    <EyeIcon open={showConfirm} />
                  </button>
                </div>
                {formData.confirmPassword && (
                  <p className={`mt-1 text-xs ${pwMatch ? 'text-green-600' : 'text-red-500'}`}>
                    {pwMatch ? '✓ Passwords match' : 'Passwords do not match'}
                  </p>
                )}
              </div>

              {/* Terms */}
              <label className="flex items-start gap-2.5 cursor-pointer select-none pt-1">
                <input
                  id="reg-terms" type="checkbox" required
                  checked={acceptedTerms}
                  onChange={(e) => setAcceptedTerms(e.target.checked)}
                  className="w-4 h-4 mt-0.5 text-primary-600 border-gray-300 rounded focus:ring-primary-500 cursor-pointer"
                />
                <span className="text-sm text-gray-600 leading-relaxed">
                  I agree to the{' '}
                  <a href="#" className="font-medium text-primary-600 hover:text-primary-700">Terms of Service</a>
                  {' '}and{' '}
                  <a href="#" className="font-medium text-primary-600 hover:text-primary-700">Privacy Policy</a>
                </span>
              </label>

              {/* Submit */}
              <button
                id="register-submit"
                type="submit"
                disabled={isLoading || !acceptedTerms}
                className="w-full flex justify-center items-center gap-2 px-6 py-3 rounded-lg font-semibold text-sm text-white
                           bg-primary-600 hover:bg-primary-700 active:bg-primary-800
                           focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                           disabled:opacity-50 disabled:cursor-not-allowed
                           transition-all duration-200 shadow-sm hover:shadow-md mt-1"
              >
                {isLoading ? (
                  <>
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Creating account…
                  </>
                ) : 'Create free account'}
              </button>
            </form>

            <p className="mt-5 text-center text-sm text-gray-500">
              Already have an account?{' '}
              <Link to="/login" className="font-semibold text-primary-600 hover:text-primary-700">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
