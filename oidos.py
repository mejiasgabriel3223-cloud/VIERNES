import os
import sys
import time
import warnings
import numpy as np
import speech_recognition as sr
import whisper
import keyboard
from dotenv import load_dotenv

from modulos.configuracion import cargar_configuracion

# Suprimir avisos secundarios de PyTorch / FP16 en CPU para mantener la terminal limpia
warnings.filterwarnings("ignore", message=".*FP16 is not supported on CPU.*")
warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()


class Oidos:
    """
    Módulo Oídos: Subsistema auditivo unificado de alta eficiencia para VIERNES.
    Utiliza OpenAI Whisper para transcripción de voz a texto multilingüe (español e inglés)
    de baja latencia y entrega de órdenes al asistente.
    """

    def __init__(self, modelo_nombre: str = None, idioma: str = None, dispositivo: str = "auto"):
        # 1. Cargar configuraciones del proyecto
        config_whisper = self._obtener_configuracion_whisper()

        self.modelo_nombre = (
            modelo_nombre
            or os.getenv("WHISPER_MODEL")
            or config_whisper.get("modelo", "base")
        )

        # Soporte para español e inglés: 'auto' o None permite a Whisper detectar automáticamente el idioma
        conf_idioma = config_whisper.get("idioma", "auto")
        idioma_seleccionado = (
            idioma
            if idioma is not None
            else os.getenv("WHISPER_LANGUAGE", conf_idioma)
        )
        if idioma_seleccionado in ["auto", "multilingual", "multi", "es,en", "en,es", None, ""]:
            self.idioma = None
        else:
            self.idioma = idioma_seleccionado

        # 2. Detección y selección de dispositivo (CUDA vs CPU)
        dispositivo_solicitado = dispositivo or config_whisper.get("dispositivo", "auto")
        if dispositivo_solicitado == "auto":
            try:
                import torch
                self.dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.dispositivo = "cpu"
        else:
            self.dispositivo = dispositivo_solicitado

        self.usar_fp16 = (self.dispositivo == "cuda")

        # Configuración de entrega por teclado
        self.pulsar_enter_por_defecto = config_whisper.get("pulsar_enter", False)

        # 3. Prompt de contexto para guiar a Whisper hacia órdenes del asistente (español e inglés)
        self.prompt_inicial = (
            "Comandos y órdenes para el asistente VIERNES en español o inglés: reproducir música en YouTube o Spotify, "
            "abrir aplicaciones, buscar en internet, apagar, pausar, siguiente canción. "
            "Commands and instructions for VIERNES assistant in Spanish or English: play music on YouTube or Spotify, "
            "open apps, search the web, shutdown, pause, next song."
        )

        # 4. Carpeta de modelos (local al proyecto si existe, o por defecto de Whisper)
        self.ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.download_root = os.getenv("WHISPER_DOWNLOAD_ROOT")
        if not self.download_root:
            ruta_modelos_local = os.path.join(self.ruta_base, "modelos_whisper")
            if os.path.exists(ruta_modelos_local):
                self.download_root = ruta_modelos_local

        # 5. Carga persistente del modelo en memoria (solo una vez para máxima eficiencia)
        print(f"[Oídos]: Inicializando Whisper (modelo='{self.modelo_nombre}', dispositivo='{self.dispositivo}')...")
        tiempo_inicio = time.time()
        try:
            self.modelo = whisper.load_model(
                self.modelo_nombre,
                device=self.dispositivo,
                download_root=self.download_root
            )
            tiempo_carga = time.time() - tiempo_inicio
            print(f"[Oídos]: Modelo Whisper cargado exitosamente en {tiempo_carga:.2f}s.")
        except Exception as e:
            print(f"[Oídos - Error crítico]: No se pudo cargar el modelo Whisper: {e}")
            raise

        # 6. Inicialización del capturador de audio (SpeechRecognition)
        self.reconocedor = sr.Recognizer()
        self.reconocedor.dynamic_energy_threshold = True
        self.reconocedor.energy_threshold = 300
        # pause_threshold a 0.8s para responder inmediatamente cuando el usuario termina la frase
        self.reconocedor.pause_threshold = 0.8
        self.indice_microfono = self._seleccionar_microfono()

    def _obtener_configuracion_whisper(self) -> dict:
        """Carga de forma segura la sección 'whisper' de config.json si existe."""
        try:
            conf_total = cargar_configuracion()
            conf = conf_total.get("configuracion", {})
            return conf.get("whisper", {})
        except Exception:
            return {}

    def _seleccionar_microfono(self):
        """Obtiene un índice de micrófono válido y resistente a cambios de Windows."""
        indice_configurado = os.getenv("MICROPHONE_INDEX")
        try:
            nombres = sr.Microphone.list_microphone_names()
        except Exception:
            return None

        if indice_configurado:
            try:
                indice = int(indice_configurado)
                if 0 <= indice < len(nombres):
                    return indice
            except ValueError:
                pass

        preferencias = ("microphone array", "frontmic", "microphone", "headset", "usb audio")
        for preferencia in preferencias:
            for indice, nombre in enumerate(nombres):
                if preferencia in nombre.lower():
                    return indice

        return None

    def capturar_audio(self, timeout: int = 15, phrase_time_limit: int = 15):
        """
        Abre el micrófono calibrado y captura el audio del usuario.
        Retorna la instancia AudioData o None si no se captó voz.
        """
        try:
            with sr.Microphone(device_index=self.indice_microfono) as origen:
                # Calibración rápida de 0.5s para no hacer esperar al usuario
                self.reconocedor.adjust_for_ambient_noise(origen, duration=0.5)
                mic_label = self.indice_microfono if self.indice_microfono is not None else "Predeterminado"
                print(f"[Oídos]: Escuchando orden... (Mic: {mic_label})")
                audio = self.reconocedor.listen(origen, timeout=timeout, phrase_time_limit=phrase_time_limit)
                return audio
        except sr.WaitTimeoutError:
            print("[Oídos]: Tiempo de espera agotado (no se detectó voz).")
        except sr.UnknownValueError:
            print("[Oídos]: Audio incomprensible.")
        except (OSError, AssertionError, AttributeError) as e:
            print(f"[Oídos - Error micrófono]: {e}")
        return None

    def transcribir_audio(self, audio_data: sr.AudioData) -> str:
        """
        Convierte el audio directamente en memoria a formato NumPy float32
        y lo transcribe con Whisper con parámetros optimizados de máxima velocidad.
        """
        if not audio_data:
            return ""

        try:
            # Conversión en RAM a 16000 Hz, 16 bits -> Float32 [-1.0, 1.0] (Sin archivos WAV temporales)
            raw_data = audio_data.get_raw_data(convert_rate=16000, convert_width=2)
            audio_np = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Si el audio es menor a 0.3 segundos, se considera ruido/vacío
            if len(audio_np) < 16000 * 0.3:
                return ""

            t0 = time.time()
            resultado = self.modelo.transcribe(
                audio_np,
                language=self.idioma,
                task="transcribe",
                fp16=self.usar_fp16,
                temperature=0.0,
                beam_size=1,
                best_of=1,
                condition_on_previous_text=False,
                without_timestamps=True,
                initial_prompt=self.prompt_inicial,
            )
            latencia = time.time() - t0

            texto = resultado.get("text", "").strip()

            # Limpieza de alucinaciones típicas de silencio
            alucinaciones = ["[música]", "(música)", "[música de fondo]", "...", "¡suscríbete!", "subtítulos"]
            if texto.lower() in alucinaciones:
                return ""

            if texto:
                print(f"[Oídos - Whisper]: Transcrito en {latencia:.2f}s -> \"{texto}\"")

            return texto
        except Exception as e:
            print(f"[Oídos - Error transcripción]: {e}")
            return ""

    def escuchar_y_transcribir(self, timeout: int = 15, phrase_time_limit: int = 15) -> str:
        """Captura audio del micrófono y devuelve el texto transcrito por Whisper."""
        audio = self.capturar_audio(timeout=timeout, phrase_time_limit=phrase_time_limit)
        if audio:
            return self.transcribir_audio(audio)
        return ""

    def grabar_y_transcribir(self, timeout: int = 15, phrase_time_limit: int = 15) -> str:
        """Método de compatibilidad para captura y transcripción de voz."""
        return self.escuchar_y_transcribir(timeout=timeout, phrase_time_limit=phrase_time_limit)

    def entregar_como_teclado(self, texto: str, pulsar_enter: bool = None, delay: float = 0.005) -> bool:
        """
        Escribe la orden transcrita emulando pulsaciones reales del teclado (keyboard.write)
        y opcionalmente presiona 'Enter' (keyboard.send('enter')).
        Esto inyecta la orden en la consola, prompt activo o cualquier ventana abierta.
        """
        if not texto:
            return False

        if pulsar_enter is None:
            pulsar_enter = self.pulsar_enter_por_defecto

        try:
            # Emulamos la escritura como instrucción de teclado física
            keyboard.write(texto, delay=delay)
            if pulsar_enter:
                time.sleep(0.05)
                keyboard.send("enter")
            return True
        except Exception as e:
            print(f"[Oídos - Error Teclado]: No se pudo escribir por teclado: {e}")
            return False

    def escuchar_transcribir_y_entregar(
        self,
        pulsar_enter: bool = True,
        timeout: int = 15,
        phrase_time_limit: int = 15,
        callback=None,
    ) -> str:
        """
        Flujo integral:
        1. Captura de audio por micrófono.
        2. Transcripción ultrarrápida con Whisper.
        3. Entrega de la orden transcrita como instrucción de teclado.
        4. Opcionalmente ejecuta un callback (ej: procesar_y_responder).
        """
        texto = self.escuchar_y_transcribir(timeout=timeout, phrase_time_limit=phrase_time_limit)
        if texto:
            print(f"[Oídos]: Entregando como orden de teclado -> '{texto}' (Enter={pulsar_enter})")
            self.entregar_como_teclado(texto, pulsar_enter=pulsar_enter)
            if callback and callable(callback):
                callback(texto)
        return texto


