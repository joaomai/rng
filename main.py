import time

from statistics import mean, stdev
from generators import LFSR, Xorshift, LCG, BlumBlumShub, Generator, RandInt
from primes import miller_rabin, solovay_strassen, is_prime

def gen_pseudos() -> None:
    from decimal import Decimal, getcontext

    bits: list['int'] = [40, 56, 80, 128, 168, 224, 256, 512, 1024, 2048, 4096]
    with open('pseudos.csv', 'w') as f:
        for gen in [LFSR, Xorshift]:
            for bit in bits:
                getcontext().prec = bit + 1

                max: Decimal = Decimal(1 << bit) - 1
                m_unif: Decimal = max/2
                s_unif: Decimal = max/Decimal(12).sqrt()

                times: list['float'] = []
                samples: list['int'] = []
                random: Generator = gen(bit)

                for _ in range(int(1e6)):
                    start = time.time()
                    samples.append(random.random())
                    times.append(time.time() - start)
                    start = time.time()

                m_test: Decimal = mean([Decimal(sample) for sample in samples])
                s_test: Decimal = stdev([Decimal(sample) for sample in samples])

                f.write(f'{gen.__name__}, {bit}, {mean(times)*1e6}, {100 * abs(m_test - m_unif)/m_unif:.5f}, {100 * abs(s_test - s_unif)/s_unif:.5f}\n')


def gen_primes() -> None:
    bits = [40, 56, 80, 128, 168, 224, 256, 512, 1024, 2048, 4096]
    with open('primes.csv', 'w') as f:
        for tester in [miller_rabin, solovay_strassen]:
            for bit in bits:
                times: list['float'] = []
                nums: list['int'] = []
                random: RandInt = RandInt(LFSR, bit)
                for _ in range(10):
                    start: float = time.time()
                    n: int = random((1 << (bit-1)), 1 << bit)
                    n -= (n % 6)
                    n -= 1

                    while True:
                        if tester(n, random):
                            nums.append(n)
                            times.append(time.time() - start)
                            start = time.time()
                            break
                
                        if tester(n+2, random):
                            nums.append(n+2)
                            times.append(time.time() - start)
                            start = time.time()
                            break
                        
                        n += 6

                f.write(f'{tester.__name__}, {bit}, {mean(times)*1e3}, {str(nums)[1:-1]}\n')

if __name__ == '__main__':
    gen_pseudos()
    gen_primes()



