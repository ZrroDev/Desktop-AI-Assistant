# TODO

## Multiple conversations

Right now there is a single chat history (`generated/history.json`). Allow
several chats and choosing which one to continue from the menu.

Options:
- One file per chat, e.g. `generated/chats/<id>.json`, with a name or date to tell them apart.
- A single file with a structure keyed by chat id: `{"<id>": {"title": ..., "history": [...]}}`.

To decide: how a chat is created, listed and selected from the menu, and what
"Clear Chat History" does (clear the current chat or delete it).

## Save data in the user data folder when packaging

`HISTORY_FILE` is inside the project folder, which is fine while developing.
Once the app is installed or packaged (e.g. PyInstaller), the install folder
may be read-only and `__file__` may point to a temporary folder.

- Use `platformdirs.user_data_dir("DesktopAIAssistant")` (add `platformdirs` to `requirements.txt`).
- Only the `HISTORY_FILE` constant in `src/assistant.py` needs to change (see the `TODO` comment there).
- Fits with "Multiple conversations": the chats folder would go there too.
