def get_change_percentage(actual, prev):
    if actual is None or prev is None or prev == 0:
        raise Exception("Invalid values")

    diff = actual - prev
    ret = diff / float(abs(prev))
    return ret


def safe_min(left, right):
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return min(left, right)


def safe_max(left, right):
    if left is None:
        return right
    elif right is None:
        return left
    else:
        return max(left, right)
