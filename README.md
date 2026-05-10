# Etherial Fantasy - Bot Discord RPG 🎭

Bot Discord RPG (Role-Playing Game) yang komprehensif untuk dunia fantasi Etherial. Bot ini dirancang untuk memberikan pengalaman bermain RPG yang mendalam dengan sistem karakter, pertarungan, quest, dan banyak fitur menarik lainnya.

## 📖 Daftar Isi

- [Kegunaan Bot](#kegunaan-bot)
- [Fitur Utama](#fitur-utama)
- [Prasyarat](#prasyarat)
- [Instalasi](#instalasi)
- [Konfigurasi](#konfigurasi)
- [Menjalankan Bot](#menjalankan-bot)
- [Perintah Bot](#perintah-bot)
- [Sistem Permainan](#sistem-permainan)
- [Struktur Proyek](#struktur-proyek)
- [Setup Firebase](#setup-firebase)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Berkontribusi](#berkontribusi)

## 🎮 Kegunaan Bot

**Etherial Fantasy** adalah bot Discord yang menyediakan pengalaman RPG interaktif penuh di dalam Discord. Bot ini memungkinkan pemain untuk:

- **Membuat dan mengelola karakter** dengan berbagai ras dan kelas
- **Menjelajahi dunia fantasi** dengan 44+ lokasi unik
- **Bertarung melawan monster** dalam sistem pertarungan berbasis giliran
- **Menyelesaikan quest** dari papan misi di Guild
- **Mengelola inventory** dengan sistem bobot dan penyimpanan
- **Membentuk party** bersama pemain lain
- **Merekrut companion** untuk menemani petualangan
- **Mengumpulkan achievement** dan reputasi
- **Mengalami story events** yang dipersonalisasi berdasarkan ras, kelas, dan lokasi

Bot ini sempurna untuk:
- **Komunitas Discord gaming** yang ingin fitur RPG interaktif
- **Roleplay server** yang membutuhkan sistem karakter terstruktur
- **Pembelajaran bahasa pemrograman** (arsitektur bot yang well-structured)

## ✨ Fitur Utama

### 🧬 Sistem Karakter
**15 Ras berbeda**: Human, Elf, Orc, Dwarf, Vampire, Dragontamer, Fairy, Griffin, Nymph, Werewolf, Pegasus, Mermaid, Angel, Demon, Bunny
**10 Kelas/Job**: Archer, Warrior, Rogue, Poet, Oracle, Witch, Hunter, Alchemist, Blacksmith, Jobless

- **Critical Hit**: Perhitungan kerusakan kritis berdasarkan stat

### 🗺️ Sistem Eksplorasi
- **44+ Lokasi**: Dari hutan mistis hingga gunung naga
- **Monster Lokal**: Setiap lokasi punya monster unik
- **World State**: Dunia yang berubah sesuai aksi pemain
- **World Events**: Event global yang mempengaruhi semua pemain

### 📜 Sistem Quest
- **Quest Board**: Di Guild untuk menerima misi
- **Quest Paths**: Pilihan cabang quest yang berbeda
- **Rewards**: Gold, EXP, items, reputasi
- **Progress Tracking**: Lacak progress quest aktif

### 💼 Sistem Inventory
- **Weight System**: Setiap item punya berat maksimal sesuai stat
- **Equipment Management**: Equip/unequip senjata dan armor
- **Crafting System**: Buat item di station khusus
- **Recipe System**: Resep crafting dengan material requirements

### 👥 Sistem Sosial
- **Party System**: Bentuk party bersama pemain lain
- **Companion Recruitment**: Rekrut NPC sebagai pendamping
- **Reputation System**: Reputasi dengan berbagai faction
- **Achievements**: Unlock milestone melalui gameplay
- **Story Events**: Event cerita personal berdasarkan karakter

### 💾 Penyimpanan Data
- **Firebase Integration**: Penyimpanan cloud dengan Firestore
- **In-Memory Fallback**: Mode offline jika Firebase tidak tersedia
- **Persistent Storage**: Data karakter tersimpan permanen
- **Real-time Sync**: Data tersinkronisasi antar sesi

## 🔧 Prasyarat

Sebelum memulai, pastikan Anda memiliki:

- **Node.js 18.0+** - Runtime JavaScript
- **npm 9.0+** - Package manager
- **Discord Bot Token** - Dari Discord Developer Portal
- **Firebase Project** - Untuk penyimpanan data (opsional, ada fallback in-memory)
- **Git** - Untuk clone repository (opsional)

## 📦 Instalasi

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/botetherial.git
cd botetherial
```

### 2. Install Dependencies

```bash
npm install
```

Dependencies utama:
- **discord.js** (^14.16.3) - Discord Bot Framework
- **firebase-admin** (^12.7.0) - Firebase Admin SDK
- **dotenv** (^16.4.5) - Environment variables management

### 3. Setup Konfigurasi

Buat file `config.json` di root directory:

```json
{
  "token": "YOUR_DISCORD_BOT_TOKEN_HERE",
  "prefix": "!"
}
```

Atau gunakan file `.env`:

```
DISCORD_BOT_TOKEN=your_token_here
GOOGLE_APPLICATION_CREDENTIALS=./etherial-fantasy-firebase-adminsdk-fbsvc-*.json
```

## ⚙️ Konfigurasi

### File Konfigurasi

**config.json** - Konfigurasi utama bot
```json
{
  "token": "YOUR_BOT_TOKEN",
  "prefix": "!",
  "defaultPrefix": "!"
}
```

### Variabel Lingkungan

Buat file `.env` untuk development:
```
DISCORD_BOT_TOKEN=your_token
NODE_ENV=development
```

Untuk production dengan Firebase:
```
DISCORD_BOT_TOKEN=your_token
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-adminsdk.json
```

## 🚀 Menjalankan Bot

### Mode Development

```bash
# Jalankan langsung
node src/index.js

# Atau gunakan npm script
npm start
```

### Mode Production dengan PM2

```bash
# Install PM2 globally
npm install -g pm2

# Start bot dengan PM2
pm2 start src/index.js --name "etherial-bot"

# Lihat status
pm2 status

# Lihat logs real-time
pm2 logs etherial-bot

# Simpan agar restart otomatis
pm2 save
pm2 startup
```

### Mode Development dengan Watch

```bash
# Install nodemon
npm install --save-dev nodemon

# Run dengan auto-reload
nodemon src/index.js
```

## 🎮 Perintah Bot

Prefix default: `!`

### 👤 Manajemen Karakter

| Perintah | Penggunaan | Deskripsi |
|----------|-----------|-----------|
| `!createchar` | `!createchar <ras> <nama>` | Buat karakter baru |
| `!profile` | `!profile` | Lihat profil karakter |
| `!status` | `!status` | Status cepat (HP, level, gold) |
| `!stats` | `!stats` | Lihat statistik detail |
| `!statpoints` | `!statpoints` | Lihat stat points tersedia |
| `!alloc` | `!alloc <stat> [jumlah]` | Alokasikan stat points |
| `!races` | `!races` | Daftar ras tersedia |
| `!jobs` | `!jobs` | Daftar kelas/job tersedia |

### 🗺️ Eksplorasi & Lokasi

| Perintah | Penggunaan | Deskripsi |
|----------|-----------|-----------|
| `!map` | `!map` | Tampilkan peta dunia |
| `!travel` | `!travel <lokasi>` | Pindah ke lokasi lain |
| `!cityhall` | `!cityhall` | Kota Utama - Pusat administrasi |
| `!guild` | `!guild` | Guild Petualang - Menerima quest |
| `!blacksmith` | `!blacksmith` | Pandai besi - Upgrade senjata |
| `!alchemist` | `!alchemist` | Alkemis - Upgrade trinket |
| `!tavern` | `!tavern` | Tavern - Istirahat & companion |
| `!frontier` | `!frontier` | Pos Perbatasan - Perjalanan |

### ⚔️ Pertarungan

| Perintah | Penggunaan | Deskripsi |
|----------|-----------|-----------|
| `!startbattle` | `!startbattle` | Mulai pertarungan |
| `!battle` | `!battle` | Cek status pertarungan |
| `!attack` | `!attack` | Serang musuh |
| `!flee` | `!flee` | Kabur dari pertarungan |
| `!loot` | `!loot <monster>` | Lihat loot table monster |
| `!bestiary` | `!bestiary [lokasi]` | Daftar monster di lokasi |

### 💼 Inventory & Item

| Perintah | Penggunaan | Deskripsi |
|----------|-----------|-----------|
| `!inventory` | `!inventory` | Lihat inventory |
| `!equip` | `!equip <item>` | Pasang equipment |
| `!unequip` | `!unequip <slot>` | Lepas equipment |
| `!equipped` | `!equipped` | Lihat equipment aktif |
| `!use` | `!use <item>` | Gunakan item consumable |
| `!recipes` | `!recipes` | Daftar resep crafting |
| `!craft` | `!craft <item> [qty]` | Buat item di station |
| `!upgrade` | `!upgrade <item>` | Tingkatkan equipment |
| `!shop` | `!shop` | Lihat toko lokasi |
| `!buy` | `!buy <item> [qty]` | Beli item dari toko |

### 📜 Quest & Misi

| Perintah | Penggunaan | Deskripsi |
|----------|-----------|-----------|
| `!questboard` | `!questboard` | Lihat papan quest |
| `!acceptquest` | `!acceptquest <nomor>` | Ambil quest |
| `!questpath` | `!questpath <id> <branch>` | Pilih cabang quest |
| `!quests` | `!quests` | Lihat quest aktif |
| `!completequest` | `!completequest <id>` | Selesaikan quest |

### 👥 Sosial & Party

| Perintah | Penggunaan | Deskripsi |
|----------|-----------|-----------|
| `!party` | `!party <create\|join\|leave\|info\|disband>` | Kelola party |
| `!companions` | `!companions` | Lihat companion |
| `!recruit` | `!recruit <nama>` | Rekrut companion |
| `!dismiss` | `!dismiss <nama>` | Lepas companion |
| `!scene` | `!scene <aksi>` | Tampilkan adegan roleplay |
| `!reputation` | `!reputation [faction]` | Lihat reputasi faction |
| `!achievements` | `!achievements` | Lihat achievement |

### ℹ️ Umum

| Perintah | Penggunaan | Deskripsi |
|----------|-----------|-----------|
| `!help` | `!help` | Tampilkan bantuan lengkap |
| `!commands` | `!commands` | Daftar semua perintah |
| `!dbstatus` | `!dbstatus` | Status database |

## 🎲 Sistem Permainan

### Ras (Races) 🧬

Setiap ras punya bonus stat unik:

- **Elf** - Bonus AGI & DEX, cocok untuk Archer/Rogue
- **Dwarf** - Bonus STR & VIT, cocok untuk Warrior
- **Human** - Balanced, cocok untuk hybrid class
- **Demon** - Bonus INT & WIS, cocok untuk Mage
- **Halfling** - Bonus LUK & AGI
- **Tiefling** - Bonus INT & CRT
- **Dragonborn** - Bonus STR & HP

### Kelas (Jobs) ⚔️

Setiap kelas punya specialty dan stat growth:

- **Warrior** - Damage tinggi, DEF tinggi

### Leveling System 📊

- **Base Level**: Mulai dari 1
- **EXP System**: Setiap kemenangan & quest beri EXP
- **Merchant Guild** - Perdagangan & bisnis
### Ras (Races) 🧬
- **Dark Society** - Underground & quest tersembunyi
Tersedia **15 ras berbeda**, masing-masing dengan bonus stat unik dan special trait:

| Ras | Keunggulan | Special Trait |
|-----|-----------|---------------|
| **Human** | Balanced, versatile | Adaptable - +5% semua resistansi |
| **Elf** | AGI, DEX tinggi | Grace - DEX +15%, loot rate +10% |
| **Orc** | STR, VIT tinggi | Warlord - ATK +15% saat HP penuh |
| **Dwarf** | VIT, TEC tinggi | Ironbody - DEF +20% untuk stone skin |
| **Vampire** | INT, CRT tinggi | Nightborn - Vampirism +25%, regen saat gelap |
| **Dragontamer** | STR, INT | Dragon Bond - Dapat ride naga, damage +20% |
| **Fairy** | AGI, MEN tinggi | Pixie Magic - MATK +15%, SP cost -20% |
| **Griffin** | STR, VIT | Sky Guardian - dapat terbang, DEF +10% udara |
| **Nymph** | INT, MEN | Nature's Child - nature magic +20%, heal +10% |
| **Werewolf** | AGI, STR | Beast Form - dapat transform, ATK +25% malam |
| **Pegasus** | AGI, VIT | Celestial Speed - ASPD +20%, dapat terbang |
| **Mermaid** | INT, MEN | Water Bond - underwater breathing, MDEF +15% |
| **Angel** | INT, VIT | Holy Light - healing +20%, undead damage +30% |
| **Demon** | INT, CRT | Dark Power - dark magic +25%, curse resistance |
| **Bunny** | AGI, LUK | Lucky Hopper - CRIT +18%, loot rate +20% |
Naik reputasi dengan menyelesaikan quest & membeli dari merchant.
### Kelas (Jobs) ⚔️

Tersedia **10 kelas/job berbeda**, dengan stat growth dan skill unik:
### Achievement 🏅
| Kelas | Role | Special Ability | Initial Skills |
|-------|------|-----------------|-----------------|
| **Archer** | DPS Ranged | Multi-shot attacks | Double Shot, Arrow Shower |
| **Warrior** | Tank/DPS | Shield Wall defense | Bash, Power Attack |
| **Rogue** | DPS Assassin | Backstab crit dmg | Quick Strike, Evasion |
| **Poet** | Support Buff | Inspiring verses | Inspiring Song, Healing Melody |
| **Oracle** | Support Divination | Foresight prediction | Divine Light, Prophecy |
| **Witch** | Control/Debuff | Hexing enemies | Curse, Hex Nail |
| **Hunter** | Tracker/Traps | Trap Master system | Lay Trap, Headshot |
| **Alchemist** | Crafter/Support | Potion Mastery | Create Potion, Potion Throw |
| **Blacksmith** | Crafter/Tank | Forge Master equipment | Forge, Weaponry |
| **Jobless** | Flexible/Hybrid | Freeform building | Basic Attack, Item Use |

- **Combat**: Victory, Boss Kill, Streak
- **Progression**: Level milestones
├── src/
│   ├── index.js                  # Entry point
│   ├── stats.js                  # Sistem statistik karakter
│   ├── monsters.json             # Monster definitions
│   ├── recipes.json              # Crafting recipes
│   └── world_events.json         # World events (opsional)
├── config.json                   # Bot configuration
├── package.json                  # Node.js dependencies
├── races.json                    # Race definitions
├── jobs.json                     # Job definitions
├── starter_kits.json             # Starting kit definitions
├── .gitignore                    # Git ignore rules
├── README.md                     # Documentation (file ini)
└── etherial-fantasy-firebase-*.json  # Firebase credentials (tidak di-commit)
```

### File Kunci

- **src/bot.js** (600+ lines) - Semua command handlers Discord.js
- **src/game-core.js** (900 lines) - Helper functions & catalogs
- **src/stats.js** (260 lines) - Stat calculation formulas
- **src/db.js** (220 lines) - Database persistence layer

## 🔥 Setup Firebase

### 1. Buat Firebase Project

1. Kunjungi [Firebase Console](https://console.firebase.google.com)
2. Klik "Buat Proyek"
3. Masukkan nama proyek (misal: "etherial-fantasy")
4. Ikuti wizard setup

### 2. Buat Firestore Database

1. Di Firebase Console, klik "Firestore Database"
2. Klik "Buat Database"
3. Pilih "Mode Pengembangan" (untuk testing)
4. Pilih lokasi regional terdekat

### 3. Generate Service Account Key

1. Klik "Project Settings" ⚙️
2. Tab "Service Accounts"
3. Klik "Generate New Private Key"
4. Simpan file sebagai `etherial-fantasy-firebase-adminsdk-fbsvc-*.json`
5. **PENTING**: Tambahkan ke `.gitignore` agar tidak di-commit

### 4. Setup Environment

Atur environment variable atau edit config.json:

```bash
# Windows PowerShell
$env:GOOGLE_APPLICATION_CREDENTIALS = "path/to/etherial-fantasy-firebase-adminsdk-fbsvc-*.json"
npm start

# Linux/macOS
export GOOGLE_APPLICATION_CREDENTIALS="path/to/etherial-fantasy-firebase-adminsdk-fbsvc-*.json"
npm start
```

### 5. Testing Koneksi

Jalankan bot dan lihat logs:
```
✅ Firestore connected successfully
✅ Bot ready as EtherialFantasy#XXXX
```

Jika tidak ada Firebase, bot akan mode fallback (in-memory):
```
⚠️ Using in-memory storage
```

## 🚀 Deployment

### Deployment ke Railway.app (Rekomendasi)

Railway adalah platform hosting yang mudah untuk bot Discord:

1. **Kunjungi** https://railway.app
2. **Login** dengan GitHub
3. **Connect** repository GitHub Anda
4. **Set Variables**:
   - `DISCORD_BOT_TOKEN`: Token bot Anda
   - `GOOGLE_APPLICATION_CREDENTIALS`: Upload Firebase JSON
5. **Deploy** - Selesai!

### Deployment ke Render.com

1. Kunjungi https://render.com
2. Create "Web Service"
3. Connect GitHub repo
4. Build command: `npm install`
5. Start command: `npm start`
6. Set environment variables
7. Deploy

### Deployment ke VPS (AWS, DigitalOcean, Linode)

```bash
# SSH ke server
ssh user@your_server_ip

# Clone repository
git clone https://github.com/yourusername/botetherial.git
cd botetherial

# Install Node.js & npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install dependencies
npm install

# Setup PM2
npm install -g pm2
pm2 start src/index.js --name "etherial-bot"
pm2 save
pm2 startup

# Setup auto-restart on reboot
sudo systemctl enable pm2-root
```

### Monitoring

Gunakan PM2 untuk monitoring:

```bash
# Dashboard
pm2 monit

# Logs
pm2 logs etherial-bot

# Restart
pm2 restart etherial-bot

# Stop
pm2 stop etherial-bot
```

## 🔧 Troubleshooting

### Bot Tidak Start

**Error: "Tidak ada token di config.json"**

Solusi:
1. Pastikan file `config.json` ada di root directory
2. Cek format JSON valid
3. Masukkan bot token yang benar

```json
{
  "token": "YOUR_TOKEN_HERE",
  "prefix": "!"
}
```

### Firebase Connection Failed

**Error: "GOOGLE_APPLICATION_CREDENTIALS not set"**

Solusi:
1. Pastikan Firebase adminsdk JSON ada
2. Set environment variable dengan benar
3. Bot akan fallback ke in-memory storage

```bash
# Test koneksi
node -e "console.log(process.env.GOOGLE_APPLICATION_CREDENTIALS)"
```

### Bot Memori Tinggi

Solusi:
1. Periksa jumlah session active: `!dbstatus`
2. Gunakan PM2 dengan memory limit: `pm2 start src/index.js --max-memory-restart 500M`
3. Bersihkan cache lama dari Firestore

### Commands Tidak Merespons

**Error: "Commands not working"**

Solusi:
1. Pastikan bot punya permission "Send Messages" di server
2. Cek prefix yang digunakan (default: `!`)
3. Ensure bot has "Message Content Intent" enabled di Developer Portal
4. Lihat logs: `pm2 logs etherial-bot`

### Firestore Quota Exceeded

Jika melebihi free tier quota Firestore:
1. Upgrade Firebase Plan
2. Atau hapus data lama dari Firestore
3. Implementasi caching layer

## 📚 Dokumentasi Lanjutan

### Menambah Lokasi Baru

Edit `data/map.json`:

```json
{
  "lokasi_baru": {
    "name": "Lokasi Baru",
    "description": "Deskripsi lokasi",
    "region": "Region Name",
    "npcs": [],
    "services": ["shop", "inn"]
  }
}
```

### Menambah Item Baru

Edit `data/items.json`:

```json
{
  "item_name": {
    "name": "Item Name",
    "description": "Item description",
    "type": "weapon|armor|consumable",
    "price": 100,
    "weight": 5,
    "rarity": "common|uncommon|rare|epic"
  }
}
```

### Menambah Monster Baru

Edit `data/monsters.json`:

```json
{
  "lokasi_name": [
    {
      "name": "Monster Name",
      "hp": 50,
      "atk": 15,
      "loot": ["item1", "item2"]
    }
  ]
}
```

### Modifikasi Stat Formula

Edit `src/stats.js` - Fungsi `calculateDerivedStats()`:

```javascript
function calculateDerivedStats(baseStats, level, bonuses) {
  // Modify formula sesuai kebutuhan
  const atk = (baseStats.str || 10) * 1.5 + bonuses.atk;
  // ...
}
```

## 🤝 Berkontribusi

Kontribusi sangat diterima! Berikut langkahnya:

1. **Fork repository** - Klik tombol Fork di GitHub
2. **Clone repo lokal**:
   ```bash
   git clone https://github.com/yourusername/botetherial.git
   ```
3. **Buat feature branch**:
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **Commit changes**:
   ```bash
   git commit -m "Add amazing feature"
   ```
5. **Push ke branch**:
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Buka Pull Request** di GitHub

### Guidelines Kontribusi

- Ikuti kode style yang ada
- Tambahkan test untuk fitur baru
- Update documentation
- Pastikan semua tests pass: `npm test`
- Jangan commit file sensitif (tokens, credentials)

## 📄 Lisensi

Proyek ini adalah open source. Pastikan credentials Firebase **TIDAK PERNAH** di-commit ke GitHub.

## 📞 Support & Komunitas

- **Lapor Bug** - Buka issue di GitHub
- **Request Fitur** - Diskusi di GitHub Discussions
- **Discord Community** - Bergabung dengan server Etherial Fantasy
- **Documentation** - Baca README ini atau buka wiki

## 🎉 Terima Kasih!

Terima kasih telah menggunakan **Etherial Fantasy Bot**! 

Jika Anda menyukai proyek ini:
- ⭐ **Star** repository ini di GitHub
- 🐛 **Report bugs** jika menemukan masalah
- 💡 **Suggest features** untuk improvement
- 🤝 **Contribute** dengan pull request

---

**Last Updated**: May 10, 2026
**Bot Version**: 2.0.0 (Node.js)
**Status**: ✅ Production Ready
