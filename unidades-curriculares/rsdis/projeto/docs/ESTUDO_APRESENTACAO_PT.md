# Preparação da apresentação e defesa

Objetivo: explicar uma missão cooperativa completa e as escolhas de integração,
com base no código e nos registos reais. Esta é uma proposta de divisão de estudo;
cada elemento deve conseguir explicar o sistema global e executar a demonstração.

| Elemento | Bloco de estudo sugerido | Código e conceitos essenciais |
| --- | --- | --- |
| Henrique Correia, 1221309 | Perceção, mapa e movimento | `perception.py`, `detector_node.py`, `planning.py`, `navigation.py`; HSV, intrínsecos, projeção, A*, inflação da pegada, lidar, distância de travagem |
| Pedro Ribeiro, 1231177 | Integração ROS/Gazebo e energia | launch, `world.py`, `power.py`, `power_node.py`, `rsdis_energy_plugins`; bridges, V/A/Ah/Wh, sinais da corrente, carga, sombra, potência da doca, proveniência Space ROS |
| Francisco Liquito, 1231216 | Cooperação, comunicação e avaliação | `core.py`, `coordinator_node.py`, `network_node.py`, `communications.py`; ownership, leases, QoS, retransmissões, avarias, protocolo experimental, interpretação dos resultados |

## Guião de 8 a 10 minutos

1. Missão e pergunta: descobrir cinco locais, confirmar por câmara e regressar.
2. Mapa e sensores: mostrar o mapa maior e uma imagem realmente renderizada.
3. Arquitetura: seguir uma deteção desde a câmara até ao coordenador e à atribuição.
4. Movimento: explicar como a pegada, o lidar e a travagem evitam colisões.
5. Energia: seguir odometria -> potência -> bateria Gazebo -> BatteryState -> decisão.
6. Comunicação e recuperação: mostrar uma tarefa libertada e atribuída ao outro rover.
7. Experiências: mostrar todos os pares, incluindo eventuais insucessos, com unidades.
8. Conclusão e limites: o que foi demonstrado, o que é aproximação e o que falta medir.

## Perguntas que todos devem saber responder

- **O que veio de fora?** Gazebo e ROS 2 fornecem simulação e middleware;
  `ros_gz` faz as bridges; OpenCV fornece operações de imagem. Os cinco ficheiros
  C++ de energia foram adaptados de Space ROS, com licença e revisão fixas.
  O modelo VIPER detalhado também tem origem Space ROS. Consultar
  `INTEGRATION_SOURCES.md`, `upstream.lock.json` e o manifesto `UPSTREAM.json`.
- **O que foi desenvolvido no projeto?** A missão de dois rovers, agentes,
  perceção de marcadores, atribuição, controlo de doca, gateway de falhas,
  segurança de navegação, consola e avaliação. A* e DDS são conceitos existentes.
- **Como há cooperação?** Um rover pode observar um marcador e o outro inspecioná-lo.
  A falha de um proprietário liberta trabalho e permite uma nova atribuição.
  Consultar os IDs do observador, proprietário e tarefa no `events.jsonl` real.
- **Como se evita trabalho duplicado?** Um proprietário por alvo, IDs de tarefa,
  leases e aceitação de resultados pelo coordenador. Resultados antigos são ignorados.
- **Porquê duas estratégias?** Ambas têm a mesma segurança e viabilidade; só muda
  a ordenação por distância ou distância mais risco energético. Não há promessa
  de a heurística energética ganhar em todos os cenários.
- **O consumo é físico?** A carga elétrica é simulada em Gazebo e medida em V/A/Wh.
  A potência depende do movimento medido e da exposição solar, mas os parâmetros
  são acelerados e não calibrados para um rover lunar real. A previsão do
  coordenador é uma aproximação separada em frações de bateria.
- **A falha de comunicação é rádio real?** É uma emulação da aplicação com perda,
  atraso e blackout definidos. O QoS é o mecanismo DDS existente. Sensores locais
  continuam disponíveis; comandos do operador são assumidos fora desse canal.
- **Há SLAM?** A localização vem da verdade de terreno Gazebo. O mapa de obstáculos
  é conhecido; as posições científicas são estimadas pelas câmaras.
- **O vídeo é uma animação offline?** A gravação de demonstração usa imagens das
  câmaras Gazebo. A reprodução cinemática Windows é um diagnóstico distinto.
- **Zero colisões significa segurança real?** O ensaio mede sobreposições de
  pegadas conservadoras no plano, não forças de contacto ou segurança em solo lunar.

## Verificação antes da defesa

Cada pessoa deve executar uma missão, localizar um evento real no registo,
explicar uma mensagem ROS e identificar a referência de um componente reutilizado.
Preparar o vídeo e o PDF localmente para a apresentação não depender da rede.
Confirmar no resumo que há cinco confirmações e ambos os rovers em `parked`.
Evitar decorar números sem saber a configuração, revisão e unidade respetivas.
