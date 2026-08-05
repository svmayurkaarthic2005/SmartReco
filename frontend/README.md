# SmartReco Frontend

Modern React + TypeScript frontend for the SmartReco Behavioral AI Recommendation Platform.

## 🏗️ Tech Stack

- **Framework**: React 18 + Vite 5
- **Language**: TypeScript
- **Styling**: Tailwind CSS 3
- **State Management**: Zustand
- **Data Fetching**: TanStack React Query (React Query v5)
- **Routing**: React Router v6
- **Icons**: Lucide React
- **Charts**: Recharts
- **HTTP Client**: Axios

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and endpoint functions
│   │   ├── client.ts     # Axios instance with interceptors
│   │   ├── auth.ts       # Authentication endpoints
│   │   ├── admin.ts      # Admin panel endpoints
│   │   ├── recommendations.ts  # Recommendation endpoints
│   │   └── tracking.ts   # Event tracking endpoints
│   │
│   ├── components/       # Reusable components
│   │   ├── layout/       # Layout components (ProtectedRoute, AdminRoute)
│   │   └── tracking/     # Event tracking components (ScrollTracker, etc.)
│   │
│   ├── context/          # React contexts
│   │   └── ToastContext.tsx  # Toast notifications
│   │
│   ├── hooks/            # Custom React hooks
│   │   ├── useRecommendations.ts
│   │   └── useTracker.ts
│   │
│   ├── pages/            # Page components
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── CoursesPage.tsx
│   │   ├── CourseDetailPage.tsx
│   │   ├── ActivityPage.tsx
│   │   └── admin/
│   │       ├── AdminLayout.tsx
│   │       ├── AdminDashboardPage.tsx
│   │       ├── AdminProductsPage.tsx
│   │       ├── AdminUsersPage.tsx
│   │       └── AdminTracesPage.tsx
│   │
│   ├── store/            # Zustand stores
│   │   └── authStore.ts  # Authentication state
│   │
│   ├── types/            # TypeScript type definitions
│   │   ├── auth.ts
│   │   ├── admin.ts
│   │   ├── recommendation.ts
│   │   └── tracking.ts
│   │
│   ├── App.tsx           # Main app with routing
│   ├── main.tsx          # App entry point
│   └── index.css         # Global styles + Tailwind
│
├── public/               # Static assets
├── index.html           # HTML template
├── package.json         # Dependencies
├── tsconfig.json        # TypeScript config
├── vite.config.ts       # Vite config
└── tailwind.config.js   # Tailwind config
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Navigate to frontend directory
cd smartreco/frontend

# Install dependencies
npm install

# Install additional required packages (if not already in package.json)
npm install recharts lucide-react @tanstack/react-query
```

### Environment Variables

Create `.env` file in `smartreco/frontend/`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Development

```bash
# Start dev server (hot reload enabled)
npm run dev

