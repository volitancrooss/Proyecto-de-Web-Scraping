import os
import sys
import time
import re
import csv
import signal
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

# Configurar variables de entorno para minimizar logs
os.environ['WDM_LOG_LEVEL'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def signal_handler(sig, frame):
    """Manejador de señal que termina el proceso de forma inmediata."""
    print("\nCtrl+C detectado. Terminando el programa de forma inmediata...")
    os._exit(0)

# Registrar el handler para SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, signal_handler)

def reiniciar_csv(nombre_archivo="datos_productos.csv"):
    """
    Reinicia el archivo CSV sobrescribiéndolo y escribiendo la cabecera,
    de modo que no se acumulen datos de sesiones anteriores.
    """
    with open(nombre_archivo, "w", newline="", encoding="utf-8") as archivo_csv:
        campos = ["nombre", "precio", "url"]
        writer = csv.DictWriter(archivo_csv, fieldnames=campos)
        writer.writeheader()
    print(f"Archivo '{nombre_archivo}' reiniciado (cabecera escrita).")

def extraer_datos(url, driver):
    """
    Extrae y parsea la información del producto usando Selenium y BeautifulSoup.
    """
    driver.get(url)
    time.sleep(3)  # Espera para que se cargue el contenido dinámico
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    # Extraer nombre del producto
    elemento_nombre = soup.find("h1")
    nombre = elemento_nombre.get_text(strip=True) if elemento_nombre else "Nombre no encontrado"
    
    # Extraer precio
    precio = None
    elemento_precio = soup.find("span", class_="price")
    if elemento_precio:
        precio = elemento_precio.get_text(strip=True)
    if not precio:
        elemento_precio = soup.find("span", class_="price_main")
        if elemento_precio:
            precio = elemento_precio.get_text(strip=True)
    if not precio:
        texto_completo = soup.get_text()
        match = re.search(r"(\d+[,.]?\d*)\s?€", texto_completo)
        if match:
            precio = match.group(0)
    if not precio:
        precio = "Precio no encontrado"
    
    return {"nombre": nombre, "precio": precio, "url": url}

def guardar_datos(datos, nombre_archivo="datos_productos.csv"):
    """
    Guarda los datos en el CSV y muestra un resumen en consola.
    """
    with open(nombre_archivo, "a", newline="", encoding="utf-8") as archivo_csv:
        campos = ["nombre", "precio", "url"]
        writer = csv.DictWriter(archivo_csv, fieldnames=campos)
        writer.writerow(datos)
    
    print("\n==============================")
    print("   Producto Monitorizado")
    print("==============================")
    print(f"Producto: {datos['nombre']}")
    print(f"Precio  : {datos['precio']}")
    print(f"URL     : {datos['url']}")
    print("==============================\n")

def monitorizar_productos(urls, intervalo=300):
    """
    Monitorea los productos en las URLs indicadas.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    try:
        while True:
            for url in urls:
                datos = extraer_datos(url, driver)
                guardar_datos(datos)
            print(f"\nEsperando {intervalo} segundos para la próxima comprobación...")
            pasos = int(intervalo * 10)
            for _ in tqdm(range(pasos), desc="Tiempo restante", bar_format="{l_bar}{bar} | {remaining} segundos restantes"):
                time.sleep(0.1)
            if intervalo == 30:
                print("Intervalo de 30 segundos alcanzado. Cerrando el programa.")
                break
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        print("Programa finalizado.")

if __name__ == "__main__":
    reiniciar_csv("datos_productos.csv")
    urls_objetivo = [
        "https://www.euronics.es/philips-na221-00-freidora-de-aire.html",
        "https://www.mediamarkt.es/es/category/freidoras-de-aire-6334.html",
        "https://www.carrefour.es/philips-2000-series-na221-00-freidora-sencillo-independiente-1500-w-freidora-de-aire-caliente-negro-plata/8720389034770/p"
    ]
    monitorizar_productos(urls_objetivo, intervalo=30)

















