import pygame
import sys

# Screen/grid dimensions
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
FPS = 30
GLOBAL_ROWS = 10
GLOBAL_COLS = 10
SUBGRID_ROWS = 7
SUBGRID_COLS = 7

# Colors (RGB)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_GRAY = (200, 200, 200)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# Grid line toggle
show_grid_lines = True

def draw_text_in_rect(screen, text, rect):
    """
    Render a single character so that it fills the rect as much as possible while
    preserving its aspect ratio.
    """
    # Font size
    font_size = int(rect.height)
    font = pygame.font.SysFont(None, font_size)
    text_surface = font.render(text, True, BLACK)
    original_width, original_height = text_surface.get_size()

    # Sync font size
    scale_factor = min(rect.width / original_width, rect.height / original_height)
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)

    scaled_surface = pygame.transform.scale(text_surface, (new_width, new_height))
    new_rect = scaled_surface.get_rect(center=rect.center)
    screen.blit(scaled_surface, new_rect)

class Cell:
    def __init__(self):
        self.char = ''
        self.subgrid = None  # Hold deterritorialized grid

    def deterritorialize(self):
        if self.subgrid is None:
            self.subgrid = Grid(SUBGRID_ROWS, SUBGRID_COLS)

    def undo_deterritorialize(self):
        self.subgrid = None

class Grid:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.cells = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self.active_row = 0
        self.active_col = 0

    def move_active(self, direction):
        if direction == 'up':
            self.active_row = max(0, self.active_row - 1)
        elif direction == 'down':
            self.active_row = min(self.rows - 1, self.active_row + 1)
        elif direction == 'left':
            self.active_col = max(0, self.active_col - 1)
        elif direction == 'right':
            self.active_col = min(self.cols - 1, self.active_col + 1)

    def input_char(self, char):
        self.cells[self.active_row][self.active_col].char = char

def draw_subgrid(screen, subgrid, cell_rect):
    """
    Recursively draw a miniature version of a subgrid inside the given cell_rect.
    Each subcell renders its text filling the cell while maintaining its aspect ratio.
    """
    subcell_width = cell_rect.width / subgrid.cols
    subcell_height = cell_rect.height / subgrid.rows

    for i in range(subgrid.rows):
        for j in range(subgrid.cols):
            subcell_rect = pygame.Rect(
                int(cell_rect.x + j * subcell_width),
                int(cell_rect.y + i * subcell_height),
                int(subcell_width),
                int(subcell_height)
            )
            # Draw grid lines if toggled on
            if show_grid_lines:
                pygame.draw.rect(screen, LIGHT_GRAY, subcell_rect, 1)
            cell = subgrid.cells[i][j]
            if cell.subgrid is not None:
                draw_subgrid(screen, cell.subgrid, subcell_rect)
                # 2x+ nested content indicator
                indicator_size = 5
                indicator_rect = pygame.Rect(subcell_rect.x + 2, subcell_rect.y + 2, indicator_size, indicator_size)
                pygame.draw.rect(screen, RED, indicator_rect)
            elif cell.char:
                draw_text_in_rect(screen, cell.char, subcell_rect)

def main():
    global show_grid_lines

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Nested Grid Editor")
    clock = pygame.time.Clock()

    # Global grid and layers.
    current_grid = Grid(GLOBAL_ROWS, GLOBAL_COLS)
    grid_stack = []  # Grid layer track

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.KEYDOWN:
                # Grid line toggle.
                if event.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                    show_grid_lines = not show_grid_lines

                # Navigation with arrow keys
                elif event.key == pygame.K_UP:
                    current_grid.move_active('up')
                elif event.key == pygame.K_DOWN:
                    current_grid.move_active('down')
                elif event.key == pygame.K_LEFT:
                    current_grid.move_active('left')
                elif event.key == pygame.K_RIGHT:
                    current_grid.move_active('right')
                # Deterritorialize current cell into a 7x7 subgrid.
                elif event.key == pygame.K_TAB:
                    cell = current_grid.cells[current_grid.active_row][current_grid.active_col]
                    cell.deterritorialize()
                # Undo deterritorialization.
                elif event.key == pygame.K_BACKSPACE:
                    cell = current_grid.cells[current_grid.active_row][current_grid.active_col]
                    if cell.subgrid is not None:
                        cell.undo_deterritorialize()
                # Zoom into/enter subgrid.
                elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    cell = current_grid.cells[current_grid.active_row][current_grid.active_col]
                    if cell.subgrid is not None:
                        grid_stack.append(current_grid)
                        current_grid = cell.subgrid
                # Return to parent grid.
                elif event.key == pygame.K_SPACE:
                    if grid_stack:
                        current_grid = grid_stack.pop()
                # Print in cell.
                else:
                    if event.unicode and event.unicode.isprintable():
                        current_grid.input_char(event.unicode)

        # Draw the current grid.
        screen.fill(WHITE)
        cell_width = SCREEN_WIDTH // current_grid.cols
        cell_height = SCREEN_HEIGHT // current_grid.rows

        for row in range(current_grid.rows):
            for col in range(current_grid.cols):
                cell_rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)
                # Cell border draw.
                if show_grid_lines:
                    pygame.draw.rect(screen, BLACK, cell_rect, 1)
                # Active cell highlight.
                if row == current_grid.active_row and col == current_grid.active_col:
                    pygame.draw.rect(screen, BLUE, cell_rect, 3)
                cell = current_grid.cells[row][col]
                if cell.subgrid is not None:
                    draw_subgrid(screen, cell.subgrid, cell_rect)
                elif cell.char:
                    draw_text_in_rect(screen, cell.char, cell_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
