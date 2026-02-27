import axios from 'axios';

const api = axios.create({
  baseURL: '/api', // Proxy handles target
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add interceptors for auth/errors later if needed
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;
