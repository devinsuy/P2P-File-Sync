#-------------------------------------------------------------------#				 
#	Devin Suy
#   ID: 017001983
#	Date: 7/14/2020
#	email: DevinSuy@gmail.com
#   version: 1.0.0
#------------------------------------------------------------------
from Board.GameBoard import GameBoard
import sys

class DFS:
    def __init__(self, graph, file_name, output_folder):
        self.graph = graph
        self.file_name = file_name[:-8]                             # Trim to just the "size" of the maze
        self.output_folder = output_folder
        self.num_expanded = self.max_fringe = self.current_fringe = 0

        self.solutions = []
        self.current_solution = []
        self.solutions_nums = []
        self.current_solution_nums = []

        self.start_cell = self.graph.cells[self.graph.start_cell]
        self.goal_cell = self.graph.cells[self.graph.goal_cell]

    
    def reset_stats(self):
        self.solutions.clear()
        self.current_solution.clear()
        self.solutions_nums.clear()
        self.current_solution_nums.clear()
        self.num_expanded = self.max_fringe = self.current_fringe = 0

    
    # Depth First Search algorithm using LIFO stack
    def DFS(self):
        stack = [self.start_cell]                                   # Initialize our stack with our starting cell
        self.start_cell.visited = True
        
        while stack:
            current_cell = stack[-1]                                # Poll the head of our "stack"

            # This is our first time at this node, expand it
            if not current_cell.visited:
                self.num_expanded += 1

            current_cell.visited = True

            # Bookkeeping
            if len(stack) > self.max_fringe:
                self.max_fringe = len(stack)
            
            # Process all unvisited neighbors of our curent cell
            dead_end = True
            for adj_cell_num, adj_cell in current_cell.adj.items():
                if adj_cell_num == self.graph.goal_cell:
                    print("\nDFS First Solution Found!\n-------------------------")
        
                    # Retrace the solution path
                    current_solution = [adj_cell]
                    path_cell = current_cell

                    while path_cell != False:
                        current_solution.append(path_cell)
                        path_cell = path_cell.prev

                    # Change the ordering of cells from end -> start to start -> end
                    return current_solution[::-1]
                    
                else:
                    if not adj_cell.visited:
                        dead_end = False
                        stack.append(adj_cell)
                        adj_cell.prev = current_cell            # Maintain a parent pointer so we can retrace our solution path
                        break                                   # Process one neighbor at a time, advance "deeper" until backtracked
                    
            # If there are no futher neighbors to traverse deeper into
            # remove from stack and backtrack
            if dead_end:
                stack.pop()            

        # If the queue empties without finding a solution, all have been found
        return False    


    def exhaustive_DFS_util(self, src, dst):
        src.visited = True
        self.current_solution_nums.append(src.cell_num)
        self.current_solution.append(src)

        # Goal cell was reached, save the solution
        if src == dst:
            self.solutions_nums.append(self.current_solution_nums[::-1])        # Append the reversed path
            self.solutions.append(self.current_solution[::-1])

        # Otherwise, process neighbors
        for adj_id, adj_node in src.adj.items():
            if not adj_node.visited:
                self.current_fringe += 1
                if self.current_fringe > self.max_fringe:
                    self.max_fringe = self.current_fringe
                
                self.exhaustive_DFS_util(adj_node, dst)                                # Recurr

        # If here we reached a dead end, no more unvisited adjacent
        # neighbors to traverse deeper into, backtrack
        self.current_solution_nums.pop()
        self.current_solution.pop()
        src.visited = False
        src.completed = True
        self.current_fringe -= 1


    def find_first_solution(self):
        self.graph.reset_cells()
        self.reset_stats()
        solution = self.DFS()
        
        # Output results
        print("Path: ", [cell.cell_num for cell in solution] )
        print("Solution Length: ", len(solution), "\n")
        print("(DFS First Solution) Number of Expanded Nodes: ", self.num_expanded)
        print("(DFS First Solution) Max Fringe Size: ", self.max_fringe, "\n\n")

        self.graph.write_solution(self.file_name + "_DFS_First_Solution", self.output_folder.joinpath("DFS"), solution)
        self.graph.write_solution(self.file_name + "_DFS_First_Solution", self.output_folder.joinpath("DFS/DFS_All_" + self.file_name + "_Solutions"), solution)


    def perform_search(self):
        self.graph.reset_cells()
        self.reset_stats()

        # Start DFS from the initial cell to goal
        self.exhaustive_DFS_util(self.start_cell, self.goal_cell)

        # Print all solution numbers
        solution_count = 1
        for solution in self.solutions_nums:
            solution = solution[::-1]
            print("(DFS Exhaustive) Solution #", solution_count, " length: ", len(solution))
            # print("Path: ", solution)
            solution_count += 1
        print("(DFS Exhaustive) Number of Expanded Nodes: ", len(self.graph.cells))
        print("(DFS Exhaustive) Max Fringe Size: ", self.max_fringe, "\n\n")

        # Write all solutions to maze .lay files and locate the optimal least cost solution
        solution_count = 1
        min_solution = None
        min_cost = float('inf')
        for solution in self.solutions:
            solution = solution[::-1]
            if len(solution) < min_cost:
                min_cost = len(solution)
                min_solution = solution

            self.graph.write_solution(self.file_name + "_DFS_Solution_" + str(solution_count), self.output_folder.joinpath("DFS/DFS_All_" + self.file_name + "_Solutions"), solution)
            solution_count += 1
        
        print("All solutions written to :", self.output_folder.joinpath("DFS/DFS_All_" + self.file_name + "_Solutions"))
        
        print("\nOptimal DFS solution located, length: ", min_cost)
        optimal_path = [cell.cell_num for cell in min_solution] 
        # print("Path: ", optimal_path)

        # Write the optimal solution
        self.graph.write_solution(self.file_name + "_DFS_Optimal_Solution", self.output_folder.joinpath("DFS"), min_solution)
        print("Optimal solution written to: ", self.output_folder.joinpath("DFS"), "\\", self.file_name + "_DFS_Optimal_Solution.lay")

        





    