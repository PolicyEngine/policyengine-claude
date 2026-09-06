# Loading model-development in delegated work

Each agent doing country-model implementation, test authoring or review must load
`policyengine-model-development` in its own context before substantive work. A parent's
load, a skill name in a dispatch prompt, and instructions to read references are not
evidence that the worker loaded the skill.

Resolve the skill from the worker's available runtime catalog. Load its full `SKILL.md`
through the runtime's supported mechanism, then read the references for the assigned
work: implementers need parameters, variables, periods/aggregation, vectorization and
style; test authors need tests and periods/aggregation; reviewers select the sections
relevant to the changed model code. Do not substitute isolated reference excerpts for
the entrypoint's mandatory rules. Load other skills explicitly required by the role too.

Before writing model code/tests or reviewing them, send a brief `SKILLS_READY` message
with the resolved skill name, load mechanism, entrypoint path/resource, references read
and the successful tool result or runtime trace identifying the load. Record this once
in the existing role manifest/progress log; no separate worker or audit stage is needed.
The coordinator checks that evidence before accepting the role's work. An agent's bare
claim of compliance is insufficient. Do not report a load as verified when its evidence
is unavailable.

If the skill is absent from the runtime catalog, loading fails, or the worker lacks the
required loading capability, return `SKILLS_BLOCKED` with the exact missing item before
writing implementation/tests. The coordinator resolves the runtime setup or reports the
blocker; it must not silently replace this with manual repository-file reading and call
it a run with an installed skill. A deliberately requested source-file experiment must be
labelled as such and cannot establish installed-command behavior.

Loading is separate from applying the rules. The coordinator's existing structural and
coverage checks inspect the actual changes against the loaded guidance, including reuse
of existing concepts, source-defined parameters, entities/periods, aggregation and
meaningful tests. Record concrete deviations and fixes in those existing checks. A load
receipt, formatting pass or test count is not evidence that these modeling decisions
are correct.
