import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Dimensions,
  TextInput,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../../src/context/AuthContext';
import { api } from '../../src/services/api';
import { COLORS, SPACING, BORDER_RADIUS } from '../../src/constants/theme';
import DateTimePicker from '@react-native-community/datetimepicker';

const { width } = Dimensions.get('window');

interface Question {
  id: string;
  question: string;
  type: 'options' | 'birthdata';
  options?: { value: string; label: string }[];
}

const QUESTIONS: Question[] = [
  {
    id: 'relationship_with_self',
    question: 'How would you describe your current relationship with yourself?',
    type: 'options',
    options: [
      { value: 'curious', label: 'Curious and exploring' },
      { value: 'gentle', label: 'Learning to be gentle' },
      { value: 'complex', label: 'Complex and evolving' },
      { value: 'rebuilding', label: 'Rebuilding foundations' },
    ],
  },
  {
    id: 'reflection_style',
    question: 'When you reflect, what feels most natural to you?',
    type: 'options',
    options: [
      { value: 'writing', label: 'Writing my thoughts down' },
      { value: 'contemplating', label: 'Sitting with a question' },
      { value: 'patterns', label: 'Looking for patterns' },
      { value: 'feeling', label: 'Feeling into my body' },
    ],
  },
  {
    id: 'desired_depth',
    question: 'How deep do you want to go in your reflections?',
    type: 'options',
    options: [
      { value: 'surface', label: 'Light and present-focused' },
      { value: 'moderate', label: 'Thoughtful but not heavy' },
      { value: 'deep', label: 'Deep and meaningful' },
      { value: 'varies', label: 'It varies day by day' },
    ],
  },
  {
    id: 'uncertainty_relationship',
    question: 'How do you relate to not knowing?',
    type: 'options',
    options: [
      { value: 'comfortable', label: 'I find comfort in mystery' },
      { value: 'learning', label: 'Learning to sit with it' },
      { value: 'challenging', label: 'It\'s challenging for me' },
      { value: 'mixed', label: 'Depends on the situation' },
    ],
  },
  {
    id: 'intention',
    question: 'What brings you here today?',
    type: 'options',
    options: [
      { value: 'self_understanding', label: 'To understand myself better' },
      { value: 'daily_practice', label: 'To build a daily practice' },
      { value: 'clarity', label: 'To find more clarity' },
      { value: 'presence', label: 'To be more present' },
    ],
  },
  {
    id: 'birthdata',
    question: 'To personalize your reflections, we can use your birth details (optional)',
    type: 'birthdata',
  },
];

