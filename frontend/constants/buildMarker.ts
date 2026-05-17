/**
 * Build marker for deployment verification.
 *
 * Bumped each time we ship a forum / Safari / Reflect-affecting
 * change. Surfaced subtly at the bottom of the Reflect entry chooser
 * and on the Forum loading / recovery screen so we can confirm
 * whether a given client is running the latest bundle.
 *
 * If a user reports they don't see the latest UI, the first
 * diagnostic step is to ask whether they see this BUILD_ID at the
 * bottom of those screens.
 */
export const BUILD_ID = 'individual-maps-v1';
export const BUILD_AT = '2026-05-17';
