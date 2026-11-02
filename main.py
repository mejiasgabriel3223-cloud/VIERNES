import threading
import time
import keyboard

# Importamos nuestros tres módulos anatómicos independientes
from modulos.cerebro import Cerebro
from modulos.oidos import Oidos
from modulos.boca import Boca


class ViernesSystem:
    def __init__(self):
        print("[Sistema]: Inicializando protocolos de VIERNES...")
        self.cerebro = Cerebro()
        self.oidos = Oidos()
        self.boca = Boca()
        self._bloqueo_despertar = threading.Lock()
        print("[Sistema]: Todos los subsistemas en línea.")

    def despertar(self):
        """Rutina que se ejecuta al presionar la combinación de teclas"""
        if not self._bloqueo_despertar.acquire(blocking=False):
            print("[Sistema]: Ya estoy atendiendo otra solicitud.")
            return

        try:
            print("\n[Escuchando...]")

            # 1. Capturamos tu voz y la convertimos a texto
            texto_usuario = self.oidos.grabar_y_transcribir()

            if texto_usuario:
                print(f"[Gabriel]: {texto_usuario}")

                # 2. El cerebro procesa el texto
                respuesta_ia = self.cerebro.generar_respuesta(texto_usuario)
                print(f"[VIERNES]: {respuesta_ia}")

                # 3. La boca sintetiza y reproduce la respuesta mediante Piper
                self.boca.hablar(respuesta_ia)

            print("\n[Sistema]: En espera. Presiona [Ctrl + Alt + J] para hablar.")
        finally:
            self._bloqueo_despertar.release()

    def iniciar_demonio(self):
        """Mantiene el sistema corriendo de forma silenciosa en segundo plano"""
        keyboard.add_hotkey("ctrl+alt+j", self.despertar)

        # Bucle pasivo que consume 0% de CPU
        while True:
            time.sleep(1)


# Alias para retrocompatibilidad
JarvisSystem = ViernesSystem


if __name__ == "__main__":
    viernes = ViernesSystem()
    print("\n----------------------------------------------------")
    print(" VIERNES oculta en segundo plano.")
    print(" Atajo activo: Presiona [Ctrl + Alt + J] para hablar.")
    print("----------------------------------------------------")

    # Lanzamos el proceso en un hilo secundario tipo Demonio
    hilo_escucha = threading.Thread(target=viernes.iniciar_demonio, daemon=True)
    hilo_escucha.start()

    # Mantiene la consola principal viva
    try:
        hilo_escucha.join()
    except KeyboardInterrupt:
        print("\n[Sistema]: Apagando VIERNES. Hasta luego, Jefe.")
