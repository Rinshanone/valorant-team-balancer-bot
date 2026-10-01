from models import Match


class MatchService:
    def __init__(self):
        self.active: dict[int, Match] = {}

    def create(self, channel_id: int, owner_id: int) -> Match:
        if channel_id in self.active:
            raise ValueError('このチャンネルではすでに募集中です。')
        match = Match(channel_id, owner_id)
        self.active[channel_id] = match
        return match

    def join(self, match: Match, user_id: int, rank: int):
        if user_id in match.participants:
            raise ValueError('すでに参加しています。')
        if len(match.participants) >= 10:
            raise ValueError('定員の10人に達しています。')
        match.participants[user_id] = rank

    def leave(self, match: Match, user_id: int):
        if user_id not in match.participants:
            raise ValueError('まだ参加していません。')
        del match.participants[user_id]

    def close(self, match: Match):
        match.closed = True
        if self.active.get(match.channel_id) is match:
            del self.active[match.channel_id]
