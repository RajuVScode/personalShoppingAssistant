const API_BASE = '/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP error ${response.status}`);
  }
  return response.json();
}

export interface LoginCredentials {
  customerId: string;
  password: string;
}

export const api = {
  login: async <T = unknown>(credentials: LoginCredentials): Promise<T> => {
    const response = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_id: credentials.customerId,
        password: credentials.password,
      }),
    });
    return handleResponse<T>(response);
  },

  getCustomer: async <T = unknown>(customerId: string): Promise<T> => {
    const response = await fetch(`${API_BASE}/customers/${customerId}`);
    return handleResponse<T>(response);
  },

  updateCustomer: async <T = unknown>(customerId: string, data: unknown): Promise<T> => {
    const response = await fetch(`${API_BASE}/customers/${customerId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },

  getCustomer360: async <T = unknown>(customerId: string): Promise<T> => {
    const response = await fetch(`${API_BASE}/customer360/${customerId}`);
    return handleResponse<T>(response);
  },

  getProduct: async <T = unknown>(productId: string | number): Promise<T> => {
    const response = await fetch(`${API_BASE}/products/${productId}`);
    return handleResponse<T>(response);
  },

  getGreeting: async (customerId: string): Promise<{ greeting: string }> => {
    const response = await fetch(`${API_BASE}/greeting/${customerId}`);
    return handleResponse<{ greeting: string }>(response);
  },

  getConversation: async <T = unknown>(userId: string): Promise<T> => {
    const response = await fetch(`${API_BASE}/conversation/${userId}`);
    return handleResponse<T>(response);
  },

  sendChatMessage: async <T = unknown>(
    message: string,
    userId: string,
    customerId?: string
  ): Promise<T> => {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        user_id: userId,
        customer_id: customerId,
      }),
    });
    return handleResponse<T>(response);
  },

  resetConversation: async (userId: string): Promise<void> => {
    const response = await fetch(`${API_BASE}/reset?user_id=${userId}`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to reset conversation: ${response.status}`);
    }
  },
};

export default api;
