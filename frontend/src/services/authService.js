import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updateProfile,
} from "firebase/auth";
import { auth, googleProvider } from "../firebase/firebase";
import { get, post } from "./api";

export async function syncFirebaseUser(user = auth.currentUser, fullName = "") {
  if (!user) {
    throw new Error("No Firebase user is available to sync.");
  }

  const payload = fullName ? { full_name: fullName } : {};
  return post("/auth/firebase-login", payload, { forceRefreshToken: true });
}

export async function getCurrentBackendUser() {
  return get("/auth/me");
}

export async function signupWithEmail(email, password, fullName = "") {
  const result = await createUserWithEmailAndPassword(auth, email, password);

  if (fullName) {
    await updateProfile(result.user, { displayName: fullName });
    await result.user.reload();
  }

  await syncFirebaseUser(auth.currentUser || result.user, fullName);
  return result.user;
}

export async function loginWithEmail(email, password) {
  const result = await signInWithEmailAndPassword(auth, email, password);
  await syncFirebaseUser(result.user);
  return result.user;
}

export async function loginWithGoogle() {
  const result = await signInWithPopup(auth, googleProvider);
  await syncFirebaseUser(result.user);
  return result.user;
}

export async function logout() {
  return signOut(auth);
}
