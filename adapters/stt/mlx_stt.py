import mlx_whisper


class LocalSTT:
    # Cambiamos a 'mlx-community/whisper-small-mlx' o 'mlx-community/whisper-large-v3-turbo'
    # El 'small' es el punto dulce entre velocidad absoluta y precisión perfecta en español.
    def __init__(self, model_name="mlx-community/whisper-small-mlx"):
        """
        Adaptador STT que utiliza el framework MLX de Apple para correr Whisper localmente en GPU.
        """
        self.model_name = model_name

    def transcribe(self, audio_file_path: str) -> str:
        """
        Toma una ruta de archivo de audio (.wav) y devuelve la transcripción en texto.
        """
        try:
            # transcribe devuelve un diccionario con la clave 'text'
            # El 'initial_prompt' le da al modelo un vocabulario "falso" previo.
            # Al leer este prompt, el modelo predispone su red neuronal para esperar
            # jerga de ingeniería de software, código, y comandos de Git/CLI.
            tech_prompt = (
                "Comandos de programación en terminal. "
                "Palabras clave: PR, Pull Request, issue, bug, branch, commit, "
                "merge, rebase, push, pull, fetch, clone, repo, proyecto, "
                "Python, JavaScript, React, Node, API, backend, frontend, "
                "script, archivo, carpeta, directorio, código, refactor, "
                "ticket, sprint, Jira, GitHub, GitLab, Gemini, CLI, Jarvis. "
                "¿Cuántos PRs abiertos tiene el proyecto? "
                "Creame un nuevo issue para este bug."
            )

            result = mlx_whisper.transcribe(
                audio_file_path,
                path_or_hf_repo=self.model_name,
                language="es",
                # Opciones para reducir alucinaciones
                temperature=(0.0, 0.2, 0.4),
                initial_prompt=tech_prompt,
            )
            text = result.get("text", "")
            if isinstance(text, list):
                text = "".join(text)
            return text.strip()
        except Exception as e:
            print(f"[STT Error] {e}")
            return ""
