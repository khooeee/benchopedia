.PHONY: openrouter-quota
github-size:
	gh api repos/khooeee/benchopedia --jq '.size / 1024'

openrouter-quota:
	@python3 -m runner.openrouter_api
