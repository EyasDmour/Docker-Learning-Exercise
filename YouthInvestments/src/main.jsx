import React from "react";
import ReactDOM from "react-dom/client";
import { Auth0Provider } from '@auth0/auth0-react';
import App from "./App.jsx";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Auth0Provider
      domain="youthinvestments.eu.auth0.com"
      clientId="zfTlibCa5GL9UiRo3WD15g2lzfG4EKfg"
      authorizationParams={{ redirect_uri: window.location.origin 
      }}
    >
      <App />
    </Auth0Provider>
  </React.StrictMode>
);
