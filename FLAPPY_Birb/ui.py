import pygame
import os
import random
import cv2
import time
from detection import ArmDetector


os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"


class FlappyBirdGame:
    def __init__(self):
        pygame.init()
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Flappy Bird")

        self.clock = pygame.time.Clock()
        self.running = True
        self.difficulty = None
        


        self.bird_img = pygame.image.load(os.path.join("assets", "yellowbird-downflap.png")).convert_alpha()
        self.background_img = pygame.transform.scale(
            pygame.image.load(os.path.join("assets", "background-day.png")).convert(),
            (self.screen_width, self.screen_height)
        )
        self.pipe_img = pygame.image.load(os.path.join("assets", "pipe-green.png")).convert_alpha()
        self.base_img = pygame.image.load(os.path.join("assets", "base.png")).convert()

        self.bird_x = 150
        self.bird_y = 300
        self.gravity = 0
        self.score = 0

        self.pipes = []
        self.pipe_speed = 3
        self.pipe_gap = 200
        self.pipe_distance = 300
        

        self.font = pygame.font.SysFont(None, 48)

        self.base_rect = self.base_img.get_rect()

        # ARM DETECTOR
        self.arm_detector = ArmDetector()

        # GAME STATE
        self.game_started = False

    def set_difficulty(self, level):
        if level == "easy":
            self.pipe_speed = 2
            self.pipe_gap = 260
            self.gravity_step = 0.2

        elif level == "normal":
            self.pipe_speed = 3
            self.pipe_gap = 200
            self.gravity_step = 0.3

        elif level == "hard":
            self.pipe_speed = 5
            self.pipe_gap = 160
            self.gravity_step = 0.4

        self.difficulty = level
        self.pipes = []
        self.spawn_pipe()




    def spawn_pipe(self):
        height = random.randint(100, 400)
        top_pipe = pygame.transform.flip(self.pipe_img, False, True)
        bottom_pipe = self.pipe_img.copy()
        self.pipes.append({
            'x': self.screen_width,
            'top_y': height - self.pipe_gap // 2 - top_pipe.get_height(),
            'bottom_y': height + self.pipe_gap // 2,
            'top_pipe': top_pipe,
            'bottom_pipe': bottom_pipe,
            'passed': False
        })

    def show_game_over_menu(self):
        font = pygame.font.SysFont("Arial", 32)
        restart_text = font.render(
            "Game Over - Raise Arm to Restart or Q to Quit", True, (255, 0, 0)
        )
        self.screen.blit(
            restart_text,
            (self.screen_width // 2 - restart_text.get_width() // 2,
             self.screen_height // 2)
        )
        pygame.display.update()

        waiting = True
        while waiting:
            if self.arm_detector.get_arm_up_event():
                self.reset_game()
                waiting = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    pygame.quit()
                    exit()

    def control(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if self.difficulty is None:
                    if event.key == pygame.K_1:
                        self.set_difficulty("easy")
                    elif event.key == pygame.K_2:
                        self.set_difficulty("normal")
                    elif event.key == pygame.K_3:
                        self.set_difficulty("hard")
                



    def update(self):

        
        if self.difficulty is None:
            
            self.arm_detector.get_arm_up_event()

            # Finger control
            fingers = self.arm_detector.get_finger_count()
            if fingers == 1:
                self.set_difficulty("easy")
            elif fingers == 2:
                self.set_difficulty("normal")
            elif fingers == 3:
                self.set_difficulty("hard")

            return


        if self.difficulty is not None and not self.game_started:

            keys = pygame.key.get_pressed()
            if self.arm_detector.get_arm_up_event() or keys[pygame.K_SPACE]:
                self.game_started = True
                self.gravity = -5
                self.space_pressed = True
            return

        # ARM UP control
        if self.arm_detector.get_arm_up_event() or pygame.key.get_pressed()[pygame.K_SPACE]:
            self.gravity = -5

        self.gravity += self.gravity_step

        self.bird_y += self.gravity
        if self.bird_y < 0:
            self.bird_y = 0
            self.gravity = 0


        if self.bird_y > self.screen_height - self.base_img.get_height():
            self.show_game_over_menu()

        for pipe in self.pipes:
            pipe['x'] -= self.pipe_speed

            bird_rect = self.bird_img.get_rect(center=(self.bird_x, self.bird_y))
            top_rect = pipe['top_pipe'].get_rect(topleft=(pipe['x'], pipe['top_y']))
            bottom_rect = pipe['bottom_pipe'].get_rect(topleft=(pipe['x'], pipe['bottom_y']))

            if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
                self.show_game_over_menu()

            if not pipe['passed'] and pipe['x'] + self.pipe_img.get_width() < self.bird_x:
                pipe['passed'] = True
                self.score += 1

                if self.difficulty == "easy":
                    self.pipe_speed = min(6, 2 + self.score // 5)
                elif self.difficulty == "normal":
                    self.pipe_speed = min(8, 3 + self.score // 5)
                elif self.difficulty == "hard":
                    self.pipe_speed = min(10, 5 + self.score // 5)


        if self.pipes and self.pipes[0]['x'] < -self.pipe_img.get_width():
            self.pipes.pop(0)

        if not self.pipes or self.pipes[-1]['x'] < self.screen_width - self.pipe_distance:
            self.spawn_pipe()

    def reset_game(self):
        self.bird_y = self.screen_height // 2
        self.gravity = 0
        self.score = 0
        self.pipes = []
        self.game_started = False
        self.difficulty = None
        self.pipe_speed = 3
        self.pipe_gap = 200
        self.gravity_step = 0.2


    def draw(self):
        self.screen.blit(self.background_img, (0, 0))

        for pipe in self.pipes:
            self.screen.blit(pipe['top_pipe'], (pipe['x'], pipe['top_y']))
            self.screen.blit(pipe['bottom_pipe'], (pipe['x'], pipe['bottom_y']))

        self.screen.blit(
            self.bird_img,
            self.bird_img.get_rect(center=(self.bird_x, self.bird_y))
        )

        self.screen.blit(self.base_img, (0, self.screen_height - self.base_img.get_height()))
        self.screen.blit(self.base_img, (self.base_rect.width, self.screen_height - self.base_img.get_height()))
        self.screen.blit(self.base_img, (self.base_rect.width * 2, self.screen_height - self.base_img.get_height()))

        score_surface = self.font.render(str(self.score), True, (255, 255, 255))
        self.screen.blit(score_surface, (self.screen_width // 2, 50))
        if self.difficulty is None:
            msg = self.font.render("Select Difficulty: 1-Easy  2-Normal  3-Hard", True, (255,255,255))
            self.screen.blit(msg, (self.screen_width//2 - msg.get_width()//2, 250))

        if self.difficulty is not None and not self.game_started:

            hint = self.font.render("RAISE ARM TO START", True, (255, 255, 0))
            self.screen.blit(hint, (self.screen_width // 2 - hint.get_width() // 2, 200))

        pygame.display.update()

    def run(self):
        while self.running:
            self.control()
            self.update()
            self.draw()
            self.clock.tick(60)

        self.arm_detector.release()
        pygame.quit()

