from timeit import default_timer as timer
import threading
import copy


class CSP:

    def __init__(self, variables, domains, neighbors, constraints):
        variables = variables or list(domains.keys())
        self.variables = variables
        self.domains = domains
        self.neighbors = neighbors
        self.constraints = constraints
        self.initial = ()
        self.curr_domains = None
        self.nassigns = 0
        self.n_bt = 0
    
    def assign(self, var, val, assignment):
        """Add {var: val} to assignment; Discard the old value if any."""
        assignment[var] = val
        self.nassigns += 1

    def unassign(self, var, assignment):
        """Remove {var: val} from assignment.
        DO NOT call this if you are changing a variable to a new value;
        just call assign for that."""
        if var in assignment:
            del assignment[var]

# @Modified: the original used a recursive function, in my opinion this one looks better
#            and is easier to understand

    def nconflicts(self, var, val, assignment):
        """Return the number of conflicts var=val has with other variables."""
        count = 0
        for var2 in self.neighbors.get(var):
            val2 = None
            if assignment.__contains__(var2):
                val2 = assignment[var2]
            if val2 is not None and self.constraints(var, val, var2, val2) is False:
                count += 1
        return count

    def display(self, assignment):
        """Show a human-readable representation of the CSP."""
        # Subclasses can print in a prettier way, or display with a GUI
        print('CSP:', self, 'with assignment:', assignment)

    def goal_test(self, state):
        """The goal is to assign all variables, with all constraints satisfied."""
        assignment = dict(state)
        return (len(assignment) == len(self.variables)
                and all(self.nconflicts(variables, assignment[variables], assignment) == 0
                        for variables in self.variables))

    # These are for constraint propagation

    def support_pruning(self):
        """Make sure we can prune values from domains. (We want to pay
        for this only if we use it.)"""
        if self.curr_domains is None:
            self.curr_domains = {v: list(self.domains[v]) for v in self.variables}

    def suppose(self, var, value):
        """Start accumulating inferences from assuming var=value."""
        self.support_pruning()
        removals = [(var, a) for a in self.curr_domains[var] if a != value]
        self.curr_domains[var] = [value]
        return removals

    def prune(self, var, value, removals):
        """Rule out var=value."""
        self.curr_domains[var].remove(value)
        if removals is not None:
            removals.append((var, value))

    def choices(self, var):
        """Return all values for var that aren't currently ruled out."""
        return (self.curr_domains or self.domains)[var]

    def restore(self, removals):
        """Undo a supposition and all inferences from it."""
        for B, b in removals:
            self.curr_domains[B].append(b)


# ______________a________________________________________________________________
# Constraint Propagation with AC-3

def AC3(csp, queue=None, removals=None):
    """[Figure 6.3]"""
    if queue is None:
        queue = [(Xi, Xk) for Xi in csp.variables for Xk in csp.neighbors[Xi]]
    csp.support_pruning()
    while queue:
        (Xi, Xj) = queue.pop()
        if revise(csp, Xi, Xj, removals):
            if not csp.curr_domains[Xi]:
                return False
            for Xk in csp.neighbors[Xi]:
                if Xk != Xi:
                    queue.append((Xk, Xi))
    return True


def revise(csp, Xi, Xj, removals):
    """Return true if we remove a value."""
    revised = False
    for x in csp.curr_domains[Xi][:]:
        # If Xi=x conflicts with Xj=y for every possible y, eliminate Xi=x
        if all(not csp.constraints(Xi, x, Xj, y) for y in csp.curr_domains[Xj]):
            csp.prune(Xi, x, removals)
            revised = True
    return revised

# ______________________________________________________________________________
# CSP Backtracking Search

# Variable ordering


# @Modified: we just want the first one that haven't been assigned so returning fast is good
def first_unassigned_variable(assignment, csp):
    """The default variable order."""
    for var in csp.variables:
        if var not in assignment:
            return var


# @Modified: the original used a function from util files and was harder to understand,
#            it also apparently used 2 for loops: one to find the minimum and
#            other one to create a list (and a lambda function)
def mrv(assignment, csp):
    """Minimum-remaining-values heuristic."""
    vars_to_check = []
    size = []
    for v in csp.variables:
        if v not in assignment.keys():
            vars_to_check.append(v)
            size.append(num_legal_values(csp, v, assignment))
    return vars_to_check[size.index(min(size))]


# @Modified: the original used a function count and a list, in my opinion it is faster to
#            just count with a loop 'for' without calling external functions
def num_legal_values(csp, var, assignment):
    if csp.curr_domains:
        return len(csp.curr_domains[var])
    else:
        count = 0
        for val in csp.domains[var]:
            if csp.nconflicts(var, val, assignment) == 0:
                count += 1
        return count

# Value ordering


def unordered_domain_values(var, assignment, csp):
    """The default value order."""
    return csp.choices(var)


def lcv(var, assignment, csp):
    """Least-constraining-values heuristic."""
    return sorted(csp.choices(var),
                  key=lambda val: csp.nconflicts(var, val, assignment))


# Inference


def no_inference(csp, var, value, assignment, removals):
    return True


def forward_checking(csp, var, value, assignment, removals):
    """Prune neighbor values inconsistent with var=value."""
    for B in csp.neighbors[var]:
        if B not in assignment:
            for b in csp.curr_domains[B][:]:
                if not csp.constraints(var, value, B, b):
                    csp.prune(B, b, removals)
            if not csp.curr_domains[B]:
                return False
    return True


