import sublime
import sublime_plugin
import subprocess
import os
import re
from datetime import datetime
import threading

class AiderSavvySendPromptCommand(sublime_plugin.WindowCommand):
    """Send command/prompt to Aider."""

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

        # Ensure context exists
        if not hasattr(self.window, 'aider_context'):
             self.window.run_command("aider_savvy")

        ctx = self.window.aider_context

        # Intercept Model Switching Command
        if text.startswith("/model "):
            new_model = text.replace("/model ", "").strip()
            ctx['model'] = new_model
            # We still let it pass through to run_aider to actually verify/set it in the tool

        # Execute in thread
        threading.Thread(
            target=self.run_aider,
            args=(text,)
        ).start()

    def run_aider(self, prompt):
        ctx = self.window.aider_context
        root = ctx['project_root']

        cmd = ["aider"]

        # Files
        for f in ctx['files']:
            cmd.extend(["--file", f])
        for f in ctx['readonly_files']:
            cmd.extend(["--read", f])

        # Flags
        if ctx['mode'] == 'ask':
            cmd.append("--ask")
        elif ctx['mode'] == 'architect':
            cmd.append("--architect")

        # Explicit model if set in context (unless command is switching it)
        # Note: Usually /model command in aider is interactive, here we pass it as message
        # but for persistence, we might want to add --model flag to every call if we want it sticky
        # For now, we assume the user's config or env vars handle the default,
        # but if we want to force it:
        if 'model' in ctx and " (default)" not in ctx['model']:
             cmd.extend(["--model", ctx['model']])

        # Message
        cmd.extend(["--message", prompt])
        cmd.append("--no-auto-commits") # We want manual control or separate commit command
        cmd.append("--yes") # Always say yes to tool use in non-interactive mode

        try:
            # Important: Set CWD to project root
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=root,
                env=os.environ.copy() # Pass current env vars
            )

            output = result.stdout + result.stderr
            timestamp = datetime.now().strftime("%H:%M:%S")

            # Update Output Log
            ctx['output'].append("[{}] > {}".format(timestamp, prompt))
            ctx['output'].extend(output.split('\n'))

            # Trigger refresh
            sublime.set_timeout(
                lambda: self.window.run_command("aider_savvy_refresh"), 0
            )

        except Exception as e:
            ctx['output'].append("Error: {}".format(str(e)))
            sublime.set_timeout(
                lambda: self.window.run_command("aider_savvy_refresh"), 0
            )

class AiderSavvyAddFilesCommand(sublime_plugin.WindowCommand):
    """Add files to chat using a Fuzzy Search Quick Panel (Project Scan)."""

    def run(self):
        if not hasattr(self.window, 'aider_context'):
             self.window.run_command("aider_savvy")

        # Scan project files
        self.file_list = []
        folders = self.window.folders()
        if not folders:
            return

        # Simple recursive scan
        # Limit to reasonable amount to avoid freezing on massive node_modules
        MAX_FILES = 5000
        count = 0

        for folder in folders:
            for root, dirs, files in os.walk(folder):
                # Exclude common ignores
                dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', 'dist', 'build', '.venv', '.idea', '.vscode']]

                for f in files:
                    if f.endswith(('.pyc', '.o', '.class')): continue

                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, folder)
                    self.file_list.append(rel_path)
                    count += 1

                if count > MAX_FILES: break
            if count > MAX_FILES: break

        self.window.show_quick_panel(
            self.file_list,
            self.on_done
        )

    def on_done(self, index):
        if index == -1: return

        selected_file = self.file_list[index]
        ctx = self.window.aider_context

        if selected_file not in ctx['files']:
            ctx['files'].append(selected_file)
            sublime.status_message("Added: {}".format(selected_file))
        else:
            sublime.status_message("Already added")

        self.window.run_command("aider_savvy_refresh")

class AiderSavvyDropFilesCommand(sublime_plugin.WindowCommand):
    """Remove files from chat."""
    def run(self):
        ctx = self.window.aider_context
        if not ctx['files']:
            return

        def on_done(index):
            if index >= 0:
                removed = ctx['files'].pop(index)
                self.window.run_command("aider_savvy_refresh")

        self.window.show_quick_panel(ctx['files'], on_done)

# --- Sidebar Integration ---

class AiderSavvyAddFileFromSidebarCommand(sublime_plugin.WindowCommand):
    """Command triggered by Sidebar context menu."""

    def run(self, files=[]):
        if not hasattr(self.window, 'aider_context'):
             self.window.run_command("aider_savvy")

        ctx = self.window.aider_context
        project_root = ctx['project_root']

        added_count = 0
        for full_path in files:
            # Verify it is inside project
            if full_path.startswith(project_root):
                rel_path = os.path.relpath(full_path, project_root)
                if rel_path not in ctx['files']:
                    ctx['files'].append(rel_path)
                    added_count += 1

        if added_count > 0:
            sublime.status_message("Added {} files to Aider".format(added_count))
            # Refresh if dashboard is open
            self.window.run_command("aider_savvy_refresh")

    def is_visible(self, files=[]):
        # Only show if we have files selected
        return len(files) > 0

class AiderSavvyChangeModeCommand(sublime_plugin.WindowCommand):
    """Change Aider Mode."""
    def run(self):
        modes = ["code", "ask", "architect"]
        def on_done(index):
            if index >= 0:
                self.window.aider_context['mode'] = modes[index]
                self.window.run_command("aider_savvy_refresh")
        self.window.show_quick_panel(modes, on_done)