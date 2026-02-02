import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

interface IncompleteBirthDataCardProps {
  missingFields?: string[];
  lensName?: string;
  onComplete?: () => void;
}

/**
 * Compact card shown when birth data is incomplete.
 * Prompts user to complete their birth details before charts can be computed.
 */
export default function IncompleteBirthDataCard({ 
  missingFields = [], 
  lensName = 'this lens',
  onComplete 
}: IncompleteBirthDataCardProps) {
  const router = useRouter();
  
  // Map field names to friendly labels
  const friendlyFieldNames: Record<string, string> = {
    'birth_date': 'Birth date',
    'birth_time_local': 'Birth time',
    'lat': 'Birth location',
    'lon': 'Birth location',
    'timezone_iana': 'Timezone',
  };
  
  // Deduplicate and get friendly names
  const uniqueFields = [...new Set(missingFields.map(f => {
    if (f === 'lat' || f === 'lon') return 'location';
    return f;
  }))];
  
  const friendlyNames = uniqueFields.map(f => 
    friendlyFieldNames[f] || friendlyFieldNames[f.replace('_', ' ')] || f
  );
  
  const handleComplete = () => {
    if (onComplete) {
      onComplete();
    } else {
      // Navigate to profile/settings to complete birth data
      router.push('/profile');
    }
  };
  
  return (
    <View style={styles.container}>
      <View style={styles.iconContainer}>
        <Ionicons name="information-circle-outline" size={24} color="#8B7355" />
      </View>
      
      <View style={styles.content}>
        <Text style={styles.title}>Complete Your Birth Details</Text>
        <Text style={styles.description}>
          To unlock {lensName}, we need a bit more information about your birth.
        </Text>
        
        {friendlyNames.length > 0 && (
          <View style={styles.missingList}>
            <Text style={styles.missingLabel}>Missing:</Text>
            <Text style={styles.missingItems}>
              {friendlyNames.join(', ')}
            </Text>
          </View>
        )}
      </View>
      
      <TouchableOpacity 
        style={styles.button} 
        onPress={handleComplete}
        activeOpacity={0.7}
      >
        <Text style={styles.buttonText}>Complete</Text>
        <Ionicons name="chevron-forward" size={16} color="#FFFFFF" />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FDF8F3',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginVertical: 12,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E8DDD4',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F5EDE5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  content: {
    flex: 1,
    marginRight: 12,
  },
  title: {
    fontSize: 15,
    fontWeight: '600',
    color: '#3D3D3D',
    marginBottom: 4,
  },
  description: {
    fontSize: 13,
    color: '#6B6B6B',
    lineHeight: 18,
  },
  missingList: {
    flexDirection: 'row',
    marginTop: 6,
    flexWrap: 'wrap',
  },
  missingLabel: {
    fontSize: 12,
    color: '#8B7355',
    fontWeight: '500',
  },
  missingItems: {
    fontSize: 12,
    color: '#8B7355',
    marginLeft: 4,
  },
  button: {
    backgroundColor: '#8B7355',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
    marginRight: 4,
  },
});
