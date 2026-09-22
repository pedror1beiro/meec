# Redes de Sensores Distribuídos (RSDIS)

Exercícios da unidade curricular de Redes de Sensores Distribuídos.

> O Exercício 1 contém implementações equivalentes em **ROS1 (Catkin)** e **ROS2 Jazzy (ament_cmake/colcon)**.

## Organização

```text
rsdis/
├── README.md
└── exercicio-1/
    ├── ros1/
    │   ├── rsdis_t1a/
    │   └── rsdis_t1b/
    └── ros2/
        ├── rsdis_t1a/
        └── rsdis_t1b/
```

## Exercício 1 — Enunciado

### T1A

Criar um package com:

- um nó publicador de mensagens `Float32` a **50 Hz**;
- um nó subscritor das mesmas mensagens.

### T1B

Criar um package com:

- um nó publicador de mensagens `Pose` a **1 Hz**;
- todos os campos de posição e orientação preenchidos;
- um nó subscritor das mesmas mensagens.

## Solução

| Parte | Tópico | Mensagem | Frequência | Executáveis |
| --- | --- | --- | --- | --- |
| T1A | `/float_topic` | `Float32` | 50 Hz | `talker_t1a`, `listener_t1a` |
| T1B | `/pose_topic` | `Pose` | 1 Hz | `talker_t1b`, `listener_t1b` |

O T1A publica o valor `3.14`. O T1B publica a posição `(1, 2, 0)` e a orientação `(0, 0, 0, 1)`, correspondente ao quaternion identidade.

## ROS1

### Compilação

Colocar os packages em `catkin_ws/src/` e executar:

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

### Execução

Executar primeiro `roscore`. Depois, em terminais separados:

```bash
rosrun rsdis_t1a talker_t1a
rosrun rsdis_t1a listener_t1a
rostopic echo /float_topic
```

Para o T1B:

```bash
rosrun rsdis_t1b talker_t1b
rosrun rsdis_t1b listener_t1b
rostopic echo /pose_topic
```

## ROS2 Jazzy

### Compilação

Colocar os packages em `ros2_ws/src/` e executar:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2_ws
colcon build
source install/setup.bash
```

Não é necessário executar `roscore` no ROS2.

### Execução

Em terminais separados, ativar primeiro o ambiente com:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

Para o T1A:

```bash
ros2 run rsdis_t1a talker_t1a
ros2 run rsdis_t1a listener_t1a
ros2 topic echo /float_topic
ros2 topic hz /float_topic
```

Para o T1B:

```bash
ros2 run rsdis_t1b talker_t1b
ros2 run rsdis_t1b listener_t1b
ros2 topic echo /pose_topic
ros2 topic hz /pose_topic
```

> Executar T1A e T1B separadamente, pois ambos usam os nomes de nós `talker` e `listener`.

## Evidências

### ROS1

- T1A: [`rostopic echo`](exercicio-1/ros1/rsdis_t1a/screenshots/rostopic_echo.png) · [`rqt_graph`](exercicio-1/ros1/rsdis_t1a/screenshots/rqt_graph.png)
- T1B: [`rostopic echo`](exercicio-1/ros1/rsdis_t1b/screenshots/rostopic_echo.png) · [`rqt_graph`](exercicio-1/ros1/rsdis_t1b/screenshots/rqt_graph.png)

### ROS2

- T1A: [`topic echo`](exercicio-1/ros2/rsdis_t1a/screenshots/topic_echo.png) · [`rqt_graph`](exercicio-1/ros2/rsdis_t1a/screenshots/rqt_graph.png) · [`50 Hz`](exercicio-1/ros2/rsdis_t1a/screenshots/frequency_50hz.png)
- T1B: [`topic echo`](exercicio-1/ros2/rsdis_t1b/screenshots/topic_echo.png) · [`rqt_graph`](exercicio-1/ros2/rsdis_t1b/screenshots/rqt_graph.png) · [`1 Hz`](exercicio-1/ros2/rsdis_t1b/screenshots/frequency_1hz.png)

## Entrega

Para submeter cada parte separadamente, incluir o respetivo package e a pasta `screenshots/`, excluindo diretórios gerados como `build/`, `install/`, `log/` e `devel/`.
