---
name: policyengine-api-v2
description: PolicyEngine API v2 - FastAPI microservices architecture (alpha)
---

# PolicyEngine API v2

The PolicyEngine API v2 is a next-generation API rewrite using FastAPI and microservices architecture. Currently in alpha development.

## For Contributors 💻

### Repository

**Location:** PolicyEngine/policyengine-api-v2-alpha (transitioning to policyengine-api-v2)

**Clone:**
```bash
git clone https://github.com/PolicyEngine/policyengine-api-v2-alpha
cd policyengine-api-v2-alpha
```

### Architecture Differences from v1

**v1 (policyengine-api):**
- Flask monolith
- Single service
- Redis caching with Flask-Cache decorators

**v2 (policyengine-api-v2-alpha):**
- FastAPI microservices
- SQLAlchemy ORM with PostgreSQL
- Database-first architecture
- Separate services for parameters, policies, simulations, etc.

### Key Components

**Database Layer:**
```bash
# Check current schema
cat app/models/  # SQLAlchemy models

# Key tables:
# - parameters: Tax/benefit parameter metadata
# - policies: Policy reforms
# - simulations: Calculation results
```

**API Endpoints:**
```bash
# Check current endpoints
ls app/routers/

# Example endpoints:
# - /parameters - Parameter search and retrieval
# - /policies - Policy creation and management
# - /simulations - Run calculations
```

## Common Patterns

### Database Queries

**Pattern: Query with filters**
```python
from sqlalchemy import select
from app.models import Parameter

# Good: Use SQLAlchemy ORM
query = select(Parameter)
if search:
    query = query.filter(Parameter.name.contains(search))
results = session.execute(query).scalars().all()
```

### Seeding Data

**Pattern: Database seeding scripts**
```bash
# Check seeding logic
cat app/seed.py  # or scripts/seed.py
```

**Common consideration:**
- Decide which parameters to seed (all vs. labeled only)
- Balance between completeness and database size
- Consult with maintainers about filtering decisions

## Critical Gotchas

### 1. Caching with Query Parameters

**Problem:** Flask-Cache style decorators cache based on route only, ignoring query parameters.

**Example of broken code:**
```python
@cache(expire=3600)
@app.get("/parameters")
def get_parameters(search: str = None):
    # BAD: All queries return same cached result
    if search:
        return filter_parameters(search)
    return all_parameters()
```

**Why it breaks:**
- `GET /parameters?search=basic_rate` caches result
- `GET /parameters?search=pension` returns cached basic_rate results
- Cache key doesn't include query parameters

**Solution 1: Remove caching decorator**
```python
@app.get("/parameters")
def get_parameters(search: str = None):
    # Let database handle queries, they're fast enough
    if search:
        return filter_parameters(search)
    return all_parameters()
```

**Solution 2: Custom cache key (if caching needed)**
```python
def cache_key_with_params(search: str = None):
    return f"parameters:{search or 'all'}"

@cache(key_func=cache_key_with_params)
@app.get("/parameters")
def get_parameters(search: str = None):
    # Now each search term gets its own cache entry
    if search:
        return filter_parameters(search)
    return all_parameters()
```

**When to cache:**
- ✅ Expensive computations (population impacts)
- ✅ Static data that rarely changes
- ❌ Simple database queries with filters
- ❌ Endpoints with many unique query combinations

### 2. Parameter Filtering Decisions

**Context:** Parameter seeding can filter by various criteria (label presence, visibility, etc.)

**Important:** These filters are often **deliberate design decisions**, not bugs.

**Before changing parameter filters:**
1. Check git history for the filtering logic
2. Ask maintainers why the filter exists
3. Consider impact on database size and API performance
4. Test that filtered-out parameters aren't needed for workflows

**Example from PR #15:**
```python
# This filter was DELIBERATE, not a bug:
parameters_to_add = [p for p in model_version.parameters if p.label is not None]

# Maintainer feedback: "the filter on labelled params was deliberate"
```

**Red flags that suggest you should ask first:**
- Changing parameter/variable filtering logic
- Modifying seeding scripts to include/exclude more data
- Altering which metadata gets stored in database

## Development Workflow

### Setup

**Check current setup instructions:**
```bash
cat README.md  # Setup guide
cat docker-compose.yml  # If using Docker
```

**Typical setup:**
```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
make db-setup  # or similar

# Seed initial data
make seed

# Run dev server
make dev
```

### Testing

**Check test patterns:**
```bash
ls tests/
cat tests/test_*.py

# Run tests
pytest
```

## Migration Notes (v1 to v2)

### If working on both APIs:

**v1 patterns that don't apply to v2:**
- Flask blueprints → FastAPI routers
- Flask-Cache decorators → Custom caching or FastAPI-cache
- Direct Redis access → Database-first with optional caching
- Country package direct imports → Service layer

**v2 patterns:**
- SQLAlchemy models for all entities
- Pydantic schemas for validation
- Dependency injection via FastAPI
- Async support (optional but available)

## Related Skills

- **policyengine-api-skill** - Original API (v1) patterns
- **policyengine-core-skill** - Understanding the engine
- **policyengine-implementation-patterns-skill** - General patterns

## Resources

**Repository:** https://github.com/PolicyEngine/policyengine-api-v2-alpha
**v1 API (for comparison):** https://github.com/PolicyEngine/policyengine-api
**Live API (v1):** https://api.policyengine.org

## Status

🚧 **Alpha Development** - Architecture is stabilizing but subject to change. Consult maintainers before major changes.
