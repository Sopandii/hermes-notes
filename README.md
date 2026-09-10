# Hermes Notes Vault

Kumpulan session export + skills dari Hermes Agent, dikelompokkan biar gampang dicari.

## Struktur

```
.
├── README.md              # ini
├── index.md              # daftar session & topik
├── sessions/             # transcript session (per bulan)
│   └── 2026-09/          # contoh: September 2026
├── topics/               # notes topik (dii extract dari session)
│   └── wordpress-n8n-setup.md
└── skills/               # skills Hermes
    └── ubuntu-wp-n8n-local-setup/
        └── SKILL.md
```

## Cara pakai

### Di terminal
```bash
# Cari di seluruh vault
grep -ri "keyword" .

# Buka session tertentu
less sessions/2026-09/nama-session.md
```

### Di Obsidian (kalau mau)
1. Buka Obsidian
2. `Open folder as vault` → pilih folder ini: `~/projects/hermes-notes/`
3. Session dan topics muncul sebagai notes

## Session yang ada

Lihat `index.md` untuk daftar lengkap.

## Otomasi

Script `export_sessions.py` jalan tiap hari jam 02:00 UTC via cron.
Export session baru → commit → push ke GitHub.

Repo: https://github.com/Sopandii/hermes-notes
