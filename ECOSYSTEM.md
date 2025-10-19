# PolicyEngine Ecosystem Map

Complete dependency graph of the PolicyEngine platform (40+ repositories).

## Version Status

| Repository | Status | Notes |
|------------|--------|-------|
| policyengine-api | ✅ Current | Production Flask API |
| policyengine-api-v2 | 🚧 Active | Monorepo with 3 microservices (ports 8081-8083) |
| policyengine-app | ✅ Current | Production React app |
| policyengine-app-v2 | 🚧 Active | Next.js/Mantine rewrite with new design tokens |
| synthimpute | ❌ Archived | Replaced by microimpute + microcalibrate |

## Layer 0: Low-Level Utilities

### L0 (PyTorch Regularization)
**Repository:** PolicyEngine/L0
**Purpose:** L0 regularization for neural network sparsification and intelligent sampling
**Used by:** microcalibrate, policyengine-us-data
**Dependencies:** torch, numpy

**Key features:**
- Hard Concrete Distribution for differentiable L0 norm
- Sparse neural network layers (L0Linear, L0Conv2d)
- Intelligent sampling gates for calibration
- Temperature scheduling

**Use cases:**
- Household selection in survey calibration
- Sample sparsification to reduce dataset size
- Feature selection in ML models

## Layer 1: Core Infrastructure

### policyengine-core (Simulation Engine)
**Repository:** PolicyEngine/policyengine-core
**Purpose:** Microsimulation engine (OpenFisca fork)
**Used by:** All country models, API, data packages
**Dependencies:** numpy, pytest, yaml

**Provides:**
- Variable and parameter infrastructure
- Entity system (Person, Household, TaxUnit, etc.)
- Simulation engine
- Formula evaluation and caching
- Period handling
- Reform application

## Layer 2: Country Models

All depend on: policyengine-core

### policyengine-us
**Status:** ✅ Current
**Dependencies:** policyengine-core
**Models:** Federal and all 50 state tax/benefit systems

### policyengine-uk
**Status:** ✅ Current
**Dependencies:** policyengine-core
**Models:** UK tax, National Insurance, Universal Credit, etc.

### policyengine-canada
**Status:** ✅ Current
**Dependencies:** policyengine-core
**Models:** Canadian federal and provincial systems

### policyengine-il (Israel)
**Status:** ✅ Current
**Dependencies:** policyengine-core

### policyengine-ng (Nigeria)
**Status:** ✅ Current
**Dependencies:** policyengine-core

### Others (Inactive/Beta)
- policyengine-au (Australia)
- policyengine-ie (Ireland)
- policyengine-nz (New Zealand)
- policyengine-sg (Singapore)

## Layer 3: Data Utilities

### microdf
**Repository:** PolicyEngine/microdf
**Purpose:** Weighted pandas DataFrames for survey analysis
**Used by:** policyengine-api, policyengine-us-data, analysis repos
**Dependencies:** pandas, numpy

**Provides:**
- MicroDataFrame (weighted DataFrame)
- MicroSeries (weighted Series)
- Gini coefficient
- Poverty calculations
- Top share calculations

### microimpute
**Repository:** PolicyEngine/microimpute
**Purpose:** ML-based variable imputation
**Used by:** policyengine-us-data
**Dependencies:** numpy, pandas, scikit-learn, quantile-forest, optuna, statsmodels

**Methods:**
- Linear regression
- Random forest
- Quantile forest
- XGBoost
- Comparison and benchmarking

### microcalibrate
**Repository:** PolicyEngine/microcalibrate
**Purpose:** Survey weight calibration to population targets
**Used by:** policyengine-us-data
**Dependencies:** torch, numpy, pandas, L0, optuna

**Features:**
- Weight adjustment to match targets
- L0 regularization for sparsity
- Automatic hyperparameter tuning
- Robustness evaluation
- Interactive dashboard at microcalibrate.vercel.app

## Layer 4: Enhanced Data

### policyengine-us-data
**Repository:** PolicyEngine/policyengine-us-data
**Purpose:** Enhanced CPS microdata for US simulations
**Dependencies:** policyengine-us, policyengine-core, microdf, microimpute

**Process:**
1. Load raw CPS data
2. Impute missing variables (microimpute)
3. Calibrate weights (microcalibrate with L0)
4. Validate against benchmarks
5. Package for distribution

### policyengine-uk-data
**Repository:** PolicyEngine/policyengine-uk-data
**Purpose:** Enhanced FRS data for UK simulations
**Dependencies:** policyengine-uk, policyengine-core, microdf

## Layer 5: Services

