"""KivyMD Application class for Leadership OS.

This module will be expanded in Phase 3 to include the full UI.
For now, it serves as a placeholder entry point.
"""

from __future__ import annotations

import logging
import sys

from leadership_os.utils.path_utils import get_app_data_dir, ensure_directory, get_log_path


def setup_logging() -> None:
    """Configure logging for the application."""
    log_path = get_log_path()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    """Main entry point for Leadership OS."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Leadership OS starting...")

    # Ensure app data directory exists
    app_dir = get_app_data_dir()
    ensure_directory(app_dir)
    logger.info("App data directory: %s", app_dir)

    try:
        # Phase 3+ will initialize the KivyMD app here
        # For now, just verify the data layer works
        from leadership_os.core.database import Database
        from leadership_os.config.config_manager import ConfigManager
        from leadership_os.core.state_manager import StateManager

        # Initialize database
        db = Database(app_dir / "leadership_os.db")
        db.initialize()
        logger.info("Database initialized")

        # Initialize config
        config = ConfigManager(app_dir / "config.toml")
        config.load()
        logger.info("Configuration loaded")

        # Initialize state
        state = StateManager(app_dir / "state.json")
        state.load()
        logger.info("State loaded")

        # Get or create today
        day = db.get_or_create_today()
        logger.info("Today: %s (status: %s)", day.date, day.status)

        db.close()
        logger.info("Leadership OS data layer verified successfully")

        print("\n✅ Leadership OS — Data layer initialized successfully!")
        print(f"   Database: {app_dir / 'leadership_os.db'}")
        print(f"   Config:   {app_dir / 'config.toml'}")
        print(f"   State:    {app_dir / 'state.json'}")
        print(f"   Today:    {day.date}")

    except Exception as e:
        logger.error("Failed to initialize: %s", e, exc_info=True)
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
