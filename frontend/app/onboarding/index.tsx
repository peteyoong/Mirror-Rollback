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
  Modal,
  Pressable,
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

// Curated timezone list for selector
const COMMON_TIMEZONES = [
  { label: 'Kuala Lumpur / Singapore', value: 'Asia/Kuala_Lumpur' },
  { label: 'Singapore', value: 'Asia/Singapore' },
  { label: 'Jakarta', value: 'Asia/Jakarta' },
  { label: 'Bangkok', value: 'Asia/Bangkok' },
  { label: 'Hong Kong', value: 'Asia/Hong_Kong' },
  { label: 'Tokyo', value: 'Asia/Tokyo' },
  { label: 'Shanghai', value: 'Asia/Shanghai' },
  { label: 'Dubai', value: 'Asia/Dubai' },
  { label: 'Mumbai', value: 'Asia/Kolkata' },
  { label: 'London', value: 'Europe/London' },
  { label: 'Paris / Berlin', value: 'Europe/Paris' },
  { label: 'New York', value: 'America/New_York' },
  { label: 'Los Angeles', value: 'America/Los_Angeles' },
  { label: 'Sydney', value: 'Australia/Sydney' },
  { label: 'UTC', value: 'UTC' },
];

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
  birthTimeKnown: boolean | null;  // null = not selected, true = knows time, false = doesn't know
  birthHour: string;        // 24-hour format (0-23)
  birthMinute: string;      // (0-59)
  timezone: string;
  locationQuery: string;
  selectedLocation: Location | null;
}

// Detect device timezone using Intl API
const detectTimezone = (): string => {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (tz && tz.length > 0 && isValidTimezone(tz)) {
      return tz;
    }
  } catch (e) {
    console.log('[Onboarding] Timezone detection failed:', e);
  }
  return DEFAULT_TIMEZONE;
};

