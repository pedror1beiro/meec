# meec

Repositório para unidades curriculares do mestrado de Sistemas Autónomos.

## Objetivo

Este repositório reúne o trabalho desenvolvido pelo grupo (3 pessoas) ao
longo do mestrado, organizando por unidade curricular o código, os
relatórios, notebooks e outros materiais das diferentes disciplinas.

O repositório é público. Não devem ser adicionados dados pessoais, notas
ou outra informação sensível; relatórios e código são partilháveis, mas
qualquer ficheiro desse tipo deve ser revisto antes do commit.

## Unidades curriculares

Códigos usados na convenção de branches, referentes ao Mestrado em
Engenharia Eletrotécnica e de Computadores, ramo de Sistemas Autónomos:

| Código | Unidade curricular |
|---|---|
| `lset` | Laboratório de Sistemas Embebidos e Tecnologias |
| `fims` | Fusão de Informação Multi-Sensorial |
| `percsens` | Perceção e Sensores |
| `pse` | Projeto de Sistemas Embebidos |
| `rsd` | Redes de Sensores Distribuídos |
| `robmov` | Robótica Móvel |
| `se` | Sistemas Embebidos |
| `smr` | Sistemas Multirobóticos |
| `sort` | Sistemas Operativos em Tempo Real |
| `tmsa` | Tópicos de Matemática para Sistemas Autónomos |
| `ace` | Atividades Complementares em Engenharia |
| `lsr` | Laboratório de Sistemas Robóticos |
| `csa` | Controlo de Sistemas Autónomos |
| `dinav` | Dinâmica Avançada |
| `estap` | Estimação Aplicada |
| `fmc` | Fundamentos Matemáticos da Computação |
| `pscc` | Projeto de Sistemas de Controlo por Computador |
| `tavr` | Tópicos Avançados de Visão para Robótica |
| `lsmr` | Laboratório de Sistemas Multirobóticos |
| `tpd` | Trabalho Preparatório para Dissertação |
| `dissertacao` | Dissertação |

## Convenção de branches

As branches seguem o formato:

```
<unidade-curricular>/<tipo>/<descricao-curta>
```

Exemplo: `robmov/feat/filtro-kalman`

Tipos possíveis: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## Fluxo de trabalho

1. Criar uma branch a partir de `main`, seguindo a convenção acima.
2. Desenvolver o trabalho, fazendo commits de acordo com a convenção
   descrita abaixo.
3. Abrir um Pull Request para `main`, com pelo menos 1 aprovação de
   outro elemento do grupo.
4. Fazer squash merge do Pull Request.
5. Apagar a branch depois do merge.

## Convenção de commits

Seguimos o padrão Conventional Commits:

- `feat:` nova funcionalidade
- `fix:` correção de um problema
- `docs:` alterações à documentação
- `refactor:` alteração de código sem mudança de comportamento
- `test:` adição ou alteração de testes

Exemplo: `feat: adicionar filtro de kalman ao modulo de localizacao`

## Verificações de CI

A integração contínua está definida em
[.github/workflows/ci.yml](.github/workflows/ci.yml) e corre
automaticamente em cada Pull Request e em cada push para `main`. Os jobs
de Python e C/C++ só correm quando há ficheiros alterados dessa
linguagem; a verificação de ficheiros grandes corre sempre, porque se
aplica a qualquer tipo de ficheiro (relatórios, notebooks, imagens).

### Python

Para correr as mesmas verificações localmente:

```bash
pip install ruff pytest
ruff check .
pytest
```

### C/C++

Para verificar a formatação localmente:

```bash
find . -regex '.*\.\(c\|cc\|cpp\|h\|hpp\)$' -print0 \
  | xargs -0 clang-format --dry-run --Werror
```
