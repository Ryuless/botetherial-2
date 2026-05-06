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
- Python 3.8+
- Discord Bot Token
- Firebase Realtime Database credentials

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/botetherial.git
cd botetherial
```

2. **Create virtual environment**
```bash
# Linux/macOS
python -m venv .venv
source .venv/bin/activate

# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure the bot**
```bash
# Copy config template
cp config.example.json config.json

# Copy environment template
cp .env.example .env
```

5. **Set up configuration**
- Edit `config.json` with your Discord bot token and Firebase credentials
- Or set environment variables in `.env`
- Download Firebase service account JSON and place it in the project root

6. **Run the bot**
```bash
python bot.py
```

The bot should output: `Bot ready as EtherialFantasy#XXXX — prefix=!`

## Configuration 📋

### config.json
```json
{
  "token": "YOUR_DISCORD_BOT_TOKEN",
  "prefix": "!",
  "firebase_database_url": "https://your-project-default-rtdb.region.firebasedatabase.app/",
  "firebase_service_account": "./etherial-fantasy-firebase-adminsdk.json"
}
```

### Environment Variables (.env)
```
DISCORD_BOT_TOKEN=your_token
BOT_PREFIX=!
FIREBASE_DATABASE_URL=https://your-project.firebasedatabase.app/
FIREBASE_SERVICE_ACCOUNT_PATH=./service-account.json
```

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
├── bot.py                          # Main bot file
├── db.py                           # Database operations (Firebase)
├── stats.py                        # Character stats calculations
├── check_users.py                  # User validation utilities
├── README.md                       # Main documentation
├── docs/                           # Deployment and setup docs
├── data/                           # Game data
├── config.example.json             # Configuration template
├── requirements.txt                # Python dependencies
├── discloud.config                 # Discloud deployment config
├── Dockerfile                      # Docker image
├── docker-compose.yml              # Docker compose
├── .env.example                    # Environment variables template
├── .gitignore                      # Git ignore rules
├── .github/                        # GitHub Actions workflows
├── races.json                      # Race definitions
├── jobs.json                       # Job definitions
├── starter_kits.json               # Starter kit definitions
└── .venv/                          # Virtual environment (not in git)
```

Dokumentasi detail dipindahkan ke [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md), [docs/QUICKSTART.md](docs/QUICKSTART.md), [docs/CONFIGURATION.md](docs/CONFIGURATION.md), dan [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md).

## Deployment 🚀

### Deploy to Discloud

Discloud is a hosting service designed for Discord bots.

1. **Create Discloud Account**
   - Go to https://discloud.app
   - Sign up with your Discord account

2. **Prepare Your Bot**
   - Ensure `discloud.config` exists
   - Ensure `requirements.txt` has all dependencies
   - Ensure `.gitignore` excludes sensitive files

3. **Upload to Discloud**
   - Create a `.zip` file with your project:
     ```bash
     # Windows
     Compress-Archive -Path . -DestinationPath botetherial.zip -Exclude .venv, __pycache__
     
     # Linux/macOS
     zip -r botetherial.zip . -x ".venv/*" "__pycache__/*" "*.pyc"
     ```
   - Or use Discloud's GitHub integration (recommended)

4. **Environment Variables on Discloud**
   - Set these in the Discloud dashboard:
     ```
     DISCORD_BOT_TOKEN=your_token
     FIREBASE_DATABASE_URL=your_firebase_url
     ```

5. **Deploy**
   - Upload the zip file or connect your GitHub repo
   - Click deploy/start
   - Monitor logs in Discloud dashboard

### Deploy to Other Platforms

The bot can also be deployed to:
- **Heroku** (free tier removed as of Nov 2022)
- **Railway.app** - See railway.app for setup
- **Replit** - See replit.com for Python setup
- **VPS (AWS, DigitalOcean, Linode)** - Standard Python deployment

## Development 💻

### Adding New Features

1. Create new command in `bot.py`
2. Update game data in `data/` if needed
3. Test locally with `python bot.py`
4. Update `README.md` with new commands
5. Commit and push to GitHub

### Code Style
- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings for functions

## Firebase Setup 🔥

1. **Create Firebase Project**
   - Go to https://console.firebase.google.com
   - Create a new project

2. **Generate Service Account Key**
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Save as `etherial-fantasy-firebase-adminsdk.json`
   - Add to `.gitignore`

3. **Enable Firestore Database**
   - Create a Realtime Database
   - Set security rules (or use development mode for testing)

4. **Update Configuration**
   - Copy the database URL to `config.json`
   - Place service account JSON in project root

## Troubleshooting 🔧

### Bot won't start
- Check if bot token is valid
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check `config.json` format
- Verify Python version: `python --version`

### Firebase connection fails
- Check service account JSON is in correct location
- Verify Firebase database URL is correct
- Check internet connection

### Commands not working
- Ensure bot has Message Content Intent enabled
- Check bot permissions in Discord server
- Verify command prefix is correct

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

- Built with [discord.py](https://discordpy.readthedocs.io/)
- Data persistence with [Firebase Admin SDK](https://firebase.google.com/docs/database)
- Hosted on [Discloud](https://discloud.app)

---

**Note**: Remember to never commit `config.json` or Firebase service account files. Use `config.example.json` as a template for new deployments.

