
def decode_regional(hex_str):
    parts = hex_str.split('_')
    decoded_parts = []
    
    base = 0x1F1E6
    
    for part in parts:
        current_word = ""
        # Chunks of 5 chars? "1F1EA"
        # Length of part should be multiple of 5
        for i in range(0, len(part), 5):
            chunk = part[i:i+5]
            val = int(chunk, 16)
            char_code = val - base + ord('A')
            current_word += chr(char_code)
        decoded_parts.append(current_word)
        
    return "_".join(decoded_parts)

s = "1F1EA1F1F21F1F41F1EF1F1EE_1F1EE1F1F8_1F1E61F1F11F1FC1F1E61F1FE1F1F8_1F1EB1F1FA1F1F31F1F31F1FE"
print(decode_regional(s))
