import time
from typing import Dict, Optional

class MatchStateManager:
    def __init__(self, match_id: str):
        self.match_id = match_id
        self.state = {
            'status': 'waiting',  # waiting, active, paused, half_time, finished
            'current_half': 1,
            'match_time': 0,
            'start_time': None,
            'pause_time': None,
            'score': [0, 0],
            'events': []
        }
        
    def start_match(self) -> bool:
        if self.state['status'] == 'waiting':
            self.state['status'] = 'active'
            self.state['start_time'] = time.time()
            return True
        return False
        
    def pause_match(self) -> bool:
        if self.state['status'] == 'active':
            self.state['status'] = 'paused'
            self.state['pause_time'] = time.time()
            return True
        return False
        
    def resume_match(self) -> bool:
        if self.state['status'] == 'paused':
            pause_duration = time.time() - self.state['pause_time']
            self.state['start_time'] += pause_duration
            self.state['status'] = 'active'
            self.state['pause_time'] = None
            return True
        return False
        
    def update_state(self) -> Optional[Dict]:
        if self.state['status'] != 'active':
            return None
            
        current_time = time.time()
        elapsed = current_time - self.state['start_time']
        self.state['match_time'] = elapsed
        
        # Check for half time (5 minutes)
        if self.state['current_half'] == 1 and elapsed >= 300:
            self.state['current_half'] = 2
            return {'type': 'half_time'}
            
        # Check for match end (10 minutes)
        if elapsed >= 600:
            self.state['status'] = 'finished'
            return {'type': 'match_end'}
            
        return None
        
    def get_state_summary(self) -> Dict:
        return {
            'status': self.state['status'],
            'current_half': self.state['current_half'],
            'match_time': self.state['match_time'],
            'score': self.state['score']
        }
        
    def get_full_state(self) -> Dict:
        return self.state
        
    def update_score(self, team: str, score: int):
        if team == 'home':
            self.state['score'][0] = score
        else:
            self.state['score'][1] = score
