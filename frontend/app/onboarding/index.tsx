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
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/colors';
import { useAppStore } from '../../store';
import { createUser, searchLocations, calculateChart } from '../../services/api';
import { Ionicons } from '@expo/vector-icons';

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

  // Auth mode: 'register' or 'login'
  const [authMode, setAuthMode] = useState<'register' | 'login'>('register');
  
  // Login fields
  const [loginEmail, setLoginEmail] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  
  // Registration fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  
  // Date fields (separate boxes)
  const [birthDay, setBirthDay] = useState('');
  const [birthMonth, setBirthMonth] = useState('');
  const [birthYear, setBirthYear] = useState('');
  
  // Time fields (separate boxes with AM/PM)
  const [birthHour, setBirthHour] = useState('');
  const [birthMinute, setBirthMinute] = useState('');
  const [birthPeriod, setBirthPeriod] = useState<'AM' | 'PM'>('AM');
  
  // Location
  const [locationQuery, setLocationQuery] = useState('');
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showLocationDropdown, setShowLocationDropdown] = useState(false);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSearchLocation = async (query: string) => {
    setLocationQuery(query);
    setError('');

    if (query.length < 3) {
      setLocations([]);
      setShowLocationDropdown(false);
      return;
    }

    setIsSearching(true);
    setShowLocationDropdown(true);
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
    setShowLocationDropdown(false);
  };

  // Convert 12-hour to 24-hour format
  const convertTo24Hour = (hour: string, period: 'AM' | 'PM'): string => {
    let h = parseInt(hour, 10);
    if (isNaN(h)) return '';
    
    if (period === 'AM') {
      if (h === 12) h = 0;
    } else {
      if (h !== 12) h += 12;
    }
    
    return h.toString().padStart(2, '0');
  };

  const handleLogin = async () => {
    setError('');
    
    if (!loginEmail.trim()) {
      setError('Please enter your email');
      return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(loginEmail)) {
      setError('Please enter a valid email address');
      return;
    }
    
    setIsLoggingIn(true);
    try {
      // TODO: Implement actual login API
      // For now, show a message that this feature is coming
      setError('Login feature coming soon. Please register as a new user.');
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleSubmit = async () => {
    setError('');

    // Validate email
    if (!email.trim()) {
      setError('Please enter your email');
      return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      return;
    }

    // Validate date fields
    if (!birthDay || !birthMonth || !birthYear) {
      setError('Please enter your complete birth date');
      return;
    }
    
    const day = parseInt(birthDay, 10);
    const month = parseInt(birthMonth, 10);
    const year = parseInt(birthYear, 10);
    
    if (isNaN(day) || day < 1 || day > 31) {
      setError('Please enter a valid day (1-31)');
      return;
    }
    
    if (isNaN(month) || month < 1 || month > 12) {
      setError('Please enter a valid month (1-12)');
      return;
    }
    
    if (isNaN(year) || year < 1900 || year > new Date().getFullYear()) {
      setError('Please enter a valid year');
      return;
    }

    // Validate time if provided
    let birthTime = '';
    if (birthHour && birthMinute) {
      const hour = parseInt(birthHour, 10);
      const minute = parseInt(birthMinute, 10);
      
      if (isNaN(hour) || hour < 1 || hour > 12) {
        setError('Please enter a valid hour (1-12)');
        return;
      }
      
      if (isNaN(minute) || minute < 0 || minute > 59) {
        setError('Please enter a valid minute (0-59)');
        return;
      }
      
      const hour24 = convertTo24Hour(birthHour, birthPeriod);
      birthTime = `${hour24}:${birthMinute.padStart(2, '0')}`;
    }

    if (!selectedLocation) {
      setError('Please select a birth location from the dropdown');
      return;
    }

    // Format date as YYYY-MM-DD
    const birthDate = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;

    setIsSubmitting(true);

    try {
      // Create user with correct API fields
      const userData = await createUser({
        name: name.trim() || undefined,
        email: email.trim() || undefined,
        birth_date: birthDate,
        birth_time: birthTime || undefined,
        city: selectedLocation.city,
        country: selectedLocation.country,
        timezone: '+00:00', // Default timezone - will be geocoded by backend
      });

      await setUser(userData);

      // Calculate chart
      const chartData = await calculateChart(userData.id);
      await setChart(chartData);

      await completeOnboarding();
      router.replace('/(tabs)');
    } catch (err: any) {
      console.error('Submit error:', err);
      setError(err.response?.data?.detail || err.message || 'Something went wrong. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Login View
  if (authMode === 'login') {
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
            <View style={styles.header}>
              <Text style={styles.title}>Project Mirror</Text>
              <Text style={styles.subtitle}>Welcome back</Text>
            </View>

            <View style={styles.form}>
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Email</Text>
                <TextInput
                  style={styles.input}
                  value={loginEmail}
                  onChangeText={setLoginEmail}
                  placeholder="your@email.com"
                  placeholderTextColor={Colors.textTertiary}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoCorrect={false}
                />
              </View>

              {error ? <Text style={styles.error}>{error}</Text> : null}

              <TouchableOpacity
                style={[styles.submitButton, isLoggingIn && styles.submitButtonDisabled]}
                onPress={handleLogin}
                disabled={isLoggingIn}
              >
                {isLoggingIn ? (
                  <ActivityIndicator color={Colors.background} />
                ) : (
                  <Text style={styles.submitButtonText}>Sign In</Text>
                )}
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.switchAuthButton}
                onPress={() => {
                  setAuthMode('register');
                  setError('');
                }}
              >
                <Text style={styles.switchAuthText}>
                  Don't have an account? <Text style={styles.switchAuthLink}>Create one</Text>
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  // Registration View
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
          <View style={styles.header}>
            <Text style={styles.title}>Project Mirror</Text>
            <Text style={styles.subtitle}>A mirror for self-understanding,{'\n'}not a map of your future.</Text>
          </View>

          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Let's begin</Text>
          </View>

          <View style={styles.form}>
            {/* Name */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Name <Text style={styles.optional}>(optional)</Text></Text>
              <TextInput
                style={styles.input}
                value={name}
                onChangeText={setName}
                placeholder="Your name"
                placeholderTextColor={Colors.textTertiary}
                autoCapitalize="words"
              />
            </View>

            {/* Email */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Email</Text>
              <TextInput
                style={styles.input}
                value={email}
                onChangeText={setEmail}
                placeholder="your@email.com"
                placeholderTextColor={Colors.textTertiary}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            {/* Birth Date - Separate Boxes */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Date of Birth</Text>
              <View style={styles.dateRow}>
                <View style={styles.dateBox}>
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
                
                <View style={styles.dateBox}>
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
                
                <View style={[styles.dateBox, styles.yearBox]}>
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

            {/* Birth Time - Separate Boxes with AM/PM */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Time of Birth <Text style={styles.optional}>(if known)</Text></Text>
              <View style={styles.timeRow}>
                <View style={styles.timeBox}>
                  <TextInput
                    style={styles.timeInput}
                    value={birthHour}
                    onChangeText={(text) => setBirthHour(text.replace(/[^0-9]/g, '').slice(0, 2))}
                    placeholder="HH"
                    placeholderTextColor={Colors.textTertiary}
                    keyboardType="number-pad"
                    maxLength={2}
                  />
                  <Text style={styles.timeLabel}>Hour</Text>
                </View>
                
                <Text style={styles.timeSeparator}>:</Text>
                
                <View style={styles.timeBox}>
                  <TextInput
                    style={styles.timeInput}
                    value={birthMinute}
                    onChangeText={(text) => setBirthMinute(text.replace(/[^0-9]/g, '').slice(0, 2))}
                    placeholder="MM"
                    placeholderTextColor={Colors.textTertiary}
                    keyboardType="number-pad"
                    maxLength={2}
                  />
                  <Text style={styles.timeLabel}>Minute</Text>
                </View>
                
                <View style={styles.periodToggle}>
                  <TouchableOpacity
                    style={[styles.periodButton, birthPeriod === 'AM' && styles.periodButtonActive]}
                    onPress={() => setBirthPeriod('AM')}
                  >
                    <Text style={[styles.periodText, birthPeriod === 'AM' && styles.periodTextActive]}>AM</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.periodButton, birthPeriod === 'PM' && styles.periodButtonActive]}
                    onPress={() => setBirthPeriod('PM')}
                  >
                    <Text style={[styles.periodText, birthPeriod === 'PM' && styles.periodTextActive]}>PM</Text>
                  </TouchableOpacity>
                </View>
              </View>
            </View>

            {/* Birth Location */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Birth Location</Text>
              <View style={styles.locationInputWrapper}>
                <TextInput
                  style={styles.input}
                  value={locationQuery}
                  onChangeText={handleSearchLocation}
                  placeholder="Search city..."
                  placeholderTextColor={Colors.textTertiary}
                />
                {isSearching && (
                  <ActivityIndicator 
                    style={styles.locationLoader} 
                    size="small" 
                    color={Colors.textSecondary} 
                  />
                )}
              </View>
              
              {showLocationDropdown && locations.length > 0 && (
                <View style={styles.locationDropdown}>
                  {locations.map((location, index) => (
                    <TouchableOpacity
                      key={index}
                      style={styles.locationItem}
                      onPress={() => handleSelectLocation(location)}
                    >
                      <Ionicons name="location-outline" size={16} color={Colors.textSecondary} />
                      <Text style={styles.locationText}>{location.display_name}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
              
              {selectedLocation && (
                <View style={styles.selectedLocationBadge}>
                  <Ionicons name="checkmark-circle" size={16} color={Colors.success} />
                  <Text style={styles.selectedLocationText}>
                    {selectedLocation.city}, {selectedLocation.country}
                  </Text>
                </View>
              )}
            </View>

            {error ? <Text style={styles.error}>{error}</Text> : null}

            <TouchableOpacity
              style={[styles.submitButton, isSubmitting && styles.submitButtonDisabled]}
              onPress={handleSubmit}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <ActivityIndicator color={Colors.background} />
              ) : (
                <Text style={styles.submitButtonText}>Continue</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.switchAuthButton}
              onPress={() => {
                setAuthMode('login');
                setError('');
              }}
            >
              <Text style={styles.switchAuthText}>
                I have an account. <Text style={styles.switchAuthLink}>Sign in</Text>
              </Text>
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
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    paddingTop: 40,
    paddingBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.text,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 15,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  sectionHeader: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
  },
  form: {
    flex: 1,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 8,
  },
  optional: {
    fontWeight: '400',
    color: Colors.textTertiary,
  },
  input: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  // Date input styles
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dateBox: {
    flex: 1,
    alignItems: 'center',
  },
  yearBox: {
    flex: 1.5,
  },
  dateInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 14,
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    textAlign: 'center',
    width: '100%',
  },
  dateLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  dateSeparator: {
    fontSize: 20,
    color: Colors.textTertiary,
    marginHorizontal: 8,
  },
  // Time input styles
  timeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timeBox: {
    flex: 1,
    alignItems: 'center',
  },
  timeInput: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 14,
    fontSize: 18,
    fontWeight: '600',
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
    textAlign: 'center',
    width: '100%',
  },
  timeLabel: {
    fontSize: 11,
    color: Colors.textTertiary,
    marginTop: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  timeSeparator: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.textTertiary,
    marginHorizontal: 8,
  },
  periodToggle: {
    flexDirection: 'row',
    marginLeft: 12,
    backgroundColor: Colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  periodButton: {
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  periodButtonActive: {
    backgroundColor: Colors.text,
  },
  periodText: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  periodTextActive: {
    color: Colors.background,
  },
  // Location styles
  locationInputWrapper: {
    position: 'relative',
  },
  locationLoader: {
    position: 'absolute',
    right: 16,
    top: 16,
  },
  locationDropdown: {
    backgroundColor: Colors.surface,
    borderRadius: 12,
    marginTop: 8,
    borderWidth: 1,
    borderColor: Colors.border,
    maxHeight: 200,
  },
  locationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
    gap: 8,
  },
  locationText: {
    flex: 1,
    fontSize: 14,
    color: Colors.text,
  },
  selectedLocationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    gap: 6,
  },
  selectedLocationText: {
    fontSize: 14,
    color: Colors.success,
  },
  error: {
    color: Colors.error,
    fontSize: 14,
    marginBottom: 16,
    textAlign: 'center',
  },
  submitButton: {
    backgroundColor: Colors.text,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    color: Colors.background,
    fontSize: 16,
    fontWeight: '600',
  },
  switchAuthButton: {
    marginTop: 20,
    alignItems: 'center',
  },
  switchAuthText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  switchAuthLink: {
    color: Colors.text,
    fontWeight: '600',
  },
});