# Server runs on http://localhost:5173
```

### Build

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

## 🎨 Key Features

### Authentication
- **JWT-based auth** with localStorage persistence
- **Split-screen design**: Gradient background with animated persona pills
- **Floating labels** for inputs
- **Password strength indicator** on registration
- **Auto-redirect** on 401 responses

### User Dashboard
- **Persona Card**: Full-width banner with persona-specific gradients and confidence arc
- **AI Learning Story**: Personalized narrative with learning goals
- **Learning Roadmap**: Horizontal scrollable stepper showing course progression
- **Course Grid**: 3-column responsive grid with:
  - AI explanations per product
  - 6-factor score breakdown tooltip
  - Difficulty badges
  - Match percentage bars
- **Refresh Recommendations**: Manual refresh with spinner

### Admin Panel (Dark Theme)
- **Dashboard**: 
  - 6 stat cards (users, events, recommendations, AI calls, risks, failures)
  - Recharts PieChart for persona distribution
  - AreaChart for 24h event volume
  - Recent recommendations table
  - Embedding status summary with retry button
  
- **Products Management**:
  - Search + multi-filter (category, difficulty, status)
  - Full CRUD with slide-in drawer form
  - Re-embed individual products
  - Retry all failed embeddings
  - Optimistic updates via React Query
  
- **Users Management**:
  - User table with search/filter
  - Role management (user/admin)
  - Activity tracking (last seen, event count)
  
- **Traces Viewer**:
  - LangSmith trace logs
  - Expandable rows showing input/output
  - Status badges, latency, token usage
  - Auto-refresh every 30s

### Event Tracking
- **Automatic tracking** via custom hooks:
  - `useTracker`: Buffered event batching (20 events or 10s)
  - `ScrollTracker`: Milestone-based scroll depth (25%, 50%, 75%, 100%)
  - `TimeOnPageTracker`: Time spent tracking
- **12 event types**: view_product, search, enroll, add_to_cart, wishlist, scroll, time_on_page, filter_applied, recommendation_clicked, course_completed, video_watched, review_submitted

## 🎨 Design System

### Colors (Tailwind Classes)
- **Primary**: `primary-{50-900}` (Indigo)
- **Personas**:
  - Explorer: `indigo-500` to `purple-600`
  - Focused Builder: `emerald-500` to `teal-600`
  - Career Switcher: `amber-500` to `orange-500`
  - Price Sensitive: `orange-500` to `red-500`
  - Overwhelmed Learner: `rose-500` to `pink-600`
  - Drop-off Risk: `red-600` to `red-800`

### Components
- **Buttons**: Rounded-lg with hover states
- **Cards**: Shadow-lg with rounded-xl
- **Inputs**: Focus ring-2 ring-primary-500
- **Badges**: Rounded-full with semantic colors
- **Toasts**: Fixed top-right, 3s auto-dismiss

## 🔧 Configuration

### Tailwind (tailwind.config.js)
```js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          // Custom primary color palette
        }
      }
    }
  }
}
```

### Vite (vite.config.ts)
```ts
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'  // Optional proxy
    }
  }
})
```

## 🧪 Testing

```bash
# Run tests (when configured)
npm test

# Run with coverage
npm run test:coverage
```

## 📝 API Integration

All API calls go through `src/api/client.ts` with:
- **Base URL**: From `VITE_API_BASE_URL` env var
- **Auth interceptor**: Attaches `Authorization: Bearer <token>`
- **Error interceptor**: Handles 401 and redirects to login
- **Request/Response types**: Fully typed with TypeScript

### API Modules
- `auth.ts`: register, login, getMe
- `admin.ts`: All admin endpoints (stats, products, users, traces)
- `recommendations.ts`: getMyRecommendations, refreshRecommendations, getHistory
- `tracking.ts`: trackEvent, trackBatchEvents

## 🔐 Authentication Flow

1. User submits login form
2. `POST /auth/login` returns `{ access_token, user }`
3. Token saved to `localStorage` key `"sr_token"`
4. `authStore.login()` updates Zustand state
5. All subsequent requests include `Authorization` header
6. On 401: auto-logout and redirect to `/login`

## 🚦 Routing

| Route | Component | Protection |
|-------|-----------|------------|
| `/login` | LoginPage | Public |
| `/register` | RegisterPage | Public |
| `/dashboard` | DashboardPage | ProtectedRoute |
| `/courses` | CoursesPage | ProtectedRoute |
| `/courses/:id` | CourseDetailPage | ProtectedRoute |
| `/activity` | ActivityPage | ProtectedRoute |
| `/admin` | AdminDashboardPage | AdminRoute (role=admin) |
| `/admin/products` | AdminProductsPage | AdminRoute |
| `/admin/users` | AdminUsersPage | AdminRoute |
| `/admin/traces` | AdminTracesPage | AdminRoute |

## 🐛 Common Issues

### Port already in use
```bash
# Kill process on port 5173
lsof -ti:5173 | xargs kill -9  # Mac/Linux
netstat -ano | findstr :5173   # Windows
```

### API connection refused
- Ensure backend is running on `http://localhost:8000`
- Check `.env` file has correct `VITE_API_BASE_URL`

### Missing dependencies
```bash
npm install recharts lucide-react @tanstack/react-query
```

## 📚 Resources

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [React Query](https://tanstack.com/query/latest)
- [Zustand](https://github.com/pmndrs/zustand)
- [Recharts](https://recharts.org)

## 📄 License

MIT License - See backend LICENSE for details
