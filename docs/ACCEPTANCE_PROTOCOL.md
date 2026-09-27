# Final acceptance gate — NOT YET FROZEN

A plan is not an untouched dataset. No final acceptance result is claimed here.

Before opening labels or executing: record task, dataset revision, licence, eligible sample population, exclusion list of all training/development/previously evaluated scene IDs, deterministic selection seed, selected IDs and file hashes. Split by source scene/event where possible, not neighbouring patches. Record unknown upstream training exposure.

Freeze the candidate code revision, package inventory, model hashes, preprocessing, metrics, thresholds and failure accounting. Define task-specific acceptance criteria before results, including refusal and invalid-input cases. Retain all selected cases and failures; never silently drop them.

Evaluate once. Export per-case predictions and timing plus aggregate task metrics. Keep VQA/caption review separate from mask metrics. If a result informs changes, retire it to regression evidence and select a genuinely new acceptance set.

Current blocker: a verified unused eligible population and predeclared acceptance thresholds have not been established. Existing 21 September cases must not be relabelled as untouched.


26 September update: a bounded temporal/component protocol was frozen and executed; see [results](SUBMISSION_VALIDATION.md). This does not close the full-system untouched acceptance gate described above.
