import pywhatkit
import webbrowser
import time
import pyautogui
import os

class Acciones:
    def __init__(self):
        print("[Sistema]: Módulo de acciones externas (Manoderecha) inicializado.")

    def ejecutar_accion(self, accion: str, parametro: str):
        """
        Recibe la acción exacta ('youtube' o 'spotify') y el parámetro limpio 
        desde el Cerebro y ejecuta la automatización correspondiente.
        """
        accion = accion.lower().strip()
        
        if accion == "youtube":
            return self.reproducir_youtube(parametro)
        elif accion == "spotify":
            return self.reproducir_spotify(parametro)
        else:
            return None

    def reproducir_youtube(self, busqueda: str):
        """Reproduce un video en YouTube y fuerza la ventana al frente."""
        try:
            print(f"[Acciones]: Reproduciendo en YouTube -> {busqueda}")
            
            # Abre el navegador y reproduce el video
            pywhatkit.playonyt(busqueda)
            
            # Le damos 2 segundos para que el navegador arranque y cargue
            time.sleep(2.0)
            
            # Forzamos el cambio de ventana (de la terminal al navegador)
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.5)
            
            # Maximizamos la ventana del navegador
            pyautogui.hotkey('win', 'up')
            
            return f"Reproduciendo {busqueda} en YouTube, jefe."
        except Exception as e:
            print(f"[Error YouTube]: {e}")
            return "Lo siento jefe, ocurrió un error al intentar reproducir en YouTube."

    def reproducir_spotify(self, query: str):
        """Busca y reproduce en Spotify usando Visión Computacional (Template Matching)."""
        try:
            print(f"[Acciones]: Abriendo Spotify para -> {query}")
            
            uri = f"spotify:search:{query.replace(' ', '%20')}"
            webbrowser.open(uri)
            
            # 5 segundos para que la interfaz cargue bien y salte al frente
            time.sleep(7.0)
            
            # Aseguramos el nombre exacto con mayúsculas como en tu explorador
            ruta_imagen = os.path.join(os.path.dirname(__file__), "play_spotify.PNG")
            
            if not os.path.exists(ruta_imagen):
                print("[Error]: Falta el archivo 'play_spotify.PNG' en la carpeta modulos.")
                return "Me falta la imagen de referencia para hacer clic, jefe."

            print("[Acciones]: Escaneando pantalla en busca del objetivo...")
            try:
                # Bajamos la exigencia (confidence) al 70% por si hay cambios de luz o color
                x, y = pyautogui.locateCenterOnScreen(ruta_imagen, confidence=0.7)
                
                pyautogui.moveTo(x, y, duration=0.2)
                pyautogui.click()
                
                ancho, alto = pyautogui.size()
                pyautogui.moveTo(ancho - 50, alto // 2)
                
                return f"Reproduciendo {query} en Spotify, jefe."
                
            except pyautogui.ImageNotFoundException:
                print("[Error Spotify]: Objetivo visual no detectado en pantalla.")
                return "No encontré el botón de reproducir en la pantalla, jefe."
                
        except Exception as e:
            print(f"[Error Spotify]: {e}")
            return "No pude automatizar Spotify en este momento, jefe."