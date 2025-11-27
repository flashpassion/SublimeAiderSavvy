# AiderSavvy - Output panel view
import sublime


class OutputPanel:
    """Renders the live output panel."""

    def __init__(self, window, context):
        self.window = window
        self.context = context
        self.content_lines = []
        self.max_lines = 5000

    def append_content(self, new_content):
        """Append new content to the output."""
        if not new_content:
            return

        new_lines = new_content.split('\n')
        self.content_lines.extend(new_lines)

        # Trim if too long
        if len(self.content_lines) > self.max_lines:
            self.content_lines = self.content_lines[-self.max_lines:]

    def set_content(self, content):
        """Set the entire content."""
        self.content_lines = content.split('\n') if content else []

    def clear(self):
        """Clear the output."""
        self.content_lines = []

    def get_content(self):
        """Get the output panel content as string."""
        lines = []

        lines.append("  AIDER OUTPUT (Live from .aider.chat.history.md)")
        lines.append("")
        lines.append("  [C] Clear output    [O] Refresh from file")
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

        if self.content_lines:
            lines.extend(self.content_lines)
        else:
            lines.append("  (No output yet. Start terminal with [t] and send a message.)")

        return "\n".join(lines)
