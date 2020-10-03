# Represents either a Row or a Column (9x1 or 1x9)
# or an Area (3x3)
class Section:
    def __init__(self, nums_in_section):
        self.valid = True
        self.values = set([])
        
        # Add each value in, checking for duplicates
        for num in nums_in_section:
            # Flag the row and stop as soon as we find a duplicate
            if num in self.values:
                self.valid = False
                break
            else:
                self.values.add(num)
                
        # Check to see if we have all 9 numbers
        if len(self.values) != 9:
            self.valid = False
        
def done_or_not(board): #board[i][j]
    # First check if every row is valid
    for i in range(9):
        if not Section(board[i]).valid:
            return "Try again!"
            
    # Check if every column is valid
    for i in range(9):
        column = []
        for j in range(9): # Generate the column
            column.append(board[j][i])
        # Check the column
        if not Section(column).valid:
            return "Try again!"
            
    # Indexing for each of the 3x3 area of the board
    section_indices = {
        0 : [0,2, 0,2], 1 : [3,5, 0,2], 2 : [6,8, 0,2],
        3 : [0,2, 3,5], 4 : [3,5, 3,5], 5 : [6,8, 3,5],
        6 : [0,2, 6,8], 7 : [3,5, 6,8], 8 : [6,8, 6,8]
    }
    
    # Lastly check each area
    for i in range(9):
        area = []   
        
        row_start = section_indices[i][0]
        row_end = section_indices[i][1]
        column_start = section_indices[i][2]
        column_end = section_indices[i][3]
        
        for row in range(row_start, row_end+1, 1):
            for column in range(column_start, column_end+1, 1):
                area.append(board[row][column])
                
        if not Section(area).valid:
            return "Try again!"
    
    return "Finished!"