# Experiment YYYY-MM-DD-NN — short name

## Question

State one falsifiable question.

## Existing evidence

List the registry rows, captures, client handlers, and prior checkpoints that
make this experiment necessary. Separate established facts from hypotheses.

## Single variable

Describe the only protocol or runtime behavior changed for this run. If more
than one behavior must change, split the experiment.

## Exact input

- Branch/commit or dirty-file identity:
- Environment switches:
- Packet direction, opcode, component, and lifecycle point:
- Exact plaintext bytes or fixture path and SHA-256:

## Predictions

Positive observation:

- What exact log, handler hit, state transition, or visible behavior confirms
  the hypothesis?

Negative observation:

- What result falsifies it?

Invalid/inconclusive conditions:

- What missing delivery proof, duplicate stream, decode error, or unrelated
  change would make the run unusable?

## Evidence to preserve

- Server log:
- Hook/client log:
- Packet-workbench report:
- Screenshots or user-visible observation:

## Result

Fill in only after the run. Quote timestamps and short decisive excerpts rather
than pasting whole logs.

## Conclusion

- Outcome: confirmed / falsified / inconclusive
- Confidence change:
- Registry rows updated:
- Runtime code retained, reverted, or still opt-in:
- Next single question:

