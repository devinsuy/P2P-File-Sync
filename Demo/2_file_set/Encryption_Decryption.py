def decrypt(encrypted_text, n):
    if encrypted_text == None or len(encrypted_text) == 1:
        return None
        
    num_chars = len(encrypted_text)
    num_swapped_chars = index = -1
    source_str = encrypted_text
    
    # First figure up to what index contains a swapped character
    while index < num_chars:
        index += 2
        num_swapped_chars += 1
        
    # Perform decryption n times
    for i in range(n):
        text_index = 0
        decrypted_index = 1
        decrypted_chars = [None] * num_chars
    
        # Each char in our encrypted string up until last_swapped_char
        # needs to be placed in the appropiate index
        while text_index < num_swapped_chars:
            decrypted_chars[decrypted_index] = source_str[text_index]
            text_index += 1
            decrypted_index += 2

        # Now add in the remaining characters (which retained their order)
        remaining_index = 0
        while text_index < num_chars:
            decrypted_chars[remaining_index] = source_str[text_index]
            text_index += 1
            remaining_index += 2
    
        # Rebuild the decrypted string
        decrypted_str = ""
        for char in decrypted_chars:
            decrypted_str += char
        
        source_str = decrypted_str
    
    return source_str

def encrypt(text, n):
    if text == None or len(text) == 1:
        return None
        
    source_str = text
    text_length = len(text)
    test = []
    
    # Perform encryption n times
    for i in range(n):
        other_chars = []
        encrypted_str = ""
    
        # Start by adding every index into the list  
        for i in range(text_length):
            other_chars.append(i)
    
        # Add every other character into our string
        remove_index = 1    
        
        while remove_index < text_length:
            encrypted_str += source_str[remove_index]
            other_chars.remove(remove_index)
            test.append(remove_index)
            remove_index += 2 
            
        # By this point the indices still in other_chars
        # are the remaining characters to append, add them 
        for index in other_chars:
            encrypted_str += source_str[index]
            
        source_str = encrypted_str
            
    return source_str