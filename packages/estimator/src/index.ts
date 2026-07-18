import type { JobSpec, VerticalConfig } from "@negotiator/shared";

/**
 * Module 1 — The Estimator.
 *
 * Build a complete, user-confirmed JobSpec from a voice interview (ElevenLabs Agents)
 * and/or document intake (photos, quotes, bills via vision/OCR). Both paths must
 * produce the SAME schema. Do not set `confirmedByUser` until the user confirms.
 *
 * See ./README.md and ../../schemas/job-spec.schema.json.
 */
export async function runEstimator(_config: VerticalConfig): Promise<JobSpec> {
  throw new Error("Not implemented — build the ElevenLabs voice intake + document parser here.");
}
