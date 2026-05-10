"use strict";

const path = require("path");
const db = require("./db");

db.init(path.join(__dirname, "..", "config.json"));

function formatCharacter(sessionData) {
  return {
    username: sessionData.title || "Unknown",
    race: sessionData.race || "Unknown",
    job: sessionData.job || "Unknown",
    level: sessionData.level || 1,
    location: sessionData.location || "Unknown",
    created: Boolean(sessionData.created),
    gold: sessionData.gold || 0,
    hp: `${sessionData.hp || 0}/${sessionData.max_hp || 100}`,
    sp: `${sessionData.sp || 0}/${sessionData.max_sp || 50}`,
  };
}

console.log("=== DATABASE STATUS ===");
console.log(`Using Firestore: ${db.isFirestoreEnabled()}`);
console.log(`Sessions collection available: ${db.getSessionsCollection() !== null}`);
console.log();

console.log("=== IN-MEMORY FALLBACK SESSIONS ===");
const allSessions = db.getFallbackSessions();
console.log(`Total sessions in memory: ${Object.keys(allSessions).length}`);
if (Object.keys(allSessions).length > 0) {
  const createdUsers = {};
  for (const [userId, sessionData] of Object.entries(allSessions)) {
    if (sessionData.created) {
      createdUsers[userId] = formatCharacter(sessionData);
    }
  }
  console.log(Object.keys(createdUsers).length > 0 ? JSON.stringify(createdUsers, null, 2) : "No users with created characters");
} else {
  console.log("No sessions in memory");
}

if (db.isFirestoreEnabled() && db.getSessionsCollection() !== null) {
  console.log("\n=== FIRESTORE SESSIONS ===");
  try {
    const firestoreUsers = {};
    db.getSessionsCollection().stream()
      .on("data", (doc) => {
        const data = doc.data() || {};
        if (data.created) {
          firestoreUsers[doc.id] = formatCharacter(data);
        }
      })
      .on("end", () => {
        console.log(`Total created users in Firestore: ${Object.keys(firestoreUsers).length}`);
        console.log(Object.keys(firestoreUsers).length > 0 ? JSON.stringify(firestoreUsers, null, 2) : "No users with created characters");
      });
  } catch (error) {
    console.log(`Error fetching from Firestore: ${error}`);
  }
}