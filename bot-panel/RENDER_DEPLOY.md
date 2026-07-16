# 🚀 Guía de despliegue en Render

## Requisitos previos
- Cuenta en [render.com](https://render.com) (gratis)
- Repo en GitHub con este proyecto subido
- Tu Neon PostgreSQL connection string
- Tu Cloudflare R2 configurado

---

## Paso 1 — Subir a GitHub

```bash
git init
git add .
git commit -m "Discord Bot Panel"
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

---

## Paso 2 — Crear el Web Service en Render

1. Ve a [dashboard.render.com](https://dashboard.render.com)
2. Clic en **New → Web Service**
3. Conecta tu cuenta de GitHub y selecciona tu repositorio
4. Render detecta el `render.yaml` automáticamente

Si pide configuración manual usa estos valores:

| Campo | Valor |
|-------|-------|
| **Root Directory** | `bot-panel` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app` |

---

## Paso 3 — Variables de entorno en Render

Ve a tu servicio → **Environment** → **Add Environment Variable** y añade:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `SECRET_KEY` | Clave secreta Flask (larga y aleatoria) | `a8f3k2...` (64 chars) |
| `ADMIN_USERNAME` | Usuario del panel | `admin` |
| `ADMIN_PASSWORD` | Contraseña del panel | `MiPassword123!` |
| `DATABASE_URL` | Neon PostgreSQL connection string | `postgresql://user:pass@host.neon.tech/db?sslmode=require` |
| `BOT_TOKEN` | Token de tu bot de Discord | `MTxxxxxxx.Gxxxxx.xxx` |
| `R2_ENDPOINT` | Endpoint S3 de Cloudflare R2 | `https://abc123.r2.cloudflarestorage.com` |
| `R2_ACCESS_KEY` | Access Key ID de R2 | `abc123...` |
| `R2_SECRET_KEY` | Secret Access Key de R2 | `xyz789...` |
| `R2_BUCKET` | Nombre del bucket R2 | `mi-bucket` |
| `R2_PUBLIC_URL` | URL pública del bucket (opcional) | `https://files.midominio.com` |
| `FLASK_ENV` | Modo Flask | `production` |
| `BOT_PREFIX` | Prefijo del bot | `!` |
| `LAVALINK_HOST` | Host de Lavalink (si usas música) | `lavalink.miservidor.com` |
| `LAVALINK_PASSWORD` | Password de Lavalink | `youshallnotpass` |

> ⚠️ **DATABASE_URL en Render**: Neon a veces da URLs con `postgres://` pero SQLAlchemy necesita `postgresql://`. Cámbialo si es necesario.

---

## Paso 4 — Deploy

1. Clic en **Create Web Service**
2. Render instala dependencias y arranca Gunicorn automáticamente
3. Espera ~2-3 minutos el primer deploy
4. Tu panel estará en `https://tu-servicio.onrender.com`

---

## Problemas comunes en Render

### ❌ `ModuleNotFoundError`
**Causa**: Falta una librería en `requirements.txt`
**Fix**: Añade el módulo faltante al archivo y haz redeploy

### ❌ `sqlalchemy.exc.OperationalError` / no se conecta a DB
**Causa**: `DATABASE_URL` mal formada o Neon rechaza la conexión
**Fix**:
- Verifica que empiece con `postgresql://` (no `postgres://`)
- En Neon: **Settings → Connection pooling** → activa pooling y usa esa URL
- Añade `?sslmode=require` al final si no lo tiene

### ❌ App carga pero da 500 al hacer login
**Causa**: `SECRET_KEY` no configurada o la DB no tiene las tablas
**Fix**:
- Asegúrate de que `SECRET_KEY` esté en las env vars de Render
- La app crea las tablas automáticamente en el primer arranque; revisa los logs

### ❌ Se cae después de 15 minutos (plan gratis)
**Causa**: Render duerme los servicios gratuitos por inactividad
**Fix**: Usa [UptimeRobot](https://uptimerobot.com) con un monitor HTTP a tu URL cada 10 minutos para mantenerlo despierto (gratis)

### ❌ Archivos subidos desaparecen
**Causa**: Render no tiene disco persistente en el plan gratis
**Fix**: Usa R2 para todos los archivos (ya está integrado). Los uploads temporales en `/uploads` se pierden al reiniciar — configura R2 para guardarlos permanentemente

### ❌ `gunicorn: command not found`
**Causa**: `gunicorn` no está en `requirements.txt`
**Fix**: Ya está incluido en el `requirements.txt` de este proyecto

---

## Plan recomendado en Render

| Plan | Precio | RAM | CPU | Sleep |
|------|--------|-----|-----|-------|
| Free | $0/mes | 512MB | 0.1 | Sí (15min) |
| Starter | $7/mes | 512MB | 0.5 | No |
| Standard | $25/mes | 2GB | 1.0 | No |

Para un bot en producción, usa mínimo **Starter** para que no se duerma.

---

## Actualizar el panel

Cada push a tu repo en GitHub hace **redeploy automático** en Render (si tienes el auto-deploy activado).

```bash
git add .
git commit -m "Actualización"
git push
```

Render detecta el push y despliega en ~1-2 minutos.
