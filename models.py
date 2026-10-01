from dataclasses import dataclass, field

RANKS = ('アイアン', 'ブロンズ', 'シルバー', 'ゴールド', 'プラチナ', 'ダイヤモンド', 'アセンダント', 'イモータル', 'レディアント')


@dataclass
class Match:
    channel_id: int
    owner_id: int
    participants: dict[int, int] = field(default_factory=dict)
    closed: bool = False
    demo: bool = False
