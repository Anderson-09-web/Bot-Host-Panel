# 🚀 Guía completa de despliegue en Render

## Lo que se despliega
Un solo **Web Service** en Render que corre:
- El panel Flask con Gunicorn (puerto asignado por Render)
- El bot de Discord como subproceso (lo lanza el panel al arrancar)

---

## Paso 1 — Subir el código a GitHub

En tu terminal (o desde Replit → Shell):

```bash
cd /home/runner/workspace   # raíz del monorepo

git init
git add .
git commit -m "Discord Bot Panel v1"

# Crea un repo vacío en github.com y copia la URL
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -u origin main
```

> El archivo `render.yaml` en la raíz le dice a Render todo lo que necesita.

---

## Paso 2 — Crear el Web Service en Render

1. Entra a [dashboard.render.com](https://dashboard.render.com) → **New → Web Service**
2. Conecta tu cuenta de GitHub y selecciona el repositorio
3. Render detecta el `render.yaml` automáticamente y propone la configuración

Si pide configuración manual usa exactamente esto:

| Campo | Valor |
|-------|-------|
| **Root Directory** | `bot-panel` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 2 --worker-class gthread --timeout 120 --keep-alive 5` |
| **Health Check Path** | `/login` |

---

## Paso 3 — Variables de entorno (Environment Variables)

Ve a tu servicio → **Environment** → **Add Environment Variable**

### Variables con valor fijo (cópialas tal cual)

| Variable | Valor |
|----------|-------|
| `FLASK_ENV` | `production` |
| `ADMIN_USERNAME` | `admin` |
| `BOT_PREFIX` | `!` |
| `BOT_TIMEZONE` | `UTC` |

### Variables secretas (copia el valor desde tus secretos de Replit)

> En Replit ve a **Secrets** (ícono del candado) para ver los valores reales.

| Variable en Render | De dónde copiar el valor | Descripción |
|--------------------|--------------------------|-------------|
| `SECRET_KEY` | Secret `SECRET_KEY` de Replit | Clave Flask (mín. 32 chars) |
| `ADMIN_PASSWORD` | Secret `ADMIN_PASSWORD` de Replit | Contraseña del panel |
| `BOT_TOKEN` | Secret `BOT_TOKEN` de Replit | Token del bot de Discord |
| `DATABASE_URL` | Secret `NEON_DATABASE_URL` de Replit | Connection string de Neon |
| `R2_ENDPOINT` | Secret `R2_ENDPOINT` de Replit | `https://ID.r2.cloudflarestorage.com` |
| `R2_ACCESS_KEY` | Secret `R2_ACCESS_KEY` de Replit | Access Key ID de Cloudflare |
| `R2_SECRET_KEY` | Secret `R2_SECRET_KEY` de Replit | Secret Key de Cloudflare |
| `R2_BUCKET` | Secret `R2_BUCKET` de Replit | Nombre del bucket |
| `R2_PUBLIC_URL` | Secret `R2_PUBLIC_URL` de Replit | URL pública del bucket (opcional) |

> ⚠️ **Importante con Neon:** El valor del secret `NEON_DATABASE_URL` en Replit
> va en la variable `DATABASE_URL` en Render (sin el prefijo NEON_).
> Si la URL empieza con `postgres://` cámbialo a `postgresql://`

### Variables de Lavalink (solo si usas tu propio nodo)

| Variable | Valor |
|----------|-------|
| `LAVALINK_HOST` | host de tu servidor Lavalink (sin `https://`) |
| `LAVALINK_PORT` | `443` (si es SSL) o `2333` (sin SSL) |
| `LAVALINK_PASSWORD` | password del nodo |
| `LAVALINK_SSL` | `true` o `false` |

> Si usas `discord-music-link.onrender.com` (el nodo de la API) no necesitas
> estas variables — el cog las obtiene automáticamente de la API al arrancar.

---

## Paso 4 — Deploy

1. Clic en **Create Web Service** (o **Save Changes** si ya existe)
2. Render instala dependencias y arranca Gunicorn (~2-3 min el primer deploy)
3. Tu panel estará en `https://tu-servicio.onrender.com`
4. Entra con el usuario `admin` y la contraseña que pusiste en `ADMIN_PASSWORD`

---

## Paso 5 — Mantenerlo despierto (plan gratuito)

El plan gratuito de Render duerme el servicio tras 15 min de inactividad.
Para evitarlo crea un monitor gratuito en [UptimeRobot](https://uptimerobot.com):

1. **New Monitor → HTTP(s)**
2. URL: `https://tu-servicio.onrender.com/login`
3. Intervalo: **5 minutos**

Así el panel y el bot estarán siempre activos.

---

## Actualizar el panel después

Cada push a GitHub hace **redeploy automático** (si tienes auto-deploy activado):

```bash
git add .
git commit -m "Actualización"
git push
```

Render detecta el push y despliega en ~1-2 minutos.

---

## Problemas comunes

### ❌ El bot no arranca / `BOT_TOKEN` inválido
Verifica que copiaste el token completo desde el portal de Discord, sin espacios.

### ❌ Error de base de datos al iniciar
- Verifica que `DATABASE_URL` empiece con `postgresql://` (no `postgres://`)
- Añade `?sslmode=require` al final si no lo tiene
- En Neon: **Settings → Connection pooling** → activa pooling y copia esa URL

### ❌ Login da error 500
- Verifica que `SECRET_KEY` esté configurada y no sea el valor por defecto
- Revisa los logs de Render → **Logs** para ver el error exacto

### ❌ Archivos subidos desaparecen
Render no tiene disco persistente en el plan gratuito. Los uploads se pierden al reiniciar.
Configura R2 para guardar archivos permanentemente (las credenciales ya están en el panel).

### ❌ `ModuleNotFoundError`
Falta una librería en `requirements.txt`. Añádela y haz push para redesplegar.

---

## Planes de Render

| Plan | Precio | RAM | Sleep |
|------|--------|-----|-------|
| Free | $0/mes | 512 MB | Sí (15 min) |
| Starter | $7/mes | 512 MB | No ✅ |
| Standard | $25/mes | 2 GB | No ✅ |

Para un bot en producción 24/7 se recomienda **Starter** ($7/mes) para evitar el sleep.
