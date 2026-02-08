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
  Pressable,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { createUser, searchLocations, calculateChart } from '../../services/api';

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

  // Refs for time inputs - to enforce focus on tap
  const hourInputRef = useRef<TextInput>(null);
  const minuteInputRef = useRef<TextInput>(null);

  // Use ref to track if we just selected a location (synchronous, not batched)
  const justSelectedRef = useRef(false);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSearchQueryRef = useRef<string>('');

  // Handler to focus hour input
  const handleHourPress = useCallback(() => {
    if (DEBUG_TOUCHES) {
      console.log('[ONBOARDING] HH pressed - focusing hour input');
    }
    hourInputRef.current?.focus();
  }, []);

  // Handler to focus minute input
  const handleMinutePress = useCallback(() => {
    if (DEBUG_TOUCHES) {
      console.log('[ONBOARDING] MM pressed - focusing minute input');
    }
    minuteInputRef.current?.focus();
  }, []);

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
          setLocations(results || []);
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

  // Convert 12-hour to 24-hour format
  const get24HourTime = (): string => {
    if (!birthHour || !birthMinute) return '';
    
    let hour = parseInt(birthHour, 10);
    if (amPm === 'PM' && hour !== 12) {
      hour += 12;
    } else if (amPm === 'AM' && hour === 12) {
      hour = 0;
    }
    
    return `${String(hour).padStart(2, '0')}:${birthMinute.padStart(2, '0')}`;
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
      
      if (hour < 1 || hour > 12) {
        setError('Please enter a valid hour (1-12)');
        return;
      }
      if (minute < 0 || minute > 59) {
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
      <StatusBar style="dark" />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Project Mirror</Text>
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
              <Text style={styles.stepTitle}>Let's begin</Text>
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
              {/* Wrapped in Pressables to ensure taps reach the inputs on iOS */}
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Birth Time (optional)</Text>
                <View style={styles.timeRow}>
                  {/* Hour input with Pressable wrapper for reliable focus */}
                  <Pressable 
                    style={styles.timeInputContainer}
                    onPress={handleHourPress}
                  >
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
                      pointerEvents="auto"
                    />
                    <Text style={styles.dateLabel}>Hour</Text>
                  </Pressable>
                  <Text style={styles.timeSeparator}>:</Text>
                  {/* Minute input with Pressable wrapper for reliable focus */}
                  <Pressable 
                    style={styles.timeInputContainer}
                    onPress={handleMinutePress}
                  >
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
                      pointerEvents="auto"
                    />
                    <Text style={styles.dateLabel}>Min</Text>
                  </Pressable>
                  <View style={styles.amPmContainer}>
                    <TouchableOpacity
                      style={[styles.amPmButton, amPm === 'AM' && styles.amPmButtonActive]}
                      onPress={() => setAmPm('AM')}
                    >
                      <Text style={[styles.amPmText, amPm === 'AM' && styles.amPmTextActive]}>AM</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.amPmButton, amPm === 'PM' && styles.amPmButtonActive]}
                      onPress={() => setAmPm('PM')}
                    >
                      <Text style={[styles.amPmText, amPm === 'PM' && styles.amPmTextActive]}>PM</Text>
                    </TouchableOpacity>
                  </View>
                </View>
                <Text style={styles.hint}>
                  If unknown, we'll use noon as a neutral time
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
                onPress={() => setStep(1)}
                disabled={isSubmitting}
              >
                <Text style={styles.buttonSecondaryText}>Back</Text>
              </TouchableOpacity>
            )}

            {step === 1 && (
              <TouchableOpacity
                style={[styles.button, !canProceed() && styles.buttonDisabled]}
                onPress={() => setStep(2)}
                disabled={!canProceed()}
              >
                <Text style={styles.buttonText}>Continue</Text>
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
                  <ActivityIndicator size="small" color={Colors.background} />
                ) : (
                  <Text style={styles.buttonText}>Begin Journey</Text>
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
  },
  header: {
    marginBottom: 32,
    marginTop: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 32,
  },
  progressDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: Colors.border,
  },
  progressDotActive: {
    backgroundColor: Colors.accent,
  },
  progressLine: {
    width: 60,
    height: 2,
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
    fontSize: 22,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  stepDescription: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 24,
    lineHeight: 20,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: Colors.text,
    marginBottom: 8,
  },
  input: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  hint: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 6,
  },
  // Date fields
  dateRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  dateInputContainer: {
    flex: 1,
  },
  yearInputContainer: {
    flex: 1.5,
  },
  dateInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 18,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    textAlign: 'center',
  },
  dateLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    textAlign: 'center',
    marginTop: 4,
  },
  dateSeparator: {
    fontSize: 24,
    color: Colors.textTertiary,
    marginHorizontal: 8,
    marginTop: 14,
  },
  // Time fields
  timeRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  timeInputContainer: {
    width: 70,
  },
  timeInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 12,
    fontSize: 18,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    textAlign: 'center',
    minHeight: 52,
  },
  timeSeparator: {
    fontSize: 24,
    color: Colors.textTertiary,
    marginHorizontal: 6,
    marginTop: 14,
  },
  amPmContainer: {
    flexDirection: 'row',
    marginLeft: 12,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  amPmButton: {
    paddingVertical: 16,
    paddingHorizontal: 16,
  },
  amPmButtonActive: {
    backgroundColor: Colors.accent,
  },
  amPmText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
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
    fontWeight: '600',
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
  // Buttons
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  button: {
    flex: 1,
    backgroundColor: Colors.text,
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
    fontWeight: '600',
    color: Colors.background,
  },
  buttonSecondaryText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.text,
  },
});
// Deployment timestamp: 20260203_102652
