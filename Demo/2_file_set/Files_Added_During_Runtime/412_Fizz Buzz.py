from collections import OrderedDict

class Solution:
    def fizzBuzz(self, n: int):
        str_num = []
        # Maps a divisor to the replacing string, scales better
        # since we can easily add new entires EX: 3 -> "Fizz", 5 -> "Buzz"
        divisible = OrderedDict()
        # We would need to use an ordered dictionary because if divisible
        # By 3 AND 5, Fizz must be appended BEFORE Buzz 
        divisible[3] = "Fizz"
        divisible[5] = "Buzz"

        for currentNumber in range (1, n+1, 1):
            str_toAppend = ""

            # Check if the current number is a multiple
            for divisor in divisible:
                if currentNumber % divisor == 0:
                    str_toAppend += divisible[divisor]

            # If a multiple of none by this point, append the value
            if len(str_toAppend) == 0:
                str_toAppend = str(currentNumber)
            
            str_num.append(str_toAppend)
        
        return str_num


s = Solution()
s.fizzBuzz(15)
