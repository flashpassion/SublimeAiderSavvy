# AiderSavvy - AI Pair Programming for Sublime Text
# Main plugin entry point

import sublime
import sublime_plugin

# Import all commands from submodules
from .commands.dashboard import (
    AiderSavvyCommand,
    AiderSavvyRefreshCommand,
    AiderSavvyCloseCommand,
    AiderSavvyNextTabCommand,
    AiderSavvyPrevTabCommand,
    AiderSavvyGoToTabCommand,
    get_aider_instance
)
from .commands.file_commands import (
    AiderSavvyAddFileCommand,
    AiderSavvyAddCurrentFileCommand,
    AiderSavvyDropFileCommand,
    AiderSavvyReadOnlyFileCommand,
    AiderSavvyScanFilesCommand
)
from .commands.session_commands import (
    AiderSavvyStartTerminalCommand,
    AiderSavvyStopTerminalCommand,
    AiderSavvySendMessageCommand,
    AiderSavvySendCommandCommand,
    AiderSavvyChangeModeCommand,
    AiderSavvyChangeModelCommand,
    AiderSavvyChangeRootCommand,
    AiderSavvyOpenEnvCommand,
    AiderSavvyOpenGlobalConfigCommand,
    AiderSavvyClearOutputCommand,
    AiderSavvyRefreshOutputCommand
)


def plugin_loaded():
    """Called when the plugin is loaded."""
    print("AiderSavvy: Plugin loaded successfully.")


def plugin_unloaded():
    """Called when the plugin is unloaded."""
    # Clean up any running instances
    for window in sublime.windows():
        if hasattr(window, 'aider_savvy'):
            try:
                window.aider_savvy.close_all()
            except Exception:
                pass
    print("AiderSavvy: Plugin unloaded.")


class AiderSavvyEventListener(sublime_plugin.EventListener):
    """Event listener for Aider views."""

    def on_query_context(self, view, key, operator, operand, match_all):
        """Handle context queries for key bindings."""
        if key == "aider_savvy_view":
            is_aider = view.settings().get("aider_savvy_view", False)
            if operator == sublime.OP_EQUAL:
                return is_aider == operand
            elif operator == sublime.OP_NOT_EQUAL:
                return is_aider != operand
        return None

    def on_close(self, view):
        """Handle view close events."""
        # If an Aider view is closed, refresh the instance
        if view.settings().get("aider_savvy_view"):
            window = view.window()
            if window and hasattr(window, 'aider_savvy'):
                # Don't refresh if we're closing all
                pass
