import json, collections
import random as r
from dataclasses import dataclass
from functools import partial
import simulation

@dataclass
class PointData:
    name: str
    cords: tuple[int, int]
    color: tuple[int, int, int]
    is_displayed: bool = True

    def __hash__(self):
        return hash(self.name)


class simulation_instructions:
    PLAYFIELD_X_MIN = simulation.playfield.left 
    PLAYFIELD_X_MAX = simulation.playfield.right
    PLAYFIELD_Y_MIN = simulation.playfield.top
    PLAYFIELD_Y_MAX = simulation.playfield.bottom

    INHABIT_RADIUS = 50
    DEFAULT_PLAYER_COLOR = (100, 149, 237)
    DEFAULT_LOCATION_COLOR = (176, 48, 96)


    def __init__(self, filepath: str):
        self.dispatch_table = {
            "initialize": self.handler_initialize,
            "drop": self.handler_drop,
            "fight": self.handler_fight,
            "alliance_break": self.handler_alliance_break,
            "alliance_form": self.handler_alliance_form,
            "flavor": self.handler_flavor,
            "move": self.handler_move,
            "close_location": self.handler_close_location,
            "winner":self.handler_winner
        }
        self.instructions = collections.deque()
        with open(filepath) as f:
            self.data = json.load(f)
        for entry in self.data:
            handler = self.dispatch_table[entry.pop("action")]
            command = handler(entry)
            self.instructions.append(command)

    def handler_initialize(self, entry):
        '''Initializes all of the player names and ties them to objects'''
        self.players = {name: PointData(name,cords=(0,0),color=self.DEFAULT_PLAYER_COLOR) for name in entry["players"]}
        self.locations = {name: PointData(name,cords=(0,0), color=self.DEFAULT_LOCATION_COLOR) for name in entry["locations"]}
        for location in self.locations.values():
            location.cords = (r.randrange(self.PLAYFIELD_X_MIN, self.PLAYFIELD_X_MAX), 
                              r.randrange(self.PLAYFIELD_Y_MIN, self.PLAYFIELD_Y_MAX))
        return partial(simulation.initialize)

    def handler_drop(self, entry):
        '''Returns the coordinates of a player and their location (destination).'''
        player = self.players[entry["player"]]
        location = self.locations[entry["destination"]]
        player.cords = (location.cords[0] + r.randrange(-self.INHABIT_RADIUS, self.INHABIT_RADIUS),
                        location.cords[1] + r.randrange(-self.INHABIT_RADIUS, self.INHABIT_RADIUS))
        return partial(simulation.draw_drop, player)

    def handler_fight(self, entry):
        '''Returns the coordinates of both players fighting, and which one wins.'''
        killer = self.players[entry["killer"]]
        victims = tuple(self.players[player] for player in entry["victims"])
        location = self.locations[entry["location"]]
        return partial(simulation.draw_fight, killer, victims)

    def handler_alliance_break(self, entry):
        '''Returns the coordinates of an alliance and changes colors to default.'''
        alliance = [self.players[name] for name in entry["alliance_members"]]
        for player in alliance:
            player.color = self.DEFAULT_PLAYER_COLOR
        return partial(simulation.draw_alliance_break, alliance)

    def handler_alliance_form(self, entry):
        '''Returns the coordinates of an alliance and changes colors to new random color.'''
        alliance = [self.players[name] for name in entry["alliance_members"]]
        for player in alliance:
            player.color = (r.randrange(0, 256), r.randrange(0, 256), r.randrange(0, 256))
        return partial(simulation.draw_alliance_form, alliance)
    
    def handler_flavor(self, entry):
        '''Returns the player and flavor text.'''
        player = self.players[entry["player"]]
        flavor_text = entry["text"]
        return partial(simulation.draw_flavor, player, flavor_text)

    def handler_move(self, entry):
        '''Returns the player's current coordinates and their destination coordinates.'''
        player = self.players[entry["player"]]
        location = self.locations[entry["destination"]]
        destination_cords = (location.cords[0] + r.randrange(-self.INHABIT_RADIUS, self.INHABIT_RADIUS),
                              location.cords[1] + r.randrange(-self.INHABIT_RADIUS, self.INHABIT_RADIUS))
        return partial(simulation.draw_move, player, destination_cords)

    def handler_close_location(self, entry):
        '''Removes location from dictionary and stops drawing it.'''
        location = self.locations.pop(entry["location"])
        return partial(simulation.close_location, location)
    
    def handler_winner(self, entry):
        return

test = simulation_instructions('output.json')

print(len(test.instructions))