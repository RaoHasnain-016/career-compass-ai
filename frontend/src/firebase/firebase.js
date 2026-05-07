import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyBwx1Kpgd0VbBH2Ei2rtkrnvNuQkLMUaQc",
  authDomain: "career-compass-ai-c058c.firebaseapp.com",
  projectId: "career-compass-ai-c058c",
  storageBucket: "career-compass-ai-c058c.firebasestorage.app",
  messagingSenderId: "717094608157",
  appId: "1:717094608157:web:654c42e164d225f76015f4",
  measurementId: "G-869Q7S86LV",
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

googleProvider.setCustomParameters({
  prompt: "select_account",
});

export { app, auth, googleProvider };
export default app;
