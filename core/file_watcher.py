# AiderSavvy - File watcher for Aider output and session changes
import sublime
import os
import time


class AiderFileWatcher:
    """Watches Aider files for live output updates and session changes."""

    def __init__(self, context, output_callback, session_callback=None):
        self.context = context
        self.output_callback = output_callback
        self.session_callback = session_callback
        self.last_size = 0
        self.last_mtime = 0
        self.cache_mtime = 0
        self.input_history_mtime = 0
        self.running = False
        self.poll_interval = 1000  # milliseconds

    def start(self):
        """Start watching the history file and session files."""
        self.running = True
        self._reset_position()
        self._poll()

    def stop(self):
        """Stop watching."""
        self.running = False

    def _reset_position(self):
        """Reset to current end of file and initialize timestamps."""
        history_path = self.context.get_aider_history_path()
        if os.path.exists(history_path):
            self.last_size = os.path.getsize(history_path)
            self.last_mtime = os.path.getmtime(history_path)
        else:
            self.last_size = 0
            self.last_mtime = 0

        # Initialize cache and input history timestamps
        cache_dir = os.path.join(self.context.project_root, ".aider.tags.cache.v3")
        cache_file = os.path.join(cache_dir, "cache.json")
        if os.path.exists(cache_file):
            self.cache_mtime = os.path.getmtime(cache_file)
        
        input_history_path = self.context.get_aider_input_history_path()
        if os.path.exists(input_history_path):
            self.input_history_mtime = os.path.getmtime(input_history_path)

    def _poll(self):
        """Poll for file changes."""
        if not self.running:
            return

        history_path = self.context.get_aider_history_path()
        cache_dir = os.path.join(self.context.project_root, ".aider.tags.cache.v3")
        cache_file = os.path.join(cache_dir, "cache.json")
        input_history_path = self.context.get_aider_input_history_path()

        try:
            # Check history file for new output
            if os.path.exists(history_path):
                current_mtime = os.path.getmtime(history_path)
                current_size = os.path.getsize(history_path)

                # Check if file was modified
                if current_mtime > self.last_mtime or current_size != self.last_size:
                    if current_size > self.last_size:
                        # Read only new content
                        with open(history_path, 'r', encoding='utf-8', errors='replace') as f:
                            f.seek(self.last_size)
                            new_content = f.read()
                            if new_content and self.output_callback:
                                self.output_callback(new_content)
                    elif current_size < self.last_size:
                        # File was truncated or recreated, read everything
                        with open(history_path, 'r', encoding='utf-8', errors='replace') as f:
                            new_content = f.read()
                            if new_content and self.output_callback:
                                self.output_callback(new_content)

                    self.last_size = current_size
                    self.last_mtime = current_mtime

            # Check cache file for session changes
            if os.path.exists(cache_file):
                current_cache_mtime = os.path.getmtime(cache_file)
                if current_cache_mtime > self.cache_mtime:
                    self.cache_mtime = current_cache_mtime
                    if self.session_callback:
                        self.session_callback("CACHE")

            # Check input history for model/mode changes
            if os.path.exists(input_history_path):
                current_input_mtime = os.path.getmtime(input_history_path)
                if current_input_mtime > self.input_history_mtime:
                    self.input_history_mtime = current_input_mtime
                    if self.session_callback:
                        self.session_callback("INPUT_HISTORY")

        except (OSError, IOError) as e:
            print("AiderSavvy: File watcher error: {0}".format(e))
        except Exception as e:
            print("AiderSavvy: Unexpected file watcher error: {0}".format(e))

        # Schedule next poll
        if self.running:
            sublime.set_timeout(self._poll, self.poll_interval)

    def get_full_history(self):
        """Read the entire history file."""
        history_path = self.context.get_aider_history_path()
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
            except Exception:
                pass
        return ""
