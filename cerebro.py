import os
import subprocess
import time
import atexit
import json
import requests
import ollama
from dotenv import load_dotenv

from modulos.configuracion import cargar_configuracion

load_dotenv()

# Variable global para rastrear el proceso de Ollama en segundo plano
proceso_ollama = None


def iniciar_motor():
    global proceso_ollama
    print("[SISTEMA] Iniciando corteza cerebral (Ollama) en segundo plano...")
    try:
        proceso_ollama = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)  # Dar tiempo al disco para levantar el servicio local
        print("[SISTEMA] Red neuronal en línea.")
    except Exception as e:
        print(f"[ERROR] No se pudo iniciar Ollama automáticamente: {e}")


def apagar_motor():
    if proceso_ollama:
        proceso_ollama.terminate()
        print("[SISTEMA] Motor cognitivo apagado. Memoria liberada.")


# Garantiza que el proceso en segundo plano se mate al cerrar el script
atexit.register(apagar_motor)


class Cerebro:
    def __init__(self):
        # Enciende el motor automáticamente al instanciar la clase
        iniciar_motor()

        configuracion_completa = cargar_configuracion()
        configuracion = configuracion_completa.get("configuracion", {})
        configuracion_ollama = configuracion.get("ollama", {})
        asistente = configuracion.get("asistente", {})

        self.host = os.getenv("OLLAMA_HOST", configuracion_ollama.get("host", "http://127.0.0.1:11434"))
        self.cliente = ollama.Client(host=self.host)

        # Variables de configuración y lectura directa de los prompts desde el JSON
        self.config = {
            "host": self.host,
            "modelo_rapido": os.getenv(
                "OLLAMA_MODEL_RAPIDO",
                configuracion_ollama.get("modelo_rapido", configuracion.get("modelo_rapido", "qwen2.5:1.5b"))
            ),
            "modelo_razonamiento": os.getenv(
                "OLLAMA_MODEL_RAZONAMIENTO",
                configuracion_ollama.get("modelo_razonamiento", configuracion.get("modelo_razonamiento", "llama3.2:3b"))
            ),
            "viernes_system_prompt": asistente.get(
                "viernes_system_prompt",
                configuracion.get(
                    "viernes_system_prompt",
                    "Eres VIERNES. Tu único usuario es Gabriel. Eres directa y seca."
                )
            ),
            # Se lee el router_prompt directamente desde la raíz de "configuracion" en el JSON
            "router_prompt": configuracion.get(
                "router_prompt", 
                "Responde en JSON con {'accion': 'ninguna', 'parametro': ''}"
            )
        }

    def _requiere_razonamiento(self, texto):
        """Evalúa si el texto contiene palabras clave que exigen razonamiento profundo."""
        palabras_clave = [
            "código",
            "programa",
            "analiza",
            "razona",
            "calcula",
            "algoritmo",
            "arquitectura",
            "explica",
            "aplicación",
            "json",
        ]
        texto_lower = (texto or "").lower()
        return any(palabra in texto_lower for palabra in palabras_clave)

    def analizar_intencion(self, texto_usuario: str) -> dict:
        """
        Enrutador ultrarrápido (GPU): extrae la acción multimedia y el parámetro limpio 
        utilizando el prompt leído directamente desde el archivo config.json.
        """
        prompt_sistema = self.config["router_prompt"]
        
        try:
            payload = {
                "model": self.config["modelo_rapido"],
                "prompt": texto_usuario,
                "system": prompt_sistema,
                "stream": False,
                "format": "json",  # Fuerza la salida en JSON puro nativo de Ollama
                "options": {"temperature": 0.0}
            }

            url = f"{self.host}/api/generate"
            respuesta = requests.post(url, json=payload, timeout=10)

            if respuesta.status_code == 200:
                contenido_json = respuesta.json().get("response", "{}")
                return json.loads(contenido_json)
            else:
                return {"accion": "ninguna", "parametro": ""}

        except Exception as e:
            print(f"[ERROR CEREBRO JSON]: {e}")
            return {"accion": "ninguna", "parametro": ""}

    def generar_respuesta(self, texto_usuario, al_recibir=None):
        """Envía el texto a la API de Ollama usando el enrutador cognitivo (GPU vs CPU)."""
        try:
            prompt_usuario = texto_usuario

            # FASE 3: Enrutador y control de hardware
            if self._requiere_razonamiento(prompt_usuario):
                print("[SISTEMA] Tarea compleja detectada. Derivando al Procesador (CPU) con red profunda...")
                modelo_activo = self.config["modelo_razonamiento"]
                tiempo_vida = "0s"
                opciones_hardware = {"num_gpu": 0}
            else:
                modelo_activo = self.config["modelo_rapido"]
                tiempo_vida = "5m"
                opciones_hardware = {}

            # FASE 4: Modificación del payload de la petición HTTP
            payload = {
                "model": modelo_activo,
                "prompt": prompt_usuario,
                "system": self.config["viernes_system_prompt"],
                "stream": False,
                "keep_alive": tiempo_vida,
                "options": opciones_hardware
            }

            url = f"{self.host}/api/generate"
            respuesta = requests.post(url, json=payload, timeout=120)

            if respuesta.status_code == 200:
                texto_respuesta = respuesta.json().get("response", "")
                if al_recibir and texto_respuesta:
                    al_recibir(texto_respuesta)
                return texto_respuesta
            else:
                return f"Permiso denegado, Jefe. Error del servidor local: código {respuesta.status_code}"

        except Exception as e:
            return f"Permiso denegado, Jefe. No puedo conectar con el servidor local: {e}"


# Código de prueba (solo se ejecuta si corres este archivo directamente)
if __name__ == "__main__":
    viernes_cerebro = Cerebro()
    print("Prueba del cerebro iniciada. Escribe 'salir' para terminar.")
    while True:
        entrada = input("Gabriel: ")
        if entrada.lower() == "salir":
            break
        
        intencion = viernes_cerebro.analizar_intencion(entrada)
        print(f"JSON Detectado: {intencion}")
        
        if intencion.get("accion") == "ninguna":
            print(f"VIERNES: {viernes_cerebro.generar_respuesta(entrada)}")
        else:
            print(f"VIERNES (Acción): Ejecutaría {intencion['accion']} para '{intencion['parametro']}'")