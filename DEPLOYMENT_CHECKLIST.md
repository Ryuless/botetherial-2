# Pre-Deployment Checklist

Use this checklist before deploying to GitHub and Discloud to ensure everything is configured correctly.

## 🔒 Security Check

- [ ] `config.json` is in `.gitignore`
- [ ] All `*firebase-adminsdk*.json` files are in `.gitignore`
- [ ] `.env` file is in `.gitignore`
- [ ] `.venv/` directory is in `.gitignore`
- [ ] No real tokens in any committed files
- [ ] Ran `git status` to verify no secrets will be committed
- [ ] `config.example.json` has only placeholder values

## 📦 Dependencies Check

- [ ] `requirements.txt` updated with all packages
- [ ] Local installation works: `pip install -r requirements.txt`
- [ ] Bot runs locally: `python bot.py`
- [ ] All imports are available

## 📋 Configuration Files

- [ ] `.gitignore` exists and is properly configured
- [ ] `.env.example` exists with all required variables
- [ ] `config.example.json` exists with placeholders
- [ ] `discloud.config` exists with correct settings
- [ ] `Dockerfile` exists (optional but recommended)
- [ ] `docker-compose.yml` exists (optional but recommended)
- [ ] `.dockerignore` exists (optional)
- [ ] `.github/workflows/lint.yml` exists (optional)

## 📚 Documentation

- [ ] `README.md` is complete and accurate
- [ ] `DEPLOYMENT.md` is available
- [ ] `QUICKSTART.md` is available
- [ ] `CONFIGURATION.md` is available
- [ ] All documentation has correct GitHub URLs

## 🔧 Credentials Prepared

**Discord Bot Token:**
- [ ] Bot created at https://discord.com/developers/applications
- [ ] Token copied (keep secure!)
- [ ] Bot invited to test server with `applications.commands` scope

**Firebase:**
- [ ] Firebase project created at https://console.firebase.google.com
- [ ] Realtime Database created
- [ ] Service account JSON downloaded
- [ ] Service account JSON NOT committed to git
- [ ] Service account file path noted

## 🌐 GitHub Setup

- [ ] GitHub account created
- [ ] New repository created (private recommended initially)
- [ ] Git initialized locally: `git init`
- [ ] All files staged: `git add .`
- [ ] Initial commit created: `git commit -m "Initial commit"`
- [ ] Remote added: `git remote add origin <url>`
- [ ] Pushed to main: `git push -u origin main`
- [ ] `.gitignore` is respected (no secrets in repo)

**Verify with:**
```bash
git log --all -- config.json          # Should show nothing
git log --all -- "*.service-account.json"  # Should show nothing
git ls-files | grep -E "(config\.json|\.env|firebase-adminsdk)"  # Should be empty
```

## ☁️ Discloud Setup

- [ ] Discloud account created at https://discloud.app
- [ ] Logged in with Discord
- [ ] Account verified

**Method A: GitHub Integration (Recommended)**
- [ ] GitHub repository created and pushed
- [ ] Connected Discloud to GitHub account
- [ ] Repository imported to Discloud
- [ ] `discloud.config` file present in repo

**Method B: ZIP Upload**
- [ ] ZIP file created excluding `.venv/`, `config.json`, etc.
- [ ] ZIP file ready to upload

## 🔑 Environment Variables on Discloud

- [ ] Created environment variable: `DISCORD_BOT_TOKEN`
- [ ] Created environment variable: `FIREBASE_DATABASE_URL`
- [ ] Verified variable values are correct
- [ ] Saved environment variables

## 📁 Firebase Setup on Discloud

**Method A: File Manager**
- [ ] Accessed Discloud file manager
- [ ] Uploaded Firebase service account JSON
- [ ] File accessible at expected path

**Method B: Environment Variable**
- [ ] Set `FIREBASE_SERVICE_ACCOUNT_PATH` in env vars
- [ ] Path points to correct location

## 🚀 Deployment

- [ ] Made final commit: `git commit -am "Ready for deployment"`
- [ ] Pushed to GitHub: `git push`
- [ ] Discloud dashboard shows latest commit
- [ ] Clicked "Start" or "Deploy" on Discloud
- [ ] Waited for bot to start (2-3 minutes)
- [ ] Checked Discloud logs for `Bot ready` message

**Expected log output:**
```
Bot ready as EtherialFantasy#XXXX — prefix=!
Database: ✅ Firestore connected
```

## ✅ Post-Deployment Tests

- [ ] Added bot to test Discord server
- [ ] Tested `!help` command responds
- [ ] Tested `!createchar Human TestChar` works
- [ ] Tested `!skills` shows 1-3 random skills
- [ ] Checked Discloud logs for errors
- [ ] Verified bot status is "Online"

## 📝 Final Documentation

- [ ] Created GitHub README with deployment instructions
- [ ] Added Discloud link to documentation
- [ ] Documented any custom configurations
- [ ] Created deployment log (date, version, notes)
- [ ] Shared access credentials securely (if team project)

## 🔄 Maintenance Setup

- [ ] Enabled Discloud notifications (optional)
- [ ] Set up monitoring/logging
- [ ] Noted Discloud dashboard access info
- [ ] Scheduled regular backups of Firebase data
- [ ] Documented rollback procedures

## 🎯 Success Criteria

All the following should be true:
- ✅ Bot is running on Discloud
- ✅ Bot responds to commands in Discord
- ✅ No secrets in GitHub repository
- ✅ Environment variables set on Discloud
- ✅ Logs show successful operation
- ✅ Firebase database connection working
- ✅ Skill gacha working (1-3 skills on new character)

## 🆘 Troubleshooting Checklist

If deployment failed, check these:

**Bot won't start:**
- [ ] Checked Discloud logs for error messages
- [ ] Verified `DISCORD_BOT_TOKEN` is set in Discloud
- [ ] Verified Discord bot token is valid
- [ ] Verified `discloud.config` exists
- [ ] Verified Python version is correct

**Firebase connection failed:**
- [ ] Verified `FIREBASE_DATABASE_URL` is correct
- [ ] Verified Firebase service account JSON is uploaded
- [ ] Verified Firebase database exists and is accessible
- [ ] Checked Firebase security rules

**Commands not responding:**
- [ ] Verified bot has correct permissions
- [ ] Verified bot has Message Content Intent enabled
- [ ] Verified prefix is correct
- [ ] Checked Discloud logs for errors

**Deployment issues:**
- [ ] Ran `git status` to verify changes
- [ ] Verified `.gitignore` is not ignoring needed files
- [ ] Verified `requirements.txt` has all dependencies
- [ ] Tested locally first: `python bot.py`

## 📞 Support

If issues persist:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting
2. Check Discloud logs in dashboard
3. Check GitHub Actions workflows
4. Consult [README.md](README.md) documentation

---

**Date of Last Deployment:** _______________
**Deployed Version:** _______________
**Discloud Bot ID:** _______________
**Notes:** _______________________________________________

