# AiderSavvy - Session context management
import os


class AiderContext:
    """Manages the Aider session state."""

    def __init__(self, window):
        self.window = window
        self.project_root = self._determine_project_root()
        self.files = []
        self.readonly_files = []
        self.mode = 'code'
        self.model = 'gpt-4o'
        self.is_running = False
        self.terminal_tag = 'aider_terminal'
        self.api_keys = self._detect_api_keys()

    def _determine_project_root(self):
        """Find the best project root directory."""
        folders = self.window.folders()
        if not folders:
            view = self.window.active_view()
            if view and view.file_name():
                return os.path.dirname(view.file_name())
            return os.path.expanduser("~")

        # Prefer folder with .env or .git
        for folder in folders:
            if os.path.exists(os.path.join(folder, ".env")):
                return folder
        for folder in folders:
            if os.path.exists(os.path.join(folder, ".git")):
                return folder
        return folders[0]

    def _detect_api_keys(self):
        """Detect available API keys from environment and .env file."""
        keys_found = []
        common_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY"]

        # Check system environment
        for key in common_keys:
            if os.environ.get(key):
                keys_found.append("{0} (env)".format(key))

        # Check .env file
        env_path = os.path.join(self.project_root, ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    content = f.read()
                    for key in common_keys:
                        if key in content and key not in [k.split()[0] for k in keys_found]:
                            keys_found.append("{0} (.env)".format(key))
            except Exception:
                pass

        return keys_found if keys_found else ["No API keys detected"]

    def add_file(self, filepath):
        """Add a file to the chat."""
        if filepath not in self.files and filepath not in self.readonly_files:
            self.files.append(filepath)
            return True
        return False

    def add_readonly_file(self, filepath):
        """Add a file as read-only."""
        if filepath in self.files:
            self.files.remove(filepath)
        if filepath not in self.readonly_files:
            self.readonly_files.append(filepath)
            return True
        return False

    def drop_file(self, filepath):
        """Remove a file from the chat."""
        if filepath in self.files:
            self.files.remove(filepath)
            return True
        if filepath in self.readonly_files:
            self.readonly_files.remove(filepath)
            return True
        return False

    def set_mode(self, mode):
        """Set the Aider mode (code/ask/architect)."""
        if mode in ['code', 'ask', 'architect']:
            self.mode = mode
            return True
        return False

    def set_model(self, model):
        """Set the AI model."""
        self.model = model

    def get_aider_history_path(self):
        """Get path to .aider.chat.history.md file."""
        return os.path.join(self.project_root, ".aider.chat.history.md")

    def get_aider_input_history_path(self):
        """Get path to .aider.input.history file."""
        return os.path.join(self.project_root, ".aider.input.history")

    def sync_from_existing_session(self):
        """Detect files from an existing Aider session."""
        import json
        
        # Méthode 1: Lire .aider.tags.cache.v3/cache.json si existe
        cache_dir = os.path.join(self.project_root, ".aider.tags.cache.v3")
        cache_file = os.path.join(cache_dir, "cache.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                    for filepath in cache.keys():
                        rel_path = os.path.relpath(filepath, self.project_root)
                        if rel_path not in self.files and rel_path not in self.readonly_files:
                            self.files.append(rel_path)
                return True
            except Exception as e:
                print("AiderSavvy: Error reading cache: {0}".format(e))
        
        # Méthode 2: Parser .aider.input.history pour les commandes /add
        history_path = self.get_aider_input_history_path()
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('/add '):
                            filepath = line[5:].strip()
                            if filepath and filepath not in self.files:
                                self.files.append(filepath)
                        elif line.startswith('/read-only ') or line.startswith('/read '):
                            parts = line.split(' ', 1)
                            if len(parts) > 1:
                                filepath = parts[1].strip()
                                if filepath and filepath not in self.readonly_files:
                                    self.readonly_files.append(filepath)
                        elif line.startswith('/drop '):
                            filepath = line[6:].strip()
                            if filepath in self.files:
                                self.files.remove(filepath)
                            if filepath in self.readonly_files:
                                self.readonly_files.remove(filepath)
                return True
            except Exception as e:
                print("AiderSavvy: Error reading input history: {0}".format(e))
        
        return False

    def to_dict(self):
        """Export context as dictionary."""
        return {
            'project_root': self.project_root,
            'files': self.files[:],
            'readonly_files': self.readonly_files[:],
            'mode': self.mode,
            'model': self.model,
            'is_running': self.is_running,
            'api_keys': self.api_keys[:]
        }
