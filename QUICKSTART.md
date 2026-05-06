# Quick Start Guide

Fast setup guide for running Etherial Fantasy Bot locally or deploying to production.

## 5-Minute Local Setup

### 1. Clone & Setup
```bash
git clone https://github.com/yourusername/botetherial.git
cd botetherial
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# or: source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 2. Configure
```bash
# Copy templates
cp config.example.json config.json
cp .env.example .env

# Edit with your credentials
# - Discord bot token
# - Firebase database URL
# - Firebase service account path
```

### 3. Get Credentials

**Discord Bot Token:**
1. Go to https://discord.com/developers/applications
2. Create New Application
3. Go to "Bot" tab → "Add Bot"
4. Copy the token
5. Paste into `config.json` or `.env`

**Firebase Credentials:**
1. Go to https://console.firebase.google.com
2. Create or select project
3. Create Realtime Database
4. Go to Project Settings → Service Accounts
5. Click "Generate New Private Key"
6. Save as `etherial-fantasy-firebase-adminsdk.json`

### 4. Run
```bash
python bot.py
```

Should see: `Bot ready as EtherialFantasy#XXXX`

## Deploy to Discloud (5-10 minutes)

### Option A: GitHub Integration (Recommended)

1. **Create GitHub repo:**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push
   ```

2. **Create Discloud account** at https://discloud.app

3. **Connect to GitHub:**
   - Discloud Dashboard → "Add Bot"
   - Select "Connect with GitHub"
   - Choose your repository
   - Click "Import"

4. **Set environment variables:**
   ```
   DISCORD_BOT_TOKEN=your_token
   FIREBASE_DATABASE_URL=your_firebase_url
   ```

5. **Upload Firebase credentials:**
   - Use Discloud file manager
   - Upload `etherial-fantasy-firebase-adminsdk.json`

6. **Deploy:**
   - Click "Start" in Discloud dashboard
   - Wait for `Bot ready` message in logs

### Option B: Direct ZIP Upload

1. **Create ZIP:**
   ```bash
   Compress-Archive -Path . -DestinationPath botetherial.zip `
     -Exclude ".venv", "__pycache__", "config.json"
   ```

2. **Upload to Discloud:**
   - Dashboard → "Upload Bot"
   - Select ZIP file
   - Set environment variables
   - Click "Deploy"

## Commands to Try

After bot is running:

```
!help              # View all commands
!createchar Human Testchar  # Create character
!profile           # View character profile
!stats             # View detailed stats
!skills            # View starting skills (1-3 random)
!map               # View world map
!travel Kota Utama # Travel to location
!explore Kota Utama # Explore location
!battle            # Start a battle
!rest              # Rest and recover
```

## File Checklist

✅ Must have:
- `bot.py` - Main bot code
- `requirements.txt` - Dependencies
- `config.example.json` - Config template
- `.gitignore` - Don't commit secrets
- `discloud.config` - Discloud config

✅ Create locally:
- `config.json` - Your actual config (not in git)
- `.env` - Local environment variables (not in git)
- Firebase service account JSON (not in git)

✅ Optional but recommended:
- `.github/workflows/lint.yml` - GitHub Actions
- `DEPLOYMENT.md` - Deployment guide

## Troubleshooting

**Bot won't start:**
- Check bot token is valid
- Verify Python 3.8+: `python --version`
- Install deps: `pip install -r requirements.txt`

**Firebase error:**
- Check service account file path is correct
- Verify file exists and is valid JSON
- Check database URL matches Firebase console

**Commands don't work:**
- Ensure bot has Message Content Intent enabled
- Check bot has permissions in Discord server
- Verify correct prefix in config

**On Discloud:**
- Check logs in Discloud dashboard
- Verify environment variables are set
- Ensure Firebase files are uploaded
- Try restarting bot

## Next Steps

1. Read full [README.md](README.md) for complete documentation
2. See [DEPLOYMENT.md](DEPLOYMENT.md) for advanced deployment options
3. Check `bot.py` for command examples
4. Explore game data in `data/` and `*.json` files

## Links

- **GitHub**: https://github.com/yourusername/botetherial
- **Discloud**: https://discloud.app
- **Discord.py**: https://discordpy.readthedocs.io/
- **Firebase**: https://firebase.google.com

---

**Need help?** Check README.md or DEPLOYMENT.md for detailed guides!
