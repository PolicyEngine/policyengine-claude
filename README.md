# PolicyEngine Claude

Official Claude Code plugin for PolicyEngine — agents, slash commands, and skills for the entire PolicyEngine ecosystem.

## Quick Start

```bash
# Add the marketplace
/plugin marketplace add PolicyEngine/policyengine-claude

# Install everything (recommended)
/plugin install complete@policyengine-claude
```

Or install for your use case:

```bash
/plugin install essential@policyengine-claude         # For users
/plugin install analysis-tools@policyengine-claude    # For analysts
/plugin install country-models@policyengine-claude    # For country model devs
/plugin install api-development@policyengine-claude   # For API devs
/plugin install app-development@policyengine-claude   # For app devs
/plugin install data-science@policyengine-claude      # For data work
```

## Plugins

| Plugin | Audience | Description |
|--------|----------|-------------|
| **essential** | Users | Platform knowledge — using the web app, understanding results |
| **country-models** | Contributors | Multi-agent workflow for implementing government benefit programs |
| **api-development** | Contributors | Flask API patterns, endpoints, caching, services |
| **app-development** | Contributors | React app patterns, components, routing, deployment |
| **analysis-tools** | Analysts | Impact analysis, dashboards, notebooks, visualizations |
| **data-science** | Contributors | Survey data, imputation, calibration, microdata utilities |
| **content** | Marketing | Social image and post generation from blog articles |
| **complete** | All | Everything above — all agents, commands, and skills |

See [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) for the full list of agents, commands, and skills in each plugin.

## Auto-Install in Repositories

Each PolicyEngine repo can auto-install the appropriate plugin via `.claude/settings.json`:

```json
{
  "plugins": {
    "marketplaces": ["PolicyEngine/policyengine-claude"],
    "auto_install": ["country-models@policyengine-claude"]
  }
}
```

When you trust the repo, the plugin auto-installs.

## Architecture

```
Layer 0: Foundation
├── L0 (PyTorch regularization for sparsification)

Layer 1: Core Engine
├── policyengine-core (simulation engine)

Layer 2: Country Models (depend on core)
├── policyengine-us (US federal + 50 states)
├── policyengine-uk (UK tax and benefits)
├── policyengine-canada (Canada federal + provincial)
├── policyengine-il (Israel)
└── policyengine-ng (Nigeria)

Layer 3: Data Utilities
├── microdf (weighted DataFrames for analysis)
├── microimpute (ML variable imputation)
└── microcalibrate (survey calibration, uses L0)

Layer 4: Enhanced Data (depend on country models + data utilities)
├── policyengine-us-data (enhanced CPS, uses microimpute + microcalibrate)
└── policyengine-uk-data (enhanced FRS)

Layer 5: Services
├── policyengine-api (v1 - production Flask API)
├── policyengine-api-v2 (v2 - monorepo with 3 microservices, in development)
└── policyengine.py (Python client)

Layer 6: Interfaces
├── policyengine-app (v1 - production React app)
└── policyengine-app-v2 (v2 - Next.js + Mantine, in development)

Layer 7: Applications
├── Analysis repos (crfb-tob-impacts, newsletters, dashboards)
└── Calculators (givecalc, salt-amt-calculator, ctc-calculator)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development workflow.

Key points:
- Every PR must include a changelog fragment in `changelog.d/` — CI enforces this
- Do NOT manually edit versions in `marketplace.json` or `CHANGELOG.md` — both are auto-generated on merge
- See [CLAUDE.md](CLAUDE.md) for instructions that Claude Code loads automatically when working in this repo

## Support

- **Issues:** https://github.com/PolicyEngine/policyengine-claude/issues
- **Email:** hello@policyengine.org
- **PolicyEngine:** https://policyengine.org

## License

MIT
