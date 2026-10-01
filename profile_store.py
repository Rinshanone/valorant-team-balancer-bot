import json
import os
from pathlib import Path


class ProfileStore:
    def __init__(self, path: Path):
        self.path = path
        self.profiles = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        if not isinstance(self.profiles, dict) or any(
            not isinstance(key, str) or not key.isdigit() or type(value) is not int or not 1 <= value <= 9
            for key, value in self.profiles.items()
        ):
            raise ValueError('profiles.json のデータ形式が不正です。')

    def get(self, user_id: int) -> int | None:
        return self.profiles.get(str(user_id))

    def set(self, user_id: int, rank: int):
        # No await: writes are serialized on the bot event loop.
        updated = {**self.profiles, str(user_id): rank}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(updated, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, self.path)
        self.profiles = updated
