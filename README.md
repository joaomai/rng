# Geração de primos pseudoaleatórios

### Considerações gerais
Todos os testes foram executados em um computador com um processaor 11th Gen Intel(R) Core(TM) i3-1115G4 @ 3.00GHz, com 8GB de RAM.

A linguagem escolhida foi o Python, por sua forma simples de lidar com números inteiros grandes, essa escolha porém fez com que análise
de complexidade dos algoritmos ficasse bastante semelhante, dado que a maioria fica limitado pelas operações de multiplicação e divisão 
com números grandes por parte do Python.

## Geração de números pseudoaleatórios

### Notas gerais sobre a estratégia utilizada
O primeiro algoritmo escolhido foi o LFSR (Linear Feedback Shift Register) onde existe a peculiaridade de que um LFSR 
de período maximal exige uma [configuração de taps](https://docs.amd.com/v/u/en-US/xapp052)
particular para cada largura de *bits*. Com essa limitação em mente, decidiu-se fixar todos os geradores para que gerem
números pseudoaleatórios de **64 *bits***, que serão concatenados para gerar números maiores.

Um detalhe importante que aparece ao fixar a palavra em 64 *bits* é a necessidade de gerar números com uma quantidade menor
de *bits*, como 40 e 56, ou que não são múltiplos de 64, e 168, onde temos 2 * 64 + 40. Não podemos simplemente pegar o resto
de uma divisão pela palavra menor, visto que isso introduz *bias* caso o maior não seja um múltiplo do menor.

Esse *bias* pode ser verificado ao analisarmos as formas que podemos obter um númeor considerando um gerador de 64 *bits*, mas queremos
números de 40 *bits*: simplesmente realizar a operação de módulo no valor obtido nos dá duas formas de obter o número 0:
- `(rand64() == 0) % 2^40 = 0`
- `(rand64() == 2^40) % 2^40 = 0`

O mesmo acontece para o número 1, 2, 3, indo até 2<sup>64</sup> - 2<sup>40</sup>. Todo número maior tem apenas 1 forma de ser gerado.

Para remediar esse problema, a técnica apresentada em [Fast Random Integer Generation in an Interval](https://arxiv.org/pdf/1805.10941)
foi utilizada. Nela, é aplicada rejeição para que não haja esse *bias* a favor de números menores. A mesma
técnica é usada para geração de números em um intervalo para os teste de primalidade.
O método funciona com base no lema descrito no artigo:
> Lemma 4.1. Given any integer s ∈ [0, 2<sup>L</sup> ), we have that for any integer y ∈ [0, s), there are exactly
> ⌊2L /s⌋ values x ∈ [0, 2<sup>L</sup> ) such that (x × s) ÷ 2<sup>L</sup> = y and (x × s) mod 2<sup>L</sup> ≥ 2<sup>L</sup> mod s.
Como todas as operações são com números de até 64 *bits* para a função `upto64()`, sua complexidade será considerada O(1) apesar da natureza
probabilitíca do método.

Como a geração dos números utiliza a concatenação de números de 64 *bits*, podemos generalizar a complexidade de cada método de geração para
O(m) para números de 64 *bits* ou menos, e O(⌈b/64⌉<sup>2</sup>* m) para números maiores que 64 *bits*, onde **b** é o tamanho em *bits* do número
que queremos gerar e *m* é a complexidade do método utilizado.

A complexidade O(⌈b/64⌉<sup>2</sup>* m) surge pois para números maiores que 64 *bits* a linguagem Python tem complexidade O(b) para operações *bitwise*.
Como o número é construído concatenando números de 64 *bits*, temos 2 operações de 64, 128, ..., ⌈b/64⌉ * 64 bits para cada concatenação, que assintoticamente
podem ser tratadas como O(⌈b/64⌉<sup>2</sup>).

```
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
```

### LFSR
Geradores LFSR funcionam com base na combinação de bits de locais específicos (taps) do estado anterior usando uma operação XOR,
criando o estado atual a partir dos primeiros 63 *bits* do estado anterior combinado ao bit obtido através da combinação.
Para que o LFSR seja maximal, foram utilizadas as taps indicadas em [Efficient Shift Registers, LFSR Counters, and Long Pseudo-Random Sequence Generators](https://docs.amd.com/v/u/en-US/xapp052).

```
 def random64(self) -> int:
        bit = ((self.state >> 0) ^ (self.state >> 1) ^ (self.state >> 3) ^ (self.state >> 4)) & 1
        self.state = (self.state >> 1) | (bit << 63)

        return self.state
```
Como todas as operações são operações *bitwise* em um número de até 64 *bits*, podemos considerar que encontrar o próximo estado usando o
LFSR tem uma complexidade O(1).

A tabela abaixo tem o tempo médio para a geração de 10<sub>6</sub> números, assim como o erro relativo desses números para a média e desvio de uma
distribuição uniforme.

|   Bits |   Tempo médio (us) | Média(%) | Desvio(%)|
|--------|--------------------|----------|----------|
|     40 | 0.7072885036468506 | 0.16817  | 0.03384  |
|     56 | 0.6959924697875977 | 0.15918  | 0.03605  |
|     80 | 1.083982229232788  | 0.07970  | 0.01302  |
|    128 | 0.9381773471832275 | 0.07970  | 0.01378  |
|    168 | 1.4261033535003662 | 0.02860  | 0.05839  |
|    224 | 1.8530001640319824 | 0.07840  | 0.06439  |
|    256 | 1.6620137691497803 | 0.07840  | 0.06439  |
|    512 | 3.1462831497192383 | 0.05669  | 0.03461  |
|   1024 | 6.250972032546997  | 0.07053  | 0.06083  |
|   2048 | 12.74595308303833  | 0.02801  | 0.00818  |
|   4096 | 26.952772617340088 | 0.04616  | 0.07531  |


### Xorshift
Geradores Xorshift são considerados um subset dos geradores LFSR, mas que não utilizam polinômios esparsos (que definem as taps) em sua construção.
O algortimo funciona realizando operações XOR com uma versão *bit-shifted* de si mesmo. É necessário tirar o módulo (operação & aqui), para garantir
que o número não passe de 64 *bits* no fim.

```
def random64(self) -> int:
    self.state ^= self.state << 13 & self.mod
    self.state ^= self.state >> 7 & self.mod
    self.state ^= self.state << 17 & self.mod
    return self.state
```
Assim como no LFSR, são apenas operações *bitwise* em um número de 64 *bits*, temos então complexidade O(1).

A tabela abaixo tem o tempo médio para a geração de 10<sub>6</sub> números, assim como o erro relativo desses números para a média e desvio de uma
distribuição uniforme.

|   Bits |   Tempo médio (us) | Média(%) | Desvio(%)|
|--------|--------------------|----------|----------|
|     40 | 0.7772812843322754 | 0.03352  | 0.04331  |
|     56 | 0.7564756870269775 | 0.04836  | 0.03999  |
|     80 | 1.1571366786956787 | 0.00399  | 0.03228  |
|    128 | 1.0256013870239258 | 0.00399  | 0.03229  |
|    168 | 2.026156425476074  | 0.01436  | 0.05590  |
|    224 | 2.247081995010376  | 0.04215  | 0.06830  |
|    256 | 1.9234981536865234 | 0.04215  | 0.06830  |
|    512 | 3.7043702602386475 | 0.02882  | 0.01530  |
|   1024 | 7.005826711654663  | 0.00036  | 0.09458  |
|   2048 | 13.830440521240234 | 0.00358  | 0.01862  |
|   4096 | 29.524301290512085 | 0.05142  | 0.03069  |

### Considerações
O tempo médio para os dois é bastante semelhante, visto que são geradores muito semelhantes e realizam os mesmos tipo de operações. Os erros relativos
para o Xorshift foram ligeiramente menores, mas nada expressivo.

Como a complexidade de ambos é O(1), podemos dizer que a complexidade para gerar um número de tamanho arbitrário é O(⌈b/64⌉<sup>2</sup>).

Outros algoritmos foram implementados também, pois era mais divertido do que escrever o relatório 😅.

## Testes de primalidade

### Notas gerais sobre a estratégia utilizada
Para a obtenção de número primos para cada tamanho de palavra, adotou-se a seguinte estratégia:
1. Gerar um número aleatório que utilize a representação máxima de *bits*
2. Subtrair n % 6 e 1 do número encontrado, de modo que n agora esteja na forma 6k - 1
3. Testa-se n (6k - 1) e n + 2 (6k + 1) utilizando Miller-Rabin
4. Caso nenhum dos dois seja primo, n += 6
5. Repete-se o passo 3 e 4 até que um primo seja encontrado

Números primos maiores que 3 sempre assumem a forma 6k - 1 ou 6k + 1, dado que as outras opções tem um divisor óbvio:
- 6k + 0: 2, 3
- 6k + 1: não há
- 6k + 2: 2
- 6k + 3: 3
- 6k + 4: 2
- 6k + 5: não há (equivalente à 6k - 1)

Adota-se essa estratégia para reduzir a quantidade de testes.

### Miller-Rabin
O algortimo de [Miller-Rabin](https://en.wikipedia.org/wiki/Miller-Rabin_primality_test
) baseia-se no pequeno teroma de Fermat, onde a<sup>n-1</sup>≡ 1 (mod n) e na propriedade
de que as únicas raízes quadradas de 1 mod n são 1 e -1, onde **n** é um primo e **a** é coprimo de **n**. O algoritmo de Miller-Rabin consiste em testar diferentes **a** contra essas duas propriedades.

O algoritmo também fatora o número n - 1 de forma a extrair a parte ímpar e a potência de 2 associada ao possível primo testado, n - 1 = 2<sup>s</sup>*d.

As complexidades estão descritas no código para cada etapa do código, com o algoritmo tendo a complexidade final de O(k*b<sup>3</sup>), com k sendo a quantidade de "rounds" de teste e b o tamanho do número em bits.

O tempo médio é obtido gerando 10 números primos, o número na tabela é o segundo gerado (os outros 9 estão no arquvio CSV).

|   Bits |   Tempo médio (ms)  | Número   | 
|--------|---------------------|----------|
|     40 | 0.11529922485351562 | 624824398487  |
|     56 | 0.10476112365722656 | 62880097421399917  |
|     80 | 0.34148693084716797 | 1064926140982500049250003  |
|    128 | 1.26459598541259770 | 170631575307718088002948509112824800357  |
|    168 | 1.80096626281738280 | 326492132305551028360577433146973792715888586956499  |
|    224 | 3.56597900390625000 | 17960609273939748780138790969774675425431809726217107580265366398953  |
|    256 | 9.65383052825927700 | 60565991794667251622712556983109360998069197610180268995687197844689157418307  |
|    512 | 48.1846332550048800 | 9408431200862516298567917277776197382066592558190011586155765506489744639868723590507726650830279932053864610790848586234547723412626335659506942089142171  |
|   1024 | 1380.79905509948730 | 144184132003806912984502978216549383054773360818126742743963826847011694523697348129677191306013552309707496496081280280498764872294118798186246829680579146985511450164231847879687856305144550301382625247690628130342237621424885681213713305503803612475442408037025206072014049544416909485096597036079002755083  |
|   2048 | 10244.9719667434700 | 32077132500127397727369780659291120022726932854195237094520871137953304786415082606116844537241613553095302109986035353952489851640825478492772230363693979062301529922117575609123495039292285757829462364521183303619323832793860941343975500660125392760967363184057995234624274158049955227324063849210864231315903899090153276921445068449577308952397587271092082103157767388302154340553392767945776799474359592290986990505335292722508481756820780696683940791368551547716039033633390155092306545978541685420907532180250886047000146447824822695274106317770534213053511091604967741664831975038380288726150305719828831011381  |
|   4096 | 235464.874958992000 | 773764903161674677005768765658320382133940372347580009486666603582778743846185366432833229660977389171051651827802631453058081824085642793445732981523721049934050353656263575545069114203598593015971045982652347997620879759453699445638672748979561890150162847381257135693874862333227421205879553475569022453010187819116077562894888872122483904734300761751898224490749080993089195069026209352668980183502083612084557681393320077763835497442562549574336973727093225339079983224015108532208774429320340987467098924326007778216399296886296278717534296526116311622273547690322367218195561128974799807992295595000298747968966769493718018507651981658203715511302331845207647589280595959312511748125888850885831772877155433732496623138650286478863025584876531794410329748421306070853263570251625292820557629525872241088011989832005113549966455208639369394245535438613608945713449097399783670863794380077471895356953838534220209326003589244464593357140581239396359191102029072699111760443157652961068152951645868411420199910630949608965362720551745825742831627140291810812450662159109796778416051940676197492173098956841511157954549526481056709739377129422076604787497773554241219742112261702732958047711952795360189721426520106071361686390523  |

### Solovay-Strassen
O teste de [Solovay-Strassen](https://en.wikipedia.org/wiki/Solovay%E2%80%93Strassen_primality_test) parte da propriedade provada por Euler que todo número primo segue:
a<sup>n-1/2</sup>≡Legendre(a,n) mod n, onde Legendre é símbolo de Legendre, **a** é um inteiro e **n** um primo. É possível generalizar símbolo de Legendre, obtendo o símbolo de Jacobi (que aceita n como um inteiro ímpar), que é então utilizado no teste de Solovay-Strassen. O teste consiste em testar utilizando o
símbolo de Jacobi para um dado valor de a.

O símbolo de Legendre/Jacobi faz ainda é misterioso para o autor do trabalho, a implementação é a que está na [Wikipedia](https://en.wikipedia.org/wiki/Jacobi_symbol).

As complexidades estão descritas no código para cada etapa do código, com o algoritmo tendo a complexidade final de O(k*b<sup>3</sup>), com k sendo a quantidade de "rounds" de teste e b o tamanho do número em bits.

O tempo médio é obtido gerando 10 números primos, o número na tabela é o segundo gerado (os outros 9 estão no arquvio CSV).

|   Bits |   Tempo médio (ms)  | Número   | 
|--------|---------------------|----------|
|     40 | 0.07162094116210938 | 884600854751  |
|     56 | 0.19459724426269530 | 59529296678025817  |
|     80 | 0.26397705078125000 | 810002804682474993405353  |
|    128 | 1.20956897735595700 | 170631575307718088002948509112824800357  |
|    168 | 3.21662425994873050 | 326492132305551028360577433146973792715888586956499  |
|    224 | 6.75745010375976600 | 17960609273939748780138790969774675425431809726217107580265366398953  |
|    256 | 5.15899658203125000 | 66038327735729160561050371088046041559137251234082979953148093073510846411669  |
|    512 | 93.1241035461425800 | 7657205019560587477616684624445030665804169451515332022307968459428924711412173254205319361138853987926426016845899948372487367341036467387009157714756133  |
|   1024 | 1204.07817363739010 | 176646738454200851001507056974845862948695667425305871444367128461363999809183408276704314824914804736457542135203366376227730652508832371341647386035589960144014974107691620243488062006333851660712227611981328764031702631693465969214807474628698446097154689955514645526306722527379382179044884883358878374821  |
|   2048 | 7155.68256378173800 | 18937316161896023873255264012477879265406457624362317322988920376257635293481647703141870116392590504302276794296245538838086151491606712870442368665986252836152361091832503321182510428388130920371330072453256356620474133360982762889767309923677179101431177405979048108350534856288771452557312510478188151158840451146166225898947208986215270896925275961241147586805784717299371700024376392268973978358470924005437029439829559843932962308683161400729249556985624500084654582271605707166471425459286510381462316518553889427571901381651205649225587284288125104449544628481716127242070615909152213002905762014282305005683  |
|   4096 | 87347.2141265869100 | 961779648984636768120961873647950389240858973623898977467913047523789043990522576943537021683221240708699175917858235402103039790842638517207539121645476437847532351281753731278099330840007160625716969696265966896540746874500794815014541105753262169218212658946825278491652891283995304350831198206586751105622862843640732486502952493768701204491758605970982065673524349124954252033052583934825966391602622271355360242460015162040614459667434878997223662757906806249868765805233956087292439843539692862827946508768136646486213372328324902031438570187610660525353694854678337662082468735652264896349282831993105854729458459037868528281368396423469941041474736088555972319750801242623685681134904891247555424971898173061942931674917794386620175932960982510832993097607905711751082756304666170716433072535150395840685116572180209609272219239846280551937158276281518890846925348558182354007696377308288421220973217103446559126342737108129824500172979311164154766262174049388974793253955134525752724911183751118539166413590760308074019920341998476380499891811708548728772885260841142950596545220238711285570532144911530441492532079802008880932386498122276790147076602349749406875826295637782504397873502227902002284157522791417181062734781  |

### Considerações
Solovay-Strassen foi mais rápido para vários tamanhos em média apesar de ambos terem a mesma complexidade, mas é difícil argumentar que ele é efetivamente mais rápido com apenas 10 números gerados.

Usando o mesmo gerador com a mesma seed, o primeiro primo encontrado é o mesmo para a maioria dos casos (o segundo está na tabela para maior diversidade).

# Referências
- LFSR
https://en.wikipedia.org/wiki/Linear-feedback_shift_register
https://www.youtube.com/watch?v=HSUvPVTVRCw
https://docs.amd.com/v/u/en-US/xapp052

- Geração de números aleatórios em um intervalo
https://arxiv.org/pdf/1805.10941

- Valor padrão pra seed (um primo de Marsenne grande)
https://en.wikipedia.org/wiki/Mersenne_prime

- Xorshift
https://en.wikipedia.org/wiki/Xorshift

- LCG (não explicado mas implementado)
https://en.wikipedia.org/wiki/Linear_congruential_generator

- Blum Blum Shub (não explicado mas implementado)
https://en.wikipedia.org/wiki/Blum_Blum_Shub

- Miller-Rabin
https://en.wikipedia.org/wiki/Miller-Rabin_primality_test

- Jacobi symbol
https://en.wikipedia.org/wiki/Jacobi_symbol

- Solovay-Strassen
https://en.wikipedia.org/wiki/Solovay-Strassen_primality_test