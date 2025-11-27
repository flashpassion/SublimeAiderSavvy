# AiderSavvy - Session context management
import os
import re


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
        self.model_aliases = self._detect_model_aliases()
        self.multiline_enabled = self._detect_multiline_config()

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
        """Detect available API keys from environment, .env and .aider.conf.yml."""
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

        # Check .aider.conf.yml (local)
        local_conf = os.path.join(self.project_root, ".aider.conf.yml")
        if os.path.exists(local_conf):
            try:
                with open(local_conf, 'r') as f:
                    content = f.read()
                    if 'openai-api-key:' in content and 'openai-api-key' not in str(keys_found).lower():
                        keys_found.append("openai-api-key (.aider.conf.yml)")
                    if 'anthropic-api-key:' in content and 'anthropic-api-key' not in str(keys_found).lower():
                        keys_found.append("anthropic-api-key (.aider.conf.yml)")
                    # Check api-key section for deepseek, gemini, etc.
                    if 'deepseek=' in content:
                        keys_found.append("deepseek (.aider.conf.yml)")
                    if 'gemini=' in content and '#' not in content.split('gemini=')[0].split('\n')[-1]:
                        keys_found.append("gemini (.aider.conf.yml)")
            except Exception:
                pass

        # Check global ~/.aider.conf.yml
        global_conf = os.path.expanduser("~/.aider.conf.yml")
        if os.path.exists(global_conf):
            try:
                with open(global_conf, 'r') as f:
                    content = f.read()
                    if 'openai-api-key:' in content and 'openai' not in str(keys_found).lower():
                        keys_found.append("openai-api-key (~/.aider.conf.yml)")
                    if 'anthropic-api-key:' in content and 'anthropic' not in str(keys_found).lower():
                        keys_found.append("anthropic-api-key (~/.aider.conf.yml)")
            except Exception:
                pass

        return keys_found if keys_found else ["No API keys detected"]

    def _detect_multiline_config(self):
        """Detect if multiline mode is enabled in aider config."""
        # Check local .aider.conf.yml
        local_conf = os.path.join(self.project_root, ".aider.conf.yml")
        if os.path.exists(local_conf):
            try:
                with open(local_conf, 'r') as f:
                    content = f.read()
                    if 'multiline: true' in content.lower():
                        return True
            except Exception:
                pass
        
        # Check global ~/.aider.conf.yml
        global_conf = os.path.expanduser("~/.aider.conf.yml")
        if os.path.exists(global_conf):
            try:
                with open(global_conf, 'r') as f:
                    content = f.read()
                    if 'multiline: true' in content.lower():
                        return True
            except Exception:
                pass
        
        return False

    def _detect_model_aliases(self):
        """Detect model aliases from .aider.conf.yml files."""
        aliases = [("gpt-4o", "gpt-4o")]  # Default (name, model)
        
        # Check local .aider.conf.yml
        local_conf = os.path.join(self.project_root, ".aider.conf.yml")
        if os.path.exists(local_conf):
            try:
                with open(local_conf, 'r') as f:
                    content = f.read()
                    # Look for alias: sections
                    lines = content.split('\n')
                    in_alias_section = False
                    for line in lines:
                        line = line.strip()
                        if line.startswith('alias:'):
                            in_alias_section = True
                            continue
                        elif in_alias_section and line and not line.startswith(' ') and not line.startswith('-'):
                            in_alias_section = False
                            continue
                        
                        if in_alias_section and line.startswith('- '):
                            # Extract alias name and model
                            alias_line = line[2:].strip()
                            if ':' in alias_line:
                                alias_name = alias_line.split(':', 1)[0].strip().strip('"\'')
                                model_name = alias_line.split(':', 1)[1].strip().strip('"\'')
                                # Check if this alias already exists
                                if not any(model == model_name for _, model in aliases):
                                    aliases.append((alias_name, model_name))
            except Exception:
                pass
        
        # Check global ~/.aider.conf.yml
        global_conf = os.path.expanduser("~/.aider.conf.yml")
        if os.path.exists(global_conf):
            try:
                with open(global_conf, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    in_alias_section = False
                    for line in lines:
                        line = line.strip()
                        if line.startswith('alias:'):
                            in_alias_section = True
                            continue
                        elif in_alias_section and line and not line.startswith(' ') and not line.startswith('-'):
                            in_alias_section = False
                            continue
                        
                        if in_alias_section and line.startswith('- '):
                            alias_line = line[2:].strip()
                            if ':' in alias_line:
                                alias_name = alias_line.split(':', 1)[0].strip().strip('"\'')
                                model_name = alias_line.split(':', 1)[1].strip().strip('"\'')
                                if not any(model == model_name for _, model in aliases):
                                    aliases.append((alias_name, model_name))
            except Exception:
                pass
        
        return aliases

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
        """Detect files, model and mode from an existing Aider session by parsing .aider.chat.history.md."""
        history_path = self.get_aider_history_path()
        
        if not os.path.exists(history_path):
            return False
        
        try:
            with open(history_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Find the last session block (starts with "# aider chat started at")
            sessions = content.split('# aider chat started at')
            if len(sessions) < 2:
                return False
            
            # Get the last session content
            last_session = sessions[-1]
            
            # Parse the last session to get current state
            self._parse_session_for_state(last_session)
            
            return True
            
        except Exception as e:
            print("AiderSavvy: Error reading chat history: {0}".format(e))
            return False

    def _parse_session_for_state(self, session_content):
        """Parse a session block to extract current model, mode and files."""
        lines = session_content.split('\n')
        
        # Track files - we need to process in order to handle add/drop
        session_files = []
        session_readonly = []
        
        # Patterns for extraction
        model_pattern = re.compile(r'Main model: ([^\s]+)')
        mode_pattern = re.compile(r'with (code|ask|architect) edit format')
        added_pattern = re.compile(r'Added ([^\s]+) to the chat\.')
        dropped_pattern = re.compile(r'Dropped ([^\s]+) from the chat\.')
        readonly_pattern = re.compile(r'Added ([^\s]+) to the chat as read-only\.')
        
        last_model = None
        last_mode = None
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and markdown headers
            if not line or line.startswith('#'):
                continue
            
            # Remove leading '> ' from aider output lines
            if line.startswith('> '):
                line = line[2:]
            
            # Check for model
            model_match = model_pattern.search(line)
            if model_match:
                last_model = model_match.group(1)
            
            # Check for mode
            mode_match = mode_pattern.search(line)
            if mode_match:
                last_mode = mode_match.group(1)
            
            # Check for added files (read-only first, then regular)
            readonly_match = readonly_pattern.search(line)
            if readonly_match:
                filepath = readonly_match.group(1)
                if filepath not in session_readonly:
                    session_readonly.append(filepath)
                if filepath in session_files:
                    session_files.remove(filepath)
                continue
            
            added_match = added_pattern.search(line)
            if added_match:
                filepath = added_match.group(1)
                if filepath not in session_files and filepath not in session_readonly:
                    session_files.append(filepath)
                continue
            
            # Check for dropped files
            dropped_match = dropped_pattern.search(line)
            if dropped_match:
                filepath = dropped_match.group(1)
                if filepath in session_files:
                    session_files.remove(filepath)
                if filepath in session_readonly:
                    session_readonly.remove(filepath)
        
        # Update context with parsed values
        if last_model:
            self.model = last_model
        
        if last_mode:
            self.mode = last_mode
        
        # Update files lists
        self.files = session_files
        self.readonly_files = session_readonly

    def sync_incremental_from_history(self, new_content):
        """Parse new content appended to history file for incremental updates.
        Returns tuple (model_changed, mode_changed, files_changed) to indicate what changed."""
        
        model_changed = False
        mode_changed = False
        files_changed = False
        
        # Patterns for extraction
        model_pattern = re.compile(r'Main model: ([^\s]+)')
        mode_pattern = re.compile(r'with (code|ask|architect) edit format')
        added_pattern = re.compile(r'Added ([^\s]+) to the chat\.')
        dropped_pattern = re.compile(r'Dropped ([^\s]+) from the chat\.')
        readonly_pattern = re.compile(r'Added ([^\s]+) to the chat as read-only\.')
        
        lines = new_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Remove leading '> ' from aider output lines
            if line.startswith('> '):
                line = line[2:]
            
            # Check for model change
            model_match = model_pattern.search(line)
            if model_match:
                new_model = model_match.group(1)
                if new_model != self.model:
                    self.model = new_model
                    model_changed = True
            
            # Check for mode change
            mode_match = mode_pattern.search(line)
            if mode_match:
                new_mode = mode_match.group(1)
                if new_mode != self.mode:
                    self.mode = new_mode
                    mode_changed = True
            
            # Check for read-only files first
            readonly_match = readonly_pattern.search(line)
            if readonly_match:
                filepath = readonly_match.group(1)
                if filepath not in self.readonly_files:
                    self.readonly_files.append(filepath)
                    files_changed = True
                if filepath in self.files:
                    self.files.remove(filepath)
                continue
            
            # Check for added files
            added_match = added_pattern.search(line)
            if added_match:
                filepath = added_match.group(1)
                if filepath not in self.files and filepath not in self.readonly_files:
                    self.files.append(filepath)
                    files_changed = True
                continue
            
            # Check for dropped files
            dropped_match = dropped_pattern.search(line)
            if dropped_match:
                filepath = dropped_match.group(1)
                if filepath in self.files:
                    self.files.remove(filepath)
                    files_changed = True
                if filepath in self.readonly_files:
                    self.readonly_files.remove(filepath)
                    files_changed = True
        
        return (model_changed, mode_changed, files_changed)

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
