import React, { useState, useRef, useCallback, useEffect } from 'react';
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
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { createUser, searchLocations, calculateChart } from '../../services/api';

// Storage key for persisting onboarding progress
const ONBOARDING_PROGRESS_KEY = 'mirror_onboarding_progress';

// Default timezone fallback
const DEFAULT_TIMEZONE = 'Asia/Kuala_Lumpur';

interface Location {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  display_name: string;
}

interface OnboardingProgress {
  step: number;
  name: string;
  email: string;
  birthDay: string;
  birthMonth: string;
  birthYear: string;
  birthHour: string;
  birthMinute: string;
  amPm: 'AM' | 'PM';
  timezone: string;
  locationQuery: string;
  selectedLocation: Location | null;
}

// Detect device timezone using Intl API
const detectTimezone = (): string => {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (tz && tz.length > 0) {
      return tz;
    }
  } catch (e) {
    console.log('[Onboarding] Timezone detection failed:', e);
  }
  return DEFAULT_TIMEZONE;
};

// Validate email format
const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
};

// Validate birth date
const isValidBirthDate = (day: string, month: string, year: string): { valid: boolean; error?: string } => {
  if (!day || !month || !year) {
    return { valid: false, error: 'Please complete all date fields.' };
  }
  
  const d = parseInt(day, 10);
  const m = parseInt(month, 10);
  const y = parseInt(year, 10);
  
  if (isNaN(d) || d < 1 || d > 31) {
    return { valid: false, error: 'Please enter a valid day (1-31).' };
  }
  if (isNaN(m) || m < 1 || m > 12) {
    return { valid: false, error: 'Please enter a valid month (1-12).' };
  }
  if (isNaN(y) || y < 1900 || y > new Date().getFullYear()) {
    return { valid: false, error: 'Please enter a valid year.' };
  }
  
  // Check if date is in the future
  const inputDate = new Date(y, m - 1, d);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  if (inputDate > today) {
    return { valid: false, error: 'Birth date cannot be in the future.' };
  }
  
  // Check if day is valid for the month
  const daysInMonth = new Date(y, m, 0).getDate();
  if (d > daysInMonth) {
    return { valid: false, error: `${month}/${year} only has ${daysInMonth} days.` };
  }
  
  return { valid: true };
};

