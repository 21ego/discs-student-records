# Hash table builder
def build_hash_table(students):
    return {s.id: s for s in students}

# Merge sort
def merge_sort(items, key, reverse=False):
    if len(items) <= 1:
        return items[:]
    mid = len(items)//2
    left = merge_sort(items[:mid], key, reverse)
    right = merge_sort(items[mid:], key, reverse)
    return merge(left, right, key, reverse)

def merge(left, right, key, reverse):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if (key(left[i]) < key(right[j]) and not reverse) or (key(left[i]) > key(right[j]) and reverse):
            result.append(left[i]); i += 1
        else:
            result.append(right[j]); j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# Undo/Redo stack
class UndoRedoManager:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def record_state(self, student):
        self.undo_stack.append(student.clone())
        self.redo_stack.clear()

    def undo(self, current):
        if not self.undo_stack: return None
        prev = self.undo_stack.pop()
        self.redo_stack.append(current.clone())
        return prev

    def redo(self, current):
        if not self.redo_stack: return None
        nxt = self.redo_stack.pop()
        self.undo_stack.append(current.clone())
        return nxt

# Sorting key functions
def sort_by_id(student):
    return student.id

def sort_by_name(student):
    return student.name.lower()

def sort_by_qpi(student):
    return student.qpi
