import sublime
import sublime_plugin
import subprocess
import os
import threading
import json
from datetime import datetime


class AiderSavvyCommand(sublime_plugin.WindowCommand):
    """Commande principale pour ouvrir le dashboard Aider"""

    def run(self):
        view = self.window.new_file()
        view.set_name("AIDER")
        view.settings().set("aider_savvy_dashboard", True)
        view.settings().set("aider_savvy_view", "status")
        view.set_scratch(True)
        view.set_read_only(True)
        view.settings().set("word_wrap", False)
        view.assign_syntax("Packages/AiderSavvy/AiderSavvy.sublime-syntax")

        # Initialiser le contexte Aider
        if not hasattr(self.window, 'aider_context'):
            self.window.aider_context = {
                'files': [],
                'readonly_files': [],
                'history': [],
                'output': [],
                'mode': 'code',
                'process': None
            }

        self.refresh_dashboard(view)

    def refresh_dashboard(self, view):
        """Rafraîchir l'affichage du dashboard"""
        current_view = view.settings().get("aider_savvy_view", "status")

        if current_view == "status":
            self.render_status(view)
        elif current_view == "files":
            self.render_files(view)
        elif current_view == "output":
            self.render_output(view)
        elif current_view == "commands":
            self.render_commands(view)

    def render_status(self, view):
        """Afficher l'écran de statut principal"""
        ctx = self.window.aider_context

        content = []
        content.append("=" * 80)
        content.append("  AIDER - AI Pair Programming")
        content.append("=" * 80)
        content.append("")
        content.append("  Mode: {}".format(ctx['mode'].upper()))
        content.append("  Files in chat: {}".format(len(ctx['files'])))
        content.append("  Read-only files: {}".format(len(ctx['readonly_files'])))
        content.append("")
        content.append("-" * 80)
        content.append("  Quick Actions:")
        content.append("-" * 80)
        content.append("")
        content.append("  a - Add files to chat")
        content.append("  r - Add read-only files")
        content.append("  d - Drop files from chat")
        content.append("  c - Send command/prompt")
        content.append("  o - Show output")
        content.append("  m - Change mode")
        content.append("  / - Run aider command")
        content.append("")
        content.append("  TAB - Cycle views (Status → Files → Output → Commands)")
        content.append("  q - Close dashboard")
        content.append("")

        if ctx['files']:
            content.append("-" * 80)
            content.append("  Files in Chat:")
            content.append("-" * 80)
            for f in ctx['files']:
                content.append("    • {}".format(f))
            content.append("")

        if ctx['output']:
            content.append("-" * 80)
            content.append("  Recent Output:")
            content.append("-" * 80)
            for line in ctx['output'][-5:]:
                content.append("    {}".format(line))
            content.append("")

        self._update_view_content(view, "\n".join(content))

    def render_files(self, view):
        """Afficher la liste des fichiers"""
        ctx = self.window.aider_context

        content = []
        content.append("=" * 80)
        content.append("  AIDER - Files Management")
        content.append("=" * 80)
        content.append("")
        content.append("  a - Add files    d - Drop files    r - Add read-only    TAB - Next view")
        content.append("")
        content.append("-" * 80)
        content.append("  Files in Chat (editable):")
        content.append("-" * 80)

        if ctx['files']:
            for i, f in enumerate(ctx['files'], 1):
                content.append("  {}. {}".format(i, f))
        else:
            content.append("    (no files)")

        content.append("")
        content.append("-" * 80)
        content.append("  Read-only Files:")
        content.append("-" * 80)

        if ctx['readonly_files']:
            for i, f in enumerate(ctx['readonly_files'], 1):
                content.append("  {}. {} [read-only]".format(i, f))
        else:
            content.append("    (no read-only files)")

        content.append("")

        self._update_view_content(view, "\n".join(content))

    def render_output(self, view):
        """Afficher l'output d'Aider"""
        ctx = self.window.aider_context

        content = []
        content.append("=" * 80)
        content.append("  AIDER - Output")
        content.append("=" * 80)
        content.append("")
        content.append("  c - Clear output    TAB - Next view")
        content.append("")
        content.append("-" * 80)

        if ctx['output']:
            content.extend(ctx['output'])
        else:
            content.append("  (no output yet)")

        content.append("")

        self._update_view_content(view, "\n".join(content))

    def render_commands(self, view):
        """Afficher la liste des commandes disponibles"""
        commands = [
            ("/add", "Add files to the chat"),
            ("/drop", "Remove files from the chat"),
            ("/read-only", "Add files as read-only"),
            ("/ask", "Ask questions without editing"),
            ("/code", "Ask for code changes"),
            ("/architect", "Use architect/editor mode"),
            ("/commit", "Commit edits to repo"),
            ("/diff", "Display diff of changes"),
            ("/undo", "Undo last git commit"),
            ("/map", "Print repository map"),
            ("/tokens", "Report token usage"),
            ("/clear", "Clear chat history"),
            ("/reset", "Drop all files and clear history"),
            ("/chat-mode", "Switch chat mode"),
            ("/model", "Switch Main Model"),
            ("/help", "Get help"),
        ]

        content = []
        content.append("=" * 80)
        content.append("  AIDER - Available Commands")
        content.append("=" * 80)
        content.append("")
        content.append("  / - Execute command    TAB - Next view")
        content.append("")
        content.append("-" * 80)

        for cmd, desc in commands:
            content.append("  {:20} - {}".format(cmd, desc))

        content.append("")
        content.append("  Press '/' to execute any command")
        content.append("")

        self._update_view_content(view, "\n".join(content))

    def _update_view_content(self, view, content):
        """Mettre à jour le contenu d'une vue"""
        view.set_read_only(False)
        view.run_command("select_all")
        view.run_command("right_delete")
        view.run_command("append", {"characters": content})
        view.set_read_only(True)
        view.sel().clear()
        view.sel().add(sublime.Region(0, 0))


