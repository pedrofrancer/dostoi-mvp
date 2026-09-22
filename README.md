# Dostói MVP

<img width="576" alt="Dostói" src="https://i.pinimg.com/736x/cc/d4/35/ccd435211b4466ac3575571f2726166b.jpg" />

Passei anos formalizando processos que não conseguia ver por dentro,
ataques, provas, modelos de ameaça, e sempre sobrava a mesma frustração:
o raciocínio que importa acontece num lugar opaco, e o que chega até mim
é só o resíduo dele, um log, um terminal rolando texto. O Dostói nasce
dessa frustração específica, aplicada a um caso concreto: um agente de
IA (tipo Claude Code) codando, enquanto eu só enxergo a casca do que ele
está pensando.

A resposta óbvia seria um avatar decorativo, reage a "rodando" com uma
carinha feliz, a "parado" com uma carinha de sono. Isso já existe, e não
resolve nada que me interesse. O que me interessa é uma frase que me
ocorreu enquanto pensava nisso:

> nós não somos nossos pensamentos, nós pensamos sobre eles

Um agente que só mostra que está trabalhando ainda é o agente sendo seus
próprios pensamentos, sem distância nenhuma deles. O que eu quero
construir é a distância: uma camada que observa o trabalho do agente e
forma um julgamento sobre ele. Não "estou trabalhando", e sim "estou
trabalhando, e essa abordagem me parece questionável".

## As duas camadas

### Camada 1, o que o agente está fazendo (operacional)

O corpo do avatar reagindo em tempo real: lendo código, executando algo,
esperando resultado, lidando com erro, mudando de direção. Contínuo,
sutil, uma linguagem corporal, postura, expressão, ritmo. É o agente
sendo seus pensamentos.

### Camada 2, o que o agente pensa sobre o próprio trabalho (metacognitiva)

Esta é a parte que me interessa de verdade. De tempos em tempos, não a
cada ação, mas em pontos de inflexão (depois de uma mudança de código
relevante, depois de um teste falhar, depois de uma reconsideração), o
avatar para e emite um comentário curto sobre o que acabou de acontecer.
Algo como "essa função já existe em outro lugar do código", ou "isso
resolve o sintoma, não a causa do erro anterior". É o agente pensando
sobre seus próprios pensamentos, a distância que dá ao projeto qualquer
qualidade reflexiva de verdade, em vez de só um indicador de status
bonito.

## Como isso se manifesta visualmente

A Camada 1 fica sempre ligada, de fundo, o avatar respirando, mudando de
postura, com microexpressões conforme o estado muda.

A Camada 2 aparece só nos checkpoints, como um balão de pensamento que
interrompe o fluxo contínuo, breve, pontual, dando a sensação de que o
avatar teve um insight sobre o trabalho, não apenas reagiu a ele.

## O sistema de "peles" (skins)

O avatar é desacoplado da lógica. A mesma consciência por trás, os
estados, os julgamentos, pode ser representada por avatares
completamente diferentes: um gato, um robô, uma raposa, um personagem
pixelado. A lógica de interpretação é uma coisa, a aparência é outra;
uma vez que o "cérebro" funcione, criar personagens novos é trabalho
simples, sem tocar no raciocínio.

## Por que a ordem de construção importa

Já vi o suficiente de sistemas mal calibrados para saber onde mora o
risco real aqui: não é o avatar ficar bonito, é a parte de
"entendimento", Camada 1 e Camada 2, fazer sentido de verdade. Um avatar
que muda de estado de forma aleatória ou incoerente é pior que nenhum
avatar, é ruído com forma de sinal. Por isso valido primeiro se a lógica
de interpretação funciona, mesmo sem nenhum visual, só os estados
impressos em texto, antes de investir em desenho, animação e variações
de personagem.
