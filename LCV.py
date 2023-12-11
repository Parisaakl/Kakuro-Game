import copy
from operator import itemgetter
import timeit

DIGITS = [1, 2, 3, 4, 5, 6, 7, 8, 9]

WHITE = 0
CLUE = -1
BLACK = -2
DOWN = 'down'
RIGHT = 'right'

class KakuroCell:
    def __init__(self, location, category):
        self.location = location
        self.category = category

class KakuroClue:
    def __init__(self, direction, length, goal_sum):
        self.direction = direction
        self.length = length
        self.goal_sum = goal_sum
        self.location = None

class KakuroClueCell(KakuroCell):
    def __init__(self, location, down_clue, right_clue):
        super().__init__(location, category=CLUE)
        self.down_clue = down_clue
        if down_clue is not None:
            self.down_clue.location = self.location
        self.right_clue = right_clue
        if right_clue is not None:
            self.right_clue.location = self.location
        self.value = 0  # Add this line to initialize the value attribute


class KakuroBlackCell(KakuroCell):
    def __init__(self, location):
        super().__init__(location, category=BLACK)

class KakuroWhiteCell(KakuroCell):
    def __init__(self, location, value=0):
        super().__init__(location, category=WHITE)
        self.value = value

class KakuroPuzzle:
    def __init__(self, height, width, cells):
        self.height = height
        self.width = width
        self.cells = cells
        self.clues = self.create_clues()
        self.puzzle = self.create_puzzle()
        self.print_puzzle()

    def print_puzzle(self):
        for i in range(self.height):
            for j in range(self.width):
                cell = self.puzzle[i][j]
                if cell.category == BLACK:
                    print("#", end=" ")
                elif cell.category == CLUE:
                    print("C", end=" ")
                elif cell.category == WHITE:
                    print(cell.value, end=" ")
            print()  # Add a new line after printing each row
        print()  # Add an extra new line between puzzles

    def create_clues(self):
        clues = []
        for cell in self.cells:
            if cell.category == CLUE:
                if cell.down_clue is not None:
                    clues.append(cell.down_clue)
                if cell.right_clue is not None:
                    clues.append(cell.right_clue)
        return clues

    def create_puzzle(self):
        puzzle = [[KakuroWhiteCell((i, j)) for j in range(self.width)] for i in range(self.height)]
        for cell in self.cells:
            puzzle[cell.location[0]][cell.location[1]] = cell
        return puzzle

    def get_cell_set(self, clue):
        cell_set = []
        if clue.direction == DOWN:
            for i in range(clue.length):
                cell_set.append(self.puzzle[clue.location[0] + i + 1][clue.location[1]])
        elif clue.direction == RIGHT:
            for i in range(clue.length):
                cell_set.append(self.puzzle[clue.location[0]][clue.location[1] + i + 1])
        return cell_set

    def assign_clue(self, clue, value_set):
        if clue.direction == DOWN:
            for i in range(clue.length):
                self.puzzle[clue.location[0] + i + 1][clue.location[1]].value = value_set[i]
        elif clue.direction == RIGHT:
            for i in range(clue.length):
                self.puzzle[clue.location[0]][clue.location[1] + i + 1].value = value_set[i]

    def is_clue_assigned(self, clue):
        return self.clue_unassigned_count(clue) == 0

    def clue_unassigned_count(self, clue):
        cell_set = self.get_cell_set(clue)
        unassigned_count = 0
        for cell in cell_set:
            if cell.value == 0:
                unassigned_count += 1
        return unassigned_count

    def is_complete(self):
        for i in range(self.height):
            for j in range(self.width):
                if self.puzzle[i][j].category == WHITE and self.puzzle[i][j].value == 0:
                    return False
        return True

    def is_consistent(self):
        for clue in self.clues:
            cell_set = self.get_cell_set(clue)
            if self.is_clue_assigned(clue):
                current_sum = 0
                values = []
                for cell in cell_set:
                    values.append(cell.value)
                    current_sum += cell.value
                if current_sum != clue.goal_sum or any(values.count(x) > 1 for x in values):
                    return False
        return True

