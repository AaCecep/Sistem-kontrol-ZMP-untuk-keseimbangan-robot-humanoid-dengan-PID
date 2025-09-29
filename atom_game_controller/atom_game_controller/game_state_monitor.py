class GameStateMonitor(Node):
    """Monitor and display game state information"""
    
    def __init__(self):
        super().__init__('robocup_game_state_monitor')
        
        self.declare_parameter('display_interval', 5.0)
        display_interval = self.get_parameter('display_interval').value
        
        # Subscriber
        self.game_state_sub = self.create_subscription(
            GameControlData,
            'robocup/game_state',
            self.game_state_callback,
            10
        )
        
        # Timer for periodic display
        self.display_timer = self.create_timer(display_interval, self.display_status)
        
        self.last_game_data = None
        self.get_logger().info('Game State Monitor started')
    
    def game_state_callback(self, msg: GameControlData):
        """Handle incoming game state data"""
        self.last_game_data = msg
        
        # Log important state changes
        state_name = STATE_NAMES.get(msg.state, f"UNKNOWN({msg.state})")
        
        self.get_logger().info(
            f'Game Update: {state_name}, '
            f'Time: {msg.secs_remaining}s, '
            f'Score: {msg.teams[0].score}-{msg.teams[1].score}'
        )
        
        # Check for penalties
        for team_idx, team in enumerate(msg.teams):
            for player_idx, player in enumerate(team.players):
                if player.penalty != PENALTY_NONE:
                    penalty_name = PENALTY_NAMES.get(player.penalty, f"PENALTY({player.penalty})")
                    self.get_logger().warn(
                        f'Team {team.team_number} Player {player_idx + 1}: '
                        f'{penalty_name} ({player.secs_till_unpenalised}s remaining)'
                    )
    
    def display_status(self):
        """Periodically display game status"""
        if self.last_game_data:
            data = self.last_game_data
            state_name = STATE_NAMES.get(data.state, f"UNKNOWN({data.state})")
            
            self.get_logger().info(
                f'Status: {state_name} | '
                f'Time: {data.secs_remaining}s | '
                f'Half: {"1st" if data.first_half else "2nd"} | '
                f'Score: Team {data.teams[0].team_number}({data.teams[0].score}) - '
                f'Team {data.teams[1].team_number}({data.teams[1].score})'
            )