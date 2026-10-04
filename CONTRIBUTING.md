# Contributing

Use Python 3.10–3.12 x64. Install requirements into an isolated environment and run `python -m unittest discover -s tests -v` before submitting changes. Management tests use temporary storage and mocked model downloads; they do not require neural weights.

Keep interface text and code documentation in English. Update README.md and readme-ptbr.md together when behavior changes. Preserve third-party notices and avoid committing data, model archives, virtual environments or translation text.

For a model-pipeline change, additionally test real offline translation in both directions and an English bridge route. For an interface change, verify both themes, mobile widths, keyboard controls and stale-request handling. Record actual checks and platform limitations in VALIDATION.md.

Describe the problem, resulting behavior and validation in each pull request. The included GitHub workflow runs lightweight Linux checks; it is not a neural accuracy benchmark or proof of Windows compatibility.
