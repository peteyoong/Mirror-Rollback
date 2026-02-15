/**
 * Safe Error Parser Utility
 * 
 * Parses API error responses safely, never exposing raw HTML to users.
 * Handles 502/503/504 gateway errors gracefully.
 */

// Gateway error status codes that warrant retry
export const GATEWAY_ERROR_CODES = [502, 503, 504];

// Network error indicators
export const NETWORK_ERROR_MESSAGES = [
  'Network Error',
  'Failed to fetch',
  'Network request failed',
  'ECONNREFUSED',
  'ETIMEDOUT',
];

export interface ParsedError {
  message: string;
  isGatewayError: boolean;
  isNetworkError: boolean;
  isRetryable: boolean;
  status: number | null;
}

/**
 * Check if a string looks like HTML content
 */
function looksLikeHtml(text: string): boolean {
  const trimmed = text.trim().toLowerCase();
  return (
    trimmed.startsWith('<!doctype') ||
    trimmed.startsWith('<html') ||
    trimmed.startsWith('<head') ||
    trimmed.startsWith('<body') ||
    /<html[\s>]/i.test(text)
  );
}

/**
 * Extract error message from JSON response
 */
function extractJsonMessage(data: any): string | null {
  if (!data || typeof data !== 'object') return null;
  
  // Common error message fields
  const messageFields = ['message', 'detail', 'error', 'msg', 'reason'];
  for (const field of messageFields) {
    if (data[field] && typeof data[field] === 'string') {
      return data[field];
    }
  }
  
  // FastAPI validation error format
  if (Array.isArray(data.detail)) {
    const first = data.detail[0];
    if (first?.msg) {
      return first.msg;
    }
  }
  
  return null;
}

/**
 * Get friendly message for HTTP status code
 */
function getFriendlyStatusMessage(status: number): string {
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input.';
    case 401:
      return 'Authentication required. Please log in.';
    case 403:
      return 'Access denied.';
    case 404:
      return 'Service not found. Please try again later.';
    case 408:
      return 'Request timed out. Please try again.';
    case 429:
      return 'Too many requests. Please wait a moment.';
    case 500:
      return 'Server error. Please try again later.';
    case 502:
      return 'Server temporarily unavailable (502). Please try again.';
    case 503:
      return 'Service temporarily unavailable (503). Please try again.';
    case 504:
      return 'Gateway timeout (504). Please try again.';
    default:
      if (status >= 500) {
        return `Server error (${status}). Please try again later.`;
      }
      return `Request failed (${status}).`;
  }
}

/**
 * Parse an API error response safely
 * Never returns raw HTML - always a user-friendly message
 */
export function parseApiError(error: any): ParsedError {
  const result: ParsedError = {
    message: 'Something went wrong. Please try again.',
    isGatewayError: false,
    isNetworkError: false,
    isRetryable: false,
    status: null,
  };

  // Handle Axios/fetch errors
  if (error.response) {
    // Server responded with error status
    const status = error.response.status;
    result.status = status;
    result.isGatewayError = GATEWAY_ERROR_CODES.includes(status);
    result.isRetryable = result.isGatewayError || status >= 500;

    // Try to extract response data
    const data = error.response.data;
    
    if (typeof data === 'string') {
      // Check if it's HTML
      if (looksLikeHtml(data)) {
        result.message = getFriendlyStatusMessage(status);
      } else {
        // Plain text error - cap length
        result.message = data.length > 200 ? data.substring(0, 200) + '...' : data;
      }
    } else if (typeof data === 'object') {
      // Try to extract JSON message
      const jsonMessage = extractJsonMessage(data);
      if (jsonMessage) {
        result.message = jsonMessage.length > 200 ? jsonMessage.substring(0, 200) + '...' : jsonMessage;
      } else {
        result.message = getFriendlyStatusMessage(status);
      }
    } else {
      result.message = getFriendlyStatusMessage(status);
    }
  } else if (error.request) {
    // Request made but no response received
    result.isNetworkError = true;
    result.isRetryable = true;
    result.message = 'Unable to reach server. Please check your connection.';
  } else if (error.message) {
    // Check for network error messages
    const isNetworkError = NETWORK_ERROR_MESSAGES.some(msg => 
      error.message.toLowerCase().includes(msg.toLowerCase())
    );
    
    if (isNetworkError) {
      result.isNetworkError = true;
      result.isRetryable = true;
      result.message = 'Unable to reach server. Please check your connection.';
    } else {
      // Other error - sanitize message
      const msg = error.message;
      if (looksLikeHtml(msg)) {
        result.message = 'An unexpected error occurred. Please try again.';
      } else {
        result.message = msg.length > 200 ? msg.substring(0, 200) + '...' : msg;
      }
    }
  }

  return result;
}

/**
 * Format error for display (even shorter for UI)
 */
export function formatErrorForDisplay(error: any, maxLength: number = 100): string {
  const parsed = parseApiError(error);
  if (parsed.message.length > maxLength) {
    return parsed.message.substring(0, maxLength) + '...';
  }
  return parsed.message;
}
