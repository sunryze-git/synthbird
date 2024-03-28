# Import Libraries
import pygame
import os
from random import randrange

# Initialize Pygame
pygame.init()

# Load the built-in pygame colors as a "class" with subvars
class MyColors(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
colors = MyColors(pygame.color.THECOLORS)

# Set some other system information with pygame stuffs
SIZE    = (800,600)
screen  = pygame.display.set_mode(size=SIZE)
clock   = pygame.time.Clock()
vector2 = pygame.Vector2
pygame.display.set_caption("SYNTHBIRD")
font    = pygame.font.Font('assets/fonts/font.ttf', 24)

# This rect exists to make sure I have an easier time with
# managing other rects to keep them visible to the user.
valid = pygame.rect.Rect((0,0), SIZE)

# Start Music Engine
pygame.mixer.init()
pygame.mixer.set_num_channels(3)

# Player object. This is considered the "bird" if you are
# comparing this to Flappy Bird. Here we call it a player.
class Player(pygame.sprite.Sprite):
    def __init__(self, pos: pygame.Vector2, size: pygame.Vector2, sfx: dict):
        pygame.sprite.Sprite.__init__(self)

        # Velocity and Acceleration vectors
        self.v = pygame.Vector2(0,0)
        self.a = pygame.Vector2(0,0.5)
        self.maxV = pygame.Vector2(0,50)

        # Rect visual information
        self.pos = pos
        self.size = size
        
        # Jump information
        self.jumptimeout = 400
        self.last_jumped = 0

        # Player attributes
        self.died = False
        self.play = False
        self.score = 0

        # Sprite Information
        # Every animation image from left to right is a 16x15 box
        # maximum is 128x15
        self.image_map = pygame.image.load('assets/sprites/fg/bird.bmp')
        self.fc = 0
        self.i_x = 0
        self.image_pre = pygame.Surface((16,15), pygame.SRCALPHA)
        self.image = pygame.Surface((16*4, 15*4), pygame.SRCALPHA)
        self.animate()

        # Create and center rectangle
        self.rect = self.image.get_rect()
        self.rect.center = pos

        # Sound Effects
        self.sfx = sfx

        self.jump_sfx  = pygame.mixer.Channel(0)
        self.death_sfx = pygame.mixer.Channel(1)
        self.score_sfx = pygame.mixer.Channel(2)

        self.jump_snd  = pygame.mixer.Sound(self.sfx["jump"])
        self.death_snd = pygame.mixer.Sound(self.sfx["death"])
        self.score_snd = pygame.mixer.Sound(self.sfx["score"])

    def update_pos(self):
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

        # Apply gravity if we are below maximum velocity
        if self.v.y < self.maxV.y:
            self.v += self.a
        
        # Handles jumping, prevents jumping from being too fast.
        if keys[pygame.K_SPACE] and (now-self.last_jumped > self.jumptimeout):
            if not self.death_sfx.get_busy() or not self.score_sfx.get_busy():
                self.jump_sfx.play(self.jump_snd)
            self.last_jumped = pygame.time.get_ticks()
            self.v.y = -9
        
        # Handles bottom-of-screen collision
        if not keys[pygame.K_SPACE] and self.rect.bottom >= valid.bottom:
            self.v.y = 0
            self.rect.clamp_ip(valid)

        self.rect.center += self.v

    def test_collision(self, pipes):
        # Test for collision with the bottom of the screen
        if self.rect.bottom >= valid.bottom:
            self.died = True
            self.play = False

        # Prevent the user from being able to go above the ceiling.
        if self.rect.top < valid.top:
            self.rect.clamp_ip(valid)
            self.v.y = 0

        # Test for collision for the pipes
        for pipe in pipes:
            if pygame.sprite.collide_mask(self, pipe):
                self.died = True
                self.play = False

        # Play death sound if we have died. Prevents overlapping sounds.
        if self.died:
            self.jump_sfx.stop()
            self.score_sfx.stop()
            self.death_sfx.play(self.death_snd)
    
    def update_score(self, pipes):
        # Check for every pipe on the screen if we are at the score threshold.
        for pipe in pipes:
            pipe_pos = pipe.pos
            if (pipe_pos.x-1) <= self.rect.centerx <= (pipe_pos.x+1):
                self.score += 1
                print(f"New Score: {self.score}")
                self.jump_sfx.stop()
                self.score_sfx.play(self.score_snd)

    def animate(self):
        self.fc += 1
        if self.fc % 10 == 0 or self.fc == 0:
            self.image_pre.fill((0,0,0,0))
            if self.i_x > 112:
                self.i_x = 0
            self.image_pre.blit(self.image_map, (0,0), (self.i_x,0, self.i_x+16,15))
            self.image = pygame.transform.scale(self.image_pre, (16*4, 15*4))
            self.image = pygame.transform.flip(self.image, True, False)
            self.i_x += 16

    def update(self):
        self.update_pos()
        self.test_collision(pipes_group)
        self.update_score(pipes_group)

# Pipe object
class Pipe(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        # Pipe Positional Information
        self.offset_V = pygame.Vector2(-3,0)
        self.pos = vector2(valid.right, randrange(200,500,50)) 

        # Hole Spacing between top/bottom pipe
        self.hW = randrange(240,320,20)

        # Variable to tell if we need to destroy this pipe
        self.destroy = False

        # Images
        self.img_dn = pygame.image.load('assets/sprites/fg/pipe_up.bmp')
        self.img_up = pygame.image.load('assets/sprites/fg/pipe_down.bmp')
        self.image  = self.combine_imgs()

        self.create_rect()

        # Create Collision Mask
        self.mask = pygame.mask.from_surface(self.image)

    def create_rect(self):
        self.rect = self.image.get_rect()
        self.rect.centery = self.pos.y
        self.rect.left = self.pos.x

    def combine_imgs(self):
        # This big function will combine the two images into one big image.
        combined_height = self.img_up.get_height() + self.hW + self.img_dn.get_height()
        combined_image  = pygame.Surface((self.img_up.get_width(),combined_height), pygame.SRCALPHA)
        combined_image.blit(self.img_up, (0,0))
        combined_image.blit(self.img_dn, (0,0+self.img_up.get_height() + self.hW))
        return combined_image

    def update(self):
        if not self.destroy:
            self.pos += self.offset_V
            self.rect.x = self.pos.x

            if self.rect.right < valid.left:
                self.destroy = True

# Text Object
class Text():
    # Init our text object
    def __init__(self, font: pygame.font.Font, color: tuple = (0,0,0), offset=int, content=None):
        # Text visual information
        self.color = color
        self.font = font
        self.content = content
        if self.content == None:
            self.content = self.score

        # Text positional information
        self.offset = offset
        self.pos = vector2(0,0)

        self.set_rect()

    def update_content(self, new_content):
        self.content = new_content
        self.set_rect()

    # Get the rect object for that text which lets us center it better later on
    def set_rect(self):
        ######### TODO: CENTER TEXT IN THE NEW TEXTBOX
        self.text = self.font.render(str(self.content), True, self.color)
        
        padding = 15

        self.text_rect = self.text.get_rect(center=self.offset)
        self.bg_rect = self.text.get_rect(center=self.offset)

        self.bg_rect.size = (self.bg_rect.size[0]+padding, self.bg_rect.size[1]+padding)
        self.bg_rect.center = self.text_rect.center

    def draw(self):
        pygame.draw.rect(screen, colors.black, self.bg_rect, 0, 5)
        screen.blit(self.text, self.text_rect)

# Sprite Management
player_group = pygame.sprite.Group()
pipes_group = pygame.sprite.Group()

# Reset pipes function, clears the sprite group
# and then recreates entire new sprites
def reset_pipes():
    global pipes_group
    pipes_group.empty()

    _p_xoffset = 100
    _p_buffer = 200
    for i in range(3):
        _p = Pipe()
        _p.pos.x += _p_xoffset
        pipes_group.add(_p)
        _p_xoffset += _p.image.get_width() + _p_buffer

# Reset player function, clears the player group
# and recreates the player sprite
def reset_player(sfx):
    global player_group
    player_group.empty()

    _p = Player(pos=vector2(SIZE[0]*.5,SIZE[1]*.5), size=vector2(50,100), sfx=sfx)
    player_group.add(_p)
    return _p

# Main function
def main():
    done = False

    # Load the assets we may use
    sfxdir = os.path.join(os.getcwd(), 'assets/sfx')
    sfx = {filename[:-4]: pygame.mixer.Sound(os.path.join(sfxdir, filename))
                               for filename in sorted(os.listdir(sfxdir))}
    
    player = reset_player(sfx)

    reset_pipes()

    death_text = Text(font=font, color=colors.white, offset=valid.center, content="You died! Press R to play again.")
    start_text = Text(font=font, color=colors.white, offset=(valid.centerx, valid.size[1]*.30), content="Press SPACE to begin! Don't hit the pipes!")
    score_text = Text(font=font, color=colors.white, offset=(valid.centerx, valid.size[1]*.10), content="0")

    sky = pygame.image.load('assets/sprites/bg/sky.bmp')
    sky_rect = sky.get_rect()
    sky_rect.center = valid.center

    buildings = pygame.image.load('assets/sprites/bg/buildings.bmp').convert_alpha()
    buildings_rect = buildings.get_rect()

    title = pygame.image.load('assets/sprites/fg/title.bmp')
    title = pygame.transform.scale(title, (title.get_width()*2, title.get_height()*2))
    t_rect = title.get_rect()
    t_rect.center = (valid.centerx, SIZE[1]*.125)

    # Start the main loop
    while not done:
        # Clear Screen
        screen.fill((0,0,0))

        # Sky Background
        screen.blit(sky, sky_rect)
        screen.blit(buildings, buildings_rect)

        # handle our events
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    player = reset_player(sfx)
                    reset_pipes()

                if event.key == pygame.K_SPACE:
                    if not player.play and not player.died:
                        player.play = True
                        player.v.y = -9

            if event.type == pygame.QUIT:
                done = True
        
        # Destroy and recreate the pipes when they leave the screen
        for pipe in pipes_group: 
            if pipe.destroy:
                pipes_group.remove(pipe)
                
                new_sprite = Pipe()
                pipes_group.add(new_sprite)

        # The actual "Game" if you haven't died yet
        if not player.died and player.play:
            # Send update request to the player and pipes
            player_group.update()
            pipes_group.update()

            # Update score text
            score_text.update_content(player.score)

        # Draw the pipes and player to the screen
        player_group.draw(screen)
        pipes_group.draw(screen)

        # Intro text if you have reset or haven't started the game yet
        if not player.died and not player.play:
            start_text.draw()
            screen.blit(title, t_rect)

        # Handle the building foreground movement illusion fun time thingymajiggy
        if not player.died:
            player.animate()
            if buildings_rect.right < valid.right:
                buildings_rect.x = 0
            buildings_rect.x -= 2
            
        # Score text in-game
        if not player.died and player.play:
            score_text.draw()

        # Death text
        if player.died:
            death_text.draw()

        # Update the display
        pygame.display.flip()

        # Limit FPS to 60
        clock.tick(60)

# Run our main loop if we are running as a script, not a module
if __name__ == "__main__":
    main()