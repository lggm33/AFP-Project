# 🚀 AFP - Personal Finance Application

**AFP (Aplicación de Finanzas Personales)** is an innovative SaaS platform that automates personal financial management through artificial intelligence by reading banking emails and extracting financial transactions automatically.

## 🎯 Value Proposition

- **Automatic Banking Email Processing**: Reads emails from multiple banks automatically
- **AI-Powered Transaction Extraction**: Uses artificial intelligence to process different email formats
- **Dynamic Multi-Bank Support**: Add new banks through configuration without code changes
- **Automated Financial Insights**: Generates automatic categorization and financial analytics
- **Scalable SaaS Architecture**: Built to grow from 100 to 1000+ users

## ✨ Key Features

### 🔐 User Management
- Complete authentication system with Django
- User profiles with timezone and currency preferences
- Subscription management (Free/Pro/Enterprise tiers)
- Stripe integration for billing

### 📧 Email Processing Engine
- **Gmail API Integration**: Automatic email fetching
- **AI Pattern Generation**: OpenAI GPT-4 generates regex patterns for new banks
- **Background Workers**: Robust Celery-based processing system
- **Multi-Bank Support**: Dynamic bank configuration without deployment

### 💳 Transaction Management
- **Automatic Extraction**: AI extracts amount, merchant, date, reference
- **Smart Categorization**: Automatic transaction categorization
- **Multiple Transaction Types**: Purchase, Transfer, ATM, Payment, Deposit
- **High Accuracy**: 80%+ accuracy in transaction extraction

### 📊 Financial Analytics
- **Interactive Dashboard**: Real-time financial insights
- **Spending Analytics**: Category-based spending analysis
- **Transaction History**: Complete searchable transaction history
- **Financial Insights**: AI-generated spending patterns and recommendations

### ⚙️ Admin Features
- **Bank Management**: Add/configure banks through Django admin
- **Pattern Management**: View and edit AI-generated patterns
- **User Management**: Complete user administration
- **System Monitoring**: Queue status and processing metrics

## 🏗️ Architecture

```
🌐 Next.js Frontend (TypeScript)
    ↕️ REST API
🐍 Django Backend + Celery Workers
    ↕️ Queue System (Redis)
⚙️ Email Processing Engine (Python)
    ↕️ Database Layer
📊 PostgreSQL + Redis Cache
```

### Architecture Highlights
- **80% Standard Stack**: Django + TypeScript for rapid development
- **20% Custom Innovation**: Email processing and AI pattern generation
- **Multi-Tenant**: Tenant-per-row strategy for user data isolation
- **Background Processing**: Celery workers for email processing
- **API-First**: Django REST Framework for clean API design

## 📁 Project Structure

```
afp-project/
├── backend/                    # 🐍 Django Backend
│   ├── afp_project/           # Django project settings
│   ├── apps/
│   │   ├── users/            # User management & auth
│   │   ├── subscriptions/    # Billing & subscription logic
│   │   ├── banking/          # Bank configuration & patterns
│   │   ├── transactions/     # Transaction processing
│   │   └── analytics/        # Financial analytics
│   ├── api/                  # Django REST Framework endpoints
│   ├── workers/              # Celery background workers
│   ├── core/                 # Email processing engine
│   ├── strategies/           # Transaction processing strategies
│   └── ai/                   # AI services (OpenAI integration)
│
├── frontend/                 # 🟨 TypeScript Frontend
│   ├── apps/
│   │   └── web/             # Next.js customer application
│   └── packages/
│       ├── ui/              # Shared UI components (shadcn/ui)
│       ├── api-client/      # Django API client
│       └── types/           # Shared TypeScript types
│
├── docs/                    # 📚 Documentation
├── scripts/                 # 🧪 Setup and testing scripts
└── README.md
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL (primary) + Redis (cache/queues)
- **Background Jobs**: Celery with Redis broker
- **AI Integration**: OpenAI GPT-4 for pattern generation
- **Email Processing**: Gmail API integration
- **Authentication**: Django auth + django-allauth
- **Billing**: django-subscriptions + Stripe

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript for type safety
- **UI Components**: shadcn/ui + Tailwind CSS
- **State Management**: React hooks + TanStack Query
- **API Client**: Custom TypeScript client for Django API

### Infrastructure
- **Deployment**: Railway (PaaS platform)
- **Database Hosting**: Railway PostgreSQL
- **Cache & Queues**: Railway Redis
- **Frontend Deploy**: Railway or Vercel
- **Monitoring**: Built-in Railway monitoring

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 15+
- Redis 6+

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd afp-project
   ```

2. **Start the application**
   ```bash
   ./start.sh
   ```

### Manual Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your database and API keys

# Run migrations
python manage.py migrate
python manage.py createsuperuser

# Start Django server
python manage.py runserver
```

#### Frontend Setup
```bash
cd frontend/apps/web
npm install

# Configure environment variables
cp .env.example .env.local
# Edit .env.local with your API endpoints

# Start development server
npm run dev
```

#### Workers Setup
```bash
# In a separate terminal, start Celery workers
cd backend
celery -A afp_project worker --loglevel=info

# In another terminal, start Celery beat (scheduler)
celery -A afp_project beat --loglevel=info
```

## 📊 Business Model

### Subscription Tiers
- **Free**: Limited transactions per month, basic analytics
- **Pro**: Unlimited transactions, advanced analytics, priority support
- **Enterprise**: Multi-user accounts, API access, custom integrations

### Target Market
- **Initial**: 100 users for market validation
- **Growth**: Scale to 1000+ users
- **Target Audience**: Professionals managing multiple bank accounts

## 🔄 Email Processing Workflow

1. **Email Import**: Celery worker fetches emails from Gmail API
2. **Bank Identification**: System identifies sender bank from email domain
3. **Transaction Detection**: AI determines transaction type (Purchase, Transfer, etc.)
4. **Strategy Selection**: Appropriate processing strategy is selected
5. **Data Extraction**: Regex patterns extract transaction data
6. **Transaction Creation**: Processed data is saved to database
7. **User Notification**: Dashboard updates with new transactions

## 🎯 Development Phases

### Phase 1: Foundation (Weeks 1-2)
- ✅ Django backend with auth and subscriptions
- ✅ Next.js frontend with login/register
- ✅ Basic API connectivity
- ✅ Railway deployment

### Phase 2: Email Processing (Weeks 3-4)
- ✅ Celery worker migration
- ✅ Redis queue system
- ✅ AI pattern generation service

### Phase 3: Dynamic Banking (Weeks 5-6)
- ✅ Configurable bank system
- ✅ Transaction processing strategies
- ✅ Frontend transaction display

### Phase 4: Analytics (Weeks 7-8)
- ✅ Financial dashboard
- ✅ Transaction categorization
- ✅ Performance optimization

### Phase 5: Launch (Week 9)
- ✅ Complete testing
- ✅ User documentation
- ✅ Beta user onboarding

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 📞 Support

For support and questions, please contact the development team or create an issue in the repository.

---

**Built with ❤️ using Django, Next.js, and AI** 