# Alias unificados para compatibilidad total
Oídos = Oidos
Timpano = Oidos
TimpanoWhisper = Oidos

# Registrar alias de módulo para soportar 'from modulos.oídos import Oidos'
sys.modules.setdefault("modulos.oídos", sys.modules[__name__])

__all__ = ["Oidos", "Oídos", "Timpano", "TimpanoWhisper"]


if __name__ == "__main__":
    print("\n=== Prueba de Módulo Oídos (Whisper Multilingüe) ===")
    oidos = Oidos()

    print("\nOpciones:")
    print("1. Hablar ahora y ver transcripción (español o inglés).")
    print("2. Hablar ahora y entregarlo como instrucción de teclado.")
    print("3. Salir.")

    opcion = input("\nSelecciona una opción [1/2/3]: ").strip()

    if opcion == "1":
        print("\nPresiona Enter para empezar a hablar...")
        input()
        orden = oidos.escuchar_y_transcribir()
        print(f"\nResultado final transcrito: '{orden}'")

    elif opcion == "2":
        print("\nEn 3 segundos el micrófono escuchará. Luego escribirá tu orden en pantalla...")
        time.sleep(2)
        orden = oidos.escuchar_transcribir_y_entregar(pulsar_enter=True)
        print(f"\nOrden entregada como teclado: '{orden}'")

    else:
        print("Saliendo de la prueba de Oídos.")
