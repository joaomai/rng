from abc import ABC, abstractmethod
from typing import Type

class Generator(ABC):
    mod = (1 << 64) - 1

    def __init__(self, bits: int = None, seed: int = None):
        self.bits = bits or 64
        self.state: int = seed or (1 << 61) - 1

    @abstractmethod
    def random64(self) -> int:
        pass

    def upto64(self, s: int) -> int:
        x: int = self.random64()
        m: int = x * s
        l: int = m & self.mod

        if (l < s):
            t: int = self.mod & s
            while l < t:
                x = self.random64()
                m = x * s
                l = m & self.mod
        
        return m >> 64

    def random(self) -> int:
        n: int = 0

        chunks_truncated: int = self.bits//64
        chunks_rounded: int = (self.bits + 63)//64

        for i in range(chunks_truncated):
            n |= (self.random64() << (i * 64))

        if chunks_truncated != chunks_rounded:
            curr: int = chunks_truncated * 64
            n |= (self.upto64(1 << (self.bits - curr)) << (curr))
        
        return n
    
    # O(b^2)
    def upto(self, s: int) -> int:
        mod: int = (1 << self.bits) - 1

        # O(⌈b/64⌉^2
        x: int = self.random()
        # O(b^2)
        m: int = x * s
        # O(b)
        l: int = m & mod

        if (l < s):
            # O(b)
            t: int = mod % s
            while l < t:
                # O(⌈b/64⌉^2
                x = self.random()
                # O(b^2)
                m = x * s
                # O(b)
                l = m & mod
        # O(b)
        return m >> self.bits


    def test(self) -> None:
        from statistics import mean, stdev

        max: int = (1 << self.bits) - 1
        m_unif: float = max/2
        if self.bits < 1024:
            s_unif: float = max//(12**0.5)

        samples: int = [self.random() for _ in range(int(1e6))]
        m_test: float = mean(samples)
        s_test: float = stdev(samples)

        print(f'[Mean]  Uniform: {m_unif:.2f}, Generated: {m_test:.2f}, Error: {100 * abs(m_test - m_unif)/m_unif:.2f}%')
        if self.bits < 1024:
            print(f'[Stdev] Uniform: {s_unif:.2f}, Generated: {s_test:.2f}, Error: {100 * abs(s_test - s_unif)/s_unif:.2f}%')
    
class LFSR(Generator):
    def __init__(self, bits: int = None, seed: int = None):
        bits = bits or 64
        state: int = seed or 0xA3B1C7D2E4F5A678 # a semente padrão do Generator não funciona muito bem para o LFSR
        super().__init__(bits, state)

    def random64(self) -> int:
        bit = ((self.state >> 0) ^ (self.state >> 1) ^ (self.state >> 3) ^ (self.state >> 4)) & 1
        self.state = (self.state >> 1) | (bit << 63)

        return self.state
    
class Xorshift(Generator):
    def random64(self) -> int:
        self.state ^= self.state << 13 & self.mod
        self.state ^= self.state >> 7 & self.mod
        self.state ^= self.state << 17 & self.mod
        return self.state
    
class LCG(Generator):
    def random64(self) -> int:
        self.state  = (6364136223846793005 * self.state + 1) & self.mod
        return self.state
    
class BlumBlumShub(Generator):
    def __init__(self, bits: int = None, seed: int = None):
        super().__init__(bits, seed)
        p: int = (1 << 89) - 1
        q: int = (1 << 107) - 1
        self.M: int = p * q

    def random64(self) -> int:
        n: int = 0
        for _ in range(64):
            self.state = (self.state ** 2) % self.M
            n = (n << 1) | (self.state & 1)
        return n
    
class RandInt:
    def __init__(self, generator: Type[Generator] = LFSR, bits: int = None, seed: int = None):
        self.__generator = generator(bits, seed)


    # A complexidade é definida pela chamada à upto(), que tem complexidade O(b^2)
    def __call__(self, num1: int = None, num2: int = None) -> int:
        if num1 == None:
            return self.__generator.random()

        low: int = 0 if num2 is None else num1
        high: int = num1 if num2 is None else num2

        amplitude = high - low
        n: int = self.__generator.upto(amplitude)

        return low + n

if __name__ == '__main__':
    xor = Xorshift()
    xor.test()

    lfsr = LFSR()
    lfsr.test()

    lcg = LCG()
    lcg.test()
    
    bbs = BlumBlumShub()
    bbs.test()