class KakuroAgent:
    def __init__(self, puzzle):
        self.puzzle = puzzle

    def solve(self):
        solution = self.backtracking_search(self.puzzle)
        if solution is not None:
            solution.print_puzzle()
            self.puzzle = solution
        else:
            print("no solution found")

    def backtracking_search(self, puzzle):
        return self.recursive_backtracking(copy.deepcopy(puzzle))

    def recursive_backtracking(self, assignment):
        if assignment.is_complete() and assignment.is_consistent():
            print("Puzzle solved!")
            return assignment

        clue = self.select_unassigned_clue(assignment)
        if clue is not None:
            cell_set = assignment.get_cell_set(clue)
            value_sets = self.order_domain_values(clue, cell_set, assignment)
            for value_set in value_sets:
                if self.is_consistent(clue, copy.deepcopy(value_set), copy.deepcopy(assignment)):
                    assignment.assign_clue(clue, value_set)
                    assignment.print_puzzle()
                    result = self.recursive_backtracking(copy.deepcopy(assignment))
                    if result is not None:
                        return result
            return None

    def select_unassigned_clue(self, assignment):
        for clue in assignment.clues:
            if not assignment.is_clue_assigned(clue):
                return clue

    def order_domain_values(self, clue, cell_set, assignment):
        value_sets = []
        assigned_cells = []
        unassigned_cells = []
        allowed_values = copy.deepcopy(DIGITS)

        for cell in cell_set:
            if cell.value == 0:
                unassigned_cells.append(cell)
            else:
                if cell.value in allowed_values:
                    allowed_values.remove(cell.value)
                assigned_cells.append(cell)

        current_sum = 0
        for cell in assigned_cells:
            current_sum += cell.value

        net_goal_sum = clue.goal_sum - current_sum
        net_cell_count = clue.length - len(assigned_cells)
        unassigned_value_sets = self.sum_to_n(net_goal_sum, net_cell_count, allowed_values)

        # Use LCV heuristic: Sort unassigned_cells based on the number of constraints on other unassigned cells
        unassigned_cells.sort(key=lambda x: self.count_constraints(x, unassigned_cells, assignment))

        for unassigned_value_set in unassigned_value_sets:
            variable_set = copy.deepcopy(cell_set)
            value_set = []
            for cell in variable_set:
                if cell.value == 0:
                    value_set.append(unassigned_value_set.pop(0))
                else:
                    value_set.append(cell.value)
            value_sets.append(value_set)

        return value_sets

    def count_constraints(self, cell, unassigned_cells, assignment):
        count = 0
        for other_cell in unassigned_cells:
            if other_cell != cell and self.is_consistent_with_other(cell, other_cell, assignment):
                count += 1
        return count

    def is_consistent_with_other(self, cell1, cell2, assignment):
        # Check if assigning the value to cell1 is consistent with the value in cell2
        assignment.assign_clue(cell1.down_clue, [cell1.value])
        assignment.assign_clue(cell2.down_clue, [cell2.value])
        consistent = assignment.is_consistent()
        # Undo the assignment for backtracking
        cell1.value = 0
        cell2.value = 0
        return consistent


    def sum_to_n(self, n, k, allowed_values):
        if k == 1 and n in allowed_values:
            return [[n]]

        combos = []
        for i in allowed_values:
            allowed_values_copy = copy.deepcopy(allowed_values)
            allowed_values_copy.remove(i)
            if n - i > 0:
                combos += [[i] + combo for combo in self.sum_to_n(n - i, k - 1, allowed_values_copy)]

        for combo in combos[:]:
            if any(combo.count(x) > 1 for x in combo):
                combos.remove(combo)

        return combos

    def is_consistent(self, clue, value_set, assignment):
        assignment.assign_clue(clue, value_set)
        assignment.print_puzzle()
        return assignment.is_consistent()

class IntelligentKakuroAgent(KakuroAgent):
    def __init__(self, puzzle):
        super().__init__(puzzle)

    def select_unassigned_clue(self, assignment):
        clue_list = []
        partial_assigned_list = []
        unassigned_list = []
        for clue in assignment.clues:
            if not assignment.is_clue_assigned(clue):
                unassigned_count = assignment.clue_unassigned_count(clue)
                if unassigned_count == clue.length:
                    unassigned_list.append((clue, unassigned_count))
                else:
                    partial_assigned_list.append((clue, unassigned_count))
        unassigned_list.sort(key=itemgetter(1))
        partial_assigned_list.sort(key=itemgetter(1))
        clue_list = partial_assigned_list + unassigned_list
        return clue_list[0][0]

