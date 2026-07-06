import json
import random as r
from numpy import add
from dataclasses import dataclass
import pygame
from copy import deepcopy

@dataclass
class Point:
    coords: tuple[int, int]
    color: pygame.Color
    visible: bool = True

pygame.init()
clock = pygame.time.Clock()
WINDOW_DIMENSIONS = (1280,720)
screen = pygame.display.set_mode(WINDOW_DIMENSIONS)
screen.fill('blue4')
pygame.display.set_caption("Ultimate Showdown")

island_image = pygame.image.load('resources/island.png').convert_alpha()
island_image = pygame.transform.scale_by(island_image, (.75, .75))
playfield = island_image.get_rect(center=(WINDOW_DIMENSIONS[0]/2,WINDOW_DIMENSIONS[1]/2))

world_cache = {}
TIMELINE = []

class playback_builder:
    PLAYFIELD_X_MIN = playfield.left 
    PLAYFIELD_X_MAX = playfield.right
    PLAYFIELD_Y_MIN = playfield.top
    PLAYFIELD_Y_MAX = playfield.bottom

    LOCATION_HITBOX_RADIUS = 8
    LOCATION_INHABIT_RADIUS = 50
    KEYFRAME_INTERVAL = 25
    DEFAULT_PLAYER_COLOR = pygame.Color("cornflowerblue")
    DEFAULT_LOCATION_COLOR = pygame.Color("maroon")
    CLOSED_LOCATION_COLOR = pygame.Color("gray30")


    def __init__(self):
        self.DISPATCH_TABLE = {
            "initialize": self._initialize,
            "keyframe": self._keyframe,
            "drop": self._drop,
            "fight": self._fight,
            "alliance_break": self._alliance_break,
            "alliance_form": self._alliance_form,
            "flavor": self._flavor,
            "move": self._move,
            "close_location": self._close_location,
            "winner":self._winner
        }
        self.cache = {}

    def build_timeline(self, filepath: str):
        '''Builds the list of instructions'''
        TIMELINE.clear()
        with open(filepath) as f:
            self.data = json.load(f)

        i = 1
        for entry in self.data:
            if i % self.KEYFRAME_INTERVAL == 0:
                self.DISPATCH_TABLE["keyframe"]()
            entry_action_type = entry.pop("action")
            entry_arguments = entry.copy()
            self.DISPATCH_TABLE[entry_action_type](entry_arguments)
            i += 1

    def _initialize(self, entry):
        '''Initializes all of the player names and ties them to objects.
        This is not sent to the timeline and is used locally to track coordinates.'''

        world_cache["players"] = {player:Point((0,0),self.DEFAULT_PLAYER_COLOR, False) for player in entry["players"]}
        world_cache["locations"] = {location:Point((0,0),self.DEFAULT_LOCATION_COLOR, False) for location in entry["locations"]}
        for location in world_cache["locations"].values():
            location.coords = (r.randrange(self.PLAYFIELD_X_MIN, self.PLAYFIELD_X_MAX), 
                              r.randrange(self.PLAYFIELD_Y_MIN, self.PLAYFIELD_Y_MAX))
            location.visible = True
        self.cache = world_cache.copy()

    def _keyframe(self):
        '''Saves a keyframe to the world cache.

        Keyframes tell the resolve function to rewrite the entire world cache to the one stored in the keyframe.'''

        TIMELINE.append({"action":"keyframe","data":deepcopy(self.cache)})

    def _drop(self, entry):
        '''Store instructions to drop players to their location'''

        location = entry["location"]
        location_data = self.cache["locations"][location]
        drop_players = entry["players"]
        destination_coords = []

        for player in drop_players:
            # Calculate how far outside the location the player will land, then add that to the location coordinates
            drop_distance = tuple(r.randrange(self.LOCATION_HITBOX_RADIUS, self.LOCATION_INHABIT_RADIUS)*r.choice((-1,1)) for _ in range(2))
            destination = tuple(add(drop_distance,location_data.coords))
            destination_coords.append(destination)

            # Update the cache to hold the new location of this player point
            self.cache["players"][player].coords = destination
            self.cache["players"][player].visible = True

        TIMELINE.append({"action":"drop", "data":[drop_players, destination_coords, location]})

    def _fight(self, entry):
        '''Store instruction to remove all fight victims.'''

        location = entry["location"]
        killer = entry["killer"]
        victims = [player for player in entry["victims"]]

        for player in victims:
            self.cache["players"][player].visible = False

        TIMELINE.append({"action":"fight", "data":{"location":location, "killer":killer, "victims":victims}})

    def _alliance_break(self, entry):
        '''Store instruction to change alliance members' colors to default.'''
        alliance = [name for name in entry["alliance_members"]]
        for player in alliance:
            self.cache["players"][player].color = self.DEFAULT_PLAYER_COLOR
        TIMELINE.append({"action":"alliance_break", "data":{"alliance":alliance}})
        
    def _alliance_form(self, entry):
        '''Store the players in the alliance and their new color.'''
        alliance = [name for name in entry["alliance_members"]]
        new_color = (r.randrange(0, 256), r.randrange(0, 256), r.randrange(0, 256))
        for player in alliance:
            self.cache["players"][player].color = new_color
        TIMELINE.append({"action":"alliance_form","data":{"alliance":alliance,"new_color":new_color}})
    
    def _flavor(self, entry):
        '''Store the player and their flavor text.'''
        player = entry["player"]
        flavor_text = entry["text"]
        TIMELINE.append({"action":"flavor", "data":{"player":player, "flavor_text":flavor_text}})

    def _move(self, entry):
        '''Store the player, their destination, and their new coordinates.'''
        player = entry["player"]
        destination = entry["destination"]
        drop_distance = tuple(r.randrange(self.LOCATION_HITBOX_RADIUS, self.LOCATION_INHABIT_RADIUS)*r.choice((-1,1)) for _ in range(2))
        destination_coords = tuple(add(drop_distance,self.cache["locations"][destination].coords))

        self.cache["players"][player].coords = destination_coords
        TIMELINE.append({"action":"move","data":{"destination":destination,"player":player,"destination_coords":destination_coords}})

    def _close_location(self, entry):
        '''Store instruction to change color on the closed location'''
        location = entry["location"]
        self.cache["locations"][location].color = self.CLOSED_LOCATION_COLOR

        TIMELINE.append({"action":"close_location","data":{"location":location}})

    
    def _winner(self, entry):
        '''Store instruction to celebrate the winner.'''
        player = entry["player"]

        TIMELINE.append({"action":"winner","data":{"player":player}})


class Playback:
    class _animation:
        ANIMATION_DISPATCH = {
            
        }

        def render(self):
            return
        
        def _draw_drop(self, players: list, coordinates: list, location):
            return
        
        def _draw_fight(self, location, killer, victims):
            return
        
        def _draw_alliance_break(self, alliance, color):
            return
        
        def _draw_alliance_form(self, alliance, color):
            return
        
        def _draw_flavor(self, location, flavor_text):
            return
        
        def _draw_move(self, player, destination):
            return
        
        def _draw_close_location(self, location):
            return
        
        def _draw_winner(self, player):
            return
        

builder = playback_builder()
builder.build_timeline("output.JSON")
print("Done")