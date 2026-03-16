import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { AuthProvider } from "./contexts/AuthContext.tsx";
import { BRAND, UI } from "./constants";

// Set dynamic document metadata from constants
document.title = BRAND.NAME;

// Update meta tags dynamically
const setMetaTag = (name: string, content: string, property?: boolean) => {
  const selector = property ? `meta[property="${name}"]` : `meta[name="${name}"]`;
  const meta = document.querySelector(selector) as HTMLMetaElement;
  if (meta) {
    meta.content = content;
  }
};

// Update all brand-specific meta tags
setMetaTag('author', BRAND.NAME);
setMetaTag('application-name', BRAND.NAME);
setMetaTag('keywords', BRAND.KEYWORDS);
setMetaTag('description', BRAND.DESCRIPTION);
setMetaTag('theme-color', UI.THEME_COLOR);
setMetaTag('og:site_name', BRAND.NAME, true);
setMetaTag('og:title', `${BRAND.NAME} - ${BRAND.TAGLINE}`, true);
setMetaTag('og:description', BRAND.DESCRIPTION, true);
setMetaTag('twitter:title', `${BRAND.NAME} - ${BRAND.TAGLINE}`);
setMetaTag('twitter:description', BRAND.DESCRIPTION);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>
);
