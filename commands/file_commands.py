# AiderSavvy - File management commands
import sublime
import sublime_plugin
import os

from .dashboard import get_aider_instance


class AiderSavvyAddFileCommand(sublime_plugin.WindowCommand):
    """Add a file to the Aider chat via quick panel."""

    def run(self):
        instance = get_aider_instance(self.window)
        instance.files_panel.scan_project_files()

        files = instance.files_panel.available_files
        if not files:
            sublime.status_message("No files available to add")
            return

        self.files = files
        self.window.show_quick_panel(files, self.on_done)

    def on_done(self, index):
        if index >= 0:
            instance = get_aider_instance(self.window)
            filepath = self.files[index]

            if instance.context.add_file(filepath):
                sublime.status_message("Added: {0}".format(filepath))

                # Send to terminal if running
                if instance.terminal.is_running():
                    instance.terminal.send_aider_command("add {0}".format(filepath))

                instance.refresh_files()


class AiderSavvyAddCurrentFileCommand(sublime_plugin.WindowCommand):
    """Add the currently open file to Aider chat."""

    def run(self):
        view = self.window.active_view()
        if not view or not view.file_name():
            sublime.status_message("No file open")
            return

        instance = get_aider_instance(self.window)
        folders = self.window.folders()

        filepath = view.file_name()
        if folders:
            filepath = os.path.relpath(filepath, folders[0])

        if instance.context.add_file(filepath):
            sublime.status_message("Added: {0}".format(filepath))

            if instance.terminal.is_running():
                instance.terminal.send_aider_command("add {0}".format(filepath))

            instance.refresh_files()
        else:
            sublime.status_message("Already in chat: {0}".format(filepath))


class AiderSavvyDropFileCommand(sublime_plugin.WindowCommand):
    """Drop a file from the Aider chat."""

    def run(self):
        instance = get_aider_instance(self.window)
        ctx = instance.context

        all_files = ctx.files + ctx.readonly_files
        if not all_files:
            sublime.status_message("No files to drop")
            return

        self.files = all_files
        display = []
        for f in ctx.files:
            display.append(f)
        for f in ctx.readonly_files:
            display.append("{0} [read-only]".format(f))

        self.window.show_quick_panel(display, self.on_done)

    def on_done(self, index):
        if index >= 0:
            instance = get_aider_instance(self.window)
            filepath = self.files[index]

            if instance.context.drop_file(filepath):
                sublime.status_message("Dropped: {0}".format(filepath))

                if instance.terminal.is_running():
                    instance.terminal.send_aider_command("drop {0}".format(filepath))

                instance.refresh_files()


class AiderSavvyReadOnlyFileCommand(sublime_plugin.WindowCommand):
    """Add a file as read-only."""

    def run(self):
        instance = get_aider_instance(self.window)
        instance.files_panel.scan_project_files()

        # Include currently editable files too
        files = instance.context.files + instance.files_panel.available_files
        if not files:
            sublime.status_message("No files available")
            return

        self.files = files
        self.window.show_quick_panel(files, self.on_done)

    def on_done(self, index):
        if index >= 0:
            instance = get_aider_instance(self.window)
            filepath = self.files[index]

            if instance.context.add_readonly_file(filepath):
                sublime.status_message("Added as read-only: {0}".format(filepath))

                if instance.terminal.is_running():
                    instance.terminal.send_aider_command("read-only {0}".format(filepath))

                instance.refresh_files()


class AiderSavvyScanFilesCommand(sublime_plugin.WindowCommand):
    """Scan project for available files."""

    def run(self):
        instance = get_aider_instance(self.window)
        instance.files_panel.scan_project_files()
        instance.refresh_files()
        sublime.status_message("Found {0} files".format(
            len(instance.files_panel.available_files)))
