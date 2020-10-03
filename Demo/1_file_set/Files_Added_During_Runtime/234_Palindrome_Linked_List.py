class Solution:
    def isPalindrome(self, head: ListNode) -> bool:
        if head == None:
            return True
        
        # Count number of nodes
        p = head
        count = 0
        while p != None:
            p = p.next
            count += 1
        
        mid_point = count // 2
        
        # Get a pointer to the middle node in the LL
        p = head
        while mid_point > 0:
            p = p.next
            mid_point -= 1
          
        
        prev = None
        #p = p.next
        
        # Reverse the right half of the LL
        while p != None:
            nxt = p.next
            p.next = prev
            prev = p
            p = nxt
           
        
        # Left half of LL is compared to right half reversed 
        right_node = prev
        left_node = head
        
        while right_node != None:
            print("left: ", left_node.val)
            print("right: ", right_node.val, "\n")
            if left_node.val != right_node.val:
                return False
            
            right_node = right_node.next
            left_node = left_node.next

        return True