class AiderSavvyTabCommand(sublime_plugin.TextCommand):
    """Commande pour cycler entre les vues avec Tab"""

    def run(self, edit):
        if not self.view.settings().get("aider_savvy_dashboard"):
            return

        current = self.view.settings().get("aider_savvy_view", "status")
        views = ["status", "files", "output", "commands"]

        try:
            current_index = views.index(current)
            next_index = (current_index + 1) % len(views)
            self.view.settings().set("aider_savvy_view", views[next_index])

            self.view.window().run_command("aider_savvy_refresh")
        except ValueError:
            pass

    def is_enabled(self):
        return self.view.settings().get("aider_savvy_dashboard", False)


class AiderSavvyRefreshCommand(sublime_plugin.WindowCommand):
    """Rafraîchir le dashboard"""

    def run(self):
        view = self.window.active_view()
        if view and view.settings().get("aider_savvy_dashboard"):
            aider_cmd = AiderSavvyCommand(self.window)
            aider_cmd.refresh_dashboard(view)


class AiderSavvyAddFilesCommand(sublime_plugin.WindowCommand):
    """Ajouter des fichiers au chat"""

    def run(self):
        # Obtenir les fichiers du projet
        folders = self.window.folders()
        if not folders:
            sublime.message_dialog("No project folder open")
            return

        self.window.show_input_panel(
            "Add files (space-separated or pattern):",
            "",
            self.on_done,
            None,
            None
        )

    def on_done(self, text):
        if not text:
            return

        files = text.split()
        ctx = self.window.aider_context

        for f in files:
            if f not in ctx['files']:
                ctx['files'].append(f)

        self.window.run_command("aider_savvy_refresh")


class AiderSavvyDropFilesCommand(sublime_plugin.WindowCommand):
    """Retirer des fichiers du chat"""

    def run(self):
        ctx = self.window.aider_context

        if not ctx['files']:
            sublime.message_dialog("No files in chat")
            return

        items = [[f, ""] for f in ctx['files']]

        def on_done(index):
            if index >= 0:
                removed = ctx['files'].pop(index)
                sublime.status_message("Removed: {}".format(removed))
                self.window.run_command("aider_savvy_refresh")

        self.window.show_quick_panel(items, on_done)


class AiderSavvySendPromptCommand(sublime_plugin.WindowCommand):
    """Envoyer une commande/prompt à Aider"""

    def run(self, text=None):
        if text is None:
            self.window.show_input_panel(
                "Enter prompt or command:",
                "",
                self.on_done,
                None,
                None
            )
        else:
            self.on_done(text)

    def on_done(self, text):
        if not text:
            return

        ctx = self.window.aider_context

        # Exécuter Aider avec la commande
        threading.Thread(
            target=self.run_aider,
            args=(text,)
        ).start()

    def run_aider(self, prompt):
        ctx = self.window.aider_context

        cmd = ["aider"]

        # Ajouter les fichiers
        for f in ctx['files']:
            cmd.extend(["--file", f])

        for f in ctx['readonly_files']:
            cmd.extend(["--read", f])

        # Ajouter le mode
        if ctx['mode'] == 'ask':
            cmd.append("--ask")
        elif ctx['mode'] == 'architect':
            cmd.append("--architect")

        # Ajouter le prompt
        cmd.extend(["--message", prompt])
        cmd.append("--no-auto-commits")
        cmd.append("--yes")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.window.folders()[0] if self.window.folders() else None
            )

            output = result.stdout + result.stderr
            timestamp = datetime.now().strftime("%H:%M:%S")

            ctx['output'].append("[{}] > {}".format(timestamp, prompt))
            ctx['output'].extend(output.split('\n'))

            sublime.set_timeout(
                lambda: self.window.run_command("aider_savvy_refresh"),
                0
            )

        except Exception as e:
            ctx['output'].append("Error: {}".format(str(e)))


class AiderSavvyChangeModeCommand(sublime_plugin.WindowCommand):
    """Changer le mode Aider"""

    def run(self):
        modes = ["code", "ask", "architect"]

        def on_done(index):
            if index >= 0:
                self.window.aider_context['mode'] = modes[index]
                self.window.run_command("aider_savvy_refresh")

        self.window.show_quick_panel(modes, on_done)


class AiderSavvyEventListener(sublime_plugin.EventListener):
    """Gestionnaire d'événements pour les raccourcis clavier"""

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "aider_savvy_dashboard":
            return view.settings().get("aider_savvy_dashboard", False)
        return None