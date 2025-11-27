# AiderSavvy - Files panel view
import sublime
import os


class FilesPanel:
    """Renders the files management panel."""

    def __init__(self, window, context):
        self.window = window
        self.context = context
        self.available_files = []

    def scan_project_files(self):
        """Scan project for available files."""
        self.available_files = []
        folders = self.window.folders()

        if not folders:
            return

        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
                       'dist', 'build', '.idea', '.vscode', '.svn', '.hg'}
        ignore_extensions = {'.pyc', '.pyo', '.so', '.o', '.a', '.dylib',
                             '.jpg', '.jpeg', '.png', '.gif', '.ico', '.pdf',
                             '.bin', '.exe', '.dll', '.obj', '.class'}
        max_files = 1000  # Limit to prevent performance issues

        for folder in folders:
            try:
                for root, dirs, files in os.walk(folder):
                    # Filter directories
                    dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
                    
                    # Early exit if we have too many files
                    if len(self.available_files) >= max_files:
                        break
                        
                    for f in files:
                        # Skip ignored extensions
                        ext = os.path.splitext(f)[1].lower()
                        if ext in ignore_extensions:
                            continue

                        # Skip aider files and hidden files
                        if f.startswith('.aider') or f.startswith('.'):
                            continue

                        full_path = os.path.join(root, f)
                        rel_path = os.path.relpath(full_path, folder)

                        # Skip if already added to context
                        if rel_path not in self.context.files and rel_path not in self.context.readonly_files:
                            self.available_files.append(rel_path)
                            
                        if len(self.available_files) >= max_files:
                            break
                            
                    if len(self.available_files) >= max_files:
                        break
            except (OSError, IOError) as e:
                print("AiderSavvy: Error scanning folder {0}: {1}".format(folder, e))
                continue

        # Remove duplicates and sort
        self.available_files = sorted(list(set(self.available_files)))

    def get_content(self):
        """Get the files panel content as string."""
        ctx = self.context
        lines = []

        # Header
        lines.append("  AIDER FILES")
        lines.append("")
        lines.append("  [a] Add file    [d] Drop file    [r] Read-only")
        lines.append("  [A] Add current [s] Scan project")
        lines.append("")

        # Editable files
        lines.append("-" * 60)
        lines.append("  Editable Files ({0})".format(len(ctx.files)))
        lines.append("-" * 60)
        if ctx.files:
            for i, f in enumerate(ctx.files, 1):
                lines.append("  {0:2}. {1}".format(i, f))
        else:
            lines.append("    (no files)")
        lines.append("")

        # Read-only files
        lines.append("-" * 60)
        lines.append("  Read-only Files ({0})".format(len(ctx.readonly_files)))
        lines.append("-" * 60)
        if ctx.readonly_files:
            for i, f in enumerate(ctx.readonly_files, 1):
                lines.append("  {0:2}. {1} [read-only]".format(i, f))
        else:
            lines.append("    (no read-only files)")
        lines.append("")

        # Available files (show first 30)
        lines.append("-" * 60)
        lines.append("  Available Files ({0} total)".format(len(self.available_files)))
        lines.append("-" * 60)
        if self.available_files:
            for f in self.available_files[:30]:
                lines.append("    {0}".format(f))
            if len(self.available_files) > 30:
                lines.append("    ... and {0} more".format(len(self.available_files) - 30))
        else:
            lines.append("    (press [s] to scan project)")

        return "\n".join(lines)
