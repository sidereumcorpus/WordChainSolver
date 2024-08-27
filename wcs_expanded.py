from tqdm import tqdm
# Word list source URL and file
WORD_LIST = '12dicts_words'

# Word length range for the transformation
MIN_WORD_LEN = 2
MAX_WORD_LEN = 6

# Maximum depth to compute a search
MAX_ITERS = 100

# Convert a string to a number
def make_number(word):
    num = 0
    mult = 1
    for w in word:
        num += (ord(w) - ord('A')) * mult
        mult *= 256
    return num

# Convert a number to a string of a specified length
def make_word(number, length):
    word = ""
    for i in range(length):
        word += chr((number & 0xFF) + ord('A'))
        number >>= 8
    return word

# Check if 2 strings differ by only 1 letter (slow)
def are_pair(w1, w2):
    numDiffs = 0
    for i in range(len(w1)):
        if w1[i] != w2[i]:
            numDiffs += 1
            if numDiffs >= 2: return False
    return numDiffs == 1

# Check if 2 numbers differ by only 1 letter (fast)
def are_pair_num(n1, n2, word_len):
    numDiffs = 0
    for i in range(word_len):
        if ((n1 >> (i * 8)) & 0xFF) != ((n2 >> (i * 8)) & 0xFF):
            numDiffs += 1
            if numDiffs >= 2: return False
    return numDiffs == 1

def add_remove_pairs(word_list_from, word_list_to, word_len_from, word_len_to):
    """Finds and adds word pairs where one word is one letter longer or shorter."""
    for w1 in word_list_from:
        word1 = make_word(w1, word_len_from)
        for w2 in word_list_to:
            word2 = make_word(w2, word_len_to)
            # Check if w2 can be formed by removing or adding one letter to w1
            if are_one_letter_diff(word1, word2):
                if len(word1) > len(word2):
                    all_pairs.append((word1, word2, "remove"))  # w1 longer than w2, thus remove
                else:
                    all_pairs.append((word1, word2, "add"))  # w2 longer than w1, thus add

def are_one_letter_diff(w1, w2):
    """Check if two words differ by exactly one letter, including adds/removes."""
    len_diff = abs(len(w1) - len(w2))
    if len_diff > 1:
        return False
    if len_diff == 0:
        return are_pair(w1, w2)
    elif len(w1) > len(w2):  # w1 longer than w2
        for i in range(len(w1)):
            if w1[:i] + w1[i+1:] == w2:
                return True
    else:  # w2 longer than w1
        for i in range(len(w2)):
            if w2[:i] + w2[i+1:] == w1:
                return True
    return False


# Create a lookup table for 1 letter diffs (fastest)
print('Creating Diff Lookup Table...')
pair_lut = set()
for length in range(MIN_WORD_LEN, MAX_WORD_LEN + 1):
    for i in range(length):
        for j in range(32):
            pair_lut.add(j << (i * 8))

# Loading dictionary for each word length with progress bar
print('Loading Dictionary...')
all_words_dict = {}
for length in tqdm(range(MIN_WORD_LEN, MAX_WORD_LEN + 1), desc="Word Length"):
    all_words_dict[length] = []
    with open(WORD_LIST + '.txt', 'r') as fin:
        for word in fin:
            word = word.strip().upper()
            if len(word) == length:
                all_words_dict[length].append(make_number(word))
    print(f'\nLoaded {len(all_words_dict[length])} words of length {length}.')

# Finding all connections with progress bar
print('Finding All Connections...')
all_pairs = []

# Create word connections with progress bar
for length in tqdm(range(MIN_WORD_LEN, MAX_WORD_LEN + 1), desc="Finding Connections"):
    for i, w1 in enumerate(all_words_dict[length]):
        word1 = make_word(w1, length)
        for j in range(i):
            w2 = all_words_dict[length][j]
            if (w1 ^ w2) in pair_lut:
                all_pairs.append((word1, make_word(w2, length), "change"))
    
    # Add connections to words one letter shorter
    if length > MIN_WORD_LEN:
        add_remove_pairs(all_words_dict[length], all_words_dict[length - 1], length, length - 1)

    # Add connections to words one letter longer
    if length < MAX_WORD_LEN:
        add_remove_pairs(all_words_dict[length], all_words_dict[length + 1], length, length + 1)

print(f"Found {len(all_pairs)} connections.")

# DOT file format does not allow these keywords, make sure to change them
keywords = ['NODE', 'EDGE', 'GRAPH', 'DIGRAPH', 'SUBGRAPH', 'STRICT']
def fix_keyword(w):
    if w in keywords:
        return '_' + w
    return w

print("Writing CSV files...")

# Writing nodes to CSV
with open("nodes.csv", 'w') as fout_nodes:
    fout_nodes.write('Id,Label\n')
    for length in range(MIN_WORD_LEN, MAX_WORD_LEN + 1):
        for w in all_words_dict[length]:
            word = fix_keyword(make_word(w, length))
            fout_nodes.write(f'"{word}","{word}"\n')

# Writing edges to CSV with transformation types as weights
with open("edges.csv", 'w') as fout_edges:
    fout_edges.write('Source,Target,Weight\n')
    for w1, w2, trans_type in all_pairs:
        if trans_type == "add":
            weight = 1  # or any other numeric value representing "add"
        elif trans_type == "remove":
            weight = 1  # or any other numeric value representing "remove"
        elif trans_type == "change":
            weight = 2  # or any other numeric value representing "change"
        fout_edges.write(f'"{fix_keyword(w1)}","{fix_keyword(w2)}",{weight}\n')


# print("")
# while True:
#     from_word = make_number(input('From Word: ').upper())
#     to_word = make_number(input('  To Word: ').upper())
#     from_word_len = len(make_word(from_word, MAX_WORD_LEN).strip('\x00'))
#     to_word_len = len(make_word(to_word, MAX_WORD_LEN).strip('\x00'))

#     if from_word_len not in all_words_dict or from_word not in all_words_dict[from_word_len]:
#         print(f"No connections to {make_word(from_word, from_word_len)}")
#         continue
#     if to_word_len not in all_words_dict or to_word not in all_words_dict[to_word_len]:
#         print(f"No connections to {make_word(to_word, to_word_len)}")
#         continue

#     connections = {}
#     dist = {word: -1 for length in range(MIN_WORD_LEN, MAX_WORD_LEN + 1) for word in all_words_dict[length]}
#     dist[to_word] = 0
#     is_found = False

#     for iter in tqdm(range(MAX_ITERS), desc="Solver Iterations"):
#         print(iter)
#         made_changes = False
#         for w1 in all_words_dict[from_word_len]:
#             if dist[w1] == iter:
#                 for w2 in all_words_dict[to_word_len]:
#                     if dist[w2] != -1: continue
#                     if (w1 ^ w2) not in pair_lut and not are_one_letter_diff(make_word(w1, from_word_len), make_word(w2, to_word_len)):
#                         continue
#                     dist[w2] = iter + 1
#                     connections[w2] = w1
#                     made_changes = True
#                     if w2 == from_word:
#                         print("Found!")
#                         is_found = True
#                         break
#             if is_found: break
#         if is_found or (not made_changes): break    

#     if from_word != 0:
#         if from_word not in connections:
#             print('Cannot connect!')
#         else:
#             w = from_word
#             while True:
#                 print(make_word(w, from_word_len))
#                 if w == to_word: break
#                 w = connections[w]
#             print(f"{dist[from_word]} steps")
#     else:
#         for word in all_words_dict[from_word_len]:
#             if dist[word] > 0:
#                 print(make_word(word, from_word_len) + " in " + str(dist[word]) + " steps")