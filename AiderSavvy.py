import sublime
import sublime_plugin
import subprocess
import os
import threading
import re
import traceback
from datetime import datetime

# Global constant for the home config file
AIDER_CONF_PATH = os.path.expanduser("~/.aider.conf.yml")

def plugin_loaded():
    """Called when the plugin is loaded."""
    print("AiderSavvy: Plugin loaded successfully.")

class AiderSavvyCommand(sublime_plugin.WindowCommand):
    """Main command to open the Aider dashboard."""

    def run(self):
        print("AiderSavvy: Run triggered")
        try:
            # Create or reuse the view
            view = self.get_existing_dashboard()
            if not view or not view.is_valid():
                view = self.window.new_file()
                view.set_name("AIDER")
                view.settings().set("aider_savvy_dashboard", True)
                view.settings().set("aider_savvy_view", "status")
                view.set_scratch(True)
                view.set_read_only(True)
                view.settings().set("word_wrap", False)

                try:
                    view.assign_syntax("Packages/AiderSavvy/AiderSavvy.sublime-syntax")
                except Exception:
                    pass

            # Initialize Aider context if needed
            if not hasattr(self.window, 'aider_context'):
                self.init_context()

            # Bring view to front and refresh
            self.window.focus_view(view)
            self.refresh_dashboard(view)

        except Exception:
            traceback.print_exc()

    def get_existing_dashboard(self):
        """Check if dashboard already exists."""
        for view in self.window.views():
            if view.settings().get("aider_savvy_dashboard"):
                return view
        return None

    def init_context(self):
        """Initialize the data structure for the window."""
        try:
            # Smart detection of the project root
            project_root = self.determine_best_root()

            self.window.aider_context = {
                'files': [],
                'readonly_files': [],
                'history': [],
                'output': [],
                'mode': 'code',
                'model': 'gpt-4o (default)',
                'project_root': project_root,
                'api_status': self.check_api_keys(project_root)
            }
        except Exception:
            print("AiderSavvy Error in init_context:")
            traceback.print_exc()

    def determine_best_root(self):
        """
        Scans all open folders to find the best candidate for the project root.
        Priority:
        1. Folder containing .env
        2. Folder containing .git
        3. First folder in the list
        4. Directory of active file
        5. User home
        """
        folders = self.window.folders()

        if not folders:
            # No folders open, try active file
            view = self.window.active_view()
            if view and view.file_name():
                return os.path.dirname(view.file_name())
            return os.path.expanduser("~")

        # 1. Look for .env (Highest priority)
        for folder in folders:
            if os.path.exists(os.path.join(folder, ".env")):
                return folder

        # 2. Look for .git
        for folder in folders:
            if os.path.exists(os.path.join(folder, ".git")):
                return folder

        # 3. Default to first folder
        return folders[0]

    def check_api_keys(self, root):
        """Check for API keys in env vars or .env file."""
        keys_found = []
        try:
            # 1. Check OS Environment
            common_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"]
            for key in common_keys:
                if os.environ.get(key):
                    keys_found.append("{} (System Env)".format(key))

            # 2. Check local .env file
            env_path = os.path.join(root, ".env")
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        for key in common_keys:
                            if key in content and key not in [k.split()[0] for k in keys_found]:
                                 keys_found.append("{} (.env)".format(key))
                except Exception:
                    pass
        except Exception:
            pass

        return keys_found if keys_found else ["No API keys detected (check .env)"]

    def refresh_dashboard(self, view):
        """Refresh dashboard display based on current view state."""
        try:
            if not view.is_valid(): return

            current_view = view.settings().get("aider_savvy_view", "status")

            # Ensure context exists (handling accidental context loss)
            if not hasattr(self.window, 'aider_context'):
                self.init_context()

            # Refresh API status if file exists (lightweight check)
            ctx = self.window.aider_context
            if os.path.exists(os.path.join(ctx['project_root'], ".env")):
                 ctx['api_status'] = self.check_api_keys(ctx['project_root'])

            if current_view == "status":
                self.render_status(view)
            elif current_view == "files":
                self.render_files(view)
            elif current_view == "output":
                self.render_output(view)
            elif current_view == "commands":
                self.render_commands(view)
        except Exception:
            traceback.print_exc()

    def render_status(self, view):
        ctx = self.window.aider_context
        content = []
        content.append("=" * 80)
        content.append("  AIDER - AI Pair Programming")
        content.append("=" * 80)
        content.append("")
        content.append("  Project Root : {}".format(ctx.get('project_root', 'Unknown')))
        content.append("  Current Model: {}".format(ctx.get('model', 'Unknown')))
        content.append("  Active Mode  : {}".format(ctx.get('mode', 'code').upper()))
        content.append("")
        content.append("-" * 80)
        content.append("  API Configuration:")
        content.append("-" * 80)
        for status in ctx.get('api_status', []):
             content.append("  * {}".format(status))
        content.append("")
        content.append("-" * 80)
        content.append("  Context:")
        content.append("-" * 80)
        content.append("  Files in chat   : {}".format(len(ctx.get('files', []))))
        content.append("  Read-only files : {}".format(len(ctx.get('readonly_files', []))))
        content.append("")
        content.append("-" * 80)
        content.append("  Quick Actions:")
        content.append("-" * 80)
        content.append("  a - Add files    d - Drop files")
        content.append("  c - Send prompt  o - Show output")
        content.append("  / - Commands     e - Open .env")
        content.append("  s - Switch Root  g - Global Config")
        content.append("")
        content.append("  TAB - Cycle views (Status -> Files -> Output -> Commands)")
        content.append("  q   - Close dashboard")
        content.append("")

        files = ctx.get('files', [])
        if files:
            content.append("-" * 80)
            content.append("  Active Files Preview:")
            content.append("-" * 80)
            for f in files[:5]:
                content.append("    • {}".format(f))
            if len(files) > 5:
                content.append("    ... and {} more".format(len(files) - 5))
            content.append("")

        self._update_view_content(view, "\n".join(content))

    def render_files(self, view):
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
        if ctx.get('files'):
            for i, f in enumerate(ctx['files'], 1):
                content.append("  {}. {}".format(i, f))
        else:
            content.append("    (no files)")
        content.append("")
        content.append("-" * 80)
        content.append("  Read-only Files:")
        content.append("-" * 80)
        if ctx.get('readonly_files'):
            for i, f in enumerate(ctx['readonly_files'], 1):
                content.append("  {}. {} [read-only]".format(i, f))
        else:
            content.append("    (no read-only files)")
        self._update_view_content(view, "\n".join(content))

    def render_output(self, view):
        ctx = self.window.aider_context
        content = []
        content.append("=" * 80)
        content.append("  AIDER - Output")
        content.append("=" * 80)
        content.append("")
        content.append("  c - Clear output    TAB - Next view")
        content.append("-" * 80)
        if ctx.get('output'):
            content.extend(ctx['output'])
        else:
            content.append("  (no output yet)")
        self._update_view_content(view, "\n".join(content))

    def render_commands(self, view):
        commands = [
            ("/add", "Add files to the chat"),
            ("/drop", "Remove files from the chat"),
            ("/model", "Switch LLM Model"),
            ("/ask", "Ask questions without editing"),
            ("/code", "Ask for code changes"),
            ("/commit", "Commit edits to repo"),
            ("/diff", "Display diff of changes"),
            ("/map", "Print repository map"),
            ("/clear", "Clear chat history"),
            ("/help", "Get help"),
        ]
        content = []
        content.append("=" * 80)
        content.append("  AIDER - Available Commands")
        content.append("=" * 80)
        content.append("")
        content.append("  Press '/' to execute any command    TAB - Next view")
        content.append("-" * 80)
        for cmd, desc in commands:
            content.append("  {:20} - {}".format(cmd, desc))
        self._update_view_content(view, "\n".join(content))

    def _update_view_content(self, view, content):
        view.set_read_only(False)
        view.run_command("select_all")
        view.run_command("right_delete")
        view.run_command("append", {"characters": content})
        view.set_read_only(True)
        view.sel().clear()
        view.sel().add(sublime.Region(0, 0))

