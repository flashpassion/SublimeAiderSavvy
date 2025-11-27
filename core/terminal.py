# AiderSavvy - Terminus terminal integration
import sublime


class AiderTerminal:
    """Manages the Aider terminal via Terminus plugin."""

    def __init__(self, window, context):
        self.window = window
        self.context = context
        self.tag = "aider_savvy"
        self.terminal_view = None

    def start(self):
        """Start Aider in a Terminus terminal panel."""
        cmd = self._build_command()

        # Close existing terminal if any
        self.stop()

        try:
            # Open Terminus as a PANEL (like Output: SFTP)
            self.window.run_command("terminus_open", {
                "cmd": ["/bin/bash", "-c", cmd],
                "cwd": self.context.project_root,
                "title": "Aider",
                "tag": self.tag,
                "auto_close": False,
                "panel_name": "Aider",  # Crée un panel "Output: Aider"
            })

            self.context.is_running = True

            # Focus the panel after a short delay
            sublime.set_timeout(self._focus_panel, 100)
        except Exception as e:
            sublime.error_message("Failed to start Aider terminal: {0}".format(e))
            self.context.is_running = False

    def _focus_panel(self):
        """Focus the Aider terminal panel."""
        self.window.run_command("show_panel", {"panel": "output.Aider"})

    def _build_command(self):
        """Build the aider command with all options."""
        parts = ["aider"]

        # Add files
        for f in self.context.files:
            parts.append("--file")
            parts.append('"{0}"'.format(f))

        # Add read-only files
        for f in self.context.readonly_files:
            parts.append("--read")
            parts.append('"{0}"'.format(f))

        # Mode
        if self.context.mode == 'ask':
            parts.append("--ask")
        elif self.context.mode == 'architect':
            parts.append("--architect")

        # Model (if not default)
        if self.context.model and self.context.model != 'gpt-4o':
            parts.append("--model")
            parts.append(self.context.model)

        return " ".join(parts)

    def send_command(self, text):
        """Send a command/text to the running Aider terminal."""
        self.window.run_command("terminus_send_string", {
            "string": text + "\n",
            "tag": self.tag
        })

    def send_message(self, message):
        """Send a chat message to Aider."""
        self.send_command(message)

    def send_aider_command(self, command):
        """Send an Aider slash command (e.g., /add, /drop)."""
        if not command.startswith("/"):
            command = "/" + command
        self.send_command(command)

    def stop(self):
        """Stop the Aider terminal."""
        # Close the terminus panel
        self.window.run_command("terminus_close", {"tag": self.tag})
        self.window.run_command("hide_panel", {"panel": "output.Aider"})
        self.terminal_view = None
        self.context.is_running = False

    def is_running(self):
        """Check if terminal is active."""
        # Check if terminus with our tag exists
        try:
            for view in self.window.views():
                if view.settings().get("terminus_view.tag") == self.tag:
                    return True
            # Also check panels
            return self.window.find_output_panel("Aider") is not None
        except Exception:
            return False

    def focus(self):
        """Focus the Aider terminal panel."""
        self.window.run_command("show_panel", {"panel": "output.Aider"})
        return True
