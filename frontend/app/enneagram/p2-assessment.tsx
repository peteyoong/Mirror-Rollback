/**
 * Backward-compatible redirect to /enneagram/assessment
 * This file exists to support any existing links to /enneagram/p2-assessment
 */

import { Redirect } from 'expo-router';

export default function P2AssessmentRedirect() {
  return <Redirect href="/enneagram/assessment" />;
}