class AiderSavvyTabCommand(sublime_plugin.TextCommand):
    """Cycle through views with Tab."""
    def run(self, edit):
        if not self.view.settings().get("aider_savvy_dashboard"):
            return

        current = self.view.settings().get("aider_savvy_view", "status")
        views = ["status", "files", "output", "commands"]
        try:
            current_index = views.index(current)
            next_index = (current_index + 1) % len(views)
            self.view.settings().set("aider_savvy_view", views[next_index])

            # Safe refresh call
            if self.view.window():
                self.view.window().run_command("aider_savvy_refresh")
        except ValueError:
            pass

class AiderSavvyRefreshCommand(sublime_plugin.WindowCommand):
    """Refreshes the dashboard."""
    def run(self):
        view = self.window.active_view()
        if view and view.settings().get("aider_savvy_dashboard"):
            aider_cmd = AiderSavvyCommand(self.window)
            aider_cmd.refresh_dashboard(view)

# --- CRITICAL MISSING PIECE RESTORED ---
class AiderSavvyEventListener(sublime_plugin.EventListener):
    """Event Listener for Key Bindings Context."""

    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "aider_savvy_dashboard":
            # Check if current view is our dashboard
            is_dashboard = view.settings().get("aider_savvy_dashboard", False)

            if operator == sublime.OP_EQUAL:
                return is_dashboard == operand
            elif operator == sublime.OP_NOT_EQUAL:
                return is_dashboard != operand

        return None

