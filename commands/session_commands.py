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
    """Change the AI model from available aliases."""

    def run(self):
        instance = get_aider_instance(self.window)
        model_aliases = instance.context.model_aliases
        
        if not model_aliases:
            sublime.status_message("No model aliases found in config files")
            return
        
        # Create display list with alias → model format
        display_list = []
        for alias_name, model_name in model_aliases:
            if model_name == instance.context.model:
                display_list.append("{0} → {1} [CURRENT]".format(alias_name, model_name))
            else:
                display_list.append("{0} → {1}".format(alias_name, model_name))
            
        self.model_aliases = model_aliases
        self.window.show_quick_panel(display_list, self.on_done)

    def on_done(self, index):
        if index >= 0:
            instance = get_aider_instance(self.window)
            selected_alias_name, selected_model = self.model_aliases[index]
            
            instance.context.set_model(selected_model)
            sublime.status_message("Model: {0} → {1}".format(selected_alias_name, selected_model))
            instance.refresh_options()
            
            # If terminal running, suggest restart
            if instance.terminal.is_running():
                sublime.message_dialog(
                    "Model changed to {0} → {1}.\n"
                    "Restart terminal [T] then [t] to apply.".format(selected_alias_name, selected_model)
                )


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


class AiderSavvyOpenLocalConfigCommand(sublime_plugin.WindowCommand):
    """Open the local .aider.conf.yml file."""

    def run(self):
        instance = get_aider_instance(self.window)
        config_path = os.path.join(instance.context.project_root, ".aider.conf.yml")
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


class AiderSavvySendMultilineCommand(sublime_plugin.WindowCommand):
    """Send a multiline message to Aider (opens in new buffer)."""

    def run(self):
        # Create a temporary buffer for multiline input
        view = self.window.new_file()
        view.set_name("Aider - Multiline Message")
        view.set_scratch(True)
        view.settings().set("aider_multiline_input", True)
        
        # Set syntax if available
        try:
            view.assign_syntax("Packages/Text/Plain text.tmLanguage")
        except:
            pass
        
        # Add an on_close event listener
        view.settings().set("on_close_callback", lambda: self.on_done(view))

    def on_done(self, view):
        """Called when the multiline buffer is saved/closed."""
        content = view.substr(sublime.Region(0, view.size()))
        if content.strip():
            instance = get_aider_instance(self.window)
            if instance.terminal.is_running():
                instance.terminal.send_message(content)
                sublime.status_message("Multiline message sent to Aider")
            else:
                sublime.status_message("Start terminal first with [t]")
        
        # Close the temporary buffer
        if view.is_valid():
            view.close()


class AiderSavvyRefreshOutputCommand(sublime_plugin.WindowCommand):
    """Refresh output from history file."""

    def run(self):
        instance = get_aider_instance(self.window)
        content = instance.file_watcher.get_full_history()
        instance.output_panel.set_content(content)
        sublime.status_message("Output refreshed from history file")
