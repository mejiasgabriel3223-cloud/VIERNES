import os
import subprocess
import pygame


class Boca:
    def __init__(self):
        # Inicializamos el mixer de audio de Pygame para reproducir el wav
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        # Rutas dinámicas basadas en la ubicación del proyecto
        self.ruta_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Integración de la carpeta cuerdasvocales
        self.ejecutable = os.path.join(self.ruta_base, "cuerdasvocales", "piper.exe")
        if not os.path.exists(self.ejecutable):
            ruta_alt_piper = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cuerdasvocales", "piper.exe")
            if os.path.exists(ruta_alt_piper):
                self.ejecutable = ruta_alt_piper

        # Modelo de voz
        self.modelo_voz = os.path.join(self.ruta_base, "voces", "viernes.onnx")
        if not os.path.exists(self.modelo_voz):
            ruta_alt_modelo = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voces", "viernes.onnx")
            if os.path.exists(ruta_alt_modelo):
                self.modelo_voz = ruta_alt_modelo

        # Archivo de salida temporal en la raíz del proyecto
        self.archivo_salida = os.path.join(self.ruta_base, "respuesta_temporal.wav")

    def hablar(self, texto):
        if not texto:
            return

        print("[SISTEMA] VIERNES procesando audio...")

        if not os.path.exists(self.ejecutable):
            print(f"[ERROR] No se encontró el ejecutable de Piper en: {self.ejecutable}")
            return

        if not os.path.exists(self.modelo_voz):
            print(f"[ERROR] No se encontró el modelo de voz en: {self.modelo_voz}")
            return

        # Usamos subprocess para enviarle el texto a Piper de forma segura
        subprocess.run(
            [self.ejecutable, "--model", self.modelo_voz, "--output_file", self.archivo_salida],
            input=texto.encode("utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Reproducir el audio generado
        if os.path.exists(self.archivo_salida):
            pygame.mixer.music.load(self.archivo_salida)
            pygame.mixer.music.play()

            # Detener el código mientras habla
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)

            # Descargar de la memoria y borrar el archivo temporal
            pygame.mixer.music.unload()
            try:
                os.remove(self.archivo_salida)
            except OSError:
                pass


# Código de prueba
if __name__ == "__main__":
    boca_viernes = Boca()
    boca_viernes.hablar("Permiso denegado, Jefe. Esa acción viola mis protocolos de seguridad de entorno.")
