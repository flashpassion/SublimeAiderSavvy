import sublime
import sublime_plugin
import subprocess
import os
import re


class AiderSavvyAddReadonlyCommand(sublime_plugin.WindowCommand):
    """Ajouter des fichiers en lecture seule"""

    def run(self):
        self.window.show_input_panel(
            "Add read-only files (space-separated):",
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
            if f not in ctx['readonly_files']:
                ctx['readonly_files'].append(f)

        self.window.run_command("aider_savvy_refresh")


class AiderSavvyRunCommandCommand(sublime_plugin.WindowCommand):
    """Exécuter une commande Aider (/, /add, /drop, etc.)"""

    def run(self):
        commands = [
            "/add - Add files to chat",
            "/drop - Remove files from chat",
            "/read-only - Add read-only files",
            "/ask - Switch to ask mode",
            "/code - Switch to code mode",
            "/architect - Switch to architect mode",
            "/commit - Commit changes",
            "/diff - Show diff",
            "/undo - Undo last commit",
            "/map - Show repository map",
            "/map-refresh - Refresh repository map",
            "/tokens - Show token usage",
            "/clear - Clear chat history",
            "/reset - Reset everything",
            "/help - Show help",
            "/ls - List all files",
            "/git - Run git command",
            "/run - Run shell command",
            "/test - Run test command",
        ]

        def on_select(index):
            if index < 0:
                return

            cmd = commands[index].split(" - ")[0]

            # Pour certaines commandes, demander des arguments
            if cmd in ["/add", "/drop", "/read-only", "/git", "/run", "/test"]:
                self.window.show_input_panel(
                    "Arguments for {}:".format(cmd),
                    "",
                    lambda args: self.execute_command(cmd, args),
                    None,
                    None
                )
            else:
                self.execute_command(cmd)

        self.window.show_quick_panel(commands, on_select)

    def execute_command(self, cmd, args=""):
        """Exécuter une commande Aider"""
        full_cmd = "{} {}".format(cmd, args).strip()

        # Mettre à jour le contexte selon la commande
        ctx = self.window.aider_context

        if cmd == "/clear":
            ctx['output'].clear()
            sublime.status_message("Output cleared")
            self.window.run_command("aider_savvy_refresh")
            return

        if cmd == "/reset":
            ctx['files'].clear()
            ctx['readonly_files'].clear()
            ctx['output'].clear()
            ctx['history'].clear()
            sublime.status_message("Reset complete")
            self.window.run_command("aider_savvy_refresh")
            return

        if cmd == "/ask":
            ctx['mode'] = 'ask'
            sublime.status_message("Switched to ask mode")
            self.window.run_command("aider_savvy_refresh")
            return

        if cmd == "/code":
            ctx['mode'] = 'code'
            sublime.status_message("Switched to code mode")
            self.window.run_command("aider_savvy_refresh")
            return

        if cmd == "/architect":
            ctx['mode'] = 'architect'
            sublime.status_message("Switched to architect mode")
            self.window.run_command("aider_savvy_refresh")
            return

        # Pour les autres commandes, exécuter via aider
        self.window.run_command("aider_savvy_send_prompt", {"text": full_cmd})


class AiderSavvyShowOutputCommand(sublime_plugin.WindowCommand):
    """Basculer vers la vue Output"""

    def run(self):
        view = self.window.active_view()
        if view and view.settings().get("aider_savvy_dashboard"):
            view.settings().set("aider_savvy_view", "output")
            self.window.run_command("aider_savvy_refresh")


class AiderSavvyDiffCommand(sublime_plugin.WindowCommand):
    """Afficher le diff des changements"""

    def run(self):
        self.window.run_command("aider_savvy_send_prompt", {"text": "/diff"})


class AiderSavvyTokensCommand(sublime_plugin.WindowCommand):
    """Afficher l'utilisation des tokens"""

    def run(self):
        self.window.run_command("aider_savvy_send_prompt", {"text": "/tokens"})


class AiderSavvyMapCommand(sublime_plugin.WindowCommand):
    """Afficher la carte du repository"""

    def run(self):
        self.window.run_command("aider_savvy_send_prompt", {"text": "/map"})


class AiderSavvyCommitCommand(sublime_plugin.WindowCommand):
    """Committer les changements"""

    def run(self):
        self.window.show_input_panel(
            "Commit message (optional):",
            "",
            lambda msg: self.window.run_command(
                "aider_savvy_send_prompt",
                {"text": "/commit {}".format(msg)}
            ),
            None,
            None
        )


class AiderSavvyFileCompletionListener(sublime_plugin.EventListener):
    """Autocomplétion des fichiers dans les input panels"""

    def on_query_completions(self, view, prefix, locations):
        # Vérifier si on est dans un input panel pour aider
        if not view.settings().get("is_widget"):
            return None

        # Obtenir les fichiers du projet
        window = view.window()
        if not window:
            return None

        folders = window.folders()
        if not folders:
            return None

        # Récupérer les settings
        settings = sublime.load_settings("AiderSavvy.sublime-settings")
        patterns = settings.get("file_patterns", ["*.py", "*.js", "*.md"])

        completions = []

        for folder in folders:
            for root, dirs, files in os.walk(folder):
                # Ignorer certains dossiers
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv']]

                for file in files:
                    # Vérifier si le fichier correspond aux patterns
                    if any(self._match_pattern(file, pattern) for pattern in patterns):
                        rel_path = os.path.relpath(os.path.join(root, file), folder)
                        completions.append((rel_path, rel_path))

        return completions

    def _match_pattern(self, filename, pattern):
        """Vérifier si un fichier correspond à un pattern"""
        regex = pattern.replace(".", r"\.").replace("*", ".*")
        return re.match("^{}$".format(regex), filename) is not None


class AiderSavvyInteractiveShellCommand(sublime_plugin.WindowCommand):
    """Lancer un shell interactif avec Aider"""

    def run(self):
        ctx = self.window.aider_context

        # Construire la commande
        cmd = ["aider"]

        for f in ctx['files']:
            cmd.extend(["--file", f])

        for f in ctx['readonly_files']:
            cmd.extend(["--read", f])

        if ctx['mode'] == 'ask':
            cmd.append("--ask")
        elif ctx['mode'] == 'architect':
            cmd.append("--architect")

        # Obtenir le terminal selon l'OS
        if sublime.platform() == "linux":
            terminal_cmd = ["gnome-terminal", "--", "bash", "-c"]
            full_cmd = " ".join(cmd) + "; exec bash"
            terminal_cmd.append(full_cmd)
        elif sublime.platform() == "osx":
            terminal_cmd = ["open", "-a", "Terminal.app"]
            terminal_cmd.extend(cmd)
        else:  # Windows
            terminal_cmd = ["cmd", "/c", "start", "cmd", "/k"] + cmd

        # Lancer le terminal
        folders = self.window.folders()
        cwd = folders[0] if folders else None

        subprocess.Popen(
            terminal_cmd,
            cwd=cwd
        )


class AiderSavvyQuickAddCommand(sublime_plugin.WindowCommand):
    """Ajouter rapidement le fichier actuel au chat"""

    def run(self):
        view = self.window.active_view()
        if not view or not view.file_name():
            sublime.message_dialog("No file open")
            return

        filename = view.file_name()
        folders = self.window.folders()

        if folders:
            rel_path = os.path.relpath(filename, folders[0])
        else:
            rel_path = filename

        ctx = self.window.aider_context

        if rel_path not in ctx['files']:
            ctx['files'].append(rel_path)
            sublime.status_message("Added: {}".format(rel_path))
        else:
            sublime.status_message("Already in chat: {}".format(rel_path))


class AiderSavvyClearOutputCommand(sublime_plugin.WindowCommand):
    """Effacer l'output"""

    def run(self):
        self.window.aider_context['output'].clear()
        sublime.status_message("Output cleared")
        self.window.run_command("aider_savvy_refresh")