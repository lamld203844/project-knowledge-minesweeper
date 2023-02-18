import itertools
import random


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __sub__(self, other):
        return Sentence(self.cells - other.cells, self.count - other.count)

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        if len(self.cells) == self.count:
            mines = set()
            for cell in self.cells:
                mines.add(cell)
        else:
            mines = None
        
        return mines
        
    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        if self.count == 0:
            safes = set()
            for cell in self.cells:
                safes.add(cell)
        else:
            safes = None

        return safes

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        if cell in self.cells:
            self.cells.remove(cell)
            self.count = self.count - 1
            

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        if cell in self.cells:
            self.cells.remove(cell)
    
    def is_null_sen(self):
        if self.cells == set():
            return True
        else:
            return False


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []

    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        """
        Called when the Minesweeper board tells us, for a given
        safe cell, how many neighboring cells have mines in them.

        This function should:
            1) mark the cell as a move that has been made
            2) mark the cell as safe
            3) add a new sentence to the AI's knowledge base
                based on the value of `cell` and `count`
            4) mark any additional cells as safe or as mines
                if it can be concluded based on the AI's knowledge base
            5) add any new sentences to the AI's knowledge base
                if they can be inferred from existing knowledge
        """
        # 1) mark the cell as a move that has been made
        self.moves_made.add(cell)

        # 2) mark the cell as safe and update all sentences in KB
        self.safes.add(cell)
        self.mark_safe(cell)

        # 3) add a new sentence to the AI's knowledge base
        #    based on the value of `cell` and `count`
        
        # get all neighbor cell
        i,j = cell[0], cell[1]
        candidates = {
            (i-1, j-1), (i-1, j),  (i-1, j+1),
            (i, j-1),             (i, j+1),
            (i+1, j-1), (i+1, j), (i+1, j+1)
        }

        candidates_clone = [c for c in candidates]
        for candidate in candidates_clone:
        # Be sure - only include undetermined state 
        # not invalid board elements, not in self.safes and self.mines
            r,c = candidate[0], candidate[1]
            invalid_coordinate = r < 0 or (r > (self.width - 1)) or c < 0 or (c > (self.height - 1))
            invalid_move = candidate in self.moves_made
            invalid = invalid_move or invalid_coordinate
            if invalid:
                candidates.remove(candidate)

        new_knowledge = Sentence(candidates, count)
        # mark mines, safes to optimize Sentence = knowledge
        for candidate in candidates:
            if candidate in self.mines:
                new_knowledge.mark_mine(candidate)

            if candidate in self.safes:
                new_knowledge.mark_safe(candidate)
        
        self.knowledge.append(new_knowledge)
        # marking anytime new knowledge appending 
        self.marking_safe_mine()
        

        # recursively inferring -when- any change in self.knowledge
        def inferring(new):

            # 4) mark any additional cells as safe or as mines
            #   if it can be concluded based on the AI's knowledge base
            self.marking_safe_mine()

            # 5) add any new sentences to the AI's knowledge base
            #   if they can be inferred from existing knowledge

            # clean KB before looping and inferring (delete null Sentence)
            null_sen = Sentence(set(), 0)
            while self.knowledge.count(null_sen):
                self.knowledge.remove(null_sen)

            for knowledge in self.knowledge:
                
                # Just infer if knowledge - not null Sentence after updating since marking mines/safes time 
                if not(knowledge.is_null_sen() or new.is_null_sen()):
                    new_cells = new.cells
                    knowledge_cells = knowledge.cells
                    if new == knowledge:
                        continue
                    elif new_cells.issubset(knowledge_cells):
                        new_infer_info = knowledge - new
                        # make sure it is really new 
                        
                        if new_infer_info not in self.knowledge:
                            self.knowledge.append(new_infer_info)
                            inferring(new_infer_info)
                    elif new_cells.issubset(knowledge_cells):
                        new_infer_info = new - knowledge

                        # make sure it is really new 
                        if new_infer_info not in self.knowledge:
                            self.knowledge.append(new_infer_info)
                            inferring(new_infer_info)

        inferring(new_knowledge)

    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        # invalid safe = safe not in self.moves_made
        invalid_safe = False
        for safe in self.safes:
            if safe not in self.moves_made:
                invalid_safe = safe
            if invalid_safe:
                break

        if invalid_safe:
            return invalid_safe
        
        return None


    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """
        # if a safe move is not possible
        if self.make_safe_move():
            # get random space:
            rand_space = set()
            for r in range(self.height):
                for c in range(self.width):
                    # Move must not - already been made, known to be a mine.
                    if ((r,c) not in self.moves_made) and ((r,c) not in self.mines):
                        rand_space.add((r,c))

            if len(rand_space):
                return rand_space.pop()
            else:
                # return None if no such moves are possible
                return None
    
    def marking_safe_mine(self):
        """
        Mark any additional cells as safe or as mines
            if it can be concluded based on the AI's knowledge base
        """
        for knowledge in self.knowledge:
            inferred_mines = knowledge.known_mines()
            if inferred_mines:
                for mine in inferred_mines:
                    self.mark_mine(mine) 
        
            inferred_safes = knowledge.known_safes()
            if inferred_safes:
                for safe in inferred_safes:
                    self.mark_safe(safe)
        
