# AiderSavvy - Options panel view
import sublime


class OptionsPanel:
    """Renders the options/status panel (GitSavvy style)."""

    def __init__(self, window, context):
        self.window = window
        self.context = context

    def get_content(self):
        """Get the options panel content as string."""
        ctx = self.context
        lines = []

        # Header
        lines.append("  AIDER SAVVY - AI Pair Programming")
        lines.append("")

        # Status
        status = "RUNNING" if ctx.is_running else "READY"
        lines.append("  Status: [{0}]".format(status))
        lines.append("")

        # Session info
        lines.append("-" * 60)
        lines.append("  Session Configuration")
        lines.append("-" * 60)
        lines.append("")
        # Find current model display with alias
        current_model_display = ctx.model
        for alias_name, model_name in ctx.model_aliases:
            if model_name == ctx.model:
                current_model_display = "{0} → {1}".format(alias_name, model_name)
                break

        lines.append("  [m] Mode    : {0}".format(ctx.mode.upper()))
        lines.append("  [M] Model   : {0}".format(current_model_display))
        lines.append("  [R] Root    : {0}".format(ctx.project_root))
        lines.append("  [L] Multiline: {0}".format("ENABLED" if ctx.multiline_enabled else "disabled"))
        lines.append("")

        # API Keys
        lines.append("-" * 60)
        lines.append("  API Keys Detected")
        lines.append("-" * 60)
        for key in ctx.api_keys:
            lines.append("    - {0}".format(key))
        lines.append("")

        # Available Models
        lines.append("-" * 60)
        lines.append("  Available Models by Alias ({0})".format(len(ctx.model_aliases)))
        lines.append("-" * 60)
        for i, (alias_name, model_name) in enumerate(ctx.model_aliases, 1):
            if model_name == ctx.model:
                lines.append("    {0:2}. {1} → {2} [CURRENT]".format(i, alias_name, model_name))
            else:
                lines.append("    {0:2}. {1} → {2}".format(i, alias_name, model_name))
        lines.append("")
        lines.append("  Note: Use [/model MODEL_NAME] in terminal for specific models")
        lines.append("")

        # Quick actions
        lines.append("-" * 60)
        lines.append("  Quick Actions")
        lines.append("-" * 60)
        lines.append("")
        lines.append("  [t] Start/Focus Terminal    [T] Stop Terminal")
        lines.append("  [c] Send Message            [/] Send Command")
        lines.append("  [e] Edit .env               [g] Open Global Config")
        lines.append("  [l] Open Local Config       [S] Sync from existing session")
        lines.append("")
        lines.append("  [TAB] Next Tab    [SHIFT+TAB] Previous Tab")
        lines.append("  [1] Options  [2] Files  [3] Output")
        lines.append("  [q] Close All Panels")
        lines.append("")

        # Files summary
        lines.append("-" * 60)
        lines.append("  Files: {0} editable, {1} read-only".format(
            len(ctx.files), len(ctx.readonly_files)))
        lines.append("-" * 60)

        return "\n".join(lines)