export default function Onboarding() {
  const router = useRouter();
  const { setUser, setChart, completeOnboarding } = useAppStore();

  // Step state (1-4)
  const [step, setStep] = useState(1);
  
  // Form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [birthDay, setBirthDay] = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthYear, setBirthYear] = useState('');
  const [birthHour, setBirthHour] = useState('');
  const [birthMinute, setBirthMinute] = useState('');
  const [amPm, setAmPm] = useState<'AM' | 'PM'>('AM');
  const [timezone, setTimezone] = useState(detectTimezone());
  const [locationQuery, setLocationQuery] = useState('');
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  
  // UI state
  const [isSearching, setIsSearching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [stepErrors, setStepErrors] = useState<{ [key: number]: string }>({});
  const [fieldErrors, setFieldErrors] = useState<{ [key: string]: string }>({});
  
  // Refs
  const hourInputRef = useRef<TextInput>(null);
  const minuteInputRef = useRef<TextInput>(null);
  const justSelectedRef = useRef(false);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastSearchQueryRef = useRef<string>('');

  // Load saved progress on mount
  useEffect(() => {
    const loadProgress = async () => {
      try {
        const saved = await AsyncStorage.getItem(ONBOARDING_PROGRESS_KEY);
        if (saved) {
          const progress: OnboardingProgress = JSON.parse(saved);
          setStep(progress.step || 1);
          setName(progress.name || '');
          setEmail(progress.email || '');
          setBirthDay(progress.birthDay || '');
          setBirthMonth(progress.birthMonth || '');
          setBirthYear(progress.birthYear || '');
          setBirthHour(progress.birthHour || '');
          setBirthMinute(progress.birthMinute || '');
          setAmPm(progress.amPm || 'AM');
          setTimezone(progress.timezone || detectTimezone());
          setLocationQuery(progress.locationQuery || '');
          setSelectedLocation(progress.selectedLocation || null);
        }
      } catch (e) {
        console.log('[Onboarding] Failed to load progress:', e);
      }
    };
    loadProgress();
  }, []);

  // Save progress whenever form changes
  useEffect(() => {
    const saveProgress = async () => {
      try {
        const progress: OnboardingProgress = {
          step,
          name,
          email,
          birthDay,
          birthMonth,
          birthYear,
          birthHour,
          birthMinute,
          amPm,
          timezone,
          locationQuery,
          selectedLocation,
        };
        await AsyncStorage.setItem(ONBOARDING_PROGRESS_KEY, JSON.stringify(progress));
      } catch (e) {
        console.log('[Onboarding] Failed to save progress:', e);
      }
    };
    saveProgress();
  }, [step, name, email, birthDay, birthMonth, birthYear, birthHour, birthMinute, amPm, timezone, locationQuery, selectedLocation]);

  // Clear progress after successful submission
  const clearProgress = async () => {
    try {
      await AsyncStorage.removeItem(ONBOARDING_PROGRESS_KEY);
    } catch (e) {
      console.log('[Onboarding] Failed to clear progress:', e);
    }
  };

  // Location search handler
  const handleSearchLocation = useCallback(async (query: string) => {
    if (justSelectedRef.current) {
      justSelectedRef.current = false;
      setLocationQuery(query);
      return;
    }
    
    setLocationQuery(query);
    setSelectedLocation(null);
    setFieldErrors(prev => ({ ...prev, location: '' }));

    if (query.length < 3) {
      setLocations([]);
      return;
    }

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    setIsSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      lastSearchQueryRef.current = query;
      
      try {
        const results = await searchLocations(query);
        if (lastSearchQueryRef.current === query) {
          setLocations(results || []);
        }
      } catch (err: any) {
        console.error('Location search error:', err);
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
    justSelectedRef.current = true;
    setSelectedLocation(location);
    setLocationQuery(`${location.city}, ${location.country}`);
    setLocations([]);
    setFieldErrors(prev => ({ ...prev, location: '' }));
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

  // Validation functions for each step
  const validateStep1 = (): boolean => {
    const trimmedName = name.trim();
    if (trimmedName.length < 2) {
      setFieldErrors(prev => ({ ...prev, name: 'Please enter at least 2 characters.' }));
      return false;
    }
    setFieldErrors(prev => ({ ...prev, name: '' }));
    return true;
  };

  const validateStep2 = (): boolean => {
    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail) {
      setFieldErrors(prev => ({ ...prev, email: 'Please enter your email.' }));
      return false;
    }
    if (!isValidEmail(trimmedEmail)) {
      setFieldErrors(prev => ({ ...prev, email: 'Please enter a valid email.' }));
      return false;
    }
    setFieldErrors(prev => ({ ...prev, email: '' }));
    return true;
  };

  const validateStep3 = (): boolean => {
    const validation = isValidBirthDate(birthDay, birthMonth, birthYear);
    if (!validation.valid) {
      setFieldErrors(prev => ({ ...prev, birthDate: validation.error || 'Invalid date.' }));
      return false;
    }
    setFieldErrors(prev => ({ ...prev, birthDate: '' }));
    return true;
  };

  const validateStep4 = (): boolean => {
    if (!selectedLocation) {
      setFieldErrors(prev => ({ ...prev, location: 'Please select a location.' }));
      return false;
    }
    setFieldErrors(prev => ({ ...prev, location: '' }));
    return true;
  };

  // Check if current step is valid (for enabling Continue button)
  const isCurrentStepValid = (): boolean => {
    switch (step) {
      case 1:
        return name.trim().length >= 2;
      case 2:
        return isValidEmail(email.trim());
      case 3:
        return isValidBirthDate(birthDay, birthMonth, birthYear).valid;
      case 4:
        return selectedLocation !== null;
      default:
        return false;
    }
  };

  // Handle step navigation
  const handleNext = () => {
    let isValid = false;
    switch (step) {
      case 1:
        isValid = validateStep1();
        break;
      case 2:
        isValid = validateStep2();
        break;
      case 3:
        isValid = validateStep3();
        break;
      case 4:
        isValid = validateStep4();
        if (isValid) {
          handleSubmit();
          return;
        }
        break;
    }
    
    if (isValid && step < 4) {
      setStep(step + 1);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep(step - 1);
    }
  };

  // Submit handler
  const handleSubmit = async () => {
    setStepErrors({});
    setIsSubmitting(true);
    
    try {
      const birthDate = getFormattedDate();
      const birthTime = get24HourTime();
      
      const userData = await createUser({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        birth_date: birthDate,
        birth_time: birthTime || undefined,
        city: selectedLocation!.city,
        country: selectedLocation!.country,
        timezone: timezone,
        latitude: selectedLocation!.latitude,
        longitude: selectedLocation!.longitude,
      });

      await setUser(userData);
      const chartData = await calculateChart(userData.id);
      await setChart(chartData.data);
      await completeOnboarding();
      await clearProgress();
      
      router.replace('/questionnaire');
    } catch (err: any) {
      console.error('Onboarding error:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Something went wrong. Please try again.';
      setStepErrors({ [step]: errorMsg });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Progress bar component
  const renderProgressBar = () => (
    <View style={styles.progressSection}>
      <Text style={styles.stepIndicator}>Step {step} of 4</Text>
      <View style={styles.progressBarContainer}>
        <View style={[styles.progressBarFill, { width: `${(step / 4) * 100}%` }]} />
      </View>
    </View>
  );

  // Render Step 1: Name
  const renderStep1 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>What's your name?</Text>
      <Text style={styles.stepDescription}>
        This is how we'll greet you in your reflection space.
      </Text>

      <View style={styles.inputGroup}>
        <Text style={styles.label}>Name *</Text>
        <TextInput
          style={[styles.input, fieldErrors.name ? styles.inputError : null]}
          value={name}
          onChangeText={(text) => {
            setName(text);
            if (fieldErrors.name) setFieldErrors(prev => ({ ...prev, name: '' }));
          }}
          placeholder="Your name"
          placeholderTextColor={Colors.textTertiary}
          autoCapitalize="words"
          autoFocus
        />
        {fieldErrors.name ? (
          <Text style={styles.fieldError}>{fieldErrors.name}</Text>
        ) : null}
      </View>
    </View>
  );

  // Render Step 2: Email
  const renderStep2 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Your email</Text>
      <Text style={styles.stepDescription}>
        Used to sign in and recover your reflection space.
      </Text>

      <View style={styles.inputGroup}>
        <Text style={styles.label}>Email *</Text>
        <TextInput
          style={[styles.input, fieldErrors.email ? styles.inputError : null]}
          value={email}
          onChangeText={(text) => {
            setEmail(text);
            if (fieldErrors.email) setFieldErrors(prev => ({ ...prev, email: '' }));
          }}
          placeholder="your@email.com"
          placeholderTextColor={Colors.textTertiary}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
          autoFocus
        />
        {fieldErrors.email ? (
          <Text style={styles.fieldError}>{fieldErrors.email}</Text>
        ) : null}
      </View>
    </View>
  );

  // Render Step 3: Birth Date + Time + Timezone
  const renderStep3 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Birth details</Text>
      <Text style={styles.stepDescription}>
        Your birth moment unlocks personalized frameworks.
      </Text>

      {/* Birth Date */}
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Birth Date *</Text>
        <View style={styles.dateRow}>
          <View style={styles.dateInputContainer}>
            <TextInput
              style={[styles.dateInput, fieldErrors.birthDate ? styles.inputError : null]}
              value={birthDay}
              onChangeText={(text) => {
                setBirthDay(text.replace(/[^0-9]/g, '').slice(0, 2));
                if (fieldErrors.birthDate) setFieldErrors(prev => ({ ...prev, birthDate: '' }));
              }}
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
              style={[styles.dateInput, fieldErrors.birthDate ? styles.inputError : null]}
              value={birthMonth}
              onChangeText={(text) => {
                setBirthMonth(text.replace(/[^0-9]/g, '').slice(0, 2));
                if (fieldErrors.birthDate) setFieldErrors(prev => ({ ...prev, birthDate: '' }));
              }}
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
              style={[styles.dateInput, fieldErrors.birthDate ? styles.inputError : null]}
              value={birthYear}
              onChangeText={(text) => {
                setBirthYear(text.replace(/[^0-9]/g, '').slice(0, 4));
                if (fieldErrors.birthDate) setFieldErrors(prev => ({ ...prev, birthDate: '' }));
              }}
              placeholder="YYYY"
              placeholderTextColor={Colors.textTertiary}
              keyboardType="number-pad"
              maxLength={4}
            />
            <Text style={styles.dateLabel}>Year</Text>
          </View>
        </View>
        {fieldErrors.birthDate ? (
          <Text style={styles.fieldError}>{fieldErrors.birthDate}</Text>
        ) : null}
        <Text style={styles.microcopy}>Used to calculate your lenses. Stored privately.</Text>
      </View>

      {/* Birth Time (Optional) */}
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Birth Time (optional)</Text>
        <View style={styles.timeRow}>
          <View style={styles.timeInputContainer}>
            <TextInput
              ref={hourInputRef}
              style={styles.timeInputLarge}
              value={birthHour}
              onChangeText={(text) => setBirthHour(text.replace(/[^0-9]/g, '').slice(0, 2))}
              placeholder="HH"
              placeholderTextColor={Colors.textTertiary}
              keyboardType="number-pad"
              maxLength={2}
              returnKeyType="next"
              onSubmitEditing={() => minuteInputRef.current?.focus()}
            />
            <Text style={styles.timeLabelBelow}>Hour</Text>
          </View>
          <Text style={styles.timeSeparator}>:</Text>
          <View style={styles.timeInputContainer}>
            <TextInput
              ref={minuteInputRef}
              style={styles.timeInputLarge}
              value={birthMinute}
              onChangeText={(text) => setBirthMinute(text.replace(/[^0-9]/g, '').slice(0, 2))}
              placeholder="MM"
              placeholderTextColor={Colors.textTertiary}
              keyboardType="number-pad"
              maxLength={2}
              returnKeyType="done"
            />
            <Text style={styles.timeLabelBelow}>Min</Text>
          </View>
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
        <Text style={styles.hint}>If unknown, we'll use noon as a neutral time.</Text>
      </View>

      {/* Timezone */}
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Timezone</Text>
        <TextInput
          style={styles.input}
          value={timezone}
          onChangeText={setTimezone}
          placeholder="e.g., Asia/Kuala_Lumpur"
          placeholderTextColor={Colors.textTertiary}
          autoCapitalize="none"
          autoCorrect={false}
        />
        <Text style={styles.microcopy}>Timezone helps calculate timing accurately.</Text>
      </View>
    </View>
  );

  // Render Step 4: Location
  const renderStep4 = () => (
    <View style={styles.stepContainer}>
      <Text style={styles.stepTitle}>Birth location</Text>
      <Text style={styles.stepDescription}>
        Where were you born?
      </Text>

      <View style={styles.inputGroup}>
        <Text style={styles.label}>City & Country *</Text>
        <TextInput
          style={[styles.input, fieldErrors.location ? styles.inputError : null]}
          value={locationQuery}
          onChangeText={handleSearchLocation}
          placeholder="Start typing a city name..."
          placeholderTextColor={Colors.textTertiary}
          autoCapitalize="words"
          autoComplete="off"
          autoCorrect={false}
          autoFocus
        />

        {isSearching && (
          <View style={styles.searchLoaderContainer}>
            <ActivityIndicator size="small" color={Colors.accent} />
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

        {fieldErrors.location ? (
          <Text style={styles.fieldError}>{fieldErrors.location}</Text>
        ) : null}

        {!isSearching && !selectedLocation && locationQuery.length >= 3 && locations.length === 0 && (
          <View style={styles.noResultsContainer}>
            <Text style={styles.noResultsText}>
              No locations found. Try a different search term.
            </Text>
          </View>
        )}
        
        <Text style={styles.microcopy}>Helps set your timezone and sky reference.</Text>
      </View>
    </View>
  );

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
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <Text style={styles.title}>Project Mirror</Text>
            <Text style={styles.subtitle}>
              A mirror for self-understanding, not a map of your future.
            </Text>
          </View>

          {/* Progress Bar */}
          {renderProgressBar()}

          {/* Step Content */}
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}
          {step === 4 && renderStep4()}

          {/* Step Error Message */}
          {stepErrors[step] && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{stepErrors[step]}</Text>
            </View>
          )}

          {/* Navigation Buttons */}
          <View style={styles.buttonContainer}>
            {step > 1 && (
              <TouchableOpacity
                style={[styles.button, styles.buttonSecondary]}
                onPress={handleBack}
                disabled={isSubmitting}
              >
                <Text style={styles.buttonSecondaryText}>Back</Text>
              </TouchableOpacity>
            )}

            <TouchableOpacity
              style={[
                styles.button,
                step > 1 && styles.buttonFlex,
                (!isCurrentStepValid() || isSubmitting) && styles.buttonDisabled
              ]}
              onPress={handleNext}
              disabled={!isCurrentStepValid() || isSubmitting}
            >
              {isSubmitting ? (
                <ActivityIndicator color={Colors.surface} />
              ) : (
                <Text style={styles.buttonText}>
                  {step === 4 ? 'Create My Space' : 'Continue'}
                </Text>
              )}
            </TouchableOpacity>
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
    flexGrow: 1,
    padding: 24,
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  
  // Progress Section
  progressSection: {
    marginBottom: 24,
  },
  stepIndicator: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginBottom: 8,
    fontWeight: '500',
  },
  progressBarContainer: {
    height: 4,
    backgroundColor: Colors.surface,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: Colors.accent,
    borderRadius: 2,
  },
  
  // Step Container
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
    fontSize: 15,
    color: Colors.textSecondary,
    marginBottom: 24,
    lineHeight: 22,
  },
  
  // Input Groups
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
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
    borderColor: 'transparent',
  },
  inputError: {
    borderColor: '#FF6B6B',
  },
  fieldError: {
    fontSize: 13,
    color: '#FF6B6B',
    marginTop: 6,
  },
  microcopy: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 6,
    fontStyle: 'italic',
  },
  hint: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 6,
  },
  
  // Date inputs
  dateRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  dateInputContainer: {
    alignItems: 'center',
  },
  yearInputContainer: {
    flex: 1,
  },
  dateInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 18,
    color: Colors.text,
    textAlign: 'center',
    minWidth: 60,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  dateLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 4,
  },
  dateSeparator: {
    fontSize: 24,
    color: Colors.textTertiary,
    marginHorizontal: 8,
    marginTop: 12,
  },
  
  // Time inputs
  timeRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  timeInputContainer: {
    alignItems: 'center',
  },
  timeInputLarge: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 18,
    color: Colors.text,
    textAlign: 'center',
    minWidth: 60,
  },
  timeLabelBelow: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 4,
  },
  timeSeparator: {
    fontSize: 24,
    color: Colors.textTertiary,
    marginHorizontal: 8,
    marginTop: 12,
  },
  amPmContainer: {
    flexDirection: 'row',
    marginLeft: 12,
  },
  amPmButton: {
    paddingVertical: 16,
    paddingHorizontal: 16,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    marginLeft: 4,
  },
  amPmButtonActive: {
    backgroundColor: Colors.accent,
  },
  amPmText: {
    fontSize: 14,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  amPmTextActive: {
    color: Colors.surface,
  },
  
  // Location search
  searchLoaderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    paddingHorizontal: 4,
  },
  searchingText: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginLeft: 8,
  },
  locationsList: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    marginTop: 8,
    maxHeight: 200,
    overflow: 'hidden',
  },
  locationItem: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  locationText: {
    fontSize: 15,
    color: Colors.text,
  },
  selectedLocation: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    padding: 12,
    backgroundColor: 'rgba(138, 180, 248, 0.1)',
    borderRadius: 8,
  },
  selectedLocationLabel: {
    fontSize: 13,
    color: Colors.textSecondary,
    marginRight: 8,
  },
  selectedLocationText: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  noResultsContainer: {
    marginTop: 8,
    padding: 12,
  },
  noResultsText: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
  },
  
  // Error
  errorContainer: {
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  errorText: {
    color: '#FF6B6B',
    fontSize: 14,
    textAlign: 'center',
  },
  
  // Buttons
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 'auto',
    paddingTop: 24,
  },
  button: {
    flex: 1,
    backgroundColor: Colors.accent,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
  },
  buttonFlex: {
    flex: 2,
  },
  buttonSecondary: {
    flex: 1,
    backgroundColor: Colors.surface,
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: Colors.surface,
    fontSize: 16,
    fontWeight: '600',
  },
  buttonSecondaryText: {
    color: Colors.text,
    fontSize: 16,
    fontWeight: '600',
  },
});