export default function OnboardingQuestions() {
  const router = useRouter();
  const { user, updateUser } = useAuth();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  
  // Birth data state
  const [birthDate, setBirthDate] = useState<Date>(new Date(1990, 0, 1, 12, 0));
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [birthLocation, setBirthLocation] = useState('');
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [skipBirthData, setSkipBirthData] = useState(false);

  const currentQuestion = QUESTIONS[currentIndex];
  const isLastQuestion = currentIndex === QUESTIONS.length - 1;
  const progress = (currentIndex + 1) / QUESTIONS.length;

  const handleSelect = (value: string) => {
    setAnswers({ ...answers, [currentQuestion.id]: value });
  };

  const handleDateChange = (event: any, selectedDate?: Date) => {
    setShowDatePicker(false);
    if (selectedDate) {
      const newDate = new Date(birthDate);
      newDate.setFullYear(selectedDate.getFullYear());
      newDate.setMonth(selectedDate.getMonth());
      newDate.setDate(selectedDate.getDate());
      setBirthDate(newDate);
    }
  };

  const handleTimeChange = (event: any, selectedTime?: Date) => {
    setShowTimePicker(false);
    if (selectedTime) {
      const newDate = new Date(birthDate);
      newDate.setHours(selectedTime.getHours());
      newDate.setMinutes(selectedTime.getMinutes());
      setBirthDate(newDate);
    }
  };

  // Common city coordinates for quick selection
  const COMMON_LOCATIONS = [
    { name: 'New York, USA', lat: 40.7128, lng: -74.0060 },
    { name: 'Los Angeles, USA', lat: 34.0522, lng: -118.2437 },
    { name: 'London, UK', lat: 51.5074, lng: -0.1278 },
    { name: 'Paris, France', lat: 48.8566, lng: 2.3522 },
    { name: 'Tokyo, Japan', lat: 35.6762, lng: 139.6503 },
    { name: 'Sydney, Australia', lat: -33.8688, lng: 151.2093 },
    { name: 'Mumbai, India', lat: 19.0760, lng: 72.8777 },
    { name: 'Berlin, Germany', lat: 52.5200, lng: 13.4050 },
  ];

  const selectLocation = (loc: typeof COMMON_LOCATIONS[0]) => {
    setBirthLocation(loc.name);
    setLatitude(loc.lat);
    setLongitude(loc.lng);
  };

  const canProceedBirthData = () => {
    if (skipBirthData) return true;
    return latitude !== null && longitude !== null;
  };

  const handleNext = async () => {
    if (currentQuestion.type === 'options' && !answers[currentQuestion.id]) {
      return;
    }
    
    if (currentQuestion.type === 'birthdata' && !canProceedBirthData()) {
      return;
    }

    if (isLastQuestion) {
      await submitOnboarding();
    } else {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handleBack = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const submitOnboarding = async () => {
    setLoading(true);
    try {
      // Build the submission data
      const submissionData: Record<string, any> = { ...answers };
      
      // Add birth data if provided
      if (!skipBirthData && latitude !== null && longitude !== null) {
        submissionData.birth_datetime_local = birthDate.toISOString();
        submissionData.tz_offset_minutes = -birthDate.getTimezoneOffset();
        submissionData.latitude = latitude;
        submissionData.longitude = longitude;
      }
      
      await api.post('/onboarding/complete', submissionData);
      
      // Refetch the full user profile to get computed_profile and birth_data
      // that were just computed on the backend
      try {
        const meResponse = await api.get('/auth/me');
        if (meResponse.data) {
          updateUser(meResponse.data);
        }
      } catch (refetchError) {
        // Fallback to basic update if refetch fails
        if (user) {
          updateUser({ ...user, onboarding_completed: true, onboarding_answers: submissionData as any });
        }
      }
      
      router.replace('/(main)/mirror');
    } catch (error: any) {
      Alert.alert('Error', 'Failed to save your responses. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderBirthDataForm = () => (
    <View style={styles.birthDataContainer}>
      <Text style={styles.birthDataSubtitle}>
        This helps personalize your sidereal astrology insights
      </Text>
      
      {/* Date Selection */}
      <View style={styles.birthDataSection}>
        <Text style={styles.birthDataLabel}>Birth Date</Text>
        <TouchableOpacity 
          style={styles.birthDataInput} 
          onPress={() => setShowDatePicker(true)}
        >
          <Text style={styles.birthDataInputText}>
            {birthDate.toLocaleDateString('en-US', { 
              year: 'numeric', 
              month: 'long', 
              day: 'numeric' 
            })}
          </Text>
          <Ionicons name="calendar-outline" size={20} color={COLORS.secondary} />
        </TouchableOpacity>
      </View>

      {/* Time Selection */}
      <View style={styles.birthDataSection}>
        <Text style={styles.birthDataLabel}>Birth Time (approximate is fine)</Text>
        <TouchableOpacity 
          style={styles.birthDataInput} 
          onPress={() => setShowTimePicker(true)}
        >
          <Text style={styles.birthDataInputText}>
            {birthDate.toLocaleTimeString('en-US', { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </Text>
          <Ionicons name="time-outline" size={20} color={COLORS.secondary} />
        </TouchableOpacity>
      </View>

      {/* Location Selection */}
      <View style={styles.birthDataSection}>
        <Text style={styles.birthDataLabel}>Birth Location</Text>
        {birthLocation ? (
          <View style={styles.selectedLocation}>
            <Text style={styles.selectedLocationText}>{birthLocation}</Text>
            <TouchableOpacity onPress={() => { setBirthLocation(''); setLatitude(null); setLongitude(null); }}>
              <Ionicons name="close-circle" size={20} color={COLORS.secondary} />
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.locationGrid}>
            {COMMON_LOCATIONS.map((loc) => (
              <TouchableOpacity
                key={loc.name}
                style={styles.locationChip}
                onPress={() => selectLocation(loc)}
              >
                <Text style={styles.locationChipText}>{loc.name}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </View>

      {/* Skip Option */}
      <TouchableOpacity 
        style={styles.skipOption} 
        onPress={() => setSkipBirthData(!skipBirthData)}
      >
        <View style={[styles.checkbox, skipBirthData && styles.checkboxChecked]}>
          {skipBirthData && <Ionicons name="checkmark" size={14} color={COLORS.white} />}
        </View>
        <Text style={styles.skipOptionText}>Skip for now (can add later)</Text>
      </TouchableOpacity>

      {/* Date/Time Pickers */}
      {showDatePicker && (
        <DateTimePicker
          value={birthDate}
          mode="date"
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          onChange={handleDateChange}
          maximumDate={new Date()}
          minimumDate={new Date(1900, 0, 1)}
        />
      )}
      {showTimePicker && (
        <DateTimePicker
          value={birthDate}
          mode="time"
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          onChange={handleTimeChange}
        />
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        {currentIndex > 0 && (
          <TouchableOpacity onPress={handleBack} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color={COLORS.primary} />
          </TouchableOpacity>
        )}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${progress * 100}%` }]} />
          </View>
          <Text style={styles.progressText}>{currentIndex + 1} of {QUESTIONS.length}</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.question}>{currentQuestion.question}</Text>

        {currentQuestion.type === 'options' && currentQuestion.options && (
          <View style={styles.options}>
            {currentQuestion.options.map((option) => (
              <TouchableOpacity
                key={option.value}
                style={[
                  styles.option,
                  answers[currentQuestion.id] === option.value && styles.optionSelected,
                ]}
                onPress={() => handleSelect(option.value)}
              >
                <Text
                  style={[
                    styles.optionText,
                    answers[currentQuestion.id] === option.value && styles.optionTextSelected,
                  ]}
                >
                  {option.label}
                </Text>
                {answers[currentQuestion.id] === option.value && (
                  <Ionicons name="checkmark" size={20} color={COLORS.accent} />
                )}
              </TouchableOpacity>
            ))}
          </View>
        )}

        {currentQuestion.type === 'birthdata' && renderBirthDataForm()}
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[
            styles.continueButton,
            (currentQuestion.type === 'options' && !answers[currentQuestion.id]) && styles.continueButtonDisabled,
            (currentQuestion.type === 'birthdata' && !canProceedBirthData()) && styles.continueButtonDisabled,
          ]}
          onPress={handleNext}
          disabled={(currentQuestion.type === 'options' && !answers[currentQuestion.id]) || 
                    (currentQuestion.type === 'birthdata' && !canProceedBirthData()) || 
                    loading}
        >
          {loading ? (
            <ActivityIndicator color={COLORS.white} />
          ) : (
            <Text style={styles.continueButtonText}>
              {isLastQuestion ? 'Begin' : 'Continue'}
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.md,
    minHeight: 60,
  },
  backButton: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    marginRight: SPACING.sm,
  },
  progressContainer: {
    flex: 1,
    alignItems: 'flex-end',
  },
  progressBar: {
    width: 120,
    height: 4,
    backgroundColor: COLORS.border,
    borderRadius: 2,
    marginBottom: SPACING.xs,
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.accent,
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: COLORS.secondary,
  },
  content: {
    flexGrow: 1,
    paddingHorizontal: SPACING.lg,
    paddingTop: SPACING.xxl,
  },
  question: {
    fontSize: 26,
    fontWeight: '300',
    color: COLORS.primary,
    lineHeight: 36,
    marginBottom: SPACING.xxl,
  },
  options: {
    gap: SPACING.md,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.white,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  optionSelected: {
    borderColor: COLORS.accent,
    backgroundColor: '#F5F8F3',
  },
  optionText: {
    fontSize: 16,
    color: COLORS.primary,
    flex: 1,
  },
  optionTextSelected: {
    color: COLORS.accent,
  },
  footer: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.lg,
  },
  continueButton: {
    backgroundColor: COLORS.accent,
    paddingVertical: SPACING.md,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
  },
  continueButtonDisabled: {
    opacity: 0.5,
  },
  continueButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: '600',
  },
  // Birth Data Form Styles
  birthDataContainer: {
    gap: SPACING.lg,
  },
  birthDataSubtitle: {
    fontSize: 15,
    color: COLORS.secondary,
    lineHeight: 22,
    marginBottom: SPACING.md,
  },
  birthDataSection: {
    gap: SPACING.sm,
  },
  birthDataLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.primary,
  },
  birthDataInput: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: COLORS.white,
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  birthDataInputText: {
    fontSize: 16,
    color: COLORS.primary,
  },
  locationGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: SPACING.sm,
  },
  locationChip: {
    backgroundColor: COLORS.white,
    paddingVertical: SPACING.sm,
    paddingHorizontal: SPACING.md,
    borderRadius: BORDER_RADIUS.sm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  locationChipText: {
    fontSize: 13,
    color: COLORS.primary,
  },
  selectedLocation: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F5F8F3',
    paddingVertical: SPACING.md,
    paddingHorizontal: SPACING.lg,
    borderRadius: BORDER_RADIUS.md,
    borderWidth: 1,
    borderColor: COLORS.accent,
  },
  selectedLocationText: {
    fontSize: 16,
    color: COLORS.accent,
    fontWeight: '500',
  },
  skipOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: SPACING.sm,
    paddingVertical: SPACING.md,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: COLORS.accent,
    borderColor: COLORS.accent,
  },
  skipOptionText: {
    fontSize: 14,
    color: COLORS.secondary,
  },
});