# --- Configuration Management Commands ---

class AiderSavvyOpenEnvCommand(sublime_plugin.WindowCommand):
    def run(self):
        # Fallback init if needed
        if not hasattr(self.window, 'aider_context'):
             self.window.run_command("aider_savvy")

        sublime.set_timeout(self._open_env, 100)

    def _open_env(self):
        if hasattr(self.window, 'aider_context'):
            root = self.window.aider_context['project_root']
            env_file = os.path.join(root, ".env")

            if os.path.exists(env_file):
                self.window.open_file(env_file)
            else:
                if sublime.ok_cancel_dialog("Create .env at {}?".format(root), "Create"):
                    try:
                        with open(env_file, 'w', encoding='utf-8') as f:
                            f.write("# Aider API Keys\n#OPENAI_API_KEY=\n")
                        self.window.open_file(env_file)
                    except Exception as e:
                        sublime.error_message("Error: {}".format(e))

class AiderSavvyOpenGlobalConfigCommand(sublime_plugin.WindowCommand):
    def run(self):
        if os.path.exists(AIDER_CONF_PATH):
            self.window.open_file(AIDER_CONF_PATH)
        else:
            if sublime.ok_cancel_dialog("Create {}?".format(AIDER_CONF_PATH), "Create"):
                try:
                    with open(AIDER_CONF_PATH, 'w', encoding='utf-8') as f:
                        f.write("# Aider Global Configuration\nmodel: gpt-4o\n")
                    self.window.open_file(AIDER_CONF_PATH)
                except Exception:
                    pass

class AiderSavvySwitchProjectRootCommand(sublime_plugin.WindowCommand):
    """Switch the project root folder."""
    def run(self):
        folders = self.window.folders()
        if not folders:
            sublime.status_message("No project folders open.")
            return

        def on_done(index):
            if index >= 0:
                new_root = folders[index]
                if hasattr(self.window, 'aider_context'):
                    ctx = self.window.aider_context
                    ctx['project_root'] = new_root
                    # Recheck keys for the new root
                    ctx['api_status'] = AiderSavvyCommand(self.window).check_api_keys(new_root)
                    self.window.run_command("aider_savvy_refresh")
                    sublime.status_message("Switched Aider root to: {}".format(os.path.basename(new_root)))

        # Display short names for better UX
        display_names = [os.path.basename(f) + " ({})".format(f) for f in folders]
        self.window.show_quick_panel(display_names, on_done)