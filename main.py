import threading
import time
import keyboard
import os

from modulos.cerebro import Cerebro
from modulos.oidos import Oidos
from modulos.boca import Boca
from modulos.Manoderecha import Acciones  


class ViernesSystem:
    def __init__(self):
        print("[Sistema]: Inicializando protocolos de VIERNES...")
        self.cerebro = Cerebro()
        self.oidos = Oidos()  # Módulo único de procesamiento de voz (Whisper - Español/Inglés)
        self.timpano = self.oidos  # Preservado por compatibilidad
        self.boca = Boca()
        self.acciones = Acciones() 
        self._bloqueo_sistema = threading.Lock()
        print("[Sistema]: Todos los subsistemas en línea y optimizados.")

    def procesar_y_responder(self, texto_usuario: str):
        """Núcleo central: enruta las intenciones con IA o pasa al chat normal."""
        if not texto_usuario:
            return

        print(f"[Procesando]: {texto_usuario}")

        # 1. El Cerebro analiza la intención y extrae el JSON limpio
        intencion = self.cerebro.analizar_intencion(texto_usuario)
        accion = intencion.get("accion", "ninguna").lower()
        parametro = intencion.get("parametro", texto_usuario)

        print(f"[Router IA]: Acción -> {accion} | Parámetro -> {parametro}")

        # 2. Si el Cerebro detecta YouTube o Spotify, disparamos Manoderecha
        if accion in ["youtube", "spotify"]:
            respuesta_accion = self.acciones.ejecutar_accion(accion, parametro)
            print(f"[VIERNES]: {respuesta_accion}")
            self.boca.hablar(respuesta_accion)
        else:
            # 3. Si no es multimedia (accion == "ninguna"), pasa al cerebro de charla normal
            respuesta_ia = self.cerebro.generar_respuesta(texto_usuario)
            print(f"[VIERNES]: {respuesta_ia}")
            self.boca.hablar(respuesta_ia)

    def escuchar_voz(self):
        """Activado por [Ctrl + Alt + J] (Micrófono con Whisper -> Instrucción de teclado -> Router)."""
        if not self._bloqueo_sistema.acquire(blocking=False):
            print("[Sistema]: El sistema ya está ocupado atendiendo una solicitud.")
            return

        try:
            print("\n[Oídos]: Escuchando orden por micrófono (Whisper)...")
            texto_usuario = self.oidos.escuchar_y_transcribir()
            if texto_usuario:
                print(f"[(Voz con Whisper)]: {texto_usuario}")
                # Entrega de la orden como instrucción de teclado al sistema
                print("[Oídos]: Entregando orden como instrucción de teclado...")
                self.oidos.entregar_como_teclado(texto_usuario, pulsar_enter=False)
                self.procesar_y_responder(texto_usuario)
        finally:
            self._bloqueo_sistema.release()
            print("\n[Sistema]: En espera. [Ctrl + Alt + J] Comandos por voz (Whisper) | [Ctrl + Alt + K] Comandos por texto.")

    def activar_texto(self):
        """Activado por [Ctrl + Alt + K] (Escribir en consola)."""
        if not self._bloqueo_sistema.acquire(blocking=False):
            print("[Sistema]: El sistema ya está ocupado atendiendo una solicitud.")
            return

        try:
            print("\n--------------------------------------------------")
            texto_usuario = input("[(Escribe tu orden)]: ").strip()
            print("--------------------------------------------------")
            
            if texto_usuario.lower() in ["salir", "apagar", "exit"]:
                despedida = "Apagando sistemas, jefe. Hasta luego."
                print(f"[VIERNES]: {despedida}")
                self.boca.hablar(despedida)
                os._exit(0)

            if texto_usuario:
                self.procesar_y_responder(texto_usuario)
        finally:
            self._bloqueo_sistema.release()
            print("\n[Sistema]: En espera. [Ctrl + Alt + J] Comandos por voz (Whisper) | [Ctrl + Alt + K] Comandos por texto.")

    def iniciar_demonios(self):
        """Registra los atajos de teclado globales en segundo plano."""
        keyboard.add_hotkey("ctrl+alt+j", self.escuchar_voz)
        keyboard.add_hotkey("ctrl+alt+k", self.activar_texto)

        while True:
            time.sleep(1)


JarvisSystem = ViernesSystem


if __name__ == "__main__":
    viernes = ViernesSystem()
    print("\n----------------------------------------------------")
    print(" VIERNES Híbrida con Whisper (Auditivo Unificado) y Manoderecha.")
    print(" - [Ctrl + Alt + J] : Comandos por voz dictada (Whisper - Español/Inglés)")
    print(" - [Ctrl + Alt + K] : Comandos por texto mediante teclado")
    print("----------------------------------------------------")

    try:
        viernes.iniciar_demonios()
    except KeyboardInterrupt:
        print("\n[Sistema]: Apagando VIERNES. Hasta luego, Jefe.")