"use strict";

const fs = require("fs");
const path = require("path");

const state = {
  useFirestore: false,
  sessionsCol: null,
  worldDoc: null,
  fallbackSessions: {},
  fallbackWorldState: {},
  appInitialized: false,
};

function init(configPath = null) {
  try {
    const firebaseAdmin = require("firebase-admin");

    let serviceAccountPath = null;
    if (configPath && fs.existsSync(configPath)) {
      try {
        const cfg = JSON.parse(fs.readFileSync(configPath, "utf8"));
        serviceAccountPath = cfg.firebase_service_account || null;
      } catch (error) {
        console.error(`Error reading config: ${error}`);
        serviceAccountPath = null;
      }
    }

    if (serviceAccountPath && fs.existsSync(serviceAccountPath)) {
      if (!state.appInitialized) {
        try {
          firebaseAdmin.initializeApp({
            credential: firebaseAdmin.credential.cert(require(path.resolve(serviceAccountPath))),
          });
          state.appInitialized = true;
        } catch (error) {
          if (!String(error).includes("already exists")) {
            throw error;
          }
          state.appInitialized = true;
        }
      }

      const client = firebaseAdmin.firestore();
      state.sessionsCol = client.collection("sessions");
      state.worldDoc = client.collection("meta").doc("world_state");
      state.useFirestore = true;
      console.info(`Firebase initialized with credentials from ${serviceAccountPath}`);
      console.info("Firestore connected successfully");
      return;
    }

    console.warn(`Firebase service account not found at ${serviceAccountPath}`);
    state.useFirestore = false;
  } catch (error) {
    console.error(`Firebase Admin SDK not available: ${error}`);
    state.useFirestore = false;
  }
}

function getSession(userId) {
  const key = String(userId);
  return state.fallbackSessions[key] || {};
}

async function getSessionAsync(userId) {
  const key = String(userId);
  if (state.useFirestore && state.sessionsCol) {
    try {
      const doc = await state.sessionsCol.doc(key).get();
      const data = doc.exists ? doc.data() : {};
      return data && typeof data === "object" ? data : {};
    } catch (error) {
      console.error(`Error loading session from Firestore for user ${key}: ${error}`);
      return state.fallbackSessions[key] || {};
    }
  }
  return state.fallbackSessions[key] || {};
}

function saveSession(userId, session) {
  const key = String(userId);
  if (!session || typeof session !== "object") {
    console.error(`Invalid session data type for user ${key}: ${typeof session}`);
    return;
  }

  state.fallbackSessions[key] = session;
}

async function saveSessionAsync(userId, session) {
  const key = String(userId);
  if (!session || typeof session !== "object") {
    console.error(`Invalid session data type for user ${key}: ${typeof session}`);
    return;
  }

  if (state.useFirestore && state.sessionsCol) {
    try {
      await state.sessionsCol.doc(key).set(session);
      return;
    } catch (error) {
      console.error(`Error saving session to Firestore for user ${key}: ${error}`);
      state.fallbackSessions[key] = session;
      return;
    }
  }

  state.fallbackSessions[key] = session;
}

function getWorldState() {
  return state.fallbackWorldState.world || {};
}

async function getWorldStateAsync() {
  if (state.useFirestore && state.worldDoc) {
    try {
      const doc = await state.worldDoc.get();
      const data = doc.exists ? doc.data() : {};
      return data && typeof data === "object" ? data : {};
    } catch (error) {
      console.error(`Error loading world state from Firestore: ${error}`);
      return state.fallbackWorldState.world || {};
    }
  }
  return state.fallbackWorldState.world || {};
}

function saveWorldState(stateData) {
  if (!stateData || typeof stateData !== "object") {
    console.error(`Invalid world state data type: ${typeof stateData}`);
    return;
  }

  state.fallbackWorldState.world = stateData;
}

async function saveWorldStateAsync(stateData) {
  if (!stateData || typeof stateData !== "object") {
    console.error(`Invalid world state data type: ${typeof stateData}`);
    return;
  }

  if (state.useFirestore && state.worldDoc) {
    try {
      await state.worldDoc.set(stateData);
      return;
    } catch (error) {
      console.error(`Error saving world state to Firestore: ${error}`);
      state.fallbackWorldState.world = stateData;
      return;
    }
  }

  state.fallbackWorldState.world = stateData;
}

function isFirestoreEnabled() {
  return state.useFirestore && state.sessionsCol !== null && state.worldDoc !== null;
}

function getFirestoreStatus() {
  return {
    enabled: state.useFirestore,
    sessions_collection: state.sessionsCol !== null,
    world_doc: state.worldDoc !== null,
    app_initialized: state.appInitialized,
    fallback_sessions_count: Object.keys(state.fallbackSessions).length,
    fallback_world_state: Boolean(state.fallbackWorldState.world),
  };
}

function getSessionsCollection() {
  return state.sessionsCol;
}

function getWorldDoc() {
  return state.worldDoc;
}

function getFallbackSessions() {
  return state.fallbackSessions;
}

module.exports = {
  init,
  getSession,
  getSessionAsync,
  saveSession,
  saveSessionAsync,
  getWorldState,
  getWorldStateAsync,
  saveWorldState,
  saveWorldStateAsync,
  isFirestoreEnabled,
  getFirestoreStatus,
  getSessionsCollection,
  getWorldDoc,
  getFallbackSessions,
  state,
};