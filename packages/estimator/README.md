# @negotiator/estimator — Module 1

**Intake by interview or documents → one confirmed [JobSpec](../../schemas/job-spec.schema.json).**

The Estimator builds the complete, structured job spec that makes a later quote *binding rather than bait*. Two paths, **one identical schema**:

- **Voice interview** — an ElevenLabs agent asks what a professional estimator would ask, guided by the vertical config's `specFields`.
- **Document intake** — photos, existing quotes, bills, inventory lists parsed via vision/OCR into the same schema.

The user **confirms the spec** before any call is made. This is the direct attack on the sight-unseen problem — incomplete intakes are why estimates blow up 40% of the time.

## Responsibilities
- Load the vertical config and drive the interview from `specFields`.
- Run an ElevenLabs Agents voice intake (system prompt + tools that write spec fields).
- Parse ≥1 document type into the same `spec` shape.
- Produce a `JobSpec`, echo it back to the user in plain language, and set `confirmedByUser: true` only on explicit confirmation.

## Acceptance (from the challenge)
> Voice interview built on ElevenLabs Agents **plus** at least one document type; both paths produce the **same** structured job spec (e.g. JSON), confirmed by the user and reused verbatim across every call.

## Interfaces
- **Output:** `JobSpec` (`@negotiator/shared`) → handed to the Caller.
