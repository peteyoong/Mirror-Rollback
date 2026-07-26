import React, { useState, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { createUser, searchLocations, calculateChart } from '../../services/api';
import { fontFamily } from '../../theme/tokens';

// Font-family shorthands so we can use them inside the local StyleSheet
// while keeping the tokens module as the single source of truth.
const displayFont = fontFamily.display;
const textFont = fontFamily.text;

// Debug flag for touch diagnostics
const DEBUG_TOUCHES = __DEV__;

interface Location {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  display_name: string;
}

export default function Onboarding() {
  const router = useRouter();
  const { setUser, setChart, completeOnboarding } = useAppStore();

  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [gender, setGender] = useState<'male' | 'female' | ''>('');
  
  // Separate date fields
  const [birthDay, setBirthDay] = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthYear, setBirthYear] = useState('');
  
  // Separate time fields
  const [birthHour, setBirthHour] = useState('');
  const [birthMinute, setBirthMinute] = useState('');
  const [amPm, setAmPm] = useState<'AM' | 'PM'>('AM');
  
  const [locationQuery, setLocationQuery] = useState('');
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Refs for time inputs
  const hourInputRef = useRef<TextInput>(null);
  const minuteInputRef = useRef<TextInput>(null);

  // Use ref to track if we just selected a location (synchronous, not batched)
  const justSelectedRef = useRef(false);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSearchQueryRef = useRef<string>('');

  const handleSearchLocation = useCallback(async (query: string) => {
    // If we just selected a location, don't search again
    if (justSelectedRef.current) {
      justSelectedRef.current = false;
      setLocationQuery(query);
      return;
    }
    
    setLocationQuery(query);
    setSelectedLocation(null);
    setError('');

    if (query.length < 3) {
      setLocations([]);
      return;
    }

    // Clear any pending search
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    // Debounce the search by 300ms
    setIsSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      // Store the query we're searching for
      lastSearchQueryRef.current = query;
      
      try {
        const results = await searchLocations(query);
        // Only update results if this is still the latest query
        if (lastSearchQueryRef.current === query) {
          // Dedupe by city+country (case-insensitive) — API can return repeats
          const seen = new Set<string>();
          const deduped = (results || []).filter((loc: Location) => {
            const key = `${(loc.city || '').toLowerCase()}|${(loc.country || '').toLowerCase()}`;
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
          });
          setLocations(deduped);
        }
      } catch (err: any) {
        console.error('Location search error:', err);
        // Only show error if we don't have a selected location
        if (!selectedLocation && lastSearchQueryRef.current === query) {
          setLocations([]);
        }
      } finally {
        if (lastSearchQueryRef.current === query) {
          setIsSearching(false);
        }
      }
    }, 300);
  }, [selectedLocation]);

  const handleSelectLocation = (location: Location) => {
    justSelectedRef.current = true; // Prevent re-search (synchronous)
    setSelectedLocation(location);
    setLocationQuery(`${location.city}, ${location.country}`);
    setLocations([]);
    setError(''); // Clear any previous errors
  };

  // Convert to 24-hour format.
  // Accepts either 24-hour input (0-23, AM/PM ignored) OR 12-hour with AM/PM (1-12).
  const get24HourTime = (): string => {
    if (!birthHour || !birthMinute) return '';

    let hour = parseInt(birthHour, 10);

    if (hour >= 13 && hour <= 23) {
      // User entered 24-hour format directly — use as-is
      // (AM/PM toggle is ignored in this case)
    } else if (hour === 0) {
      // 00:xx is valid 24-hour midnight
      hour = 0;
    } else {
      // 1-12 → apply AM/PM
      if (amPm === 'PM' && hour !== 12) {
        hour += 12;
      } else if (amPm === 'AM' && hour === 12) {
        hour = 0;
      }
    }

    return `${String(hour).padStart(2, '0')}:${birthMinute.padStart(2, '0')}`;
  };

  // Helper: navigate between steps and clear any stale error
  const goToStep = (next: number) => {
    setError('');
    setStep(next);
  };

  // Format date as YYYY-MM-DD
  const getFormattedDate = (): string => {
    if (!birthDay || !birthMonth || !birthYear) return '';
    return `${birthYear}-${birthMonth.padStart(2, '0')}-${birthDay.padStart(2, '0')}`;
  };

  const handleSubmit = async () => {
    setError('');

    // Validate birth date
    if (!birthDay || !birthMonth || !birthYear) {
      setError('Please enter your complete birth date');
      return;
    }

    const day = parseInt(birthDay, 10);
    const month = parseInt(birthMonth, 10);
    const year = parseInt(birthYear, 10);

    if (day < 1 || day > 31) {
      setError('Please enter a valid day (1-31)');
      return;
    }
    if (month < 1 || month > 12) {
      setError('Please enter a valid month (1-12)');
      return;
    }
    if (year < 1900 || year > new Date().getFullYear()) {
      setError('Please enter a valid year');
      return;
    }

    // Validate time if provided
    if (birthHour || birthMinute) {
      const hour = parseInt(birthHour, 10);
      const minute = parseInt(birthMinute, 10);

      if (isNaN(hour) || hour < 0 || hour > 23) {
        setError('Please enter a valid hour (0-23, or 1-12 with AM/PM)');
        return;
      }
      if (isNaN(minute) || minute < 0 || minute > 59) {
        setError('Please enter a valid minute (0-59)');
        return;
      }
    }

    if (!selectedLocation) {
      setError('Please select a birth location from the dropdown');
      return;
    }

    setIsSubmitting(true);
    try {
      // Get device timezone offset and convert to string format
      const tzOffsetMinutes = new Date().getTimezoneOffset();
      const tzHours = Math.floor(Math.abs(tzOffsetMinutes) / 60);
      const tzMins = Math.abs(tzOffsetMinutes) % 60;
      const tzSign = tzOffsetMinutes <= 0 ? '+' : '-';
      const timezoneStr = `${tzSign}${String(tzHours).padStart(2, '0')}:${String(tzMins).padStart(2, '0')}`;
      
      const birthDate = getFormattedDate();
      const birthTime = get24HourTime();
      
      // Create user - include latitude/longitude if available (from fallback cities)
      const userData = await createUser({
        name: name || undefined,
        email: email || undefined,
        gender: gender || undefined,
        birth_date: birthDate,
        birth_time: birthTime || undefined,
        city: selectedLocation.city,
        country: selectedLocation.country,
        timezone: timezoneStr,
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
      });

      // Persist user data (wait for storage to complete)
      await setUser(userData);

      // Calculate chart
      const chartData = await calculateChart(userData.id);
      
      // Persist chart data (wait for storage to complete)
      await setChart(chartData.data);

      // Complete onboarding
      await completeOnboarding();

      // Navigate to questionnaire (post-registration onboarding)
      router.replace('/questionnaire');
    } catch (err: any) {
      console.error('Onboarding error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Something went wrong. Please try again.';
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const canProceed = () => {
    if (step === 1) return birthDay && birthMonth && birthYear;
    if (step === 2) return selectedLocation !== null;
    return false;
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>The Mirror</Text>
            <Text style={styles.subtitle}>
              A mirror for self-understanding, not a map of your future.
            </Text>
          </View>

          {/* Progress */}
          <View style={styles.progressContainer}>
            <View style={[styles.progressDot, step >= 1 && styles.progressDotActive]} />
            <View style={[styles.progressLine, step >= 2 && styles.progressLineActive]} />
            <View style={[styles.progressDot, step >= 2 && styles.progressDotActive]} />
          </View>

          {/* Step 1: Basic Info */}
          {step === 1 && (
            <View style={styles.stepContainer}>
              <Text style={styles.stepTitle}>Create your space</Text>
              <Text style={styles.stepDescription}>
                We'll gather a few details to create your unique reflection space.
              </Text>

              {/* Name Field */}
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Name (optional)</Text>
                <TextInput
                  style={styles.input}
                  value={name}
                  onChangeText={setName}
                  placeholder="What should we call you?"
                  placeholderTextColor={Colors.textTertiary}
                  autoCapitalize="words"
                />
              </View>

              {/* Email Field - After Name */}
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Email (optional)</Text>
                <TextInput
                  style={styles.input}
                  value={email}
                  onChangeText={setEmail}
                  placeholder="your@email.com"
                  placeholderTextColor={Colors.textTertiary}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>

              {/* Gender Selector */}
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Gender *</Text>
                <View style={styles.genderRow}>
                  <TouchableOpacity
                    style={[styles.genderButton, gender === 'male' && styles.genderButtonActive]}
                    onPress={() => setGender('male')}
                  >
                    <Text style={[styles.genderButtonText, gender === 'male' && styles.genderButtonTextActive]}>Male</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.genderButton, gender === 'female' && styles.genderButtonActive]}
                    onPress={() => setGender('female')}
                  >
                    <Text style={[styles.genderButtonText, gender === 'female' && styles.genderButtonTextActive]}>Female</Text>
                  </TouchableOpacity>
                </View>
              </View>

              {/* Birth Date - Separate DD/MM/YYYY boxes */}
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Birth Date *</Text>
                <View style={styles.dateRow}>
                  <View style={styles.dateInputContainer}>
                    <TextInput
                      style={styles.dateInput}
                      value={birthDay}
                      onChangeText={(text) => setBirthDay(text.replace(/[^0-9]/g, '').slice(0, 2))}
                      placeholder="DD"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                    />
                    <Text style={styles.dateLabel}>Day</Text>
                  </View>
                  <Text style={styles.dateSeparator}>/</Text>
                  <View style={styles.dateInputContainer}>
                    <TextInput
                      style={styles.dateInput}
                      value={birthMonth}
                      onChangeText={(text) => setBirthMonth(text.replace(/[^0-9]/g, '').slice(0, 2))}
                      placeholder="MM"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                    />
                    <Text style={styles.dateLabel}>Month</Text>
                  </View>
                  <Text style={styles.dateSeparator}>/</Text>
                  <View style={[styles.dateInputContainer, styles.yearInputContainer]}>
                    <TextInput
                      style={styles.dateInput}
                      value={birthYear}
                      onChangeText={(text) => setBirthYear(text.replace(/[^0-9]/g, '').slice(0, 4))}
                      placeholder="YYYY"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={4}
                    />
                    <Text style={styles.dateLabel}>Year</Text>
                  </View>
                </View>
              </View>

              {/* Birth Time - Separate HH:MM with AM/PM */}
              {/* Task 45: Fixed native input - removed Pressable wrappers that were blocking touches */}
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Birth Time</Text>
                <View style={styles.timeRow}>
                  {/* Hour input - no wrapper, direct TextInput for reliable native focus */}
                  <View style={styles.timeInputContainer}>
                    <TextInput
                      ref={hourInputRef}
                      style={styles.timeInput}
                      value={birthHour}
                      onChangeText={(text) => setBirthHour(text.replace(/[^0-9]/g, '').slice(0, 2))}
                      placeholder="HH"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                      returnKeyType="next"
                      onSubmitEditing={() => minuteInputRef.current?.focus()}
                      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                      selectTextOnFocus={true}
                    />
                    <Text style={styles.dateLabel}>Hour</Text>
                  </View>
                  <Text style={styles.timeSeparator}>:</Text>
                  {/* Minute input - no wrapper, direct TextInput for reliable native focus */}
                  <View style={styles.timeInputContainer}>
                    <TextInput
                      ref={minuteInputRef}
                      style={styles.timeInput}
                      value={birthMinute}
                      onChangeText={(text) => setBirthMinute(text.replace(/[^0-9]/g, '').slice(0, 2))}
                      placeholder="MM"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                      returnKeyType="done"
                      hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                      selectTextOnFocus={true}
                    />
                    <Text style={styles.dateLabel}>Min</Text>
                  </View>
                  <View style={styles.amPmContainer}>
                    <TouchableOpacity
                      style={[styles.amPmButton, amPm === 'AM' && styles.amPmButtonActive]}
                      onPress={() => setAmPm('AM')}
                      activeOpacity={0.7}
                    >
                      <Text style={[styles.amPmText, amPm === 'AM' && styles.amPmTextActive]}>AM</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.amPmButton, amPm === 'PM' && styles.amPmButtonActive]}
                      onPress={() => setAmPm('PM')}
                      activeOpacity={0.7}
                    >
                      <Text style={[styles.amPmText, amPm === 'PM' && styles.amPmTextActive]}>PM</Text>
                    </TouchableOpacity>
                  </View>
                </View>
                <Text style={styles.hint}>
                  Enter 1–12 with AM/PM, or 13–23 for 24-hour time. Unknown? We'll use noon.
                </Text>
              </View>
            </View>
          )}

          {/* Step 2: Location */}
          {step === 2 && (
            <View style={styles.stepContainer}>
              <Text style={styles.stepTitle}>Birth location</Text>
              <Text style={styles.stepDescription}>
                Where were you born? This helps us calculate your unique frameworks.
              </Text>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>City & Country *</Text>
                <TextInput
                  style={styles.input}
                  value={locationQuery}
                  onChangeText={handleSearchLocation}
                  placeholder="Start typing a city name..."
                  placeholderTextColor={Colors.textTertiary}
                  autoCapitalize="words"
                  autoComplete="off"
                  autoCorrect={false}
                />

                {isSearching && (
                  <View style={styles.searchLoaderContainer}>
                    <ActivityIndicator
                      size="small"
                      color={Colors.accent}
                    />
                    <Text style={styles.searchingText}>Searching...</Text>
                  </View>
                )}

                {locations.length > 0 && (
                  <View style={styles.locationsList}>
                    <FlatList
                      data={locations}
                      keyExtractor={(item, index) => `${item.city}-${item.country}-${index}`}
                      renderItem={({ item }) => (
                        <TouchableOpacity
                          style={styles.locationItem}
                          onPress={() => handleSelectLocation(item)}
                        >
                          <Text style={styles.locationText}>
                            {item.city}, {item.country}
                          </Text>
                        </TouchableOpacity>
                      )}
                      scrollEnabled={false}
                    />
                  </View>
                )}

                {selectedLocation && (
                  <View style={styles.selectedLocation}>
                    <Text style={styles.selectedLocationLabel}>Selected:</Text>
                    <Text style={styles.selectedLocationText}>
                      {selectedLocation.city}, {selectedLocation.country}
                    </Text>
                  </View>
                )}

                {!isSearching && !selectedLocation && locationQuery.length >= 3 && locations.length === 0 && (
                  <View style={styles.noResultsContainer}>
                    <Text style={styles.noResultsText}>
                      No locations found. Try a different search term.
                    </Text>
                  </View>
                )}
              </View>
            </View>
          )}

          {/* Error Message */}
          {error && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          {/* Navigation Buttons */}
          <View style={styles.buttonContainer}>
            {step === 2 && (
              <TouchableOpacity
                style={[styles.button, styles.buttonSecondary]}
                onPress={() => goToStep(1)}
                disabled={isSubmitting}
              >
                <Text style={styles.buttonSecondaryText}>Back</Text>
              </TouchableOpacity>
            )}

            {step === 1 && (
              <TouchableOpacity
                style={[styles.button, !canProceed() && styles.buttonDisabled]}
                onPress={() => goToStep(2)}
                disabled={!canProceed()}
              >
                <Text style={styles.buttonText}>Enter</Text>
              </TouchableOpacity>
            )}

            {step === 2 && (
              <TouchableOpacity
                style={[
                  styles.button,
                  (!canProceed() || isSubmitting) && styles.buttonDisabled,
                ]}
                onPress={handleSubmit}
                disabled={!canProceed() || isSubmitting}
              >
                {isSubmitting ? (
                  <ActivityIndicator size="small" color={Colors.text} />
                ) : (
                  <Text style={styles.buttonText}>Begin</Text>
                )}
              </TouchableOpacity>
            )}
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 100, // Extra padding to prevent footer overlap with inputs
  },
  header: {
    marginBottom: 32,
    marginTop: 24,
  },
  title: {
    fontFamily: displayFont,
    fontSize: 28,
    fontWeight: '400',
    color: Colors.text,
    marginBottom: 8,
    letterSpacing: 0.3,
    lineHeight: 34,
  },
  subtitle: {
    fontFamily: textFont,
    fontSize: 15,
    color: Colors.textSecondary,
    lineHeight: 24,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 32,
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.border,
  },
  progressDotActive: {
    backgroundColor: Colors.accent,
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  progressLine: {
    width: 48,
    height: 1,
    backgroundColor: Colors.border,
    marginHorizontal: 8,
  },
  progressLineActive: {
    backgroundColor: Colors.accent,
  },
  stepContainer: {
    marginBottom: 24,
  },
  stepTitle: {
    fontFamily: displayFont,
    fontSize: 22,
    fontWeight: '400',
    color: Colors.text,
    marginBottom: 8,
    letterSpacing: 0.2,
    lineHeight: 28,
  },
  stepDescription: {
    fontFamily: textFont,
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 24,
    lineHeight: 22,
  },
  inputGroup: {
    marginBottom: 24,
  },
  label: {
    fontFamily: textFont,
    fontSize: 12,
    fontWeight: '500',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
  input: {
    fontFamily: textFont,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    fontWeight: '400',
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    minHeight: 52,
  },
  hint: {
    fontFamily: textFont,
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 8,
    lineHeight: 18,
  },
  // Date fields
  genderRow: {
    flexDirection: 'row',
    gap: 12,
  },
  genderButton: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: Colors.border,
    backgroundColor: Colors.surface,
    alignItems: 'center',
    minHeight: 48,
    justifyContent: 'center',
  },
  genderButtonActive: {
    borderColor: Colors.accent,
    backgroundColor: Colors.accent + '15',
  },
  genderButtonText: {
    fontFamily: textFont,
    fontSize: 16,
    color: Colors.textSecondary,
    fontWeight: '400',
  },
  genderButtonTextActive: {
    color: Colors.accent,
    fontWeight: '500',
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
  },
  dateInputContainer: {
    flex: 1,
    minWidth: 0,
  },
  yearInputContainer: {
    flex: 1.6,
    minWidth: 0,
  },
  dateInput: {
    fontFamily: textFont,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 8,
    fontSize: 18,
    fontWeight: '400',
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    textAlign: 'center',
    minHeight: 56,
  },
  dateLabel: {
    fontFamily: textFont,
    fontSize: 11,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 6,
    letterSpacing: 0.4,
  },
  dateSeparator: {
    fontFamily: textFont,
    fontSize: 20,
    color: Colors.textTertiary,
    marginTop: 18,
  },
  // Time fields — flex-based so AM/PM never clips on narrow viewports.
  timeRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 6,
    flexWrap: 'wrap',
  },
  timeInputContainer: {
    flex: 1,
    minWidth: 0,
  },
  timeInput: {
    fontFamily: textFont,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 8,
    fontSize: 18,
    fontWeight: '400',
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    textAlign: 'center',
    minHeight: 56,
  },
  timeSeparator: {
    fontFamily: textFont,
    fontSize: 20,
    color: Colors.textTertiary,
    marginTop: 18,
  },
  amPmContainer: {
    flexDirection: 'row',
    marginLeft: 4,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
    height: 56,
  },
  amPmButton: {
    paddingVertical: 0,
    paddingHorizontal: 14,
    justifyContent: 'center',
    alignItems: 'center',
    minWidth: 44,
  },
  amPmButtonActive: {
    backgroundColor: Colors.accent,
  },
  amPmText: {
    fontFamily: textFont,
    fontSize: 13,
    fontWeight: '500',
    color: Colors.textSecondary,
    letterSpacing: 0.4,
  },
  amPmTextActive: {
    color: Colors.surface,
  },
  // Location
  searchLoaderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    gap: 8,
  },
  searchingText: {
    fontSize: 13,
    color: Colors.textSecondary,
  },
  locationsList: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    marginTop: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    maxHeight: 200,
  },
  locationItem: {
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  locationText: {
    fontSize: 15,
    color: Colors.text,
  },
  selectedLocation: {
    marginTop: 12,
    padding: 14,
    backgroundColor: Colors.accent + '15',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.accent + '30',
  },
  selectedLocationLabel: {
    fontSize: 11,
    color: Colors.accent,
    fontWeight: '500',
    marginBottom: 4,
  },
  selectedLocationText: {
    fontSize: 15,
    color: Colors.text,
    fontWeight: '500',
  },
  noResultsContainer: {
    marginTop: 12,
    padding: 14,
    backgroundColor: Colors.surface,
    borderRadius: 12,
  },
  noResultsText: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
  },
  // Error
  errorContainer: {
    backgroundColor: Colors.error + '20',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },
  errorText: {
    fontSize: 14,
    color: Colors.error,
    textAlign: 'center',
  },
  // Buttons - Dark mode with warm beige CTA
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  button: {
    flex: 1,
    backgroundColor: Colors.accent,  // Warm beige #EAE3D9
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.background,  // Dark text on warm beige
  },
  buttonSecondaryText: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.text,
  },
});
// Deployment timestamp: 20260203_102652
