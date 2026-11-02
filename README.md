# J.A.R.V.I.S.

## Configuración

Edita `config.json` para cambiar las opciones agrupadas por sección:

- `configuracion.ollama`: host y modelo local.
- `configuracion.asistente`: personalidad y directrices del prompt.
- `configuracion.contexto_usuario`: información contextual del usuario que se incluye en el prompt para adaptar la ayuda; debes mantenerla separada de la identidad del asistente y evitar convertir esos datos en información personal propia.
- `configuracion.voz`: voz y velocidad de Edge TTS, además del idioma y activación de la voz local de Windows como respaldo.

Las variables `OLLAMA_HOST` y `OLLAMA_MODEL` del archivo `.env` tienen prioridad sobre los valores de Ollama en `config.json`.

## Voz

J.A.R.V.I.S. intenta usar primero Edge TTS. Si Edge rechaza la conexión (por ejemplo, con HTTP 403), usa gTTS en español latinoamericano (`idioma_gtts` y `region_gtts` en `config.json`). Si ambos servicios fallan, usa la voz local de Windows cuando `usar_respaldo_local` está habilitado. Edge TTS y gTTS requieren conexión a internet. Para instalar las dependencias:

```powershell
python -m pip install -r requirements.txt
```

Si Windows no tiene instalada una voz en español, el respaldo usa la voz predeterminada del sistema. Puedes instalar una voz española en la configuración de voz de Windows.
