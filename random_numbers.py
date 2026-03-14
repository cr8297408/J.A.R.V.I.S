import random

class GeneradorPorcentajes:
    """Clase para generar porcentajes basados en una entrada."""

    def calcular(self, entrada: str) -> int:
        """Genera un porcentaje determinista basado en la entrada."""
        random.seed(entrada)
        return random.randint(0, 100)

    def iniciar_interaccion(self):
        """Inicia el bucle de interacción con el usuario."""
        print("--- Generador de Porcentajes (Clase) ---")
        print("Escribe algo para obtener un valor (o 'salir' para terminar):")
        
        while True:
            try:
                entrada = input("Input: ")
                if entrada.lower() in ['salir', 'exit', 'quit', 'q']:
                    print("¡Adiós!")
                    break
                
                if not entrada:
                    continue
                    
                porcentaje = self.calcular(entrada)
                print(f"Resultado para '{entrada}': {porcentaje}%")
                
            except (EOFError, KeyboardInterrupt):
                print("\nFinalizando...")
                break

if __name__ == "__main__":
    generador = GeneradorPorcentajes()
    generador.iniciar_interaccion()
