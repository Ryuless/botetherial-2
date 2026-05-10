# Etherial Fantasy - Discord RP Bot 🎭

A comprehensive Discord roleplay bot for the Etherial fantasy world. Features include character creation, exploration, monster encounters, battles, quests, inventory management, and world state persistence using Firebase.

## Features ✨

- **Character Creation & Management** - Create characters with different races and jobs
- **Exploration System** - Travel between locations and discover encounters
- **Battle System** - Turn-based combat with skills and items
- **Quest System** - Quest board with rewards and progression
- **Inventory & Shop** - Manage items and equipment
- **Party System** - Form parties with other players
- **Companion Recruitment** - Recruit NPCs to accompany you
- **Story Events** - Personalized events based on race, job, and location
- **World State** - Dynamic world that changes based on player actions
- **Reputation System** - Track faction reputation
- **Achievements** - Unlock achievements through gameplay
- **Skill Gacha** - Random starting skills (1-3 initial skills)
- **Firebase Integration** - Persistent data storage

## Quick Start 🚀

### Prerequisites
- Node.js 18.0+
- npm 9.0+
- Discord Bot Token
- Firebase service account credentials

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/botetherial.git
cd botetherial
```

2. **Install dependencies**
```bash
npm install
```

3. **Configure the bot**
```bash
# Edit config.json with your settings
# Set DISCORD_BOT_TOKEN in environment or config.json
```

4. **Set up Firebase credentials**
- Download Firebase service account JSON
- Place it as `etherial-fantasy-firebase-adminsdk-fbsvc-*.json` in project root
- Or set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

5. **Run the bot**
```bash
# Development
npm start

# Or directly
node src/index.js
```

The bot should output when Discord is available: `Bot ready as EtherialFantasy#XXXX — prefix=!`

## Configuration 📋

### config.json
```json
{
  "token": "YOUR_DISCORD_BOT_TOKEN",
  "prefix": "!"
}
```

### Environment Variables (.env)
```
DISCORD_BOT_TOKEN=your_token
GOOGLE_APPLICATION_CREDENTIALS=./etherial-fantasy-firebase-adminsdk-fbsvc-*.json
```

The bot uses **Firestore** for data persistence with automatic in-memory fallback when Firebase is unavailable.

## Discord Commands 🎮

### Character Management
- `!createchar <race> <name>` - Create a new character
- `!profile` - View your character profile
- `!stats` - View detailed character stats
- `!changejob <job>` - Change your job
- `!races` - List available races
- `!jobs` - List available jobs
- `!skills` - View your current skills

### Exploration & Battle
- `!map` - View the world map
- `!travel <location>` - Travel to a location
- `!explore <location>` - Explore and find encounters
- `!battle` - Start a battle
- `!attack [skill]` - Attack in battle
- `!flee` - Flee from battle
- `!loot <monster>` - Loot defeated monster
- `!rest` - Rest to recover HP/MP

### Inventory & Shop
- `!inventory` - View your inventory
- `!equip <item>` - Equip an item
- `!unequip <slot>` - Unequip an item
- `!use <item>` - Use an item
- `!shop` - View available items
- `!buy <item> [qty]` - Buy items

### Quests & Party
- `!questboard` - View active quests
- `!acceptquest <id>` - Accept a quest
- `!quests` - View your active quests
- `!completequest <id>` - Complete a quest
- `!party <create|join|leave|info|disband> [name]` - Manage parties

### Social & Progression
- `!companions` - View your companions
- `!recruit <name>` - Recruit a companion
- `!story` - Trigger a story event
- `!reputation [faction]` - View faction reputation
- `!achievements` - View your achievements

### General
- `!help` or `!commands` - View all commands
- `!status` - Quick status check

## Project Structure 📁

```
botetherial/
├── src/
│   ├── bot.js                      # Discord.js bot runtime
│   ├── index.js                    # Entry point
│   ├── db.js                       # Firestore operations with fallback
│   ├── stats.js                    # Character stat calculations
│   ├── game-core.js                # Core game logic (catalogs, sessions, quests)
│   ├── command-data.js             # Command payload builders
│   ├── presentation.js             # Discord embed builders
│   ├── check_users.js              # User validation
│   └── test_stats.js               # Stats validation tests
├── data/                           # Game data files
│   ├── items.json                  # Item definitions
│   ├── map.json                    # World map layout
│   ├── monsters.json               # Monster definitions
│   ├── recipes.json                # Crafting recipes
│   ├── world_events.json           # World events
│   └── ...
├── config.json                     # Bot configuration
├── package.json                    # Node.js dependencies
├── etherial-fantasy-firebase-adminsdk-fbsvc-*.json  # Firebase credentials (not in git)
├── races.json                      # Race definitions
├── jobs.json                       # Job definitions
├── starter_kits.json               # Starter kit definitions
└── .gitignore                      # Git ignore rules
```