### policyengine-api (v1 - Current Production)
**Repository:** PolicyEngine/policyengine-api
**Purpose:** Flask REST API for calculations
**Status:** ✅ Production
**Dependencies:**
- All country models (us, uk, canada, il, ng)
- policyengine-core
- policyengine (Python client)
- microdf
- flask, redis, rq
- anthropic, openai (AI features)
- streamlit (internal tools)

**Endpoints:**
- POST /us/calculate - Household calculations
- GET /us/economy/{reform}/{baseline} - Population impacts
- GET /us/policy/{id} - Policy metadata
- GET /us/parameters, /us/variables - Metadata

### policyengine-api-v2 (v2 - Active Development)
**Repository:** PolicyEngine/policyengine-api-v2
**Purpose:** Next-generation API (monorepo, microservices)
**Status:** 🚧 Active development

**Services:**
- api-full (port 8081): Main API with household calculations
- api-simulation (port 8082): Economic simulation engine
- api-tagger (port 8083): Deployment management

**Technology:**
- Docker + Docker Compose
- Supabase (PostgreSQL)
- Python 3.13+
- uv package manager
- OpenAPI spec generation
- Auto-generated Python clients

### policyengine.py (Python Client)
**Repository:** PolicyEngine/policyengine.py
**Purpose:** Python client for programmatic API access
**Status:** ✅ Current
**Dependencies:** sqlalchemy, sqlmodel, pandas, microdf, rich
**Optional:** policyengine-us, policyengine-uk (for local simulation)

**Usage:**
```python
from policyengine import Simulation
sim = Simulation(situation=household, country_id="us")
```

## Layer 6: User Interfaces

### policyengine-app (v1 - Current Production)
**Repository:** PolicyEngine/policyengine-app
**Purpose:** React web application
**Status:** ✅ Production at policyengine.org

**Technology:**
- React 18
- React Router v6
- Plotly.js
- Ant Design
- axios

**Colors:**
- Teal: #39C6C0
- Blue: #2C6496

### policyengine-app-v2 (v2 - Active Development)
**Repository:** PolicyEngine/policyengine-app-v2
**Purpose:** Next-generation app
**Status:** 🚧 Active development

**Technology:**
- Next.js (vs Create React App)
- Mantine (vs Ant Design)
- TypeScript
- Vite

**Design tokens:**
- Primary (teal): #319795 (slightly different from v1)
- Blue: #026AA2 (different from v1)
- Complete 50-900 color scales

## Layer 7: Application Layer

### Calculators
- **givecalc** - Charitable giving calculator (Streamlit)
- **salt-amt-calculator** - SALT and AMT calculator
- **ctc-calculator** - Child Tax Credit calculator
- Others...

**Common dependencies:**
- policyengine-us (or policyengine.py)
- streamlit
- plotly
- pandas

