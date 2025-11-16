import { useEffect, useState } from "react";
import Footer from "./Footer";
import Header from "./Header";
import Projects from "./Projects";
import { useAuth0 } from "@auth0/auth0-react";


export default function App() {
  const [hash, setHash] = useState('#/projects');

  useEffect(() => {
    // Initialize from current location
    setHash(window.location.hash || '#/projects');
    const onHash = () => setHash(window.location.hash || '#/projects');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  let page;
  switch (hash) {
    case '#/projects':
    default:
      page = <Projects />;
  }

  return (
    <>
      <Header />
      
      <Footer />
    </>
  );
}
