import sys
from loguru import logger

# Remove default handler to prevent duplicate outputs if app is reloaded
# or if loguru was already used with its default stderr handler.
try:
    logger.remove(0)  # Try to remove the default handler (ID 0)
except ValueError:
    pass  # No handler with ID 0, or no handlers configured yet, which is fine.

# Define custom log levels
# Using uppercase for level names (THOUGHT, ACTION) is a common convention.
logger.level("THOUGHT", no=35, color="<red>")
logger.level("ACTION", no=25, color="<blue>")

# Define the functions that will be assigned as attributes to the logger.
# These functions use the global `logger` object from loguru.
def thought(message, *args, **kwargs):
    logger.log("THOUGHT", message, *args, **kwargs)

def action(message, *args, **kwargs):
    logger.log("ACTION", message, *args, **kwargs)

# Add a new handler with the user's specified format.
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>"
    # The <level> tag itself will be replaced by the (colored) level name.
    # Example: For a THOUGHT message, <level> becomes <red>THOUGHT</red> (or similar, with padding)
    # So the full message might look like: <green>HH:mm:ss</green> | <red>THOUGHT</red> The actual thought message.
)

# Attach the custom functions as attributes to the global logger instance.
# This makes `logger.thought(...)` and `logger.action(...)` available.
logger.thought = thought
logger.action = action

# Clean up to avoid polluting the module's namespace if someone were to use `from .logging_config import *`
del thought
del action
