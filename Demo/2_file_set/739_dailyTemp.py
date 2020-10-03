class Solution:
    def dailyTemperatures(self, T):
        # Initialize all values to 0
        greater_index = [0] * len(T)
        stack = []

        # Iterate backwards, use indices not the actual values
        for index in range(len(T)-1, -1, -1):
            currentValue = T[index]
            if stack:
                top_stackValue = T[stack[-1]]

            # Remove all values on the stack <= our current value
            while stack and top_stackValue <= currentValue:
                stack.pop()
                if stack:
                    top_stackValue = T[stack[-1]]

            # Anything still remaining on the stack has a value > currentValue, 
            # take the first one as our answer  FILO 
            if stack:
                greater_index[index] = stack[-1] - index

            # Every index is added to the stack, since we later remove 
            # those that are smaller anyway to only consider higher temps
            stack.append(index)
        
        return greater_index
        


        # days = []
        # temps = {}
        # # Maps a value to a list of values greater than our current value in T
        # # EX: For [73, 74, 75, 71, 69, 72, 76, 73], values_greater[74] stores a list of all values > 74: 75, 76
        # values_greater = {} 
        

        # # First linear pass to map our values, (value -> list of indexes this value is found) and initializes values_greater
        # # NOTE: The list of indices the value maps to retains ascending order
        # index = 0
        # for temperature in T:
        #     if temperature in temps:
        #         temps[temperature].append(index)
        #     else:
        #         temps[temperature] = [index]

        #     if temperature not in values_greater:
        #         values_greater[temperature] = []
        #     index += 1

        # # Now pass through the set of temperatures and map values_greater
        # for i in values_greater:
        #     for j in values_greater:
        #         if i == j: continue
        #         elif j > i:
        #             values_greater[i].append(j)

        # for i in range(len(T)):
        #     currentValue = T[i]
        #     # Append 0 if there are no values greater than ours in the entire array
        #     if len(values_greater[currentValue]) == 0:
        #         days.append(0)
        #         continue

        #     # Temperatures are constrainted to [30,100], indices [1, 30000]
        #     minIndex = 30001
        #     stopSearch = False
        #     search_value_index = 0
            
        #     while search_value_index < len(values_greater[currentValue]):
        #         if stopSearch:
        #             break
        #         search_value = values_greater[currentValue][search_value_index]
        #         search_value_index += 1

        #         indices = temps[search_value]

        #         # Get the list of all indices where the the value is found
        #         for index in indices:
        #             if index - i > minIndex:
        #                 continue
        #             if index > i:
        #                 if index - i < minIndex:
        #                     minIndex = index - i
        #                     if minIndex == 1:
        #                         stopSearch = True
        #                         break    

        #     if minIndex == 30001: # A value was not found
        #         days.append(0)
        #     else:
        #         days.append(minIndex)

        # print(days)
        # return days

        # n^2 solution
        # for i in range(len(T)):
        #     currentValue = T[i]
        #     count = 0
        #     valueFound = False
        #     for j in range(i+1, len(T)):
        #         count += 1
        #         nextValue = T[j]
        #         if nextValue > currentValue:
        #             days.append(count)
        #             valueFound = True
        #             break
        #     if not valueFound:
        #         days.append(0)
        # return days


T = [73, 74, 75, 71, 69, 72, 76, 73]
s = Solution()
s.dailyTemperatures(T)
