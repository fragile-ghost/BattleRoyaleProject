import random, csv, math
import tomllib
from operator import attrgetter

from _pytest.logging import _LiveLoggingNullHandler

# TO ADD - Variation of alliances with marriage instead?
# Flavor "turned gay"
    
#Specify character profiles
class Player:

    def __init__(self, name, district):
        self.name = name
        self.kills = 0
        self.district = district
    
    def __repr__(self):
        return f'{self.name}'

#Create location objects to hold and manage players
class Location:

    def __init__(self, name):
        self.name = name
        self.populus = []
        self.num_population = None

    def __repr__(self):
        return f'{self.name}'

    def leave(self, victims: list[Player]):
        """Removes a list of players from the location"""
        victims = set(victims)
        self.populus = [player for player in self.populus if player not in victims]
        self.num_population = len(self.populus)

    def populate(self, players: list[Player]):
        """Adds a list of players to the location"""
        self.populus.extend(players)
        self.num_population = len(self.populus)

class Round:

    def __init__(self):
        self.content = ""
        self.deaths = 0
        self.location = None

    def __init__(self, content: str, deaths, location: Location):
        self.content = content
        self.deaths = deaths
        self.location = location



    
class BattleRoyale:
    loc_ratio = 0 ## Ratio of max players to locations, used when drops is off
    victim_range = range(1,config["max-fight-kills"]+1)
    kill_chance = [(1/(percent**2)) for percent in victim_range]
    travel_players = []

    def __init__(self, filename, config_file):
        """Uses spreadsheet to import players, districts, and locations."""
        # Creates config dictionary from config file
        with open(config_file, "rb") as file:
            self.config = tomllib.load(file)
        try:
            # Opens and reads the spreadsheet
            with open(filename, 'r', newline='') as file:
                reader = csv.reader(file, delimiter=',')
                next(reader)
                rows = (reader,)
                print('Spreadsheet Detected...')

            # Constructs the playerbase and related data
            self.roster = tuple(Player(col[0], col[1]) for col in rows)
            self.MAX_POP_SIZE = len(self.roster)
            self.live_roster = list(self.roster)            
            print(f'Population of {self.MAX_POP_SIZE} detected...')

            # Constructs the locations and related data
            self.locations = [Location(col[2]) for col in rows if col[2]]
            if self.config["drops"] and not self.locations:
                print("Why did you turn drops on with no locations, silly? \n Disabling drops...")
                self.config["drops"] = False

            # Constructs the list of emotes
            self.emotes = [col[3] for col in rows if col[3]]

            if not self.locations:
                return

            self.loc_ratio = self.MAX_POP_SIZE / len(self.locations)
            print(f'Number of locations: {len(self.locations)}')

            # Randomly assigns each player a list corresponding to a starting location, then mass populates each location
            random.shuffle(self.locations)
            random.shuffle(self.live_roster)
            if self.config["drops"]:
                start = 0
                stop = None
                for i in range(len(self.locations)):
                    stop = random.randrange(start,self.MAX_POP_SIZE)
                    self.locations[i].populate(self.live_roster[start:stop])
                    start = stop


            # if self.config["drops"]:
            #     random.shuffle(self.locations)
            #     random.shuffle(self.live_roster)
            #     index = [0]
            #     while len(index) < len(self.locations):
            #         r = random.randrange(1,len(self.locations))
            #         if r not in index:
            #             index.append(r)
            #         else:
            #             continue
            #     index.sort()
            #     # for location, i in self.locations:
            #     #     location.populate(self.live_roster[index[i]:index[i+1]])
            #     location_assignments = [[] for location in self.locations]
            #     for player in self.roster:
            #         location_assignments[random.randrange(len(self.locations))].append(player)
            #     for location, assignment in zip(self.locations, location_assignments):
            #         location.populate(assignment)

        except Exception as e:
            print(f"Error, {str(e)} has occured. Please ensure that all files are formatted correctly.")
            exit(1)
             
    def select_location(self):
        """Selects, displays, and then removes one of the locations, if any"""

        # Check if drops are on and that a location was selected
        if config["drops"]:
            while True:
                if not self.current_loc:
                    self.new_location()

                # Check to ensure an empty location is not selected for battle
                if self.current_loc.num_population == 0:
                    self.content += ("Looks like nobody is here...\nOh well...")
                    self.locations.remove(self.current_loc)
                    self.current_loc = None;
                    continue

                # Check if there are no longer players in the area
                if self.current_loc.num_population == 1:
                    self._transfer_players()
                    self.new_location()

                break
                
        # Big scary formula that evenly "distributes" players to locations when drops are off
        elif len(self.live_roster) <= math.floor(self.loc_ratio * len(self.locations)):
            self.new_location()

    def new_location(self):
        '''Create and announce a new location'''
        self.content += (f'{len(self.live_roster)} remain.\n')
        # if (len(self.locations) < self.MAX_POP_SIZE/self.loc_ratio):
        #     self._story()
        self.current_loc = random.choice(self.locations)
        self.locations.remove(self.current_loc)

        # Check to see if this is the last location for a final showdown
        if config["drops"]:
            if len(self.locations) == 0:
                self.current_loc.populate(self.travel_players)
                self.content += (f"Everyone makes their way to the final showdown \n...")
            self.content += (f"-- {self.current_loc}: Population {self.current_loc.num_population} --")
        else:
            self.content += (f"-- {self.current_loc} --\n")

    def _transfer_players(self):
        '''Store players left in previous location for use in the last location'''
        transfer = self.current_loc.populus
        self.current_loc.leave(transfer)
        self.travel_players.extend(transfer)

    def _remove_dead(self, dead: list):
        """Kills a player or group of players by removing them from the roster and location"""
        # Creates a set of the dead to easily remove them, then reconstructs the living roster.
        dead = set(dead)
        self.live_roster = [player for player in self.live_roster if player not in dead]
        if config["drops"]:
            self.current_loc.leave(dead)

    def generate_fight(self, num_killed):
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

    def emote(self):
        """At the end of each event, one random player hits the griddy in epic mode. Thanks for the feature request Jeffrey."""
        # Chance of emoting decreases as the number of players do.
        if random.randrange(self.MAX_POP_SIZE) > len(self.live_roster):
            return
        griddier = random.choice(self.live_roster)
        self.live_roster.remove(griddier)
        if random.randint(1,100) == 100:
            for player in self.live_roster:
                    self.content += (f'{player.name} [{player.kills} kills],')
                    griddier.kills+=1
            self.content += (f' died to {griddier} when they hit the {random.choice(self.emotes)}!')
            self.live_roster[0] = griddier
            self.leaderboard()
        else:
            self.content += (f'{griddier} hit the {random.choice(self.emotes)} and died.')
            
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
        num_killed = random.choices(self.victim_range, weights=(self.kill_chance), k=1)[0]
        killer, fight = self.generate_fight(num_killed)
        
        # Display death messages for each victim and destroy them
        s = "killed "
        for victim in fight:
            ## \033[1;36;40m for blue
            ## \033[1;37;40m for white
            s+= f'{victim.name} [{victim.kills} kill(s)]'
            if fight.index(victim) == len(fight) - 1:
                s+= "."
            elif fight.index(victim) == len(fight) - 2:
                s+= " and "
            else:
                s+=", "
                ## \033[1;31;40m for red
                ## \033[1;37;40m for white
        self.content += (f'{killer.name} {s}\n')
        self._remove_dead(fight)
        # Griddy
        if config["epic-mode"]:
            self.emote()
          
    def leaderboard(self):
        """Shows the winner and the top 10 kills"""
        # Epic mode failsafe
        if not self.live_roster:
            self.content += ("No one wins...")
        else:
            winner = self.live_roster[0]
            self.content += (f'{winner.name} from district {winner.district} wins with {winner.kills} kills!')
            if config["epic-mode"]:
                self.content += (f'{winner} hits the {random.choice(self.emotes)} in victory')
        self._story()
        print ("\nKill Leaderboards: ")
        # Ranks the top 10 kill leaders
        top_killers = sorted(self.roster, key=attrgetter('kills'), reverse=True)[:10]
        for place, player in enumerate(top_killers, 1):
            print(f'{place}. {player.name} -- {player.kills} kill(s)!')
       
        exit(0)
            
br = BattleRoyale()
br.game_initialize()
while True:
    br.round_loop()
