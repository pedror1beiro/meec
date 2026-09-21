# Redes de Sensores Distribuídos (RSDIS)

Repositório de exercícios da unidade curricular de Redes de Sensores Distribuídos.

> O Exercício 1 foi desenvolvido em **ROS1**, utilizando Catkin. Os exercícios seguintes poderão utilizar **ROS2**; por isso, cada exercício identifica explicitamente a versão de ROS utilizada.

## Organização

```text
rsdis/
├── README.md
└── exercicio-1/
    └── ros1/
        ├── rsdis_t1a/
        └── rsdis_t1b/
```

Para futuros trabalhos, deve manter-se a mesma convenção, por exemplo:

```text
exercicio-2/
└── ros2/
```

## Exercício 1 — Enunciado

### T1A

Criar o package `rsdis_t1a` com:

- um nó publicador de mensagens `std_msgs/Float32` a **50 Hz**;
- um nó subscritor de mensagens `std_msgs/Float32`.

### T1B

Criar o package `rsdis_t1b` com:

- um nó publicador de mensagens `geometry_msgs/Pose` a **1 Hz**;
- todos os campos de posição e orientação preenchidos;
- um nó subscritor de mensagens `geometry_msgs/Pose`.

### Submissão

Entregar os dois packages com screenshots de:

- `rostopic echo`;
- `rqt_graph`.

Os ficheiros finais pedidos são `GX_t1a.zip` e `GX_t1b.zip`.

## Resolução

### Package `rsdis_t1a`

| Componente | Implementação |
| --- | --- |
| Publicador | Nó `talker`, tópico `/float_topic`, tipo `std_msgs/Float32`, frequência de 50 Hz |
| Subscritor | Nó `listener`, subscrição do tópico `/float_topic` |
| Executáveis | `talker_t1a` e `listener_t1a` |

O publicador envia o valor de exemplo `3.14`. O subscritor apresenta cada valor recebido através de `ROS_INFO`.

### Package `rsdis_t1b`

| Componente | Implementação |
| --- | --- |
| Publicador | Nó `talker`, tópico `/pose_topic`, tipo `geometry_msgs/Pose`, frequência de 1 Hz |
| Subscritor | Nó `listener`, subscrição do tópico `/pose_topic` |
| Executáveis | `talker_t1b` e `listener_t1b` |

O publicador preenche os campos `position.x`, `position.y`, `position.z`, `orientation.x`, `orientation.y`, `orientation.z` e `orientation.w`. A orientação `(0, 0, 0, 1)` corresponde ao quaternion identidade.

## Compilação

Colocar as pastas `rsdis_t1a` e `rsdis_t1b` dentro de `catkin_ws/src/`. Depois executar:

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

É necessário executar `source ~/catkin_ws/devel/setup.bash` em cada novo terminal usado para correr os nós.

## Execução

Iniciar primeiro o ROS Master:

```bash
roscore
```

### T1A

Abrir terminais separados e executar:

```bash
rosrun rsdis_t1a talker_t1a
rosrun rsdis_t1a listener_t1a
rostopic echo /float_topic
rqt_graph
```

O `rostopic echo` deve apresentar valores `3.14`, e o `rqt_graph` deve mostrar a comunicação do nó publicador para o subscritor através de `/float_topic`.

### T1B

Abrir terminais separados e executar:

```bash
rosrun rsdis_t1b talker_t1b
rosrun rsdis_t1b listener_t1b
rostopic echo /pose_topic
rqt_graph
```

O `rostopic echo` deve apresentar todos os campos de `position` e `orientation`, e o `rqt_graph` deve mostrar a comunicação através de `/pose_topic`.

> Executar T1A e T1B separadamente, porque ambos os packages usam os nomes de nós `talker` e `listener`.

## Evidências e entrega

As evidências de funcionamento encontram-se na pasta `screenshots/` de cada package:

- T1A: [`rostopic echo`](exercicio-1/ros1/rsdis_t1a/screenshots/rostopic_echo.png) e [`rqt_graph`](exercicio-1/ros1/rsdis_t1a/screenshots/rqt_graph.png);
- T1B: [`rostopic echo`](exercicio-1/ros1/rsdis_t1b/screenshots/rostopic_echo.png) e [`rqt_graph`](exercicio-1/ros1/rsdis_t1b/screenshots/rqt_graph.png).

Para a entrega, compactar cada package separadamente com os nomes `GX_t1a.zip` e `GX_t1b.zip`.
