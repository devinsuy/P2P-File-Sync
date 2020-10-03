class Solution:
    exponentValues = {}

    def createBitString(self, decimalValue):
        if decimalValue == 0 : return "0"
        numBits = 1
        currentValue = self.findBitValue(numBits)


        # Determine the number of bits needed to represent the value
        while currentValue < decimalValue:
            numBits += 1
            currentValue = self.findBitValue(numBits)
    
        if(currentValue > decimalValue):
            numBits -= 1
            currentValue = self.findBitValue(numBits)

        
        # Sets our highest bit
        bits = []
        bits.append("1")

        for currentBit in range (numBits-1, -1, -1):
            if(currentValue + self.findBitValue(currentBit) <= decimalValue):
                currentValue += self.findBitValue(currentBit)
                bits.append("1")
            else:
                bits.append("0")

        bitString = ""
        for bit in bits:
            bitString += bit

        return bitString
        

    # Calculates 2^n
    def findBitValue(self, n):
        if n == 0: 
            return 1
        # Dynamic approach, save to avoid recalculating values
        elif(str(n) in self.exponentValues):
            return self.exponentValues.get(str(n))
        else:
            currentBitValue = 1
            exp_counter = 0
            while exp_counter != n:
                currentBitValue *= 2
                exp_counter += 1

            self.exponentValues[str(n)] = currentBitValue
            return currentBitValue

    
    def convertToDecimal(self, bitString):
        numBits = len(bitString) - 1
        decimalValue = 0
        radix_position = 1
            
        # Calculate the decimal value of binary string 
        for bitIndex in range(numBits,-1,-1):
            if(bitString[bitIndex] == "1"):
                decimalValue += self.findBitValue(numBits - bitIndex)
        
        return decimalValue


    def addBinary(self, a: str, b: str) -> str:
        decimalA = self.convertToDecimal(a)
        decimalB = self.convertToDecimal(b)

        print(decimalA)
        print(decimalB)

        return self.createBitString(decimalA + decimalB)

s = Solution()
print(s.addBinary("0", "1"))