def mac(csp, var, value, assignment, removals):
    """Maintain arc consistency."""
    return AC3(csp, [(X, var) for X in csp.neighbors[var]], removals)

# The search, proper

# @Modified: we should notice that with MRV it works good since the partial initial state
#            leaves some variables with unitary domain so we will start to assign these variables.
#            Added csp.n_bt+=1


def backtracking_search(csp,
                        select_unassigned_variable,
                        order_domain_values,
                        inference):
    """[Figure 6.5]"""
    def backtrack(assignment):
        if len(assignment) == len(csp.variables):
            return assignment
        var = select_unassigned_variable(assignment, csp)
        for value in order_domain_values(var, assignment, csp):
            if 0 == csp.nconflicts(var, value, assignment):
                csp.assign(var, value, assignment)
                removals = csp.suppose(var, value)
                if inference(csp, var, value, assignment, removals):
                    result = backtrack(assignment)
                    if result is not None:
                        return result
                    else:
                        csp.n_bt += 1
                csp.restore(removals)
        csp.unassign(var, assignment)
        return None

    result = backtrack({})
    assert result is None or csp.goal_test(result)
    return result


def different_values_constraint(A, a, B, b):
    """A constraint saying two neighboring variables must differ in value."""
    return a != b

class SudokuCSP(CSP):

    def __init__(self, board):

        self.domains = {}
        self.neighbors = {}
        # our variables will be named as "CELL NUMBER"
        for v in range(81):
            self.neighbors.update({'CELL' + str(v): {}})
        for i in range(9):
            for j in range(9):
                name = (i * 9 + j)
                var = "CELL"+str(name)
                self.add_neighbor(var, self.get_row(i) | self.get_column(j) | self.get_square(i, j))
                # if the board has a value in cell[i][j] the domain of this variable will be that number
                if board[i][j] != 0:
                    self.domains.update({var: str(board[i][j])})
                else:
                    self.domains.update({var: '123456789'})

        CSP.__init__(self, None, self.domains, self.neighbors, different_values_constraint)

    # returns the right square box given row and column index
    def get_square(self, i, j):
        if i < 3:
            if j < 3:
                return self.get_square_box(0)
            elif j < 6:
                return self.get_square_box(3)
            else:
                return self.get_square_box(6)
        elif i < 6:
            if j < 3:
                return self.get_square_box(27)
            elif j < 6:
                return self.get_square_box(30)
            else:
                return self.get_square_box(33)
        else:
            if j < 3:
                return self.get_square_box(54)
            elif j < 6:
                return self.get_square_box(57)
            else:
                return self.get_square_box(60)

    # returns the square of the index's variabile, it must be 0, 3, 6, 27, 30, 33, 54, 57 or 60
    def get_square_box(self, index):
        tmp = set()
        tmp.add("CELL"+str(index))
        tmp.add("CELL"+str(index+1))
        tmp.add("CELL"+str(index+2))
        tmp.add("CELL"+str(index+9))
        tmp.add("CELL"+str(index+10))
        tmp.add("CELL"+str(index+11))
        tmp.add("CELL"+str(index+18))
        tmp.add("CELL"+str(index+19))
        tmp.add("CELL"+str(index+20))
        return tmp

    def get_column(self, index):
        return {'CELL'+str(j) for j in range(index, index+81, 9)}

    def get_row(self, index):
            return {('CELL' + str(x + index * 9)) for x in range(9)}

    def add_neighbor(self, var, elements):
        # we dont want to add variable as its self neighbor
        self.neighbors.update({var: {x for x in elements if x != var}})

class Main:

    def __init__(self):
        # we start with a blank board
        self.original_board = [[0 for j in range(9)] for i in range(9)]

        x,y = 0,0
        for x in range(9):
            for y in range(9):
                self.original_board[x][y] = sudoku.Cellules[x][y]

        # ofc we should have another board in which we will show solution
        self.current_board = copy.deepcopy(self.original_board)
        self.row, self.col = 0, 0
             

    def solve_sudoku(self):

        s = SudokuCSP(self.current_board)
        inf, dv, suv = None, None, None

        if inference == 0:
            inf = no_inference
        elif inference == 1:
            inf = forward_checking
        elif inference == 2:
            inf = mac


        suv = first_unassigned_variable
        if useMRVHeuristics:
            suv = mrv
        odv = unordered_domain_values
        if useLCVHeuristics:
            odv = lcv

        start = timer()
        a = backtracking_search(s, select_unassigned_variable=suv, order_domain_values=odv, inference=inf)
        end = timer()
        # if a isn't null we found a solution so we will show it in the current board
        # if a is null then we send a message to the user that the initial board
        # breaks some constraints
        if a:
            for i in range(9):
                for j in range(9):
                    index = i * 9 + j
                    self.current_board[i][j] = a.get("CELL" + str(index))
                    sudoku.Cellules[i][j] = int(a.get("CELL" + str(index)))
        else:
           print("Error", "Invalid sudoku puzzle, please check the initial state")


    def __clear_board(self):
        self.current_board = copy.deepcopy(self.original_board)
        self.__draw_puzzle()

main = Main()
main.solve_sudoku()