/**
 * Birth Time Utilities
 * 
 * Helper functions for determining if a user's birth time is known,
 * and for conditionally showing time-dependent lens content.
 */

interface UserWithBirthTime {
  birth_time?: string | null;
  birth_time_known?: boolean | null;
}

/**
 * Determines if the user has a known birth time.
 * 
 * Logic:
 * 1. If birth_time_known is explicitly set, use that value
 * 2. Otherwise, fall back to checking if birth_time is present and non-empty
 * 
 * @param user - User object with optional birth_time and birth_time_known fields
 * @returns boolean - true if birth time is known, false otherwise
 */
export const hasKnownBirthTime = (user: UserWithBirthTime | null | undefined): boolean => {
  if (!user) return false;
  
  // If birth_time_known is explicitly set, use it
  if (user.birth_time_known !== undefined && user.birth_time_known !== null) {
    return user.birth_time_known;
  }
  
  // Fall back to presence of birth_time
  return !!user.birth_time && user.birth_time.length > 0;
};

/**
 * Returns a display string for when birth time is unknown.
 * Used in UI components to inform users about limitations.
 */
export const BIRTH_TIME_REQUIRED_MESSAGE = {
  astrology: {
    title: "Birth time needed for houses",
    body: "Your birth time is not set. Houses, Ascendant/MC, and house placements are time-dependent and are hidden to avoid inaccurate readings.",
    cta: "Add birth time"
  },
  humanDesign: {
    title: "Birth time required for Human Design",
    body: "Human Design is highly time-sensitive. Add your birth time to unlock accurate results.",
    cta: "Add birth time"
  }
};

/**
 * Time-dependent astrology features that should be hidden when birth time is unknown.
 */
export const TIME_DEPENDENT_ASTROLOGY_FEATURES = [
  'houses',
  'ascendant',
  'midheaven',
  'house_placements',
  'rising_sign'
];

/**
 * Filters out time-dependent content from astrology data when birth time is unknown.
 * @param data - Raw astrology data
 * @param hasTime - Whether the user has a known birth time
 * @returns Filtered data safe to display
 */
export const filterAstrologyForUnknownTime = <T extends Record<string, any>>(
  data: T,
  hasTime: boolean
): T => {
  if (hasTime) return data;
  
  // Create a filtered copy
  const filtered = { ...data };
  
  // Remove time-dependent fields
  TIME_DEPENDENT_ASTROLOGY_FEATURES.forEach(feature => {
    if (feature in filtered) {
      delete filtered[feature];
    }
  });
  
  return filtered;
};
