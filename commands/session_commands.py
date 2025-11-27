# AiderSavvy - Session management commands
import sublime
import sublime_plugin
import os

from .dashboard import get_aider_instance


class AiderSavvyStartTerminalCommand(sublime_plugin.WindowCommand):
    """Start or focus the Aider terminal."""

    def run(self):
        instance = get_aider_instance(self.window)

        if instance.terminal.is_running():
            instance.terminal.focus()
        else:
            instance.terminal.start()
            instance.context.is_running = True
            instance.refresh_options()


class AiderSavvyStopTerminalCommand(sublime_plugin.WindowCommand):
    """Stop the Aider terminal."""

    def run(self):
        instance = get_aider_instance(self.window)
        instance.terminal.stop()
        instance.context.is_running = False
        instance.refresh_options()
        sublime.status_message("Aider terminal stopped")


class AiderSavvySendMessageCommand(sublime_plugin.WindowCommand):
    """Send a message/prompt to Aider."""

    def run(self):
        self.window.show_input_panel(
            "Message to Aider:",
            "",
            self.on_done,
            None,
            None
        )

    def on_done(self, text):
        if not text.strip():
            return

        instance = get_aider_instance(self.window)

        if not instance.terminal.is_running():
            # Start terminal first
            instance.terminal.start()
            # Wait a bit then send message
            sublime.set_timeout(lambda: instance.terminal.send_message(text), 1000)
        else:
            instance.terminal.send_message(text)


class AiderSavvySendCommandCommand(sublime_plugin.WindowCommand):
    """Send an Aider slash command."""

    def run(self):
        self.window.show_input_panel(
            "Aider command (e.g., /help, /tokens, /map):",
            "/",
            self.on_done,
            None,
            None
        )

    def on_done(self, text):
        if not text.strip():
            return

        instance = get_aider_instance(self.window)

        if not instance.terminal.is_running():
            sublime.status_message("Start terminal first with [t]")
            return

        instance.terminal.send_command(text)


class AiderSavvyChangeModeCommand(sublime_plugin.WindowCommand):
    """Change the Aider mode."""

    def run(self):
        modes = ["code", "ask", "architect"]
        self.window.show_quick_panel(modes, self.on_done)

    def on_done(self, index):
        if index >= 0:
            modes = ["code", "ask", "architect"]
            instance = get_aider_instance(self.window)
            instance.context.set_mode(modes[index])
            sublime.status_message("Mode: {0}".format(modes[index]))
            instance.refresh_options()

            # If terminal running, need to restart with new mode
            if instance.terminal.is_running():
                sublime.message_dialog(
                    "Mode changed to {0}.\n"
                    "Restart terminal [T] then [t] to apply.".format(modes[index])
                )


class AiderSavvyChangeModelCommand(sublime_plugin.WindowCommand):
    """Change the AI model."""

    def run(self):
        models = [
            "gpt-4o",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "claude-3-sonnet",
            "claude-3-haiku",
            "deepseek/deepseek-coder",
            "deepseek/deepseek-chat",
        ]
        self.window.show_quick_panel(models, self.on_done)

    def on_done(self, index):
        if index >= 0:
            models = [
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
                "claude-3-opus",
                "claude-3-sonnet",
                "claude-3-haiku",
                "deepseek/deepseek-coder",
                "deepseek/deepseek-chat",
            ]
            instance = get_aider_instance(self.window)
            instance.context.set_model(models[index])
            sublime.status_message("Model: {0}".format(models[index]))
            instance.refresh_options()


class AiderSavvyChangeRootCommand(sublime_plugin.WindowCommand):
    """Change the project root directory."""

    def run(self):
        folders = self.window.folders()
        if not folders:
            sublime.status_message("No folders in project")
            return

        self.window.show_quick_panel(folders, self.on_done)

    def on_done(self, index):
        if index >= 0:
            folders = self.window.folders()
            instance = get_aider_instance(self.window)
            instance.context.project_root = folders[index]
            instance.context.api_keys = instance.context._detect_api_keys()
            sublime.status_message("Root: {0}".format(folders[index]))
            instance.refresh_options()


class AiderSavvyOpenEnvCommand(sublime_plugin.WindowCommand):
    """Open the .env file."""

    def run(self):
        instance = get_aider_instance(self.window)
        env_path = os.path.join(instance.context.project_root, ".env")
        self.window.open_file(env_path)


class AiderSavvyOpenGlobalConfigCommand(sublime_plugin.WindowCommand):
    """Open the global Aider config file."""

    def run(self):
        config_path = os.path.expanduser("~/.aider.conf.yml")
        self.window.open_file(config_path)


class AiderSavvyClearOutputCommand(sublime_plugin.WindowCommand):
    """Clear the output panel."""

    def run(self):
        instance = get_aider_instance(self.window)
        instance.output_panel.clear()
        sublime.status_message("Output cleared")


class AiderSavvySyncSessionCommand(sublime_plugin.WindowCommand):
    """Sync files from existing Aider session."""

    def run(self):
        instance = get_aider_instance(self.window)
        if instance.context.sync_from_existing_session():
            sublime.status_message("Synced files from existing Aider session")
            instance.refresh_files()
        else:
            sublime.status_message("No existing Aider session found")


class AiderSavvyRefreshOutputCommand(sublime_plugin.WindowCommand):
    """Refresh output from history file."""

    def run(self):
        instance = get_aider_instance(self.window)
        content = instance.file_watcher.get_full_history()
        instance.output_panel.set_content(content)
        sublime.status_message("Output refreshed from history file")
