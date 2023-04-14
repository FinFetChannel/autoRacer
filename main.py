import asyncio
import pygame as pg
import random
import os

PATH = os.path.abspath('.')+'/'
PLATFORM = 'windows'
if 'ANDROID_ARGUMENT' in os.environ:
    PLATFORM = 'android'
elif __import__("sys").platform == "emscripten":
    PLATFORM = 'web'
    from platform import window

async def main():
    pg.mixer.init()    
    size = (360, 640)
    if PLATFORM == 'android':# or PLATFORM == 'windows':
        screen = pg.display.set_mode(size, pg.SCALED) # |pg.FULLSCREEN)
    else:
        screen = pg.display.set_mode(size)

    background = []
    for i in range(4):
        background.append(pg.image.load(PATH+'sprites/road'+str(i)+'.png').convert())

    pause_button = pg.image.load(PATH+'sprites/pause.png').convert()
    pause_button.set_colorkey((255,255,255))
    pause_button_rect = pause_button.get_rect()
    pause_button_rect.center = [30, 25]
    sound_button = [pg.image.load(PATH+'sprites/sound_off.png').convert(),
                    pg.image.load(PATH+'sprites/sound_on.png').convert()]
    sound_button[0].set_colorkey((255,255,255))
    sound_button[1].set_colorkey((255,255,255))
    sound_button_rect = sound_button[0].get_rect()
    sound_button_rect.center = [90, 25]

    music_button = [pg.image.load(PATH+'sprites/music_off.png').convert(),
                    pg.image.load(PATH+'sprites/music_on.png').convert()]
    music_button[0].set_colorkey((255,255,255))
    music_button[1].set_colorkey((255,255,255))

    music_button_rect = music_button[0].get_rect()
    music_button_rect.center = [150, 25]
    explosion = pg.image.load(PATH+'sprites/explosion.png').convert()
    explosion.set_colorkey((255,255,255))

    black_frame = pg.Surface(size)
    black_frame.fill(pg.Color('black'))
    black_frame.set_alpha(50)

    font = pg.font.SysFont('arial bold', 100)
    small_font = pg.font.SysFont('arial bold', 30)
    medium_font = pg.font.SysFont('arial bold', 50)

    title_sprite, title_rect = button('AutoRacer', 70, font, 'lightsalmon')
    start_sprite, start_rect = button('Play!', 300, font, 'lightgreen')
    resume_sprite, resume_rect = button('Resume', 300, font, 'lightgreen')
    quit_sprite, quit_rect = button('Quit!', 380, medium_font, 'lightcoral')


    sounds = load_sounds()
    clock = pg.time.Clock()

    mult_sprite, mult_rect = button('', 150, font, 'lightgreen')
    points_sprite, points_rect = button('', 100, font, 'greenyellow')


    tree_sprites = []
    trees = pg.image.load(PATH+'sprites/trees.png').convert()
    trees.set_colorkey((0,0,255))
    for i in range(4):
        tree_sprites.append(pg.Surface.subsurface(trees, (i*50, 0, 50, 50)))
        tree_sprites.append(pg.transform.flip(tree_sprites[-1], 1, 0))
        
    trees = []
    for i in range(5): #[side, distance, lane, sprite]
        add_tree(trees, tree_sprites)
    
    coins = pg.image.load(PATH+'sprites/coins.png').convert()
    coins.set_colorkey((255,0,255))

    yellow_coin = []
    blue_coin = []
    red_coin = []
    bomb = []
    heart = []
    for i in range(8):
        yellow_coin.append(pg.Surface.subsurface(coins, (i*32, 0, 32, 32)))
        blue_coin.append(pg.Surface.subsurface(coins, (i*32, 32, 32, 32)))
        red_coin.append(pg.Surface.subsurface(coins, (i*32, 64, 32, 32)))
        bomb.append(pg.Surface.subsurface(coins, (i*32, 96, 32, 32)))
        heart.append(pg.Surface.subsurface(coins, (i*32, 128, 32, 32)))
    elements = [yellow_coin, blue_coin, red_coin, heart, bomb]
    
    color_list = [(c, v) for c, v in pg.color.THECOLORS.items() if 'light' in c and 'gray' not in c and 'grey' not in c]
    car_sheet = pg.image.load(PATH+'sprites/other_cars.png').convert_alpha()
    for i in range(20):
        color = random.choice(color_list) #random.sample(range(100, 255), 3)
        elements.append(gen_car(color[1], car_sheet))
    
    color = random.choice(color_list)
    car = gen_car(color[1], car_sheet)
    car_size = car[0].get_size()

    max_lives = 3
    enable_sounds = 1
    enable_music = 1
    error_delay = 0
    sound_delay = 0
    speed_target = 0.0025
    speed = 0.0015
    total_time = 0
    total_points = 0
    streak = 0
    animation_time = 0
    car_x = 0
    animations = []
    lives = 0

    lane_target = 0

    status = 'start'
    if enable_music: sounds['music'][0].play(-1) #pg.mixer.music.play(-1)

    while status != 'quit':
        clicked = 0
        mouse_position = pg.mouse.get_pos()

        delta_time = min(50, clock.tick(60))
        total_time += delta_time
        animation_time += speed*delta_time*10
        fps = 1000/delta_time
        for event in pg.event.get():
            if event.type == pg.QUIT: status = 'quitting'
            if event.type == pg.MOUSEBUTTONDOWN:
                clicked = 1
                initial_x = mouse_position[0]
                if enable_sounds and status != 'playing': sounds['bumped'].play()
            # if event.type == pg.FINGERMOTION:
            #     print( 'what')
            #     pass
            if event.type == pg.MOUSEBUTTONUP and abs(mouse_position[0] - initial_x) > 50:
                if mouse_position[0] - initial_x > 50:
                    lane_target = min(1, lane_target+1)
                elif mouse_position[0] - initial_x < 50:
                    lane_target = max(-1, lane_target-1)

            if event.type == pg.KEYDOWN:
                if event.key == ord('a') or event.key == pg.K_LEFT:
                    lane_target = max(-1, lane_target-1)
                elif event.key == ord('d') or event.key == pg.K_RIGHT:
                    lane_target = min(1, lane_target+1)
            if event.type == pg.WINDOWFOCUSLOST and status == 'playing':
                status = 'pause'
                if enable_sounds: sounds['engine'][streak].stop()
        
        screen.blit(background[int(animation_time)%4], (0,0))

        for tree in trees: #[side, distance, lane, sprite]
            scale = min(1, abs(1/(tree[1]+10)))
            new_size = (400*scale, 400*scale)
            tree_resized = pg.transform.scale(tree_sprites[tree[3]], new_size)
            tree_position = (180+tree[0]*(tree[2]*4-2.5)*10*scale-new_size[0]/2, 200+(420*scale-new_size[1]))
            screen.blit(tree_resized, tree_position)
            tree[1] -= delta_time*speed*10
        
        if tree_position[0] + new_size[0] < 0 or tree_position[0] > size[0] or tree[1] < -7:
            trees.remove(tree)

        if (fps > 55 and trees[0][1] < 100) or len(trees) < 5:
            add_tree(trees, tree_sprites)

        if status == 'start':
            screen.blit(black_frame, (0,0))
            if clicked:
                add_explosions(5, animations, mouse_position, explosion, total_time)
            
            screen.blit(title_sprite, title_rect)
            if generic_button(start_sprite, start_rect, screen, mouse_position, clicked):
                exploding_animation(start_sprite, start_rect.x, start_rect.y, animations, total_time, [10,5])
                status = 'playing'
                lives = 1
                total_points = 0
                speed = 0
                streak = 0
                error_delay = total_time
                if enable_sounds: sounds['engine'][0].play(-1)
                
                lane_elements = []
                for i in range(20): #[side, distance, lane, sprite]
                    add_lane_element(lane_elements, elements)
            if generic_button(quit_sprite, quit_rect, screen, mouse_position, clicked):
                exploding_animation(quit_sprite, quit_rect.x, quit_rect.y, animations, total_time, [10,5])
                status = 'quitting'
        
        elif status == 'quitting' and len(animations) == 0:
            status = 'quit'

        elif status == 'pause':
            screen.blit(black_frame, (0,0))
            screen.blit(title_sprite, title_rect)
            if generic_button(resume_sprite, resume_rect, screen, mouse_position, clicked):
                status = 'playing'
                if enable_sounds: sounds['engine'][0].play(-1)
                add_explosions(5, animations, resume_rect.center, explosion, total_time)
                exploding_animation(resume_sprite, resume_rect.x, resume_rect.y, animations, total_time, [10,5])
            if generic_button(quit_sprite, quit_rect, screen, mouse_position, clicked):
                add_explosions(5, animations, quit_rect.center, explosion, total_time)
                exploding_animation(quit_sprite, quit_rect.x, quit_rect.y, animations, total_time, [10,5])
                status = 'quitting'

        elif status == 'playing':    
            if pause_button_rect.collidepoint(mouse_position) and clicked:
                status = 'pause'
                sounds['engine'][streak].fadeout(100)
            else:
                # screen.blit(small_font.render(str(int(fps)), 1, pg.Color('black')), (335, 5))
                screen.blit(pause_button, pause_button_rect)
                screen.blit(sound_button[enable_sounds], sound_button_rect)
                screen.blit(music_button[enable_music], music_button_rect)
                screen.blit(mult_sprite, mult_rect)

                if sound_button_rect.collidepoint(mouse_position) and clicked:
                    enable_sounds = not(enable_sounds)
                    if enable_sounds: 
                        sounds['engine'][streak].play(-1, fade_ms=200)
                    else: 
                        sounds['engine'][streak].fadeout(200)
                elif music_button_rect.collidepoint(mouse_position) and clicked:
                    enable_music = not(enable_music)
                    if enable_music: 
                        sounds['music'][0].play(-1) #pg.mixer.music.play(-1, fade_ms=200)
                    else: 
                        sounds['music'][0].fadeout(200) #pg.mixer.music.stop()

            car_position = (180 + car_x*100 - car_size[0]/2, 520 + (total_time*0.01)%3)
            screen.blit(car[int(car_x+1.5)], car_position)

            old_x = car_x

            if lane_target - car_x > 0.05: left = -1
            elif lane_target - car_x < -0.05: left = 1
            else: left = 0

            car_x = max(-1, min( 1, car_x - left*delta_time*(0.003)))
        
            if enable_sounds and car_x != old_x and total_time - sound_delay > 300:
                sound_delay = total_time
                sounds['tire'].play()
            
            
            if speed < speed_target* (1+ total_points/20000) and total_time - error_delay > 250:
                speed = speed + delta_time*1e-6
            elements_to_remove = []     
            for element in lane_elements: # lane, distance, type
                scale = min(1, abs(1/element[1]))
                new_size = (100*scale, 100*scale)
                if element[2] < 5:
                    resized = pg.transform.scale(elements[element[2]][int((total_time*0.01))%8], new_size)
                else:
                    resized = pg.transform.scale(elements[element[2]][element[0]], new_size)
                element_position = (180+(element[0]-1)*120*scale-new_size[0]/2, 200+(420*scale-new_size[1]/2))
                screen.blit(resized, element_position)
                element[1] -= delta_time*speed#*100
                if element[1] < 9:
                    element_collider = pg.mask.from_surface(resized)
                    car_collider = pg.mask.from_surface(car[int(car_x+1.5)])

                    if  element_position[1] > size[1] or element[1] < 1:
                        elements_to_remove.append(element)
                    
                    elif car_collider.overlap(element_collider, (element_position[0] - car_position[0], element_position[1] - car_position[1])):
                        # exploding_animation(elements[element[2]][-1], element_position[0], 500, animations, total_time) 
                        exploding_animation(resized, element_position[0], 500, animations, total_time) 

                        if element[2] < 3 or (element[2] == 3 and lives >= max_lives):
                            if enable_sounds: sounds['powerup'][element[2]].play()
                            points_added = (element[2]+1)*(streak+1)*10
                            total_points += points_added
                            points_sprite, points_rect = button(str(total_points), 130, font, 'greenyellow')

                            for i in range((element[2]+1)*(streak+1)):
                                x_position = 180 + random.randint(-40,40)
                                y_position = 100 + random.randint(-40,40)
                                animations.append([yellow_coin[random.randint(0,7)], x_position,  y_position, total_time+400])

                            if element[2] == 2 and streak < 10:
                                speed_target = speed_target*1.1
                                sounds['engine'][streak].fadeout(100)
                                sounds['music'][int(streak/2)].fadeout(100)
                                streak += 1
                                if enable_sounds: sounds['engine'][streak].play(-1)
                                if enable_music: sounds['music'][int(streak/2)].play(-1)
                                mult_sprite, mult_rect = button('x'+str(streak+1), 180, medium_font, 'lightgreen')
                                animations.append([medium_font.render('x'+str(streak+1), 1, pg.Color('lightgreen')), element_position[0], element_position[1], total_time])
                        elif element[2] == 3:
                            if enable_sounds: sounds['powerup'][element[2]].play()
                            lives = min(max_lives, lives +1)
                            animations.append([heart[-1], element_position[0],  element_position[1], total_time+400])
                        elif element[2] > 3:
                            lives -= 1
                            speed = 0
                            error_delay = total_time
                            speed_target = 0.0025
                            if enable_sounds:
                                sounds['engine'][streak].fadeout(50)
                                sounds['bumped'].play()
                            if enable_music: sounds['music'][int(streak/2)].fadeout(50)
                            
                            if element[2] == 4 or streak == 10:
                                lives -= 1
                                add_explosions(3, animations, element_position, explosion, total_time)
                            
                            streak = 0
                            if enable_sounds: sounds['engine'][0].play(-1)
                            if enable_music: sounds['music'][0].play(-1)
                            mult_sprite = medium_font.render('', 1, pg.Color('white'))

                            add_explosions(3, animations, element_position, explosion, total_time)                            
                            
                            if lives < 1:
                                exploding_animation(car[int(car_x+1.5)], car_position[0], 570, animations, total_time)
                                sounds['engine'][0].stop()
                                status = 'dying'
                                speed = 0.0015
                                points_sprite, points_rect = button('Total points: '+str(total_points), 120, medium_font, 'greenyellow')
                                max_animations = 10
                        elements_to_remove.append(element)

            for element in elements_to_remove:
                lane_elements.remove(element)

            for i in range(lives):
                screen.blit(heart[int((total_time*0.01))%8], (300-i*32, 8))

            if len(lane_elements) < 20:
                add_lane_element(lane_elements, elements, total_points, max_lives-lives)
        
        if status == 'dying':
            if enable_sounds: sounds['bumped'].play()
            animation_sprite = pg.transform.scale(explosion, (100,100))
            x_position = car_position[0] + random.randint(-120,120)
            y_position = 400 + random.randint(-120,120)
            order = random.randint(0, len(animations))
            animations.insert(order,[animation_sprite, x_position,  y_position, total_time+random.randint(0,400)])
            max_animations -= 1
            pg.time.wait(30)
            if  max_animations == 0:
                status = 'start'

        for animation in animations:
            anim_frame = animation[0]
            last_size = animation[0].get_size()
            time_scale = ( total_time + 1500 - animation[3])/1000
            anim_frame = pg.transform.scale(anim_frame, (last_size[0]*time_scale, last_size[1]*time_scale))
            if fps > 50:
                anim_frame.set_alpha(255-(total_time - animation[3])*0.2)
                if len(animation) > 4 and animation[4] != 0:
                    anim_frame = pg.transform.rotate(anim_frame, time_scale*animation[4])
                    animation[1] += animation[5][0]*delta_time
                    animation[2] += animation[5][1]*delta_time
            animation[1] += random.randint(-1,1)
            animation[2] -= delta_time*.1 + random.randint(-1,1)
            screen.blit(anim_frame, (animation[1], animation[2]))
            if total_time - animation[3] > 500 or (fps < 30 and total_time - animation[3] > 0):
                animations.remove(animation)
        
        screen.blit(points_sprite, points_rect)
        pg.display.update()
        await asyncio.sleep(0)
    pg.mixer.quit() 
    pg.quit() 

