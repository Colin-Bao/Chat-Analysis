def min_moves_to_sort(arr):
    old_arr = arr.copy()
    arr.sort()
    moves = 0
    for i, _ in enumerate(arr):
        if arr[i] != old_arr[i]:
            moves += 1
    return moves


servers = [2, 3, 1, 4, 6, 5, 7, 10, 12, 11, 9, 16, 14]
print(min_moves_to_sort(servers))
