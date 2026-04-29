import axios from "axios";
import keycloak from "./auth";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
});

api.interceptors.request.use((config) => {
  return Promise.resolve()
    .then(async () => {
      if (keycloak.authenticated) {
        await keycloak.updateToken(30);
      }
      if (keycloak.token) {
        config.headers.Authorization = `Bearer ${keycloak.token}`;
      }
      return config;
    });
});

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && original && !original.headers["X-Retry-Auth"]) {
      try {
        await keycloak.updateToken(-1);
        original.headers.Authorization = `Bearer ${keycloak.token}`;
        original.headers["X-Retry-Auth"] = "1";
        return api.request(original);
      } catch {
        await keycloak.login();
      }
    }
    return Promise.reject(error);
  }
);

export default api;
