/**
 * Predefined rejection reasons for smart regeneration.
 * These map to backend RejectionReasonType literal.
 */
export const REJECTION_REASONS = {
  off_brand_tone: "Off-brand tone",
  generic_boring: "Generic/boring",
  factually_wrong: "Factually wrong",
  seo_issues: "SEO issues",
} as const;

export type RejectionReason = keyof typeof REJECTION_REASONS;

/**
 * Get human-readable label for a rejection reason.
 */
export function getReasonLabel(reason: RejectionReason): string {
  return REJECTION_REASONS[reason];
}

/**
 * Validate that a value is a valid rejection reason.
 */
export function isValidReason(value: string): value is RejectionReason {
  return value in REJECTION_REASONS;
}
