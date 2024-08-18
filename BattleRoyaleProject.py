from asyncio.windows_events import NULL
import random, csv
from operator import attrgetter


    
#Specify character profiles
class Player:
    def __init__(self, name, district):
        self.name = name
        self.living = True
        self.district = district
        self.kills = 0
    
    def __repr__(self):
        return f'{self.name}'
    
    
class BattleRoyale:
    def __init__(self):
        self.roster = []
        self.live_roster = []
        self.max_pop_size = 0
        self.locations = []
        self.victims = [1,2,3,4]
        self.ally_bool = input_check("Would you like alliances?")
        
    def make_roster(self, filename='BR.csv'):
        """Uses spreadsheet to import players, districts, and locations. Default is BR.csv"""
        with open(filename, 'r', newline='') as file:
            try:
                reader = csv.reader(file, delimiter=',')
                next(reader)
                rows = list(reader)
                self.roster = [Player(col[0], col[1]) for col in rows]
                self.locations = [col[2] for col in rows if col[2]]
            except Exception:
                print(f"Error {Exception} has occured. Please ensure that the spreadsheet is formatted correctly.")
                exit(1)
        print('Spreadhseet Detected...')
        self.max_pop_size = len(self.roster)
        print(f'Population of {self.max_pop_size} detected...')
        self.live_roster = self.roster.copy()
        if self.locations:
            print(f'Number of locations: {len(self.locations)}')
        print ("Beginning battle!!")
            
    def select_location(self):
        """Selects, displays, and then removes one of the locations, if any"""
        if self.locations: 
            place = random.choice(self.locations)
            print (f"-- {place} --")
            self.locations.remove(place)
        
    def round_loop(self,round_length=5):
        """Create a single round loop. Default length is 5 events"""
        self.select_location()
        for event in range(round_length):
            # Check the current size of the population
            pop_size = len(self.live_roster)
            
            # Check if there is already a winner
            if pop_size <= 1:
                    self.leaderboard()
                               
            # Determines the number of victims            
            kill_chance = [1, 0.5, (pop_size / self.max_pop_size), (pop_size / (2*self.max_pop_size))]
            num_killed = random.choices(self.victims, weights=(kill_chance), k=1)[0]
        
            # Failsafe in case the number of victims selected is more than the number of living contestants
            if num_killed >= pop_size:
                fight = random.sample(self.live_roster, k=(pop_size))
                num_killed = pop_size - 1
            else:
                fight = random.sample(self.live_roster, k=(num_killed + 1))
        
            # Determine the killer in the fight using the first person in it
            killer = fight[0]
            fight.remove(killer) 
            killer.kills += num_killed
        
            # Display death messages for each victim and destroy them
            for victim in fight: 
                print(f'{victim.name} [{victim.kills} kills]',end=', ')
                self.live_roster.remove(victim)
            print(f'died to {killer.name}')
            if event==(round_length-1):
                print(f'{len(self.live_roster)} remain.')
          
    def leaderboard(self):
        """Shows the winner and the top 10 kills"""
        winner = self.live_roster[0]
        print(f'{winner.name} from district {winner.district} wins with {winner.kills} kills!\n')
        print ("Kill Leaderboards: ")
        # Ranks the top 10 kill leaders
        top_killers = sorted(self.roster, key=attrgetter('kills'), reverse=True)[:10]
        for place, player in enumerate(top_killers, 1):
            print(f'{place}. {player.name} -- {player.kills} kill(s)!')

        exit(0)
            
def input_check(prompt="Default Prompt?"):
    """Validates user responses and converts to bool"""
    while True:
        setting = input(f'{prompt} (Y/N)\n').strip().upper()
        if setting not in ('Y','N'):
            print(f'Invalid input. Please try again.')
            continue
        else:
            return setting == "Y"
        
br = BattleRoyale()
br.make_roster()
while True:
    br.round_loop()
