// Firebase Web (ES Module) client initialization example
// Save this file as public/firebase-config.js and include it in your web client

// NOTE: This example uses the Firebase CDN ES modules. If you use a bundler (webpack/rollup/vite)
// import from 'firebase/app' and other packages instead.

// Replace the config below with your project config (already provided)
export const firebaseConfig = {
  apiKey: "AIzaSyDlSPWeD1EZYhojPuu5ro7wW8o2Nf79g9c",
  authDomain: "etherial-fantasy.firebaseapp.com",
  databaseURL: "https://etherial-fantasy-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "etherial-fantasy",
  storageBucket: "etherial-fantasy.firebasestorage.app",
  messagingSenderId: "837640290780",
  appId: "1:837640290780:web:36a6d31884bcaf42378f19",
  measurementId: "G-41LGLGFXG6"
};

// CDN module imports (works in modern browsers with <script type="module">)
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js';
import { getAnalytics } from 'https://www.gstatic.com/firebasejs/9.22.2/firebase-analytics.js';
import {
  getFirestore,
  doc,
  getDoc,
  setDoc,
  collection,
  getDocs,
} from 'https://www.gstatic.com/firebasejs/9.22.2/firebase-firestore.js';
import { getAuth, signInAnonymously } from 'https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js';

// Initialize
export const app = initializeApp(firebaseConfig);
export const analytics = (() => {
  try { return getAnalytics(app); } catch (e) { return null; }
})();
export const db = getFirestore(app);
export const auth = getAuth(app);

// Helper: sign in anonymously (useful for quick client reads if rules allow)
export async function signInAnon() {
  try {
    const res = await signInAnonymously(auth);
    return res.user;
  } catch (err) {
    console.error('Anon sign-in failed', err);
    throw err;
  }
}

// Helper: fetch the skills document stored under meta/assets -> skills (matches server seeder)
export async function fetchSkills() {
  try {
    const ref = doc(db, 'meta', 'world_state');
    const snap = await getDoc(ref);
    // seeding script stores skills under meta/world_state/assets/skills or meta/assets/skills depending on rules
    if (!snap.exists()) return {};
    const data = snap.data();
    // attempt common shapes
    if (data?.assets?.skills) return data.assets.skills;
    if (data?.skills) return data.skills;
    // fallback: try reading nested doc (meta/assets/skills)
    try {
      const assetsRef = doc(db, 'meta', 'assets_skills');
      const snap2 = await getDoc(assetsRef);
      if (snap2.exists()) return snap2.data()?.skills || {};
    } catch (_) {
      // ignore
    }
    return {};
  } catch (err) {
    console.error('fetchSkills error', err);
    return {};
  }
}

// Helper: write skills (use only if authenticated and rules allow)
export async function writeSkills(skillsObj) {
  try {
    // write into meta/assets/skills as a single doc
    await setDoc(doc(db, 'meta', 'assets'), { skills: skillsObj }, { merge: true });
    return true;
  } catch (err) {
    console.error('writeSkills error', err);
    throw err;
  }
}

// Example usage (to run in a client page):
// <script type="module">
// import { signInAnon, fetchSkills } from './firebase-config.js';
// await signInAnon();
// const skills = await fetchSkills();
// console.log('Skills loaded', skills);
// </script>
