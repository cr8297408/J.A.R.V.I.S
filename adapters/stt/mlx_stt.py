import mlx_whisper


class LocalSTT:
    # Cambiamos a 'mlx-community/whisper-small-mlx' o 'mlx-community/whisper-large-v3-turbo'
    # El 'small' es el punto dulce entre velocidad absoluta y precisión perfecta en español.
    def __init__(self, model_name="mlx-community/whisper-large-v3-turbo"):
        """
        Adaptador STT que utiliza el framework MLX de Apple para correr Whisper localmente en GPU.
        """
        self.model_name = model_name

    def transcribe(self, audio_file_path: str) -> str:
        """
        Toma una ruta de archivo de audio (.wav) y devuelve la transcripción en texto.
        """
        try:
            # Palabras sueltas para sesgar el vocabulario hacia jerga técnica.
            # IMPORTANTE: sin oraciones completas — Whisper las alucina cuando hay silencio.
            tech_vocab = "Jarvis, Safari, Chrome, terminal, Python, Git, PR, branch, commit, archivo, carpeta, código, API"

            result = mlx_whisper.transcribe(
                audio_file_path,
                path_or_hf_repo=self.model_name,
                language="es",
                temperature=(0.0, 0.2, 0.4),
                initial_prompt=tech_vocab,
            )

            # Si todos los segments tienen no_speech_prob alto → era silencio/ruido, no voz real.
            segments = result.get("segments", [])
            if segments:
                avg_no_speech = sum(s.get("no_speech_prob", 0) for s in segments) / len(segments)
                if avg_no_speech > 0.6:
                    return ""

            text = result.get("text", "")
            if isinstance(text, list):
                text = "".join(text)
            return text.strip()
        except Exception as e:
            print(f"[STT Error] {e}")
            return ""
