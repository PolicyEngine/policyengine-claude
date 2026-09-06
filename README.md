# PolicyEngine Claude

Generated Claude Code wrapper for PolicyEngine.

This repository is built from `PolicyEngine/policyengine-skills`. Do not edit it directly unless you are fixing a sync emergency.

`encode-policy-v2`, `review-program` and `fix-pr` are skill entrypoints and retain their
namespaced [slash commands](https://code.claude.com/docs/en/plugins). They have no same-named command stubs: duplicate registration
can resolve to the stub instead of the skill. The wrapper builder rejects such collisions.

## Install

```bash
/plugin marketplace add PolicyEngine/policyengine-claude
/plugin install complete@policyengine-claude
```

Other bundles:

```bash
/plugin install essential@policyengine-claude
/plugin install country-models@policyengine-claude
/plugin install api-development@policyengine-claude
/plugin install app-development@policyengine-claude
/plugin install analysis-tools@policyengine-claude
/plugin install data-science@policyengine-claude
/plugin install dashboard-builder@policyengine-claude
/plugin install content@policyengine-claude
```
