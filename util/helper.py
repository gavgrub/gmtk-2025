def smoothstep(start, end, t):
    t = max(0, min(1, t))  # Clamp t between 0 and 1
    t = t * t * (3 - 2 * t)  # Smoothstep easing
    return start + (end - start) * t