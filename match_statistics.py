from typing import Dict
import time

class MatchStatistics:
    def __init__(self, match_id: str):
        self.match_id = match_id
        self.stats = {
            'home': {
                'shots': 0,
                'shots_on_target': 0,
                'possession': 0,
                'passes': 0,
                'fouls': 0
            },
            'away': {
                'shots': 0,
                'shots_on_target': 0,
                'possession': 0,
                'passes': 0,
                'fouls': 0
            }
        }
        self.possession_timer = {'home': 0, 'away': 0}
        self.last_possession = None
        self.start_time = time.time()

    def update_possession(self, team: str):
        current_time = time.time()
        if self.last_possession:
            self.possession_timer[self.last_possession] += (current_time - self.start_time)
        self.last_possession = team
        self.start_time = current_time

    def calculate_possession(self) -> Dict[str, float]:
        total_time = sum(self.possession_timer.values())
        if total_time == 0:
            return {'home': 50, 'away': 50}
        return {
            'home': round((self.possession_timer['home'] / total_time) * 100, 1),
            'away': round((self.possession_timer['away'] / total_time) * 100, 1)
        }

    def update_stat(self, team: str, stat_type: str, value: int = 1):
        if team in self.stats and stat_type in self.stats[team]:
            self.stats[team][stat_type] += value

    def get_stats(self) -> Dict:
        stats = self.stats.copy()
        stats['possession'] = self.calculate_possession()
        return stats