"""
Backend base para el Screen Reader Engine.

Cada plataforma implementa este protocolo.
El engine llama a estos métodos sin saber qué backend está corriendo.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class ScreenReaderBackend(ABC):
    """Protocolo que todos los backends deben implementar."""

    @abstractmethod
    async def read_active_window(self) -> str:
        """Devuelve el contenido textual de la ventana activa."""

    @abstractmethod
    async def read_focused_element(self) -> str:
        """Devuelve el texto del elemento de UI que tiene el foco."""

    @abstractmethod
    async def navigate(self, direction: str) -> str:
        """
        Navega la UI.
        direction: "next" | "prev" | "up" | "down" | "tab" | "shift_tab"
        Devuelve el texto del nuevo elemento enfocado.
        """

    @abstractmethod
    async def click_element(self, description: str) -> bool:
        """
        Hace click en el elemento que mejor coincide con la descripción.
        Devuelve True si encontró y clickeó el elemento.
        """

    @abstractmethod
    async def type_text(self, text: str) -> None:
        """Escribe texto en el elemento activo."""

    @abstractmethod
    async def get_ui_tree(self) -> dict:
        """Devuelve el árbol de accesibilidad de la ventana activa."""

    @abstractmethod
    def is_available(self) -> bool:
        """Devuelve True si el backend puede funcionar en este sistema."""
