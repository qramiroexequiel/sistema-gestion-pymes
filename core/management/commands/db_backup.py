"""
Comando de gestión para copia de seguridad de la base de datos SQLite.

Uso:
    python manage.py db_backup

Realiza:
    - Copia del archivo de base de datos actual (ej. db.sqlite3).
    - Guarda en backups/ en la raíz del proyecto.
    - Nombre: backup_YYYYMMDD_HHMMSS.sqlite3.gz (comprimido con gzip).
    - Elimina backups con más de 7 días (rotación).
    - Mensajes de éxito o error aptos para logs.
"""

import gzip
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Copia de seguridad de la base de datos SQLite en backups/ con compresión gzip y rotación de 7 días."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Eliminar backups con más de N días (default: 7).",
        )

    def handle(self, *args, **options):
        retention_days = options["days"]
        db = settings.DATABASES.get("default", {})
        engine = db.get("ENGINE", "")
        name = db.get("NAME")

        if "sqlite3" not in engine:
            msg = (
                "db_backup solo soporta SQLite. "
                "Base de datos actual: {}.".format(engine)
            )
            logger.warning(msg)
            self.stderr.write(self.style.ERROR(msg))
            return

        path = Path(name)
        if not path.is_file():
            msg = "No se encontró el archivo de base de datos: {}.".format(path)
            logger.error(msg)
            self.stderr.write(self.style.ERROR(msg))
            return

        base_dir = Path(settings.BASE_DIR)
        backups_dir = base_dir / "backups"
        try:
            backups_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            msg = "No se pudo crear la carpeta backups/: {}.".format(e)
            logger.exception(msg)
            self.stderr.write(self.style.ERROR(msg))
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = "backup_{}.sqlite3.gz".format(timestamp)
        backup_path = backups_dir / backup_name

        try:
            with open(path, "rb") as f_in:
                with gzip.open(backup_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except OSError as e:
            msg = "Error al crear la copia de seguridad: {}.".format(e)
            logger.exception(msg)
            self.stderr.write(self.style.ERROR(msg))
            return

        size_mb = backup_path.stat().st_size / (1024 * 1024)
        msg = "Copia de seguridad creada: {} ({:.2f} MB).".format(backup_path.name, size_mb)
        logger.info(msg)
        self.stdout.write(self.style.SUCCESS(msg))

        deleted = self._rotate_old_backups(backups_dir, retention_days)
        if deleted:
            for p in deleted:
                logger.info("Backup eliminado (rotación): {}.".format(p.name))
            self.stdout.write(
                self.style.WARNING("Rotación: {} archivo(s) eliminado(s).".format(len(deleted)))
            )
        else:
            self.stdout.write("Rotación: sin archivos que eliminar.")

    def _rotate_old_backups(self, backups_dir, days):
        """Elimina archivos backup_*.sqlite3.gz con más de `days` días. Retorna lista de Path eliminados."""
        cutoff = datetime.now() - timedelta(days=days)
        deleted = []
        for path in backups_dir.glob("backup_*.sqlite3.gz"):
            if not path.is_file():
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if mtime < cutoff:
                try:
                    path.unlink()
                    deleted.append(path)
                except OSError as e:
                    logger.warning("No se pudo eliminar {}: {}.".format(path.name, e))
        return deleted
