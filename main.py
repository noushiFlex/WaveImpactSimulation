import pygame
import numpy as np
import sys

# Initialisation de Pygame
pygame.init()

# Paramètres de la simulation
WIDTH, HEIGHT = 800, 600
FPS = 60
SURFACE_POINTS = 100  # Nombre de points pour représenter la surface
DAMPING = 0.98  # Coefficient d'amortissement
TENSION = 0.05  # Coefficient de tension
SPREAD = 0.15  # Coefficient de propagation
GRAVITY = 0.05  # Force de gravité

# Couleurs
BACKGROUND = (0, 0, 0)
SURFACE_COLOR = (0, 120, 255)
PROJECTILE_COLOR = (255, 0, 0)

# Configuration de l'écran
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulation de Perturbation de Surface")
clock = pygame.time.Clock()

class Surface:
    def __init__(self, num_points, y_baseline):
        self.num_points = num_points
        self.y_baseline = y_baseline  # Position y de base de la surface
        self.points = np.zeros(num_points)  # Déplacement vertical des points
        self.velocities = np.zeros(num_points)  # Vitesse de déplacement des points
        self.point_spacing = WIDTH / (num_points - 1)  # Espacement entre les points
    
    def update(self):
        # Calcul des forces pour chaque point
        left_deltas = np.zeros(self.num_points)
        right_deltas = np.zeros(self.num_points)
        
        # Calcul des différences de hauteur entre points adjacents
        for i in range(1, self.num_points):
            left_deltas[i] = TENSION * (self.points[i] - self.points[i-1])
            self.velocities[i-1] += left_deltas[i]
        
        for i in range(self.num_points-1):
            right_deltas[i] = TENSION * (self.points[i] - self.points[i+1])
            self.velocities[i+1] += right_deltas[i]
        
        # Application du coefficient de propagation
        for i in range(self.num_points):
            if i > 0:
                self.points[i-1] += left_deltas[i] * SPREAD
            if i < self.num_points-1:
                self.points[i+1] += right_deltas[i] * SPREAD
        
        # Mise à jour des positions avec les vitesses
        self.points += self.velocities
        
        # Application de la gravité et de l'amortissement
        self.velocities -= self.points * GRAVITY
        self.velocities *= DAMPING
    
    def disturb(self, index, magnitude):
        """Perturbe la surface à un point spécifique"""
        if 0 <= index < self.num_points:
            self.points[index] += magnitude
    
    def disturb_at_position(self, x_pos, magnitude, radius=10):
        """Perturbe la surface autour d'une position x avec un certain rayon"""
        center_index = int(x_pos / self.point_spacing)
        
        # Applique la perturbation aux points proches selon le rayon
        for i in range(self.num_points):
            distance = abs(i - center_index)
            if distance * self.point_spacing <= radius:
                # Plus proche du centre, plus forte la perturbation
                factor = 1 - (distance * self.point_spacing) / radius
                self.points[i] += magnitude * factor * factor
    
    def draw(self, screen):
        # Dessine la surface comme une série de lignes entre les points
        points = []
        for i in range(self.num_points):
            x = i * self.point_spacing
            y = self.y_baseline + self.points[i]
            points.append((x, y))
        
        # Ajoute des points pour fermer la forme
        bottom_points = [(WIDTH, HEIGHT), (0, HEIGHT)]
        all_points = points + bottom_points
        
        # Dessine un polygone rempli
        pygame.draw.polygon(screen, SURFACE_COLOR, all_points)
        
        # Dessine une ligne pour le haut de la surface
        if len(points) >= 2:
            pygame.draw.lines(screen, (255, 255, 255), False, points, 2)

class Projectile:
    def __init__(self, x, y, radius, velocity_x, velocity_y):
        self.x = x
        self.y = y
        self.radius = radius
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.active = True
        self.gravity = 0.1
    
    def update(self):
        if not self.active:
            return False
            
        # Mise à jour de la position
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Ajout de la gravité
        self.velocity_y += self.gravity
        
        # Vérification collision avec les bords
        if self.x < 0 or self.x > WIDTH:
            self.active = False
        
        return self.active
    
    def draw(self, screen):
        if self.active:
            pygame.draw.circle(screen, PROJECTILE_COLOR, (int(self.x), int(self.y)), self.radius)
    
    def check_surface_collision(self, surface):
        """Vérifie la collision avec la surface"""
        if not self.active:
            return False
            
        # Trouve le point de surface le plus proche
        nearest_point_index = int(self.x / surface.point_spacing)
        if 0 <= nearest_point_index < surface.num_points:
            surface_y = surface.y_baseline + surface.points[nearest_point_index]
            
            # Si le projectile touche la surface
            if self.y + self.radius >= surface_y:
                # Calcul de la force d'impact basée sur la vitesse
                impact_force = abs(self.velocity_y) * 2
                
                # Perturbe la surface
                surface.disturb_at_position(self.x, -impact_force, self.radius * 2)
                
                # Rebond ou désactivation selon la force
                if impact_force > 10:
                    # Rebond avec perte d'énergie
                    self.velocity_y = -self.velocity_y * 0.6
                    self.y = surface_y - self.radius - 1  # Évite de rester coincé
                else:
                    # Trop peu d'énergie pour rebondir
                    self.active = False
                
                return True
        return False

def main():
    # Création de la surface à mi-hauteur de l'écran
    surface = Surface(SURFACE_POINTS, HEIGHT * 0.6)
    
    # Liste pour stocker les projectiles
    projectiles = []
    
    # Boucle principale
    running = True
    while running:
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Création d'un projectile à la position du clic
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Calcul de la vitesse en fonction de la position (tire vers la surface)
                vel_x = 0
                vel_y = 2
                
                # Création du projectile
                projectiles.append(Projectile(mouse_x, mouse_y, 10, vel_x, vel_y))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Perturbe aléatoirement la surface
                    index = np.random.randint(0, SURFACE_POINTS)
                    surface.disturb(index, -20)
        
        # Mise à jour des objets
        surface.update()
        
        # Mise à jour des projectiles et vérification des collisions
        for proj in projectiles[:]:
            if not proj.update():
                projectiles.remove(proj)
            else:
                proj.check_surface_collision(surface)
        
        # Rendu
        screen.fill(BACKGROUND)
        surface.draw(screen)
        for proj in projectiles:
            proj.draw(screen)
        
        # Rafraîchissement de l'écran
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()