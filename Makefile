changelog:
	build-changelog changelog.yaml --output changelog.yaml --update-last-date --start-from 0.0.1 --append-file changelog_entry.yaml
	build-changelog changelog.yaml --org PolicyEngine --repo policyengine-claude --output CHANGELOG.md --template .github/changelog_template.md
	@echo ""
	@echo "REMINDER: Manually bump version in .claude-plugin/marketplace.json"
	@echo "Example: sed -i '' 's/\"version\": \"X.Y.Z\"/\"version\": \"X.Y.W\"/g' .claude-plugin/marketplace.json"
	rm changelog_entry.yaml || true
	touch changelog_entry.yaml
