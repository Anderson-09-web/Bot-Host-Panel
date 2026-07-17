# Discord Bot Panel

A Flask web application that serves as an admin panel for a Discord bot.

## Stack
- **Backend:** Python 3.12, Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Bot:** discord.py, wavelink (Lavalink music)
- **Database:** Neon PostgreSQL (via `NEON_DATABASE_URL`)
- **Storage:** Cloudflare R2 (optional)
- **Entry point:** `bot-panel/app.py`

## How to run
The **Bot Panel** workflow runs `cd bot-panel && python app.py` and serves on port 5000.

## Required secrets (Replit Secrets)
| Secret | Description |
|--------|-------------|
| `BOT_TOKEN` | Discord bot token |
| `NEON_DATABASE_URL` | Neon PostgreSQL connection string |
| `SECRET_KEY` | Flask session secret key |
| `ADMIN_PASSWORD` | Password for the admin panel user |

## Optional secrets (for Cloudflare R2 storage)
| Secret | Description |
|--------|-------------|
| `R2_ENDPOINT` | `https://ACCOUNT_ID.r2.cloudflarestorage.com` |
| `R2_ACCESS_KEY` | R2 access key |
| `R2_SECRET_KEY` | R2 secret key |
| `R2_BUCKET` | Bucket name |
| `R2_PUBLIC_URL` | Public R2 URL |

## Optional secrets (for Lavalink music)
| Secret | Description |
|--------|-------------|
| `LAVALINK_HOST` | Lavalink server host |
| `LAVALINK_PASSWORD` | Lavalink password |

## User preferences
- Spanish-language project; keep comments and logs in Spanish where present.
