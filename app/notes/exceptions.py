class NoteNotFoundError(Exception):
    def __init__(self, note_id: int) -> None:
        super().__init__(f"note {note_id} not found")
        self.note_id = note_id
