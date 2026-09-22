# Dostói MVP

<img width="576" alt="Dostói" src="https://i.pinimg.com/736x/59/00/b6/5900b6af41718502834e3a8f556a6c3a.jpg" />

Um avatar visual, um "bonequinho", que aparece na tela enquanto um agente
de IA (tipo Claude Code) está codando, e que reage ao que está
acontecendo internamente na sessão, em vez de você só olhar um terminal
cheio de texto rolando.

A ideia não é fazer um mascote decorativo. É criar uma forma de enxergar
o que normalmente é invisível: o processo de trabalho de um agente de
IA, quando ele está lendo, quando está com uma hipótese, quando algo deu
errado, quando ele está reconsiderando a abordagem.

## Por que isso é diferente de coisas que já existem

Já existem ferramentas que conectam um avatar a um agente e fazem ele
reagir tipo "rodando = 😐, parado = 😴". Isso é simples e já foi feito.

O que torna esse projeto diferente é uma frase que surgiu na conversa
que o originou:

> nós não somos nossos pensamentos, nós pensamos sobre eles

Ou seja: não basta mostrar que o agente está fazendo alguma coisa. A
ideia é que o avatar também reflita sobre o que está sendo feito, tenha
uma espécie de segunda camada, que olha pro trabalho do agente e forma
um julgamento sobre ele. Não é só "estou trabalhando", é "estou
trabalhando, e essa abordagem me parece questionável".

## As duas camadas

### Camada 1, o que o agente está fazendo (operacional)

Isso é o corpo do avatar reagindo em tempo real: lendo código,
executando algo, esperando resultado, lidando com erro, mudando de
direção. É contínuo, sutil, tipo uma "linguagem corporal" do agente:
postura, expressão, ritmo.

### Camada 2, o que o agente pensa sobre o próprio trabalho (metacognitiva)

Essa é a parte nova e mais interessante. De tempos em tempos, não a
cada ação, mas em pontos-chave (depois de uma mudança de código
relevante, depois de um teste falhar, depois de uma reconsideração), o
avatar "para" e emite um comentário curto sobre o que acabou de
acontecer. Tipo: "essa função já existe em outro lugar do código", ou
"isso resolve o sintoma, não a causa do erro anterior".

A Camada 1 é o avatar fazendo. A Camada 2 é o avatar pensando sobre o
que fez. É essa segunda camada que transforma o projeto de "indicador
de status bonito" em algo que de fato tem uma qualidade reflexiva.

## Como isso se manifesta visualmente

A Camada 1 fica sempre ligada, de fundo: o avatar respirando, mudando
de postura, com microexpressões conforme o estado muda.

A Camada 2 aparece só nos momentos de checkpoint, como um balão de
pensamento que interrompe o fluxo contínuo, um comentário pontual,
breve, que dá a sensação de que o avatar teve um insight sobre o
trabalho, não apenas reagiu a ele.

## O sistema de "peles" (skins)

O avatar em si é desacoplado da lógica: a mesma "consciência" por trás
(os estados, os julgamentos) pode ser representada por avatares
completamente diferentes: um gato, um robô, uma raposa, um personagem
pixelado. A lógica de interpretação é uma coisa, a aparência é outra.
Isso significa que, uma vez que o "cérebro" funcione bem, criar novos
personagens visuais é trabalho relativamente simples e não exige tocar
em nada da parte de raciocínio.

## Por que a ordem de construção importa

O maior risco do projeto não é o avatar ficar bonito, é a parte de
"entendimento" (tanto a Camada 1 quanto a Camada 2) fazer sentido de
verdade, ou seja, o avatar realmente refletir o que está acontecendo, e
não ficar mudando de estado de forma aleatória ou incoerente. Por isso
o caminho certo é validar primeiro se a lógica de interpretação funciona
bem, mesmo sem nenhum visual, só vendo os estados sendo impressos em
texto, antes de investir em desenho, animação e variações de
personagem.
