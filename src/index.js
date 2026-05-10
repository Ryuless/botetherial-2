"use strict";

try {
	require("./bot");
} catch (error) {
	if (String(error).includes("discord.js") || String(error).includes("Cannot find module")) {
		console.log("JS runtime scaffold initialized.");
		console.log("Discord runtime is not available in this environment yet.");
	} else {
		throw error;
	}
}