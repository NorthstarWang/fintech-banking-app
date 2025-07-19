# Frontend Documentation


## Getting Started

### Running with Docker
```bash
# From the root directory
docker-compose up frontend
```

### Local Development
```bash
cd frontend
npm install
npm run dev
```

The application will be available at `http://localhost:3000`.

## Architecture

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom design system
- **State Management**: React Context API
- **Animations**: Framer Motion
- **API Client**: Custom fetch wrapper with error handling

## Directory Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js app router pages
│   │   ├── (authenticated)/    # Protected pages
│   │   └── (public)/          # Public pages
│   ├── components/            # Reusable components
│   │   ├── ui/               # Base UI components
│   │   ├── dashboard/        # Dashboard widgets
│   │   ├── transactions/     # Transaction components
│   │   └── mobile/           # Mobile-specific components
│   ├── contexts/             # React contexts
│   ├── lib/                  # Utilities and API
│   └── services/             # Service layer
```

## Pages

### Public Pages

#### Landing Page (`/`)
- Welcome screen with feature highlights
- Login/Register navigation
- Responsive hero section

#### Login (`/login`)
- Username/email and password authentication
- Remember me functionality
- Error handling with user feedback

#### Register (`/register`)
- New user registration form
- Password strength requirements
- Automatic login after registration

### Authenticated Pages

#### Dashboard (`/dashboard`)
- Account balance overview
- Quick action buttons
- Recent transactions
- Spending overview chart
- Goal progress tracking
- Mobile-optimized with pull-to-refresh

#### Accounts (`/accounts`)
- List all user accounts
- Account balances and details
- Create new accounts
- Account type icons and colors

#### Transactions (`/transactions`)
- Transaction history with pagination
- Advanced filtering (date, category, amount)
- Search functionality
- Transaction categorization
- Mobile-responsive table/card view

#### Budget (`/budget`)
- Budget creation and management
- Category-based spending limits
- Visual progress bars
- Alert thresholds (80% warning)
- Monthly/weekly/yearly periods

#### Goals (`/goals`)
- Financial goal tracking
- Progress visualization
- Contribution history
- Goal milestones
- Automated savings setup

#### Cards (`/cards`)
- Credit/debit card management
- Card freeze/unfreeze toggle
- Virtual card generation
- Spending controls
- Transaction history per card

#### P2P Payments (`/p2p`)
- Send money to contacts
- Contact list with avatars
- Quick send functionality
- Transaction history
- Request money feature

#### Messages (`/messages`)
- Chat interface for payment context
- Conversation list
- Real-time message updates
- Payment notifications in chat
- Read receipts

#### Transfer (`/transfer`)
- Inter-account transfers
- Account selection dropdowns
- Amount validation
- Transfer confirmation
- Transaction receipt

#### Subscriptions (`/subscriptions`)
- Active subscription list
- Cost analysis
- Cancellation reminders
- Usage tracking
- Optimization suggestions

#### Business (`/business`)
- Invoice creation
- Expense tracking
- Tax categorization
- Receipt management
- Business analytics

#### Settings (`/settings`)
- Profile management
- Notification preferences
- Currency settings
- Theme selection
- Data export options

#### Security (`/security`)
- Two-factor authentication setup
- Biometric authentication
- Login history
- Active sessions
- Security alerts

## Components

### UI Components

- **Button**: Interactive button with animations
- **Input**: Focus, blur, and change events
- **Dropdown**: Custom select component
- **Modal**: Open/close events
- **Tabs**: Tab navigation component
- **Card**: Hover and click interactions

### Special Components

#### SlideToConfirm
- Swipe gesture for transaction confirmation
- Progress indicators
- Haptic feedback simulation
- Customizable thresholds

#### TwoFactorInput
- 6-digit code input
- Auto-focus progression
- Paste support
- Error states

#### BiometricAuth
- Fingerprint/Face ID UI
- Fallback to PIN
- Remember device option

#### MobileDrawer
- Swipe-enabled navigation
- Gesture support
- Smooth animations

- Page views
- Button clicks
- Form interactions
- Navigation events
- API calls
- Error occurrences

- All button clicks
- Form field changes
- Page navigation
- Modal interactions
- Dropdown selections
- Tab switches
- Gesture events

## API Integration

### API Client
Located in `lib/api/client.ts`:
- Automatic token management
- Error handling
- Request/response logging
- Session management

### Services
- **authService**: Login, logout, registration
- **accountsService**: Account CRUD operations
- **transactionsService**: Transaction management
- **budgetsService**: Budget tracking
- **goalsService**: Goal management

## Responsive Design

### Breakpoints
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

### Mobile Features
- Touch-optimized interactions
- Swipe gestures
- Pull-to-refresh
- Responsive tables → cards
- Mobile navigation drawer

## Performance Optimizations

- React Server Components
- Dynamic imports for code splitting
- Image optimization with Next.js Image
- Virtualized lists for large datasets
- Debounced search inputs
- Memoized expensive computations

## Theming

### CSS Variables
```css
--primary-blue: #3B82F6
--primary-navy: #1E3A8A
--success-green: #10B981
--warning-amber: #F59E0B
--danger-red: #EF4444
```

### Dark Mode
- System preference detection
- Manual toggle in settings
- Persistent user preference

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

## Development Tips

### Adding a New Page
1. Create page in `app/(authenticated)/`
2. Add navigation link
4. Add loading and error states
5. Test responsive design

### Creating Components
1. Use TypeScript interfaces
2. Include analytics props
4. Support dark mode
5. Test on mobile devices