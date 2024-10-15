from generators import RandInt
            
# O(k*b^3)
def miller_rabin(n: int, random: RandInt, k: int = 1) -> bool:
    if n == 2: return True
    if n & 1 == 0: return False

    # n é sempre gerado com o tamanho máximo de bits
    # Fatora-se n, encontrando s e d, como acontece o deslocamento de 1 bit por iteração
    # temos como complexidade O(b)
    s = 0
    d = n - 1
    while d & 1 == 0:
        s += 1
        d >>= 1

    # k é definido como padrão como 1, mas é um termo constante
    for _ in range(k):
        # O(b) (complexidade de cada operação descritos na função)
        a = random(2, n-2)
        # pow é uma exponenciação rápida modular, sendo O(log n) para inteiros de até 64 bits e O(b^3)
        x = pow(a, d, n)

        # O(s)
        for _ in range(s):
            # O(b^3)
            y = pow(x, 2, n)
            if y == 1 and x != 1 and x != (n-1):
                return False
            x = y
        if y != 1:
            return False
        
    return True


# O(b^3) (O(b^2) b vezes)
def jacobi(a: int, n: int) -> int:
    a %= n
    t: int = 1
    while a != 0:
        while a & 1 == 0:
            a >>= 1
            r = n % 8
            if r == 3 or r == 5:
                t *= -1
        n, a = a, n
        if a % 4 == 3 and n % 4 == 3:
            t *= -1
        a %= n
    return t if n == 1 else 0

# O(k*b^3)
def solovay_strassen(n: int, random: RandInt, k: int = 1) -> bool:
    if n == 2: return True
    if n & 1 == 0: return False

    # O(k)
    for _ in range(k):
        # O(b)
        a = random(2, n-1)
        # O(b^3)
        x = jacobi(a, n)
        # O(b^3)
        if x == 0 or pow(a, (n-1)//2, n) != x % n:
            return False
        
    return True

def is_prime(n):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False

    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6

    return True

if __name__ == '__main__':
    pass