## Deployment 🚀

### Deploy to Node.js Hosting

The bot can be deployed to any Node.js hosting platform:

- **Railway.app** - Easy deployment with GitHub integration
- **Render.com** - Free tier available
- **Fly.io** - Global deployment
- **Heroku** - Using Procfile (not free anymore)
- **VPS (AWS, DigitalOcean, Linode)** - Full control
- **Replit** - Node.js runtime support

### General Deployment Steps

1. **Prepare project**
   - Ensure `package.json` and all files are committed
   - Exclude `.env`, `node_modules`, and Firebase credentials from git
   - Verify `.gitignore` is correct

2. **Set environment variables** on your hosting platform:
   ```
   DISCORD_BOT_TOKEN=your_token
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-adminsdk.json
   ```

3. **Install and run**
   ```bash
   npm install
   npm start
   ```

4. **Firebase credentials**
   - Upload your Firebase service account JSON to the hosting platform
   - Or use the platform's secrets/environment management

## Development 💻

### Adding New Features

1. Create new command handler in `src/bot.js`
2. Add payload builder in `src/command-data.js` if needed
3. Update game data in `data/` JSON files if needed
4. Test locally with `npm start` or `node src/index.js`
5. Update `README.md` with new commands
6. Commit and push to GitHub

### Code Style
- Follow JavaScript conventions (consistent indentation, descriptive names)
- Use async/await for async operations
- Add JSDoc comments for functions
- Test changes before committing

## Firebase Setup 🔥

1. **Create Firebase Project**
   - Go to https://console.firebase.google.com
   - Create a new project

2. **Enable Firestore Database**
   - Create a Firestore Database
   - Set security rules (or use development mode for testing)

3. **Generate Service Account Key**
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save as `etherial-fantasy-firebase-adminsdk-fbsvc-*.json`
   - **IMPORTANT**: Add to `.gitignore` (never commit credentials)

4. **Update Configuration**
   - Set `GOOGLE_APPLICATION_CREDENTIALS` to path of service account JSON
   - Or place file in project root and let app auto-detect it

5. **Fallback Mode**
   - Bot works without Firebase (uses in-memory storage)
   - Data persists locally only during session
   - Add Firebase credentials to enable persistent storage

## Troubleshooting 🔧

### Bot won't start
- Check if bot token is valid in `config.json`
- Ensure all dependencies are installed: `npm install`
- Check `config.json` format is valid JSON
- Verify Node.js version: `node --version` (need 18.0+)
- Check for errors: `npm start` (shows detailed error messages)

### Firebase connection fails
- Check service account JSON is accessible
- Verify Firestore database exists in Firebase project
- Check internet connection
- Bot will work in fallback mode without Firebase (data lost on restart)

### Commands not working
- Ensure bot has Message Content Intent enabled in Discord Developer Portal
- Check bot permissions in Discord server settings
- Verify command prefix is correct (default: `!`)
- Ensure bot has permission to send messages

### Discord.js not available
- Install discord.js: `npm install discord.js`
- Or check console output for fallback mode notice

### Skills are limited
- This is intentional! Characters get 1-3 random starting skills
- More skills unlock through leveling and progression

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is open source. Please ensure Firebase credentials are never committed.

## Support & Community 💬

- **GitHub Issues** - Report bugs or request features
- **Discord** - Join our community server for support

## Credits ✨

- Built with [discord.js](https://discord.js.org/)
- Data persistence with [Firebase Admin SDK](https://firebase.google.com/docs/firestore)
- Game design and content for Etherial Fantasy RPG

---

**Important Security Notes:**
- Never commit `config.json` with real bot tokens
- Never commit Firebase service account JSON files
- Always use `.gitignore` to protect sensitive credentials
- Use environment variables or secure secret management for production
- Rotate bot tokens if accidentally exposed

