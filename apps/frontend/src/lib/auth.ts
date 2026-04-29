import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8080",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "pki",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "pki-frontend",
});

export async function initAuth() {
  await keycloak.init({
    onLoad: "login-required",
    pkceMethod: "S256",
    checkLoginIframe: false,
  });
  return keycloak;
}

export default keycloak;
