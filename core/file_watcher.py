# AiderSavvy - File watcher for Aider output and session changes
import sublime
import os


class AiderFileWatcher:
    """Watches Aider chat history file for live updates and session changes."""

    def __init__(self, context, output_callback, session_callback=None):
        self.context = context
        self.output_callback = output_callback
        self.session_callback = session_callback
        self.last_size = 0
        self.last_mtime = 0
        self.running = False
        self.poll_interval = 1000  # milliseconds

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
                    new_content = ""
                    
                    if current_size > self.last_size:
                        # Read only new content
                        with open(history_path, 'r', encoding='utf-8', errors='replace') as f:
                            f.seek(self.last_size)
                            new_content = f.read()
                    elif current_size < self.last_size:
                        # File was truncated or recreated, read everything
                        with open(history_path, 'r', encoding='utf-8', errors='replace') as f:
                            new_content = f.read()
                    
                    if new_content:
                        # Call output callback for display
                        if self.output_callback:
                            self.output_callback(new_content)
                        
                        # Parse new content for session changes (model, mode, files)
                        if self.session_callback:
                            model_changed, mode_changed, files_changed = \
                                self.context.sync_incremental_from_history(new_content)
                            
                            if model_changed or mode_changed:
                                self.session_callback("OPTIONS")
                            if files_changed:
                                self.session_callback("FILES")

                    self.last_size = current_size
                    self.last_mtime = current_mtime

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
