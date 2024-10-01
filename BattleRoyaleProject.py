from asyncio.windows_events import NULL
import random, csv, math
import tomllib
from operator import attrgetter

# Creates config dictionary from config file
with open("config.toml", "rb") as file:
    config = tomllib.load(file)
    
#Specify character profiles
class Player:
    def __init__(self, name, district):
        self.name = name
        self.living = True
        self.district = district
        self.kills = 0
    
    def __repr__(self):
        return f'{self.name}'


#Create location objects to hold and manage players
class Location:
    def __init__(self, name):
        self.name = name
        self.populus = []
        self.num_population = NULL

    def populate(self, players):
        self.populus.extend(players)
        self.num_population = len(self.populus)

    def kick(self, victims: list):
        victims = set(victims)
        self.populus = [player for player in self.populus if player not in victims]
        self.num_population = len(self.populus)

    def __repr__(self):
        return f'{self.name}'
    
class BattleRoyale:
    def __init__(self):
        self.current_loc = NULL
        self.loc_ratio = 0
        self.killcount = range(1,config["max-fight-kills"]+1)
        self.travel_players = []
        
    def game_initialize(self, filename='BR.csv'):
        """Uses spreadsheet to import players, districts, and locations. Default is BR.csv"""
        try:
            # Opens and reads the spreadsheet
            with open(filename, 'r', newline='') as file:
                reader = csv.reader(file, delimiter=',')
                next(reader)
                rows = list(reader)
                print('Spreadsheet Detected...')

            # Constructs the playerbase and related data
            self.roster = [Player(col[0], col[1]) for col in rows]
            self.max_pop_size = len(self.roster)
            self.live_roster = self.roster.copy()
            print(f'Population of {self.max_pop_size} detected...')

            # Constructs the locations and related data
            self.locations = [Location(col[2]) for col in rows if col[2]]
            if config["drops"] and not self.locations:
                print("Why did you turn drops on with no locations, silly? \n Disabling drops...")
                config["drops"] = False

            if not self.locations:
                return

            self.loc_ratio = self.max_pop_size / len(self.locations)
            print(f'Number of locations: {len(self.locations)}')

            # Randomly assigns each player a list corresponding to a starting location, then mass populates each location
            if config["drops"]:
                random.shuffle(self.locations)
                location_assignments = [[] for location in self.locations]
                for player in self.roster:
                    location_assignments[random.randrange(len(self.locations))].append(player)
                for location, assignment in zip(self.locations, location_assignments):
                    location.populate(assignment)

        except Exception as e:
            print(f"Error, {str(e)} has occured. Please ensure that the spreadsheet is formatted correctly.")
            exit(1)
             
    def select_location(self):
        """Selects, displays, and then removes one of the locations, if any"""

        # Check if drops are on and that a location was selected
        if config["drops"]:
            while True:
                if not self.current_loc:
                    self._new_location()

                # Check to ensure an empty location is not selected for battle
                if self.current_loc.num_population == 0:
                    print("Looks like nobody is here...\nOh well...")
                    self.locations.remove(self.current_loc)
                    self.current_loc = NULL;
                    continue

                # Check if there are no longer players in the area
                if self.current_loc.num_population == 1:
                    self._transfer_players()
                    self._new_location()

                break
                
        # Big scary formula that evenly "distributes" players to locations when drops are off
        elif len(self.live_roster) <= math.floor(self.loc_ratio * len(self.locations)):
            self._new_location()

    def _new_location(self):
        '''Create and announce a new location'''
        print(f'{len(self.live_roster)} remain.')
        self.current_loc = random.choice(self.locations)
        self.locations.remove(self.current_loc)

        # Check to see if this is the last location for a final showdown
        if len(self.locations) == 0:
            self.current_loc.populate(self.travel_players)
            print(f"Everyone makes their way to the final showdown \n...")
        if config["drops"]:
            print (f"-- {self.current_loc}: Population {self.current_loc.num_population} --")
        else:
            print (f"-- {self.current_loc} --")

    def _transfer_players(self):
        '''Store players left in previous location for use in the last location'''
        transfer = self.current_loc.populus
        self.current_loc.kick(transfer)
        self.travel_players.extend(transfer)

    def kill(self, dead: list):
        """Kills a player or group of players by removing them from the roster and location"""
        # Creates a set of the dead to easily remove them, then reconstructs the living roster.
        dead = set(dead)
        self.live_roster = [player for player in self.live_roster if player not in dead]
        if config["drops"]:
            self.current_loc.kick(dead)

    def fight_logic(self, num_killed):
        """Determines who participates in a fight"""
        # Determine where to pull participating players from
        if config["drops"]:
            pull_from = self.current_loc.populus
        else:
            pull_from = self.live_roster
        num_fight = len(pull_from)

        # Check to ensure there are not too many players, then choose players for the fight
        if num_killed >= num_fight:
            fight = pull_from.copy()
            num_killed = num_fight - 1
        else:
            fight = random.sample(pull_from, k=(num_killed + 1))
        
        # Determine the killer in the fight using the first person in it after a shuffle
        random.shuffle(fight)
        killer = fight[0]
        fight.remove(killer)
        killer.kills += num_killed
        return killer, fight

    def griddy(self):
        """At the end of each event, one random player hits the griddy in epic mode. Thanks for the feature request Jeffrey."""
        griddier = random.choice(self.live_roster)
        self.live_roster.remove(griddier)
        if random.randint(1,100) == 100:
            for player in self.live_roster:
                    print(f'{player.name} [{player.kills} kills]',end=', ')
                    griddier.kills+=1
            print(f' died to {griddier} when they hit the griddy!')
            self.live_roster[0] = griddier
            self.leaderboard()
        else:
            print(f'{griddier} hit the griddy and died.')
            
    def round_loop(self):
        """Create a single round loop."""
        # Check the current size of the population
        pop_size = len(self.live_roster)
        
        # Check if there is already a winner
        if pop_size <= 1:
                self.leaderboard()

        # Determine the location of the battlefield and if it has changed
        if len(self.locations):
            self.select_location()
                               
        # Determines the number of victims and runs the fight script      
        kill_chance = [1, 0.5, (pop_size / self.max_pop_size), (pop_size / (2*self.max_pop_size))]
        num_killed = random.choices(self.killcount, weights=(kill_chance), k=1)[0]
        killer, fight = self.fight_logic(num_killed)
        
        # Display death messages for each victim and destroy them
        for victim in fight: 
            print(f'{victim.name} [{victim.kills} kills]',end=', ')
        print(f'died to {killer.name}')
        self.kill(fight)

        # Griddy
        if config["epic-mode"]:
            self.griddy()
          
    def leaderboard(self):
        """Shows the winner and the top 10 kills"""
        # Epic mode failsafe
        if config["epic-mode"] and not self.live_roster:
            print("That was so epic. No one wins. Epicsauce")
        else:
            winner = self.live_roster[0]
            print(f'{winner.name} from district {winner.district} wins with {winner.kills} kills!\n')
        print ("Kill Leaderboards: ")
        # Ranks the top 10 kill leaders
        top_killers = sorted(self.roster, key=attrgetter('kills'), reverse=True)[:10]
        for place, player in enumerate(top_killers, 1):
            print(f'{place}. {player.name} -- {player.kills} kill(s)!')

        exit(0)
            
br = BattleRoyale()
br.game_initialize()
while True:
    br.round_loop()