**Branding:**
- Use v1 colors for now (#39C6C0, #2C6496)
- Roboto Serif for charts
- PolicyEngine logo
- .streamlit/config.toml theme

### Analysis Repositories
- **crfb-tob-impacts** - Policy impact analyses
- **newsletters** - Data-driven newsletters
- **2024-election-dashboard** - Policy comparisons
- **marginal-child** - Specialized analyses
- Others...

**Common dependencies:**
- policyengine-us (or policyengine.py)
- microdf (for inequality/poverty)
- pandas, numpy
- plotly
- jupyter (notebooks)

### Dashboards
Interactive policy exploration tools

## Complete Dependency Graph

```
L0 (regularization)
├── microcalibrate
    └── policyengine-us-data

microimpute (imputation)
└── policyengine-us-data

microdf (weighted DataFrames)
├── policyengine-api
├── policyengine-us-data
├── policyengine.py
└── analysis repos

policyengine-core (engine)
├── policyengine-us
├── policyengine-uk
├── policyengine-canada
├── policyengine-il
├── policyengine-ng
└── policyengine-us-data

Country models
├── policyengine-api (uses all countries)
├── policyengine-api-v2 (uses all countries)
└── policyengine.py (optional, per country)

policyengine-us-data
└── policyengine-us (uses enhanced data)

policyengine-api
├── policyengine-app (calls API)
└── policyengine.py (wraps API)

policyengine-app
└── End users

Analysis repos
├── Use policyengine-us directly, OR
└── Use policyengine.py (API wrapper)
```

## Technology Stack by Layer

| Layer | Primary Tech | Package Manager | Testing | Deployment |
|-------|-------------|-----------------|---------|------------|
| L0 | PyTorch | pip/uv | pytest | PyPI |
| Core | Python 3.10-3.13 | pip/uv | pytest | PyPI |
| Country models | Python 3.10-3.13 | pip/uv | pytest | PyPI |
| Data utilities | Python 3.13 | pip/uv | pytest | PyPI |
| API v1 | Flask, Python 3.11+ | pip | pytest | Google App Engine |
| API v2 | FastAPI, Python 3.13+ | uv | pytest | Docker, GCP Cloud Run |
| App v1 | React 18 | npm | Jest | Netlify |
| App v2 | Next.js, TypeScript | npm | Vitest | TBD |
| Calculators | Streamlit | pip/uv | pytest | Streamlit Cloud |
| Analysis | Jupyter, Python | pip/uv | pytest | GitHub |

## Key Transitions

### API v1 → v2

**Status:** Both active, v2 in development

**Changes:**
- Monorepo structure (3 microservices)
- Docker + Supabase (vs App Engine + Cloud SQL)
- uv package manager (vs pip)
- OpenAPI spec generation
- Auto-generated clients

### App v1 → v2

**Status:** Both active, v2 in development

**Changes:**
- Next.js (vs Create React App)
- Mantine (vs Ant Design)
- TypeScript (vs JavaScript)
- New design tokens (#319795 vs #39C6C0)
- Vite (vs webpack)

### Data: synthimpute → microimpute + microcalibrate

**Status:** ✅ Migrated

**Changes:**
- synthimpute archived
- microimpute for imputation
- microcalibrate for calibration
- Both use modern ML (optuna for hyperparameter tuning)
- microcalibrate uses L0 regularization

## Package Dependencies Summary

### Core Packages (Stable)
- policyengine-core
- policyengine-us, policyengine-uk, etc.
- microdf

### Data Packages (Current)
- ✅ microimpute (imputation)
- ✅ microcalibrate (calibration)
- ✅ L0 (regularization)
- ❌ synthimpute (archived)

### Services (Dual Version)
- ✅ policyengine-api (v1, production)
- 🚧 policyengine-api-v2 (v2, development)
- ✅ policyengine.py (client, stable)

### Interfaces (Dual Version)
- ✅ policyengine-app (v1, production)
- 🚧 policyengine-app-v2 (v2, development)

## Skills Coverage Analysis

### Well Covered ✅
- policyengine-core ✅
- policyengine-us ✅
- policyengine-api ✅ (v1)
- policyengine-app ✅ (v1)
- microdf ✅
- Analysis patterns ✅

### Needs Skills 🆕
- policyengine-api-v2 (monorepo, microservices)
- policyengine-app-v2 (Next.js, Mantine, TypeScript)
- microimpute (ML imputation)
- microcalibrate (survey calibration)
- L0 (regularization)
- policyengine-us-data (data pipeline)
- policyengine.py (Python client) ✅ (basic, could enhance)

### Country-Specific 🔜
- policyengine-uk-skill
- policyengine-canada-skill

## Recommendations

### Immediate Updates
1. ✅ Update ecosystem references (synthimpute → microimpute + microcalibrate)
2. 🆕 Add note about v1/v2 status in relevant skills
3. 🆕 Create data ecosystem skills (microimpute, microcalibrate, L0)
4. 🆕 Note API v2 and App v2 as "coming soon" with architecture differences

### Future Skills
- policyengine-api-v2-skill (when closer to production)
- policyengine-app-v2-skill (when closer to production)
- policyengine-us-data-skill (data pipeline)

### Documentation Priority
1. **High:** Current production stack (core, us, api v1, app v1, microdf)
2. **Medium:** Data ecosystem (microimpute, microcalibrate, L0)
3. **Low:** v2 services (document patterns as they stabilize)

## Complete Repository List

### Core Infrastructure (5)
- policyengine-core ⭐
- policyengine-api ⭐
- policyengine-api-v2 🚧
- policyengine-app ⭐
- policyengine-app-v2 🚧

### Country Models (9)
- policyengine-us ⭐
- policyengine-uk ⭐
- policyengine-canada ⭐
- policyengine-il
- policyengine-ng
- policyengine-au
- policyengine-ie
- policyengine-nz
- policyengine-sg

### Data Packages (6)
- policyengine-us-data ⭐
- policyengine-uk-data ⭐
- microdf ⭐
- microimpute ⭐
- microcalibrate ⭐
- L0 ⭐

### Clients and Tools (3)
- policyengine.py ⭐
- policyengine-chat
- policyengine-gpt

### Analysis Repositories (10+)
- crfb-tob-impacts
- newsletters
- 2024-election-dashboard
- marginal-child
- analysis-notebooks
- And many more...

### Calculators (5+)
- givecalc
- salt-amt-calculator
- ctc-calculator
- And others...

### Utility Packages (3)
- policyengine-profiler
- policyengine-taxsim
- policyengine-social

⭐ = Has active development, should have skill coverage
🚧 = In development, document as patterns stabilize
