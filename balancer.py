from itertools import combinations
import random


def balance(participants: dict[int, int]) -> tuple[list[int], list[int]]:
    if len(participants) != 10:
        raise ValueError('チーム分けには10人必要です。')
    users = list(participants)
    total = sum(participants.values())
    best_difference = float('inf')
    candidates = []
    for team in combinations(users, 5):
        # Keep one of each mirrored pair.
        if users[0] not in team:
            continue
        difference = abs(total - 2 * sum(participants[user] for user in team))
        if difference < best_difference:
            best_difference, candidates = difference, [team]
        elif difference == best_difference:
            candidates.append(team)
    first = list(random.choice(candidates))
    second = [user for user in users if user not in first]
    if random.choice((True, False)):
        first, second = second, first
    return first, second
