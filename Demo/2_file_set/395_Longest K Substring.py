class Solution:
    def __init__(self):
        self.max_subLength = 0

    def isValidSubstring(self, s, k):
        occurrences = self.findNumOccurrences(s)

        for letter in occurrences:
            if occurrences[letter] < k:
                return False
        
        return True

    def findNumOccurrences(self, s):
        occurrences = {}

        for currentLetter in s:
            if currentLetter not in occurrences:
                occurrences[currentLetter] = 1
            else:
                occurrences[currentLetter] += 1
        
        return occurrences

    def findLetterIndices(self, s):
        indices = {}

        index = 0
        for currentLetter in s:
            if currentLetter not in indices:
                indices[currentLetter] = [index]
            else:
                indices[currentLetter].append(index)

            index += 1
        
        return indices

    def createSubStrings(self, s, k):
        excluded_letters = []
        occurrences = self.findNumOccurrences(s)
        indices = self.findLetterIndices(s)

        # Determine which letter we must exclude from any substring
        for currentLetter in occurrences:
            if occurrences[currentLetter] < k:
                excluded_letters.append(currentLetter)

        if not excluded_letters:
            return [s]

        excluded_indices = []
        # Obtain a list of sorted indices no substring may include
        for letter in excluded_letters:
            for excluded_index in indices[letter]:
                excluded_indices.append(excluded_index)
        excluded_indices.sort()

        # Generate a list of substrings around each excluded index
        exclusive_substrs = []
        sliceStart = 0
        for xIndex in excluded_indices:
            exclusive_substrs.append(s[sliceStart:xIndex])
            sliceStart = xIndex + 1
        
        # If our last excluded index isn't the end of the string, there
        # is still one more substr that goes to the end of the string
        if excluded_indices[-1] != (len(s) - 1):
            exclusive_substrs.append(s[excluded_indices[-1] + 1 : len(s)])

        return exclusive_substrs


    # Updates max length of valid substrings from our original string
    # Returns all substrings that are not valid, because they may have
    # potentially valid substrings within them
    def update_maxLength(self, s, k):
        exclusive_substrs = self.createSubStrings(s, k)
        invalid_substrs = []

        # Now consider each of our valid substrings to find the longest one
        for substr in exclusive_substrs:
            if self.isValidSubstring(substr, k):
                if len(substr) > self.max_subLength:
                    self.max_subLength = len(substr)
            else:
                invalid_substrs.append(substr)

        return invalid_substrs


    def longestSubstring(self, s: str, k: int) -> int:
        numStrs = index = 0

        # Updates max_subLength and assigns all invalid substrings to nextStrings
        nextStrings = self.update_maxLength(s, k)
        numStrs = len(nextStrings)

        # Iterates over nextStrings, appending the returned invalid strings to be
        # checked to the end of the list
        while index < numStrs:
            currentString = nextStrings[index]
            index += 1
            
            strs_toAdd = self.update_maxLength(currentString, k)
            numStrs += len(strs_toAdd)
            nextStrings.extend(strs_toAdd)

        # By here all substrings of the orignal string have been checked as well as
        # all possible substrings of every layer of invalid substrings
        return self.max_subLength


            

s = Solution()
print(s.longestSubstring("zzzzzzzzzzaaaaaaaaabbbbbbbbhbhbhbhbhbhbhicbcbcibcbccccccccccbbbbbbbbaaaaaaaaafffaahhhhhiaahiiiiiiiiifeeeeeeeeee",10))
