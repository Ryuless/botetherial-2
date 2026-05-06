# Deployment Guide - Etherial Fantasy Bot

This guide covers deploying the Etherial Fantasy Discord bot to various platforms.

## Prerequisites

- GitHub account (for version control)
- Discord Bot Token
- Firebase account with Realtime Database

## Table of Contents

1. [Discloud Deployment](#discloud-deployment)
2. [GitHub Setup](#github-setup)
3. [Environment Variables](#environment-variables)
4. [Troubleshooting](#troubleshooting)

## Discloud Deployment

Discloud is the recommended platform for Discord bots.

### Step 1: Create Discloud Account

1. Visit https://discloud.app
2. Click "Sign In with Discord"
3. Authorize with your Discord account
4. Complete account setup

### Step 2: Prepare the Project

1. **Ensure files are ready:**
   - ✅ `discloud.config` exists
   - ✅ `requirements.txt` has all dependencies
   - ✅ `.gitignore` excludes `.venv/`, `config.json`, `*.service-account.json`
   - ✅ `config.example.json` is clean (no real credentials)

2. **Test locally:**
   ```bash
   python bot.py
   ```

### Step 3: Upload to GitHub

This is the easiest way to deploy on Discloud.

1. **Create GitHub repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/botetherial.git
   git push -u origin main
   ```

2. **Ensure sensitive files are ignored:**
   - Check `.gitignore` includes: `config.json`, `*.service-account.json`, `.env`
   - Verify these are NOT committed: `git log --all -- config.json`

### Step 4: Connect Discloud to GitHub

1. Go to https://discloud.app/dashboard
2. Click "Add bot" or "Upload bot"
3. Select "Connect with GitHub"
4. Authorize Discloud to access your repositories
5. Select the `botetherial` repository
6. Click "Import"

### Step 5: Set Environment Variables on Discloud

1. In Discloud dashboard, find your bot
2. Click "Settings" or "Environment Variables"
3. Add the following variables:

```
DISCORD_BOT_TOKEN=your_actual_bot_token_here
FIREBASE_DATABASE_URL=https://your-project.firebasedatabase.app
```

**Do NOT paste these in code - only in Discloud dashboard!**

### Step 6: Upload Firebase Credentials

1. In Discloud dashboard, look for "Files" or "Upload Files"
2. Upload your Firebase service account JSON:
   - Filename: `etherial-fantasy-firebase-adminsdk.json`
   - Path: Project root

Alternatively, you can upload via the web interface or use Discloud's file manager.

### Step 7: Deploy

1. Click "Start" or "Deploy" button
2. Monitor the logs to ensure the bot starts correctly
3. Should see: `Bot ready as EtherialFantasy#XXXX`

### Step 8: Test

1. Join a Discord server where your bot is added
2. Type `!help` to verify the bot is responding
3. Create a test character with `!createchar Human TestChar`

## GitHub Setup

### Creating a GitHub Repository

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Etherial Fantasy Bot"

# Rename branch to main
git branch -M main

# Add remote (replace with your repo URL)
git remote add origin https://github.com/yourusername/botetherial.git

# Push to GitHub
git push -u origin main
```

### GitHub Best Practices

1. **Create a `.gitignore`** (already done)
2. **Use branches for features:**
   ```bash
   git checkout -b feature/new-feature
   # Make changes
   git commit -am "Add new feature"
   git push origin feature/new-feature
   # Create Pull Request on GitHub
   ```

3. **Tag releases:**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

4. **Keep credentials secure:**
   - Never commit `config.json`
   - Never commit Firebase service account files
   - Use `.env` for local development only

## Environment Variables

### Local Development (.env file)

Create `.env` in project root:
```
DISCORD_BOT_TOKEN=your_token_here
BOT_PREFIX=!
FIREBASE_DATABASE_URL=https://your-project.firebasedatabase.app/
FIREBASE_SERVICE_ACCOUNT_PATH=./etherial-fantasy-firebase-adminsdk.json
```

**Important:** Add `.env` to `.gitignore` - never commit this file!

### Discloud Dashboard

Set these in Discloud's environment variables section:
- `DISCORD_BOT_TOKEN` - Your Discord bot token
- `FIREBASE_DATABASE_URL` - Your Firebase database URL
- `FIREBASE_SERVICE_ACCOUNT_PATH` - Path to service account (e.g., `/root/etherial-fantasy-firebase-adminsdk.json`)

### Bot Configuration (config.json)

Locally, create `config.json` from `config.example.json`:
```json
{
  "token": "your_actual_token",
  "prefix": "!",
  "firebase_database_url": "https://your-project.firebasedatabase.app/",
  "firebase_service_account": "./etherial-fantasy-firebase-adminsdk.json"
}
```

**Important:** This file is in `.gitignore` - it won't be committed.

On Discloud, instead of `config.json`, use environment variables in the dashboard.

## Alternative: Manual ZIP Upload

If you prefer not to use GitHub:

1. Create a ZIP file:
   ```bash
   # Windows
   Compress-Archive -Path . -DestinationPath botetherial.zip `
     -Exclude ".venv", "__pycache__", "config.json", "*.service-account.json"
   
   # Linux/macOS
   zip -r botetherial.zip . -x ".venv/*" "__pycache__/*" "config.json" "*.service-account.json"
   ```

2. Go to Discloud dashboard
3. Click "Upload ZIP"
4. Select your `botetherial.zip` file
5. Set environment variables
6. Click "Deploy"

## Troubleshooting

### Bot doesn't start on Discloud

**Check logs:**
1. Go to Discloud dashboard
2. Click your bot
3. View "Logs"
4. Look for error messages

**Common issues:**
- Missing `DISCORD_BOT_TOKEN` environment variable
- Firebase credentials not uploaded
- Missing dependencies in `requirements.txt`
- Python version mismatch

### "ModuleNotFoundError: No module named 'discord'"

**Fix:**
1. Ensure `requirements.txt` has all dependencies
2. Check `discloud.config` has correct `lang=python`
3. Redeploy the bot

### Firebase connection fails

**Fix:**
1. Verify `FIREBASE_DATABASE_URL` in environment variables
2. Ensure service account file is uploaded to Discloud
3. Check Firebase security rules aren't blocking access
4. Verify service account has correct permissions

### Bot works locally but not on Discloud

**Debug steps:**
1. Compare local `.env` with Discloud environment variables
2. Check file paths (relative paths on Discloud might differ)
3. Verify all JSON data files are included in upload
4. Check logs in Discloud dashboard for specific errors

### "config.json not found"

**On Discloud**, the bot should use environment variables instead:
1. Remove `config.json` from your local repository
2. Update `bot.py` to read from environment variables (or use the existing fallback)
3. Set variables in Discloud dashboard

## Maintenance

### Updating the Bot

1. Make changes locally
2. Test with `python bot.py`
3. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update feature"
   git push
   ```
4. Discloud will auto-redeploy if configured
5. Or manually restart from Discloud dashboard

### Monitoring

1. Check logs regularly in Discloud dashboard
2. Monitor bot uptime
3. Keep Discord.py and Firebase Admin SDK updated:
   ```bash
   pip install --upgrade discord.py firebase-admin
   ```

### Backups

1. Keep GitHub repository up to date
2. Regularly backup your Firebase data from Firebase console
3. Consider creating releases/tags for stable versions

## Support

- **Discloud Support**: https://discloud.app/support
- **Discord.py Docs**: https://discordpy.readthedocs.io/
- **Firebase Docs**: https://firebase.google.com/docs
