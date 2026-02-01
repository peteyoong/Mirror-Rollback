import React, { useState } from 'react';
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

interface Location {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
  display_name: string;
  timezone?: string;
}

export default function Onboarding() {
  const router = useRouter();
  const { setUser, setChart, completeOnboarding } = useAppStore();

  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  
  // Separate date fields for clarity
  const [birthDay, setBirthDay] = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthYear, setBirthYear] = useState('');
  
  // Separate time fields
  const [birthHour, setBirthHour] = useState('');
  const [birthMinute, setBirthMinute] = useState('');
  
  const [locationQuery, setLocationQuery] = useState('');
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSearchLocation = async (query: string) => {
    setLocationQuery(query);
    setError('');

    if (query.length < 3) {
      setLocations([]);
      return;
    }

    setIsSearching(true);
    try {
      const results = await searchLocations(query);
      setLocations(results);
    } catch (err) {
      console.error('Location search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectLocation = (location: Location) => {
    setSelectedLocation(location);
    setLocationQuery(`${location.city}, ${location.country}`);
    setLocations([]);
  };

  // Validate and format date components
  const getFormattedDate = (): string | null => {
    const day = parseInt(birthDay, 10);
    const month = parseInt(birthMonth, 10);
    const year = parseInt(birthYear, 10);
    
    if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
    if (day < 1 || day > 31) return null;
    if (month < 1 || month > 12) return null;
    if (year < 1900 || year > new Date().getFullYear()) return null;
    
    // Format as YYYY-MM-DD
    return `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
  };

  // Validate and format time components
  const getFormattedTime = (): string | null => {
    const hour = parseInt(birthHour, 10);
    const minute = parseInt(birthMinute, 10);
    
    if (isNaN(hour) || isNaN(minute)) return null;
    if (hour < 0 || hour > 23) return null;
    if (minute < 0 || minute > 59) return null;
    
    return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
  };

  const handleSubmit = async () => {
    setError('');

    const birthDate = getFormattedDate();
    if (!birthDate) {
      setError('Please enter a valid birth date');
      return;
    }

    const birthTime = getFormattedTime();
    if (!birthTime) {
      setError('Please enter a valid birth time');
      return;
    }

    if (!selectedLocation) {
      setError('Please select a birth location from the dropdown');
      return;
    }

    setIsSubmitting(true);
    try {
      // Create user
      const userData = await createUser({
        name: name || undefined,
        birth_date: birthDate,
        birth_time: birthTime,
        city: selectedLocation.city,
        country: selectedLocation.country,
      });

      setUser(userData);

      // Calculate chart
      const chartData = await calculateChart(userData.id);
      setChart(chartData.data);

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
    if (step === 1) {
      // Need valid date and time
      return getFormattedDate() !== null && getFormattedTime() !== null;
    }
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

              {/* Name */}
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Name</Text>
                <TextInput
                  style={styles.input}
                  value={name}
                  onChangeText={setName}
                  placeholder="What should we call you?"
                  placeholderTextColor={Colors.textTertiary}
                  autoCapitalize="words"
                  autoCorrect={false}
                  returnKeyType="next"
                  selectionColor={Colors.accent}
                />
              </View>

              {/* Date of Birth - Separate boxes */}
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Date of Birth</Text>
                <View style={styles.dateRow}>
                  <View style={styles.dateInputWrapper}>
                    <Text style={styles.dateLabel}>Day</Text>
                    <TextInput
                      style={styles.dateInput}
                      value={birthDay}
                      onChangeText={(text) => setBirthDay(text.replace(/[^0-9]/g, '').slice(0, 2))}
                      placeholder="DD"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                      autoCorrect={false}
                      selectionColor={Colors.accent}
                    />
                  </View>
                  <View style={styles.dateInputWrapper}>
                    <Text style={styles.dateLabel}>Month</Text>
                    <TextInput
                      style={styles.dateInput}
                      value={birthMonth}
                      onChangeText={(text) => setBirthMonth(text.replace(/[^0-9]/g, '').slice(0, 2))}
                      placeholder="MM"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                      autoCorrect={false}
                      selectionColor={Colors.accent}
                    />
                  </View>
                  <View style={[styles.dateInputWrapper, styles.yearInputWrapper]}>
                    <Text style={styles.dateLabel}>Year</Text>
                    <TextInput
                      style={styles.dateInput}
                      value={birthYear}
                      onChangeText={(text) => setBirthYear(text.replace(/[^0-9]/g, '').slice(0, 4))}
                      placeholder="YYYY"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={4}
                      autoCorrect={false}
                      selectionColor={Colors.accent}
                    />
                  </View>
                </View>
              </View>

              {/* Time of Birth - Separate boxes */}
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Time of Birth</Text>
                <View style={styles.timeRow}>
                  <View style={styles.timeInputWrapper}>
                    <Text style={styles.dateLabel}>Hour</Text>
                    <TextInput
                      style={styles.timeInput}
                      value={birthHour}
                      onChangeText={(text) => setBirthHour(text.replace(/[^0-9]/g, '').slice(0, 2))}
                      placeholder="00"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                      autoCorrect={false}
                      selectionColor={Colors.accent}
                    />
                  </View>
                  <Text style={styles.timeSeparator}>:</Text>
                  <View style={styles.timeInputWrapper}>
                    <Text style={styles.dateLabel}>Min</Text>
                    <TextInput
                      style={styles.timeInput}
                      value={birthMinute}
                      onChangeText={(text) => setBirthMinute(text.replace(/[^0-9]/g, '').slice(0, 2))}
                      placeholder="00"
                      placeholderTextColor={Colors.textTertiary}
                      keyboardType="number-pad"
                      maxLength={2}
                      autoCorrect={false}
                      selectionColor={Colors.accent}
                    />
                  </View>
                </View>
                <Text style={styles.hint}>
                  24-hour format (e.g., 14:30 for 2:30 PM)
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
                  placeholder="Start typing..."
                  placeholderTextColor={Colors.textTertiary}
                  autoCapitalize="words"
                />

                {isSearching && (
                  <ActivityIndicator
                    size="small"
                    color={Colors.textSecondary}
                    style={styles.searchLoader}
                  />
                )}

                {locations.length > 0 && (
                  <View style={styles.locationsList}>
                    <FlatList
                      data={locations}
                      keyExtractor={(item, index) => `${item.city}-${index}`}
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
                    <Text style={styles.selectedLocationText}>
                      Selected: {selectedLocation.city}, {selectedLocation.country}
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
    fontSize: 32,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.textSecondary,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 40,
  },
  progressDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: Colors.surfaceLight,
  },
  progressDotActive: {
    backgroundColor: Colors.text,
  },
  progressLine: {
    flex: 1,
    height: 2,
    backgroundColor: Colors.surfaceLight,
    marginHorizontal: 8,
  },
  progressLineActive: {
    backgroundColor: Colors.text,
  },
  stepContainer: {
    marginBottom: 32,
  },
  stepTitle: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  stepDescription: {
    fontSize: 15,
    lineHeight: 22,
    color: Colors.textSecondary,
    marginBottom: 32,
  },
  inputGroup: {
    marginBottom: 24,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
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
    minHeight: 52,
  },
  hint: {
    fontSize: 12,
    color: Colors.textTertiary,
    marginTop: 6,
  },
  // Date row styles
  dateRow: {
    flexDirection: 'row',
    gap: 12,
  },
  dateInputWrapper: {
    flex: 1,
  },
  yearInputWrapper: {
    flex: 1.5,
  },
  dateLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  dateInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 18,
    fontWeight: '500',
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    minHeight: 52,
    textAlign: 'center',
  },
  // Time row styles
  timeRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
  },
  timeInputWrapper: {
    flex: 1,
  },
  timeInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    padding: 16,
    fontSize: 18,
    fontWeight: '500',
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    minHeight: 52,
    textAlign: 'center',
  },
  timeSeparator: {
    fontSize: 24,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 14,
  },
  searchLoader: {
    marginTop: 12,
  },
  locationsList: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    marginTop: 8,
    maxHeight: 200,
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
    marginTop: 12,
    padding: 12,
    backgroundColor: Colors.surfaceLight,
    borderRadius: 8,
  },
  selectedLocationText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  errorContainer: {
    backgroundColor: Colors.error + '20',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  errorText: {
    fontSize: 14,
    color: Colors.error,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    flex: 1,
    backgroundColor: Colors.text,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
  },
  buttonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  buttonDisabled: {
    opacity: 0.4,
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