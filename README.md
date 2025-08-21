# WorldAlphabets
A python tool to get languages of the world. 

engAlpha = worldAlpha("eng")
engAlpha.UpperCase() ==> A, B C
engAlpha.LowerCase() ==> a, b , c


engAlpha.WordFreq ==> A,10, B,4 etc..

## How we are gong to do this

- We can use python libraries like langcode, unicode etc
- Use this JAVA repo as a source to generate our base lists in different languages
- Store data in JSON - in files per langcode

To get frequency use something like

```python
from collections import Counter

def analyze_text_frequency(file_path):
    """
    Reads a text file and returns a dictionary of character frequencies.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().lower()  # Read text and convert to lowercase
            # Filter out non-alphabetic characters if needed, e.g., using regex
            # import re
            # text = re.sub(r'[^a-z\u00C0-\u1FFF]+', '', text) 
            
            # Use Counter to get the frequency of each character
            char_counts = Counter(text)
            
            # Calculate total alphabetic characters for frequency percentage
            total_chars = sum(char_counts.values())
            
            frequencies = {char: count / total_chars * 100 for char, count in char_counts.items()}
            
            # Sort the dictionary by frequency in descending order
            sorted_frequencies = dict(sorted(frequencies.items(), key=lambda item: item[1], reverse=True))

            return sorted_frequencies

    except FileNotFoundError:
        return "Error: File not found."

# Example usage: Assuming you have a file named 'english_corpus.txt'
# from an online source or a text you've collected.
# english_freq = analyze_text_frequency('english_corpus.txt')
# print(english_freq)

```

for texts found online froma  source to calculate frequencies. 

Identify missing languges and create a TO-D0 csv