def add_lane_element(lane_elements, elements, total_points=0, need_lives=1):
    lane = random.randint(0,2)
    distance = 10
    if len(lane_elements)>0:
        distance = lane_elements[0][1]+ min(4, 1+ lane_elements[0][2])
    if random.randint(0,20000) < total_points and random.randint(0,100) > 20:
        element_type = random.choice([2,4,5,5,5,5])
    else:
        element_type = random.choice([0,0,0,0,0,0,0,0,0,1,1,1,1,2,2,2,3,4,5,5,5,5,5,5])
        if element_type == 3 and need_lives < 1:
            element_type = 2
    if element_type == 5: 
        element_type = random.randint(5,len(elements) -1)
    

    lane_elements.insert(0,[lane, distance, element_type])
    if element_type == 0:
        for i in range(3):
            lane_elements.insert(0,[lane, distance+i+1, 0])


def add_tree(trees, tree_sprites):
    distance = random.uniform(1, 5)
    if len(trees) > 0:
        distance += trees[0][1]
    trees.insert(0,[random.choice([-1,1]), # side
                    distance, # distance
                    random.uniform(15,50), # lateral distance
                    random.randint(0,len(tree_sprites)-1)])  # sprite

def load_sounds():
    sounds = {'engine':[], 'powerup':[], 'music':[]}
    volume = 0.5
    if PLATFORM == 'android':
        volume = 0.3
    for i in range(11):
        sounds['engine'].append(pg.mixer.Sound(PATH+'sounds/engine'+str(i)+'.ogg'))
        sounds['engine'][-1].set_volume(volume*1.5)
    for i in range(4):
        sounds['powerup'].append(pg.mixer.Sound(PATH+'sounds/powerup'+str(i)+'.ogg'))
        sounds['powerup'][-1].set_volume(volume*0.5)
    for i in range(6):
        sounds['music'].append(pg.mixer.Sound(PATH+'sounds/music'+str(i)+'.ogg'))
        sounds['music'][-1].set_volume(volume)

    sound_strings = ['bumped', 'tire', 'finish', 'change']
    for string in sound_strings:
        sounds[string] = pg.mixer.Sound(PATH+'sounds/' + string + '.ogg')
        sounds[string].set_volume(volume)
        
    return sounds

