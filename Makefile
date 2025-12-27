PYTEST=python -m pytest

.PHONY: test test-unit test-integration test-api test-e2e test-load test-security test-ai-eval

test: test-unit test-integration test-api test-e2e test-load test-security test-ai-eval

test-unit:
	@mkdir -p artifacts
	$(PYTEST) -m "unit" tests/paperpilot --junitxml=artifacts/pytest-unit.xml

test-integration:
	@mkdir -p artifacts
	$(PYTEST) -m "integration" tests/paperpilot --junitxml=artifacts/pytest-integration.xml

test-api:
	@mkdir -p artifacts
	$(PYTEST) -m "api" tests/paperpilot --junitxml=artifacts/pytest-api.xml

test-e2e:
	@mkdir -p artifacts/playwright
	npx playwright test --config=e2e/playwright.config.ts

test-load:
	@mkdir -p artifacts/k6
	k6 run load/health_smoke.js

test-security:
	@chmod +x security/sast.sh security/dast.sh
	security/sast.sh
	security/dast.sh

test-ai-eval:
	@mkdir -p artifacts
	$(PYTEST) -m "ai_eval" tests/paperpilot --junitxml=artifacts/pytest-ai-eval.xml
