# 🤖 Selenium Login Bot — 24/7

Bot de automatización que lee correos desde `correos.txt` y prueba el login en tu sitio de forma continua. Diseñado para correr en **Railway** sin intervención manual.

---

## ⚙️ Cómo funciona

```
correos.txt (en GitHub)
        ↓
  Railway lo clona
        ↓
  login_bot.py lee las cuentas
        ↓
  Selenium prueba cada una
        ↓
  Guarda resultados en logs/resultados.csv
        ↓
  Espera X segundos y repite 🔄 (24/7)
```

---

## 📝 Formato de correos.txt

```
# Líneas con # son comentarios
correo1@universidad.edu,contraseña1
correo2@universidad.edu,contraseña2
correo3@universidad.edu,contraseña3
```

---

## 🚀 Despliegue en Railway

### 1. Sube a GitHub
```bash
git init
git add .
git commit -m "feat: selenium login bot 24/7"
git remote add origin https://github.com/tu-usuario/selenium-login.git
git push -u origin main
```

### 2. En Railway
1. Nuevo proyecto → **Deploy from GitHub repo**
2. Ve a **Variables** y agrega:

| Variable | Valor |
|---|---|
| `LOGIN_URL` | `https://tu-sitio.com/login` |
| `ESPERA_SEGUNDOS` | `5` (pausa entre cada cuenta) |
| `ESPERA_CICLO` | `60` (pausa al terminar el ciclo) |

Railway instalará **Chromium** automáticamente gracias a `nixpacks.toml`. ✅

---

## 📊 Resultados

Los resultados se guardan en `logs/resultados.csv`:

```
timestamp,email,exitoso,mensaje
2026-03-15 10:00:01,correo1@uni.edu,SÍ,EXITOSO — Redirigido a /dashboard
2026-03-15 10:00:07,correo2@uni.edu,NO,FALLIDO — Credenciales incorrectas
```

---

## 🔒 Seguridad

> Las contraseñas están en `correos.txt` — si tu repo es **público**, considera encriptar las contraseñas o moverlas a variables de entorno de Railway.