def button(text, center_y, font, color='white', center_x=180):
    button_sprite = font.render(text, 1, pg.Color(color))
    button_rect = button_sprite.get_rect()
    button_rect.center = (center_x, center_y)

    return button_sprite, button_rect

def generic_button(button_sprite, button_rect, screen, mouse_position, clicked):
    selected = 0
    if button_rect.collidepoint(mouse_position):
        pg.draw.rect(screen, pg.Color('gray'), button_rect)
        if clicked: selected = 1
    screen.blit(button_sprite, button_rect)

    return selected

def exploding_animation(surf, pos_x, pos_y, animations, total_time, slices=[5,5]):
    sizes = list(surf.get_size())
    sizes[0] = int(sizes[0]/slices[0])
    sizes[1] = int(sizes[1]/slices[1])

    for i in range(slices[0]):
        for j in range(slices[1]):
            sub1 = pg.Surface.subsurface(surf, [i*sizes[0],j*sizes[1],sizes[0], sizes[1]])
            x_position = pos_x + random.randint(-1,1) + i*sizes[0]#*3 - sizes
            y_position = pos_y + random.randint(-1,1) + j*sizes[1]#*3 - sizes
            angle = random.randint(-90,90)#-i*10+5
            direction = [random.uniform(-.1,.1), random.uniform(-.1,.1)]
            order = random.randint(0, len(animations))
            animations.insert(order, [sub1, x_position, y_position, total_time+500, angle, direction])

def add_explosions(number, animations, element_position, explosion, total_time):
    for i in range(number):
        x_position = element_position[0] + random.randint(-100,50)
        y_position = element_position[1] + random.randint(-100,50)
        order = random.randint(0, len(animations))
        animations.insert(order,[explosion, x_position,  y_position, total_time+random.randint(0,400)])

def gen_car(color, car_sheet):
        car_background = pg.surface.Surface((160,80))
        car_background.fill(color)
        car_background.blit(car_sheet, (0,0))
        car_background.set_colorkey((255,0,255))
        new_car = []
        new_car.append(pg.Surface.subsurface(car_background, (0, 0, 80, 80)))
        new_car.append(pg.Surface.subsurface(car_background, (80, 0, 80, 80)))
        new_car.append(pg.transform.flip(new_car[0], flip_x=1, flip_y=0))
        
        return new_car

if __name__ == '__main__':
    pg.init()
    asyncio.run(main())
