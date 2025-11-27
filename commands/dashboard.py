# AiderSavvy - Dashboard command
import sublime
import sublime_plugin

from ..core.context import AiderContext
from ..core.terminal import AiderTerminal
from ..core.file_watcher import AiderFileWatcher
from ..views.options_panel import OptionsPanel
from ..views.output_panel import OutputPanel
from ..views.files_panel import FilesPanel


def get_aider_instance(window):
    """Get or create the AiderSavvy instance for a window."""
    if not hasattr(window, 'aider_savvy'):
        window.aider_savvy = AiderSavvyInstance(window)
    return window.aider_savvy


class AiderSavvyInstance:
    """Main instance managing all Aider components for a window."""

    # Tab modes
    TAB_OPTIONS = 0
    TAB_FILES = 1
    TAB_OUTPUT = 2

    def __init__(self, window):
        self.window = window
        self.context = AiderContext(window)
        self.terminal = AiderTerminal(window, self.context)
        self.file_watcher = None
        self.current_tab = self.TAB_OPTIONS
        self.main_view = None

        # Views (they share the same view, just different content)
        self.options_panel = OptionsPanel(window, self.context)
        self.output_panel = OutputPanel(window, self.context)
        self.files_panel = FilesPanel(window, self.context)

    def setup_layout(self):
        """Setup the layout: main view on top, terminal in panel below."""
        # Sync from existing Aider session
        self.context.sync_from_existing_session()
        
        # Simple single-group layout (terminal will be in output panel)
        self.window.set_layout({
            "cols": [0.0, 1.0],
            "rows": [0.0, 1.0],
            "cells": [[0, 0, 1, 1]]
        })

        # Create main view
        self._create_main_view()

        # Initial render
        self.render_current_tab()

        # Start file watcher
        self.start_file_watcher()

    def _create_main_view(self):
        """Create or get the main view."""
        # Look for existing view
        for view in self.window.views():
            if view.settings().get("aider_savvy_main"):
                self.main_view = view
                self.window.set_view_index(self.main_view, 0, 0)
                return

        # Create new view
        self.main_view = self.window.new_file()
        self.main_view.set_name("AIDER")
        self.main_view.set_scratch(True)
        self.main_view.set_read_only(True)
        self.main_view.settings().set("aider_savvy_main", True)
        self.main_view.settings().set("aider_savvy_view", True)
        self.main_view.settings().set("word_wrap", False)
        self.main_view.settings().set("line_numbers", False)
        self.main_view.settings().set("gutter", False)
        self.main_view.settings().set("scroll_past_end", False)

        try:
            self.main_view.assign_syntax("Packages/AiderSavvy/AiderSavvy.sublime-syntax")
        except Exception as e:
            print("AiderSavvy: Failed to set syntax - {0}".format(e))

        self.window.set_view_index(self.main_view, 0, 0)
        self.window.focus_view(self.main_view)

    def next_tab(self):
        """Switch to next tab."""
        self.current_tab = (self.current_tab + 1) % 3
        self.render_current_tab()

    def prev_tab(self):
        """Switch to previous tab."""
        self.current_tab = (self.current_tab - 1) % 3
        self.render_current_tab()

    def go_to_tab(self, tab_index):
        """Go to specific tab."""
        if 0 <= tab_index <= 2:
            self.current_tab = tab_index
            self.render_current_tab()

    def render_current_tab(self):
        """Render the current tab content."""
        if not self.main_view or not self.main_view.is_valid():
            self._create_main_view()

        # Update view name based on tab
        tab_names = ["AIDER: Options", "AIDER: Files", "AIDER: Output"]
        self.main_view.set_name(tab_names[self.current_tab])

        # Build content with tab header
        content = self._build_tab_header()

        if self.current_tab == self.TAB_OPTIONS:
            content += self.options_panel.get_content()
        elif self.current_tab == self.TAB_FILES:
            self.files_panel.scan_project_files()
            content += self.files_panel.get_content()
        elif self.current_tab == self.TAB_OUTPUT:
            content += self.output_panel.get_content()

        self._update_view_content(content)

    def _build_tab_header(self):
        """Build the tab navigation header."""
        tabs = ["[1] Options", "[2] Files", "[3] Output"]
        indicators = []

        for i, tab in enumerate(tabs):
            if i == self.current_tab:
                indicators.append(">> {0} <<".format(tab))
            else:
                indicators.append("   {0}   ".format(tab))

        header = "  ".join(indicators)
        separator = "=" * 70

        return "{0}\n{1}\n\n".format(header, separator)

    def _update_view_content(self, content):
        """Update the main view content."""
        self.main_view.set_read_only(False)
        self.main_view.run_command("select_all")
        self.main_view.run_command("right_delete")
        self.main_view.run_command("append", {"characters": content})
        self.main_view.set_read_only(True)
        self.main_view.sel().clear()
        # Move cursor to top
        self.main_view.show(0)

    def start_file_watcher(self):
        """Start watching Aider output file."""
        if self.file_watcher:
            self.file_watcher.stop()

        self.file_watcher = AiderFileWatcher(
            self.context,
            self.on_new_output
        )
        self.file_watcher.start()

    def on_new_output(self, new_content):
        """Callback when new output is detected."""
        self.output_panel.append_content(new_content)
        # If on output tab, refresh
        if self.current_tab == self.TAB_OUTPUT:
            self.render_current_tab()

    def refresh_all(self):
        """Refresh current view."""
        self.render_current_tab()

    def refresh_options(self):
        """Refresh if on options tab."""
        if self.current_tab == self.TAB_OPTIONS:
            self.render_current_tab()

    def refresh_files(self):
        """Refresh if on files tab."""
        if self.current_tab == self.TAB_FILES:
            self.render_current_tab()

    def close_all(self):
        """Close all Aider views and stop terminal."""
        if self.file_watcher:
            self.file_watcher.stop()

        self.terminal.stop()

        # Close main view
        if self.main_view and self.main_view.is_valid():
            self.main_view.close()

        # Close any other aider views
        for view in self.window.views():
            if view.settings().get("aider_savvy_view"):
                view.close()


class AiderSavvyCommand(sublime_plugin.WindowCommand):
    """Main command to open the Aider dashboard."""

    def run(self):
        instance = get_aider_instance(self.window)
        instance.setup_layout()


class AiderSavvyRefreshCommand(sublime_plugin.WindowCommand):
    """Refresh all Aider panels."""

    def run(self):
        if hasattr(self.window, 'aider_savvy'):
            self.window.aider_savvy.refresh_all()


class AiderSavvyCloseCommand(sublime_plugin.WindowCommand):
    """Close all Aider panels."""

    def run(self):
        if hasattr(self.window, 'aider_savvy'):
            self.window.aider_savvy.close_all()
            del self.window.aider_savvy


class AiderSavvyNextTabCommand(sublime_plugin.WindowCommand):
    """Switch to next tab."""

    def run(self):
        if hasattr(self.window, 'aider_savvy'):
            self.window.aider_savvy.next_tab()


class AiderSavvyPrevTabCommand(sublime_plugin.WindowCommand):
    """Switch to previous tab."""

    def run(self):
        if hasattr(self.window, 'aider_savvy'):
            self.window.aider_savvy.prev_tab()


class AiderSavvyGoToTabCommand(sublime_plugin.WindowCommand):
    """Go to specific tab."""

    def run(self, tab=0):
        if hasattr(self.window, 'aider_savvy'):
            self.window.aider_savvy.go_to_tab(tab)
