# AiderSavvy - File watcher for Aider output
import sublime
import os


class AiderFileWatcher:
    """Watches .aider.chat.history.md for live output updates."""

    def __init__(self, context, callback):
        self.context = context
        self.callback = callback
        self.last_size = 0
        self.last_mtime = 0
        self.running = False
        self.poll_interval = 500  # milliseconds

    def start(self):
        """Start watching the history file."""
        self.running = True
        self._reset_position()
        self._poll()

    def stop(self):
        """Stop watching."""
        self.running = False

    def _reset_position(self):
        """Reset to current end of file."""
        history_path = self.context.get_aider_history_path()
        if os.path.exists(history_path):
            self.last_size = os.path.getsize(history_path)
            self.last_mtime = os.path.getmtime(history_path)
        else:
            self.last_size = 0
            self.last_mtime = 0

    def _poll(self):
        """Poll for file changes."""
        if not self.running:
            return

        history_path = self.context.get_aider_history_path()

        try:
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
                            if new_content and self.callback:
                                self.callback(new_content)
                    elif current_size < self.last_size:
                        # File was truncated or recreated, read everything
                        with open(history_path, 'r', encoding='utf-8', errors='replace') as f:
                            new_content = f.read()
                            if new_content and self.callback:
                                self.callback(new_content)

                    self.last_size = current_size
                    self.last_mtime = current_mtime
            else:
                # File doesn't exist, reset tracking
                self.last_size = 0
                self.last_mtime = 0

        except (OSError, IOError) as e:
            print("AiderSavvy: File watcher error accessing {0}: {1}".format(history_path, e))
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
