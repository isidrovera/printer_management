# server/app/services/driver_storage.py
import os
from pathlib import Path
from fastapi import HTTPException
from server.app.core.config import settings

class DriverStorage:
    def __init__(self):
        self.storage_path = settings.DRIVERS_STORAGE_PATH
        # Asegurarse de que el directorio exista
        os.makedirs(self.storage_path, exist_ok=True)

    def save_driver_file(self, filename: str, content: bytes) -> str:
        """
        Guarda un archivo de driver en la carpeta de almacenamiento
        y devuelve la ruta completa.
        """
        file_path = Path(self.storage_path) / filename

        if file_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"El archivo {filename} ya existe en el almacenamiento."
            )

        try:
            with open(file_path, "wb") as f:
                f.write(content)
            return str(file_path)
        except Exception as e:
            raise RuntimeError(f"Error al guardar el archivo: {e}")

    def validate_driver_file(self, filename: str) -> str:
        """
        Verifica que un archivo de driver exista en la carpeta de almacenamiento
        y devuelve su ruta completa.
        """
        file_path = Path(self.storage_path) / filename
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Archivo de driver no encontrado: {filename}"
            )
        return str(file_path)

    def delete_driver_file(self, filename: str) -> bool:
        """
        Elimina el archivo de driver del almacenamiento si existe.
        """
        file_path = Path(self.storage_path) / filename
        if file_path.exists():
            os.remove(file_path)
            return True
        return False
