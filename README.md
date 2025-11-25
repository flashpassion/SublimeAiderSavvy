# AiderSavvy - Sublime Text Plugin for Aider

Sublime Text 4 plugin that integrates [Aider](https://aider.chat/) with an interface inspired by GitSavvy.

## 🚀 Features

- **Interactive Dashboard** with Tab navigation
- **File Management** : easy addition/removal in the Aider context
- **Multiple Panels** : Status, Files, Output, Commands
- **Intuitive Keyboard Shortcuts**
- **File Autocompletion**
- **Custom Syntax Highlighting**
- **Multiple Modes** : code, ask, architect
- **Real-time Output** of Aider commands

## 📦 Installation

### Prerequisites

1. **Sublime Text 4** installed
2. **Aider** installed on Ubuntu :
   ```bash
   pip install aider-chat
   ```

### Plugin Installation

1. **Clone this repository in your package folder** :

```bash
$ cd ~/.config/sublime-text-3/Packages
$ git clone git@github.com:flashpassion/SublimeAiderSavvy.git AiderSavvy
```

## 🎯 Usage

### Open the Dashboard

- **Shortcut** : `Ctrl+Shift+A`
- **Menu** : Tools → AiderSavvy → Open Dashboard

### Dashboard Navigation

The dashboard has 4 views accessible with **Tab** :

1. **Status** : Overview, quick actions
2. **Files** : File management
3. **Output** : Output of Aider commands
4. **Commands** : List of available commands

### Keyboard Shortcuts in the Dashboard

| Key | Action |
|--------|--------|
| `Tab` | Switch to the next view |
| `a` | Add files |
| `r` | Add files as read-only |
| `d` | Remove files |
| `c` | Send a command/prompt |
| `/` | Execute an Aider command |
| `m` | Change mode |
| `o` | Show output |
| `q` | Close the dashboard |
| `F5` | Refresh |

### Quickly Add the Current File

**Menu** : Tools → AiderSavvy → Add Current File

Or from the context menu in any file.

### Available Modes

- **code** : Default mode, for modifying code
- **ask** : Question/answer mode without modification
- **architect** : Architect mode with 2 different models

Change mode with `m` in the dashboard.

### Available Aider Commands

The plugin supports all Aider commands :

- `/add` - Add files
- `/drop` - Remove files
- `/ask` - Ask questions
- `/code` - Request modifications
- `/commit` - Commit changes
- `/diff` - View the diff
- `/undo` - Undo the last commit
- `/map` - View the repo map
- `/tokens` - View token usage
- `/clear` - Clear history
- `/reset` - Reset everything

## ⚙️ Configuration

Edit settings : **Preferences → Package Settings → AiderSavvy → Settings**

Main options :

```json
{
    "aider_executable": "aider",
    "default_mode": "code",
    "model": "gpt-4",
    "auto_show_output": true,
    "auto_commit": false,
    "file_patterns": ["*.py", "*.js", "*.md"]
}