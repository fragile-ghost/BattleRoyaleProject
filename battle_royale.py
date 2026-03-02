from dataclasses import dataclass, field
from typing import Callable
from operator import attrgetter
import random, csv
import tomllib
    
@dataclass
class Player:
    name: str
    submitted_by: str
    alliance = None
    kills: int = 0
    alive: bool = True

    def __hash__(self):
        return hash(self.name)

@dataclass
class Location:
    name: str
    population: set = field(default_factory=set)

@dataclass
class Event:
    name: str
    behavior: Callable
    weight: int

    def execute(self, location: Location):
        self.behavior(location)

class BattleRoyale:
    # All players are stored to the base location
    def __init__(self):
        """Uses spreadsheet to import players, districts, and locations. Then, populates each location."""

        self.base_location = Location("base")
        
        # Ensure all files can be opened
        try:
            with open("config.toml", 'rb') as config_file:
                self.config = tomllib.load(config_file)
            print("Config detected...")

            with open(self.config["file-addresses"]["br-path"], 'r', newline='') as file:
                br_reader = csv.reader(file, delimiter=',')
                next(br_reader)
                self.base_location.population = set([Player(row[0], row[1]) for row in br_reader])
            print('Spreadsheet Detected...')

            with open(self.config["file-addresses"]["extras-path"], 'r', newline='') as file2:
                extras_reader = csv.reader(file2)
                next(extras_reader)
                self.locations = [Location(row[0]) for row in extras_reader]
                if self.config["settings"]["emotes"]:
                    self.emotes = [row[2] for row in extras_reader]
                print("Extras detected..")
            
            print("All files found.")
        except FileNotFoundError:
            print("The file path(s) provided was incorrect. Be sure to provide paths in the config file," \
            "and that the config is in the same folder as the program.")

        self.MAX_FIGHT_KILLS = self.config["settings"]["max-fight-kills"]
        self.MAX_ALLIANCE_SIZE = self.config["settings"]["max-alliance-size"]
        self.MAX_MOVEMENTS = self.config["settings"]["max-movements"]
        self.BAN_ALLIANCES_AT = self.config["settings"]["ban-alliances-at"]
        self.can_ally = True
        self.output = ""
        self.round = 0
        self.num_alliances = 1
        self._alliance_table = {
        }
        self.EVENT_LIST = self._generate_events()
        self.event_weights = [event.weight for event in self.EVENT_LIST]
        
        # Constructs the playerbase and related data
        self.living_players = len(self.base_location.population)
        print(f'Population of {self.living_players} generated.')
        print(f'{len(self.locations)} locations generated.')
        self._populate_locations()
    
    def play(self, rounds = None):
        """Plays the specified number of rounds (default runs until a victor is declared).
        Round data is saved to a string for output."""

        if not rounds:
            while (self.living_players > 1):
                if self.living_players <= self.BAN_ALLIANCES_AT and self.can_ally:
                    self.can_ally = False
                    self.event_weights[1] = 0
                for location in self.locations:
                    event = random.choices(self.EVENT_LIST, weights=self.event_weights, k=1)[0]
                    event.execute(location)
                if len(self.locations) > 1:
                    self._movement_step()
        
        # elif rounds:
        #     for i in range(rounds):
        #         for location in self.locations:
        #             event = random.choices(self.EVENT_LIST, weights=self.EVENT_WEIGHTS, k=1)[0]
        #             event.execute(location)
        #         if len(self.locations) > 1:
        #             self._movement_step()
        #         if self.living_players == 1:
        #             break

        if self.living_players == 1:
            players = list(self.base_location.population)
            for player in players:
                if player.alive:
                    print(f'{player} has won the game!')
                    break
        # self._leaderboard(players)

    def _generate_events(self):
        events = []
        events.append(Event("fight",self._event_fight, weight=5))
        events.append(Event("alliance",self._event_alliance, weight=2))
        events.append(Event("flavor",self._event_flavor, weight=1))
        return events
    
    def _populate_locations(self):
        for player in self.base_location.population:
            location = random.choice(self.locations)
            location.population.add(player)
    
    def _event_fight(self, location):
        # Choose some number of players from that location
        output = ""
        if self.MAX_FIGHT_KILLS >= len(location.population):
            fight_kills = random.randint(1, len(location.population)-1)
        else:
            fight_kills = random.randint(1, self.MAX_FIGHT_KILLS)
        fight_players = random.sample(list(location.population), k=fight_kills+1)

        # Fight logic
        killer = random.choice(fight_players)
        betrayal = True
        output += f'{killer.name} kills '
        if killer.alliance and self.can_ally:
            killer_current_alliance = self._alliance_table[killer.alliance]
        else:
            killer_current_alliance = []
        for player in fight_players:
            if player is not killer:
                if player in killer_current_alliance and betrayal:
                    output+= f'and betrays their ALLY {player.name}, '
                    self._alliance_table[killer.alliance].remove(killer)
                    killer.alliance = None
                if player not in killer_current_alliance:
                    if betrayal:
                        betrayal = False 
                    output += f'{player.name}, '
                else:
                    continue
                player.alive = False
                self.living_players -= 1
                killer.kills += 1
                location.population.remove(player)

        if output == f'{killer.name} kills ':
            pass
        print(output)
    
    def _event_alliance(self, location):
        # Remove dead players from alliances
        for id, alliance in self._alliance_table.items():
            for ally in alliance:
                if not ally.alive:
                    ally.alliance = None
                    alliance.remove(ally)
            if len(alliance) == 1:
                alliance[0].alliance = None
                alliance.pop()
        self._alliance_table = {k: v for k, v in self._alliance_table.items() if v}

        output = ""

        # Determine if an alliance will form or break
        alliance_break = random.randint(0,3)
        num_population = len(location.population)

        # Alliance logic
        if alliance_break == 3 and len(self._alliance_table) > 0:
            output += "The alliance between "
            broken_id = random.choice(list(self._alliance_table.keys()))
            for player in self._alliance_table[broken_id]:
                player.alliance = None
                output+= f'{player.name}, '
            self._alliance_table.pop(broken_id)
            output += "has ended!!"
        elif num_population > 1:
            if self.MAX_ALLIANCE_SIZE > num_population:
                alliance_size = random.randint(2,num_population)
            else:
                alliance_size = random.randint(2, self.MAX_ALLIANCE_SIZE)
            new_alliance = random.sample(list(location.population), k=alliance_size)
            output+="An alliance between "
            for player in new_alliance:
                if player.alliance:
                    self._alliance_table[player.alliance].remove(player)
                output += f'{player.name}, '
                player.alliance = self.num_alliances
            self._alliance_table[self.num_alliances] = new_alliance
            output += "has formed!!"
            self.num_alliances+=1
        
        print(output)
    
    def _event_flavor(self, location):
        player = random.choice(list(location.population))
        print(player.name + " flavor text.")

    def _movement_step(self):
        for location in self.locations:
            if len(location.population) > 1:
                population_list = list(location.population)
                if self.MAX_MOVEMENTS > len(location.population):
                    num_movements = random.randint(0,len(location.population))
                else:
                    num_movements = random.randint(1,self.MAX_MOVEMENTS)
                moving_players = random.sample(population_list, k=num_movements)
                for player in moving_players:
                    location.population.remove(player)
                    new_location = location
                    while new_location == location:
                        new_location = random.choice(self.locations)
                    new_location.population.add(player)
            if len(location.population) == 1:
                    player = location.population.pop()
                    self.locations.remove(location)
                    print(f'{location} has been removed.')
                    random.choice(self.locations).population.add(player)
            elif len(location.population) < 1:
                self.locations.remove(location)
                print(f'{location} has been removed.')                

    def _leaderboard(self, players: list):
        players.sort(key=attrgetter("kills"), reverse=True)
        for index, player in enumerate(players):
            print(f'{index+1} -- {player.name}: {player.kills} kills.')