if __name__ == "__main__":
    print("Choose a puzzle to solve:")
    print("1. 8x8 puzzle(Easy)")
    print("2. 8x8 puzzle(Medium)")
    print("3. 10x10 puzzle(Hard)")
    print("4. 10x10 puzzle(Expert)")

    choice = input("Enter your choice (1 to 4): ")

    if choice == "1":
        cells = []
        # 8x8 sample:
        # row 1
        cells.append(KakuroBlackCell((0, 0)))
        cells.append(KakuroBlackCell((0, 1)))
        cells.append(KakuroClueCell((0, 2), KakuroClue(DOWN, 4, 30), None))
        cells.append(KakuroClueCell((0, 3), KakuroClue(DOWN, 2, 4), None))
        cells.append(KakuroClueCell((0, 4), KakuroClue(DOWN, 3, 24), None))
        cells.append(KakuroBlackCell((0, 5)))
        cells.append(KakuroClueCell((0, 6), KakuroClue(DOWN, 2, 4), None))
        cells.append(KakuroClueCell((0, 7), KakuroClue(DOWN, 2, 16), None))


        # row 2
        cells.append(KakuroBlackCell((1, 0)))
        cells.append(KakuroClueCell((1, 1), KakuroClue(DOWN, 2, 16), KakuroClue(RIGHT, 3, 19)))
        cells.append(KakuroClueCell((1, 5), KakuroClue(DOWN, 3, 9), KakuroClue(RIGHT, 2, 10)))

        # row 3
        cells.append(KakuroClueCell((2, 0), None, KakuroClue(RIGHT, 7, 39)))


        # row 4
        cells.append(KakuroClueCell((3, 0), None, KakuroClue(RIGHT, 2, 15)))
        cells.append(KakuroClueCell((3, 3), KakuroClue(DOWN, 3, 23), KakuroClue(RIGHT, 2, 10)))
        cells.append(KakuroClueCell((3, 6), KakuroClue(DOWN, 4, 10), None))
        cells.append(KakuroBlackCell((3, 7)))

        # row 5
        cells.append(KakuroBlackCell((4, 0)))
        cells.append(KakuroClueCell((4, 1), None, KakuroClue(RIGHT, 2, 16)))
        cells.append(KakuroClueCell((4, 4), KakuroClue(DOWN, 3, 6), KakuroClue(RIGHT, 2, 4)))
        cells.append(KakuroClueCell((4, 7), KakuroClue(DOWN, 2, 16), None))

        # row 6
        cells.append(KakuroBlackCell((5, 0)))
        cells.append(KakuroClueCell((5, 1), KakuroClue(DOWN, 2, 14), None))
        cells.append(KakuroClueCell((5, 2), KakuroClue(DOWN, 2, 16), KakuroClue(RIGHT, 2, 9)))
        cells.append(KakuroClueCell((5, 5), KakuroClue(DOWN, 2, 4), KakuroClue(RIGHT, 2, 12)))


        # row 7
        cells.append(KakuroClueCell((6, 0), None, KakuroClue(RIGHT, 7, 35)))

        # row 8
        cells.append(KakuroClueCell((7, 0), None, KakuroClue(RIGHT, 2, 16)))
        cells.append(KakuroClueCell((7, 3), None, KakuroClue(RIGHT, 3, 7)))
        cells.append(KakuroBlackCell((7, 7)))

        # create the puzzle
        puzzle = KakuroPuzzle(8, 8, cells)
        
    elif choice == "2":
        cells = []
        # 8x8 sample:
        # row 1
        cells.append(KakuroBlackCell((0, 0)))
        cells.append(KakuroBlackCell((0, 1)))
        cells.append(KakuroClueCell((0, 2), KakuroClue(DOWN, 4, 20), None))
        cells.append(KakuroClueCell((0, 3), KakuroClue(DOWN, 2, 3), None))
        cells.append(KakuroClueCell((0, 4), KakuroClue(DOWN, 3, 23), None))
        cells.append(KakuroBlackCell((0, 5)))
        cells.append(KakuroClueCell((0, 6), KakuroClue(DOWN, 2, 12), None))
        cells.append(KakuroClueCell((0, 7), KakuroClue(DOWN, 2, 16), None))


        # row 2
        cells.append(KakuroBlackCell((1, 0)))
        cells.append(KakuroClueCell((1, 1), KakuroClue(DOWN, 2, 5), KakuroClue(RIGHT, 3, 12)))
        cells.append(KakuroClueCell((1, 5), KakuroClue(DOWN, 3, 24), KakuroClue(RIGHT, 2, 16)))

        # row 3
        cells.append(KakuroClueCell((2, 0), None, KakuroClue(RIGHT, 7, 41)))

        # row 4
        cells.append(KakuroClueCell((3, 0), None, KakuroClue(RIGHT, 2, 3)))
        cells.append(KakuroClueCell((3, 3), KakuroClue(DOWN, 3, 24), KakuroClue(RIGHT, 2, 13)))
        cells.append(KakuroClueCell((3, 6), KakuroClue(DOWN, 4, 11), None))
        cells.append(KakuroBlackCell((3, 7)))

        # row 5
        cells.append(KakuroBlackCell((4, 0)))
        cells.append(KakuroClueCell((4, 1), None, KakuroClue(RIGHT, 2, 17)))
        cells.append(KakuroClueCell((4, 4), KakuroClue(DOWN, 3, 23), KakuroClue(RIGHT, 2, 10)))
        cells.append(KakuroClueCell((4, 7), KakuroClue(DOWN, 2, 16), None))

        # row 6
        cells.append(KakuroBlackCell((5, 0)))
        cells.append(KakuroClueCell((5, 1), KakuroClue(DOWN, 2, 14), None))
        cells.append(KakuroClueCell((5, 2), KakuroClue(DOWN, 2, 5), KakuroClue(RIGHT, 2, 16)))
        cells.append(KakuroClueCell((5, 5), KakuroClue(DOWN, 2, 17), KakuroClue(RIGHT, 2, 11)))

        # row 7
        cells.append(KakuroClueCell((6, 0), None, KakuroClue(RIGHT, 7, 42)))

        # row 8
        cells.append(KakuroClueCell((7, 0), None, KakuroClue(RIGHT, 2, 10)))
        cells.append(KakuroClueCell((7, 3), None, KakuroClue(RIGHT, 3, 22)))
        cells.append(KakuroBlackCell((7, 7)))

        # create the puzzle
        puzzle = KakuroPuzzle(8, 8, cells)

    elif choice == "3":
        cells = []
        # 10x10 sample:
        # row 1
        cells.append(KakuroBlackCell((0, 0)))
        cells.append(KakuroClueCell((0, 1), KakuroClue(DOWN, 2, 10), None))
        cells.append(KakuroClueCell((0, 2), KakuroClue(DOWN, 3, 10), None))
        cells.append(KakuroBlackCell((0, 3)))
        cells.append(KakuroBlackCell((0, 4)))
        cells.append(KakuroBlackCell((0, 5)))
        cells.append(KakuroBlackCell((0, 6)))
        cells.append(KakuroBlackCell((0, 7)))
        cells.append(KakuroClueCell((0, 8), KakuroClue(DOWN, 3, 23), None))
        cells.append(KakuroClueCell((0, 9), KakuroClue(DOWN, 2, 16), None))

        # row 2
        cells.append(KakuroClueCell((1, 0), None, KakuroClue(RIGHT, 2, 4)))
        cells.append(KakuroClueCell((1, 3), KakuroClue(DOWN, 2, 17), None))
        cells.append(KakuroBlackCell((1, 4)))
        cells.append(KakuroBlackCell((1, 5)))
        cells.append(KakuroBlackCell((1, 6)))
        cells.append(KakuroClueCell((1, 7), KakuroClue(DOWN, 3, 17), KakuroClue(RIGHT, 2, 16)))

        # row 3
        cells.append(KakuroClueCell((2, 0), None, KakuroClue(RIGHT, 3, 23)))
        cells.append(KakuroClueCell((2, 4), KakuroClue(DOWN, 5, 20), None))
        cells.append(KakuroBlackCell((2, 5)))
        cells.append(KakuroClueCell((2, 6), KakuroClue(DOWN, 5, 30), KakuroClue(RIGHT, 3, 24)))

        # row 4
        cells.append(KakuroBlackCell((3, 0)))
        cells.append(KakuroClueCell((3, 1), None, KakuroClue(RIGHT, 3, 13)))
        cells.append(KakuroClueCell((3, 5), KakuroClue(DOWN, 3, 20), KakuroClue(RIGHT, 3, 23)))
        cells.append(KakuroBlackCell((3, 9)))

        # row 5
        cells.append(KakuroBlackCell((4, 0)))
        cells.append(KakuroBlackCell((4, 1)))
        cells.append(KakuroBlackCell((4, 2)))
        cells.append(KakuroClueCell((4, 3), None, KakuroClue(RIGHT, 4, 11)))
        cells.append(KakuroBlackCell((4, 8)))
        cells.append(KakuroBlackCell((4, 9)))

        # row 6
        cells.append(KakuroBlackCell((5, 0)))
        cells.append(KakuroBlackCell((5, 1)))
        cells.append(KakuroBlackCell((5, 2)))
        cells.append(KakuroClueCell((5, 3), KakuroClue(DOWN, 3, 6), KakuroClue(RIGHT, 3, 23)))
        cells.append(KakuroBlackCell((5, 7)))
        cells.append(KakuroBlackCell((5, 8)))
        cells.append(KakuroBlackCell((5, 9)))

        # row 7
        cells.append(KakuroBlackCell((6, 0)))
        cells.append(KakuroBlackCell((6, 1)))
        cells.append(KakuroClueCell((6, 2), KakuroClue(DOWN, 3, 7), KakuroClue(RIGHT, 4, 25)))
        cells.append(KakuroClueCell((6, 7), KakuroClue(DOWN, 2, 3), None))
        cells.append(KakuroClueCell((6, 8), KakuroClue(DOWN, 3, 9), None))
        cells.append(KakuroBlackCell((6, 9)))

        # row 8
        cells.append(KakuroBlackCell((7, 0)))
        cells.append(KakuroClueCell((7, 1), KakuroClue(DOWN, 2, 4), KakuroClue(RIGHT, 3, 8)))
        cells.append(KakuroClueCell((7, 5), None, KakuroClue(RIGHT, 3, 7)))
        cells.append(KakuroClueCell((7, 9), KakuroClue(DOWN, 2, 4), None))

        # row 9
        cells.append(KakuroClueCell((8, 0), None, KakuroClue(RIGHT, 3, 6)))
        cells.append(KakuroBlackCell((8, 4)))
        cells.append(KakuroBlackCell((8, 5)))
        cells.append(KakuroClueCell((8, 6), None, KakuroClue(RIGHT, 3, 6)))

        # row 10
        cells.append(KakuroClueCell((9, 0), None, KakuroClue(RIGHT, 2, 3)))
        cells.append(KakuroBlackCell((9, 3)))
        cells.append(KakuroBlackCell((9, 4)))
        cells.append(KakuroBlackCell((9, 5)))
        cells.append(KakuroBlackCell((9, 6)))
        cells.append(KakuroClueCell((9, 7), None, KakuroClue(RIGHT, 2, 4)))

        # create the puzzle
        puzzle = KakuroPuzzle(10, 10, cells)

    elif choice == "4":
        cells = []
        # 10x10 sample:
        # row 1
        cells.append(KakuroBlackCell((0, 0)))
        cells.append(KakuroBlackCell((0, 1)))
        cells.append(KakuroBlackCell((0, 2)))
        cells.append(KakuroClueCell((0, 3), KakuroClue(DOWN, 2, 17), None))
        cells.append(KakuroClueCell((0, 4), KakuroClue(DOWN, 3, 19), None))
        cells.append(KakuroBlackCell((0, 5)))
        cells.append(KakuroBlackCell((0, 6)))
        cells.append(KakuroClueCell((0, 7), KakuroClue(DOWN, 3, 7), None))
        cells.append(KakuroClueCell((0, 8), KakuroClue(DOWN, 8, 44), None))
        cells.append(KakuroBlackCell((0, 9)))

        # row 2
        cells.append(KakuroBlackCell((1, 0)))
        cells.append(KakuroClueCell((1, 1), KakuroClue(DOWN, 2, 3), None))
        cells.append(KakuroClueCell((1, 2), KakuroClue(DOWN, 8, 37), KakuroClue(RIGHT, 2, 17)))
        cells.append(KakuroBlackCell((1, 5)))
        cells.append(KakuroClueCell((1, 6), None, KakuroClue(RIGHT, 2, 10)))
        cells.append(KakuroClueCell((1, 9), KakuroClue(DOWN, 3, 23), None))

        # row 3
        cells.append(KakuroClueCell((2, 0), None, KakuroClue(RIGHT, 4, 20)))
        cells.append(KakuroClueCell((2, 5), KakuroClue(DOWN, 2, 6), None))
        cells.append(KakuroClueCell((2, 6), KakuroClue(DOWN, 2, 3), KakuroClue(RIGHT, 3, 15)))

        # row 4
        cells.append(KakuroClueCell((3, 0), None, KakuroClue(RIGHT, 2, 5)))
        cells.append(KakuroClueCell((3, 3), KakuroClue(DOWN, 2, 3), KakuroClue(RIGHT, 6, 25)))

        # row 5
        cells.append(KakuroBlackCell((4, 0)))
        cells.append(KakuroClueCell((4, 1), None, KakuroClue(RIGHT, 2, 8)))
        cells.append(KakuroClueCell((4, 4), None, KakuroClue(RIGHT, 2, 3)))
        cells.append(KakuroClueCell((4, 7), KakuroClue(DOWN, 2, 10), KakuroClue(RIGHT, 2, 15)))

        # row 6
        cells.append(KakuroBlackCell((5, 0)))
        cells.append(KakuroClueCell((5, 1), KakuroClue(DOWN, 3, 13), KakuroClue(RIGHT, 2, 3)))
        cells.append(KakuroClueCell((5, 4), KakuroClue(DOWN, 2, 7), None))
        cells.append(KakuroClueCell((5, 5), KakuroClue(DOWN, 2, 5), None))
        cells.append(KakuroClueCell((5, 6), None, KakuroClue(RIGHT, 2, 17)))
        cells.append(KakuroBlackCell((5, 9)))

        # row 7
        cells.append(KakuroClueCell((6, 0), None, KakuroClue(RIGHT, 2, 9)))
        cells.append(KakuroClueCell((6, 3), KakuroClue(DOWN, 3, 10), KakuroClue(RIGHT, 2, 3)))
        cells.append(KakuroClueCell((6, 6), KakuroClue(DOWN, 3, 16), KakuroClue(RIGHT, 2, 6)))
        cells.append(KakuroClueCell((6, 9), KakuroClue(DOWN, 2, 11), None))

        # row 8
        cells.append(KakuroClueCell((7, 0), None, KakuroClue(RIGHT, 6, 38)))
        cells.append(KakuroClueCell((7, 7), KakuroClue(DOWN, 2, 3), KakuroClue(RIGHT, 2, 17)))

        # row 9
        cells.append(KakuroClueCell((8, 0), None, KakuroClue(RIGHT, 3, 7)))
        cells.append(KakuroBlackCell((8, 4)))
        cells.append(KakuroClueCell((8, 5), None, KakuroClue(RIGHT, 4, 12)))

        # row 10
        cells.append(KakuroBlackCell((9, 0)))
        cells.append(KakuroClueCell((9, 1), None, KakuroClue(RIGHT, 2, 4)))
        cells.append(KakuroBlackCell((9, 4)))
        cells.append(KakuroClueCell((9, 5), None, KakuroClue(RIGHT, 2, 3)))
        cells.append(KakuroBlackCell((9, 8)))
        cells.append(KakuroBlackCell((9, 9)))

        # create the puzzle
        puzzle = KakuroPuzzle(10, 10, cells)
    else:
        print("Invalid choice. Exiting.")
        exit()

    intelligent_agent = IntelligentKakuroAgent(copy.deepcopy(puzzle))
    intelligent_start = timeit.default_timer()
    intelligent_agent.solve()
    intelligent_stop = timeit.default_timer()
    intelligent_time = intelligent_stop - intelligent_start

    print("Intelligent agent solved the puzzle in:", str(intelligent_time))