// Validate timezone format: Region/City pattern or UTC/GMT or offset
const isValidTimezone = (tz: string): boolean => {
  if (!tz || !tz.trim()) return false;
  const trimmed = tz.trim();
  // IANA format: Region/City
  const ianaPattern = /^[A-Za-z_]+\/[A-Za-z0-9_\-]+$/;
  // Offset format: +08:00 or -05:30
  const offsetPattern = /^[+-]\d{2}:\d{2}$/;
  // Special cases
  if (trimmed === 'UTC' || trimmed === 'GMT') return true;
  return ianaPattern.test(trimmed) || offsetPattern.test(trimmed);
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
  const [birthTimeKnown, setBirthTimeKnown] = useState<boolean | null>(null); // null = not selected yet
  const [birthHour, setBirthHour] = useState('');   // 24-hour format (0-23)
  const [birthMinute, setBirthMinute] = useState('');
  const [timezone, setTimezone] = useState(detectTimezone());
  const [showTimezoneModal, setShowTimezoneModal] = useState(false);
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
          // Keep saved selection or null if not yet selected
          setBirthTimeKnown(progress.birthTimeKnown !== undefined ? progress.birthTimeKnown : null);
          // Validate saved timezone
          const savedTz = progress.timezone || detectTimezone();
          setTimezone(isValidTimezone(savedTz) ? savedTz : detectTimezone());
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
          birthTimeKnown,
          birthHour,
          birthMinute,
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
  }, [step, name, email, birthDay, birthMonth, birthYear, birthTimeKnown, birthHour, birthMinute, timezone, locationQuery, selectedLocation]);

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

  // Build canonical birth time string (24-hour format "HH:MM")
  const get24HourTime = (): string | null => {
    // Only return time if user knows their birth time AND has entered valid values
    if (!birthTimeKnown) return null;
    if (!birthHour || !birthMinute) return null;
    
    const hour = parseInt(birthHour, 10);
    const minute = parseInt(birthMinute, 10);
    
    // Validate ranges
    if (isNaN(hour) || hour < 0 || hour > 23) return null;
    if (isNaN(minute) || minute < 0 || minute > 59) return null;
    
    return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`;
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
    // Validate year length first
    if (birthYear.length !== 4) {
      setFieldErrors(prev => ({ ...prev, birthDate: 'Enter full 4-digit year.' }));
      return false;
    }
    
    // Validate birth date
    const dateValidation = isValidBirthDate(birthDay, birthMonth, birthYear);
    if (!dateValidation.valid) {
      setFieldErrors(prev => ({ ...prev, birthDate: dateValidation.error || 'Invalid date.' }));
      return false;
    }
    setFieldErrors(prev => ({ ...prev, birthDate: '' }));
    
    // Birth time selection is REQUIRED
    if (birthTimeKnown === null) {
      setFieldErrors(prev => ({ ...prev, birthTime: 'Please select whether you know your birth time.' }));
      return false;
    }
    
    // Validate birth time if user says they know it
    if (birthTimeKnown === true) {
      const hour = parseInt(birthHour, 10);
      const minute = parseInt(birthMinute, 10);
      
      if (!birthHour || isNaN(hour) || hour < 0 || hour > 23) {
        setFieldErrors(prev => ({ ...prev, birthTime: 'Please enter a valid hour (0-23).' }));
        return false;
      }
      if (!birthMinute || isNaN(minute) || minute < 0 || minute > 59) {
        setFieldErrors(prev => ({ ...prev, birthTime: 'Please enter a valid minute (0-59).' }));
        return false;
      }
    }
    setFieldErrors(prev => ({ ...prev, birthTime: '' }));
    
    // Validate timezone
    if (!isValidTimezone(timezone)) {
      setFieldErrors(prev => ({ ...prev, timezone: 'Please select a valid timezone.' }));
      return false;
    }
    setFieldErrors(prev => ({ ...prev, timezone: '' }));
    
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
      case 3: {
        // Year must be exactly 4 digits
        if (birthYear.length !== 4) {
          return false;
        }
        const dateValid = isValidBirthDate(birthDay, birthMonth, birthYear).valid;
        const tzValid = isValidTimezone(timezone);
        
        // Birth time selection is REQUIRED (null = not selected)
        if (birthTimeKnown === null) {
          return false;
        }
        
        // If time is known, also validate hour/minute
        if (birthTimeKnown === true) {
          const hour = parseInt(birthHour, 10);
          const minute = parseInt(birthMinute, 10);
          const timeValid = !isNaN(hour) && hour >= 0 && hour <= 23 &&
                            !isNaN(minute) && minute >= 0 && minute <= 59;
          return dateValid && tzValid && timeValid;
        }
        
        // If time is explicitly unknown (false), just need date + timezone
        return dateValid && tzValid;
      }
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

  // Submit handler with timeout and robust error handling
  const handleSubmit = async () => {
    if (isSubmitting) return; // Prevent double-submit
    
    setStepErrors({});
    setFieldErrors({});
    setIsSubmitting(true);
    
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s timeout
    
    try {
      const birthDate = getFormattedDate();
      const birthTime = get24HourTime();
      
      // Final client-side validation
      if (!selectedLocation) {
        setFieldErrors(prev => ({ ...prev, location: 'Please select a birth location.' }));
        return;
      }
      
      if (!isValidTimezone(timezone)) {
        setFieldErrors(prev => ({ ...prev, timezone: 'Please select a valid timezone (e.g., Asia/Kuala_Lumpur).' }));
        return;
      }
      
      const payload = {
        name: name.trim(),
        email: email.trim().toLowerCase(),
        birth_date: birthDate,
        birth_time: birthTime || null,  // null if unknown
        birth_time_known: birthTimeKnown,
        city: selectedLocation.city,
        country: selectedLocation.country,
        timezone: timezone.trim(),
        latitude: selectedLocation.latitude,
        longitude: selectedLocation.longitude,
      };
      
      console.log('[Onboarding] Submitting payload:', JSON.stringify(payload, null, 2));
      
      const userData = await createUser(payload);

      clearTimeout(timeoutId);
      
      await setUser(userData);
      const chartData = await calculateChart(userData.id);
      await setChart(chartData.data);
      await completeOnboarding();
      await clearProgress();
      
      router.replace('/questionnaire');
    } catch (err: any) {
      clearTimeout(timeoutId);
      console.error('[Onboarding] Submit error:', err);
      
      // Parse error response
      let errorMsg = 'Something went wrong. Please try again.';
      let errorField: string | null = null;
      
      // Handle timeout
      if (err.name === 'AbortError' || err.code === 'ECONNABORTED') {
        errorMsg = 'Connection timed out — please try again.';
      }
      // Handle network error
      else if (err.message === 'Network Error' || !err.response) {
        errorMsg = 'Network error — please check your connection and try again.';
      }
      // Handle server errors (500+)
      else if (err.response?.status >= 500) {
        const errorId = err.response?.data?.error_id || 'unknown';
        errorMsg = `Server error — please try again in a moment. (ref: ${errorId})`;
      }
      // Handle validation/client errors (400-499)
      else if (err.response?.data) {
        const data = err.response.data;
        if (data.message) {
          errorMsg = data.message;
        } else if (data.detail) {
          errorMsg = typeof data.detail === 'string' ? data.detail : 'Validation error — please check your inputs.';
        }
        if (data.field) {
          errorField = data.field;
        }
        // Include error_id if present
        if (data.error_id) {
          errorMsg += ` (ref: ${data.error_id})`;
        }
      }
      
      // Show field-specific error or general error
      if (errorField) {
        setFieldErrors(prev => ({ ...prev, [errorField!]: errorMsg }));
        // If it's email error, go back to step 2
        if (errorField === 'email') {
          setStep(2);
        }
      } else {
        setStepErrors({ [step]: errorMsg });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Timezone selector modal
  const renderTimezoneModal = () => (
    <Modal
      visible={showTimezoneModal}
      animationType="slide"
      transparent={true}
      onRequestClose={() => setShowTimezoneModal(false)}
    >
      <Pressable 
        style={styles.modalOverlay} 
        onPress={() => setShowTimezoneModal(false)}
      >
        <Pressable style={styles.modalContent} onPress={e => e.stopPropagation()}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Select Timezone</Text>
            <TouchableOpacity onPress={() => setShowTimezoneModal(false)}>
              <Text style={styles.modalClose}>Done</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.modalHint}>
            Format: Region/City (e.g., Asia/Kuala_Lumpur)
          </Text>
          <ScrollView style={styles.timezoneList}>
            {COMMON_TIMEZONES.map((tz) => (
              <TouchableOpacity
                key={tz.value}
                style={[
                  styles.timezoneItem,
                  timezone === tz.value && styles.timezoneItemSelected
                ]}
                onPress={() => {
                  setTimezone(tz.value);
                  setFieldErrors(prev => ({ ...prev, timezone: '' }));
                  setShowTimezoneModal(false);
                }}
              >
                <Text style={[
                  styles.timezoneLabel,
                  timezone === tz.value && styles.timezoneLabelSelected
                ]}>
                  {tz.label}
                </Text>
                <Text style={styles.timezoneValue}>{tz.value}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </Pressable>
      </Pressable>
    </Modal>
  );

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
          <View style={styles.dateFieldWrapper}>
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
          <View style={styles.dateFieldWrapper}>
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
          <View style={styles.dateFieldWrapper}>
            <TextInput
              style={[styles.dateInputYear, fieldErrors.birthDate ? styles.inputError : null]}
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

      {/* Birth Time Known Toggle */}
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Do you know your birth time? *</Text>
        <View style={styles.segmentedControl}>
          <TouchableOpacity
            style={[
              styles.segmentButton,
              birthTimeKnown === false && styles.segmentButtonActive
            ]}
            onPress={() => {
              setBirthTimeKnown(false);
              setBirthHour('');
              setBirthMinute('');
              setFieldErrors(prev => ({ ...prev, birthTime: '' }));
            }}
          >
            <Text style={[
              styles.segmentText,
              birthTimeKnown === false && styles.segmentTextActive
            ]}>I don't know</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[
              styles.segmentButton,
              birthTimeKnown === true && styles.segmentButtonActive
            ]}
            onPress={() => {
              setBirthTimeKnown(true);
              setFieldErrors(prev => ({ ...prev, birthTime: '' }));
            }}
          >
            <Text style={[
              styles.segmentText,
              birthTimeKnown === true && styles.segmentTextActive
            ]}>I know my time</Text>
          </TouchableOpacity>
        </View>
        {birthTimeKnown === null && (
          <Text style={styles.microcopy}>Please select one option.</Text>
        )}
      </View>

      {/* Birth Time Input (24-hour format) - Only shown when known */}
      {birthTimeKnown === true && (
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Birth Time (24-hour format)</Text>
          <View style={styles.timeRow}>
            <View style={styles.timeInputContainer}>
              <TextInput
                ref={hourInputRef}
                style={[styles.timeInputLarge, fieldErrors.birthTime ? styles.inputError : null]}
                value={birthHour}
                onChangeText={(text) => {
                  const cleaned = text.replace(/[^0-9]/g, '').slice(0, 2);
                  setBirthHour(cleaned);
                  if (fieldErrors.birthTime) setFieldErrors(prev => ({ ...prev, birthTime: '' }));
                }}
                placeholder="HH"
                placeholderTextColor={Colors.textTertiary}
                keyboardType="number-pad"
                maxLength={2}
                returnKeyType="next"
                onSubmitEditing={() => minuteInputRef.current?.focus()}
              />
              <Text style={styles.timeLabelBelow}>Hour (0-23)</Text>
            </View>
            <Text style={styles.timeSeparator}>:</Text>
            <View style={styles.timeInputContainer}>
              <TextInput
                ref={minuteInputRef}
                style={[styles.timeInputLarge, fieldErrors.birthTime ? styles.inputError : null]}
                value={birthMinute}
                onChangeText={(text) => {
                  const cleaned = text.replace(/[^0-9]/g, '').slice(0, 2);
                  setBirthMinute(cleaned);
                  if (fieldErrors.birthTime) setFieldErrors(prev => ({ ...prev, birthTime: '' }));
                }}
                placeholder="MM"
                placeholderTextColor={Colors.textTertiary}
                keyboardType="number-pad"
                maxLength={2}
                returnKeyType="done"
              />
              <Text style={styles.timeLabelBelow}>Min (0-59)</Text>
            </View>
          </View>
          {fieldErrors.birthTime ? (
            <Text style={styles.fieldError}>{fieldErrors.birthTime}</Text>
          ) : null}
          <Text style={styles.hint}>e.g., 07:25 = 7:25 AM, 19:40 = 7:40 PM</Text>
        </View>
      )}

      {/* Helper text for unknown time */}
      {birthTimeKnown === false && (
        <View style={styles.unknownTimeInfo}>
          <Text style={styles.unknownTimeText}>
            You can add your birth time later to unlock Human Design and exact house placements.
          </Text>
        </View>
      )}

      {/* Timezone - Read-only with Change button */}
      <View style={styles.inputGroup}>
        <Text style={styles.label}>Timezone</Text>
        <TouchableOpacity 
          style={[styles.timezoneDisplay, fieldErrors.timezone ? styles.inputError : null]}
          onPress={() => setShowTimezoneModal(true)}
        >
          <Text style={styles.timezoneText}>{timezone}</Text>
          <Text style={styles.timezoneChange}>Change</Text>
        </TouchableOpacity>
        {fieldErrors.timezone ? (
          <Text style={styles.fieldError}>{fieldErrors.timezone}</Text>
        ) : null}
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
      
      {/* Timezone Selector Modal */}
      {renderTimezoneModal()}
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
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 24,
  },
  header: {
    marginBottom: 20,
  },
  title: {
    fontSize: 26,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  
  // Progress Section - Fixed for mobile Safari
  progressSection: {
    marginBottom: 20,
    width: '100%',
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
    width: '100%',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: Colors.accent,
    borderRadius: 2,
  },
  
  // Step Container
  stepContainer: {
    marginBottom: 20,
  },
  stepTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 6,
  },
  stepDescription: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 20,
    lineHeight: 20,
  },
  
  // Input Groups
  inputGroup: {
    marginBottom: 18,
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
    padding: 14,
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
    justifyContent: 'flex-start',
  },
  dateFieldWrapper: {
    alignItems: 'center',
  },
  dateInput: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 12,
    fontSize: 16,
    color: Colors.text,
    textAlign: 'center',
    width: 52,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  dateInputYear: {
    backgroundColor: Colors.surface,
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 10,
    fontSize: 16,
    color: Colors.text,
    textAlign: 'center',
    minWidth: 80,  // Ensure 4 digits fit comfortably
    borderWidth: 1,
    borderColor: 'transparent',
  },
  dateLabel: {
    fontSize: 10,
    color: Colors.textTertiary,
    marginTop: 4,
  },
  dateSeparator: {
    fontSize: 18,
    color: Colors.textTertiary,
    marginHorizontal: 4,
    marginTop: 10,
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
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 14,
    fontSize: 16,
    color: Colors.text,
    textAlign: 'center',
    minWidth: 55,
    borderWidth: 1,
    borderColor: 'transparent',
  },
  timeLabelBelow: {
    fontSize: 10,
    color: Colors.textTertiary,
    marginTop: 4,
  },
  timeSeparator: {
    fontSize: 20,
    color: Colors.textTertiary,
    marginHorizontal: 6,
    marginTop: 10,
  },
  amPmContainer: {
    flexDirection: 'row',
    marginLeft: 10,
  },
  amPmButton: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    backgroundColor: Colors.surface,
    borderRadius: 10,
    marginLeft: 4,
  },
  amPmButtonActive: {
    backgroundColor: Colors.accent,
  },
  amPmText: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  amPmTextActive: {
    color: Colors.surface,
  },
  
  // Timezone display
  timezoneDisplay: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 14,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'transparent',
  },
  timezoneText: {
    fontSize: 15,
    color: Colors.text,
    flex: 1,
  },
  timezoneChange: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '600',
  },
  
  // Segmented control (birth time known toggle)
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: Colors.surface,
    borderRadius: 10,
    padding: 4,
  },
  segmentButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  segmentButtonActive: {
    backgroundColor: Colors.accent,
  },
  segmentText: {
    fontSize: 14,
    color: Colors.textSecondary,
    fontWeight: '500',
  },
  segmentTextActive: {
    color: Colors.surface,
    fontWeight: '600',
  },
  
  // Unknown time helper
  unknownTimeInfo: {
    backgroundColor: 'rgba(147, 130, 255, 0.1)',
    borderRadius: 10,
    padding: 12,
    marginTop: 8,
  },
  unknownTimeText: {
    fontSize: 13,
    color: Colors.accent,
    lineHeight: 18,
  },
  
  // Modal
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '70%',
    paddingBottom: Platform.OS === 'ios' ? 34 : 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  modalTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: Colors.text,
  },
  modalClose: {
    fontSize: 16,
    color: Colors.accent,
    fontWeight: '600',
  },
  modalHint: {
    fontSize: 12,
    color: Colors.textTertiary,
    paddingHorizontal: 16,
    paddingVertical: 8,
    fontStyle: 'italic',
  },
  timezoneList: {
    paddingHorizontal: 16,
  },
  timezoneItem: {
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  timezoneItemSelected: {
    backgroundColor: 'rgba(138, 180, 248, 0.1)',
    marginHorizontal: -16,
    paddingHorizontal: 16,
    borderRadius: 8,
  },
  timezoneLabel: {
    fontSize: 15,
    color: Colors.text,
    marginBottom: 2,
  },
  timezoneLabelSelected: {
    color: Colors.accent,
    fontWeight: '600',
  },
  timezoneValue: {
    fontSize: 12,
    color: Colors.textTertiary,
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
    maxHeight: 180,
    overflow: 'hidden',
  },
  locationItem: {
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  locationText: {
    fontSize: 14,
    color: Colors.text,
  },
  selectedLocation: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
    padding: 10,
    backgroundColor: 'rgba(138, 180, 248, 0.1)',
    borderRadius: 8,
  },
  selectedLocationLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginRight: 6,
  },
  selectedLocationText: {
    fontSize: 14,
    color: Colors.accent,
    fontWeight: '500',
  },
  noResultsContainer: {
    marginTop: 8,
    padding: 10,
  },
  noResultsText: {
    fontSize: 13,
    color: Colors.textTertiary,
    textAlign: 'center',
  },
  
  // Error
  errorContainer: {
    backgroundColor: 'rgba(255, 107, 107, 0.1)',
    borderRadius: 10,
    padding: 14,
    marginBottom: 14,
  },
  errorText: {
    color: '#FF6B6B',
    fontSize: 14,
    textAlign: 'center',
  },
  
  // Buttons
  buttonContainer: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 'auto',
    paddingTop: 20,
  },
  button: {
    flex: 1,
    backgroundColor: Colors.accent,
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 50,
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
