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

Códigos oficiais usados na convenção de branches:

| Código | Unidade curricular |
|---|---|
| `csiau` | Controlo de Sistemas Autónomos |
| `estap` | Estimação Aplicada |
| `dinav` | Dinâmica Avançada |
| `fumac` | Fundamentos Matemáticos da Computação |
| `laset` | Laboratório de Sistemas Embebidos e Tecnologias |
| `lasir` | Laboratório de Sistemas Robóticos |
| `perse` | Perceção e Sensores |
| `prose` | Projeto de Sistemas Embebidos |
| `psico` | Projeto de Sistemas de Controlo por Computador |
| `romov` | Robótica Móvel |
| `rsdis` | Redes de Sensores Distribuídos |
| `sisem` | Sistemas Embebidos |
| `soter` | Sistemas Operativos em Tempo Real |
| `tavru` | Tópicos Avançados de Visão para Robótica |

## Convenção de branches

As branches seguem o formato:

```
<unidade-curricular>/<tarefa>
```

Onde `<unidade-curricular>` é o código da tabela acima, em minúsculas, e
`<tarefa>` é uma descrição curta da tarefa, em minúsculas e com palavras
separadas por hífen.

Exemplo: `romov/filtro-kalman`

## Fluxo de trabalho

1. Atualizar a `main` local:

   ```bash
   git checkout main
   git pull origin main
   ```

2. Criar a branch a partir da `main`, seguindo a convenção acima:

   ```bash
   git checkout -b romov/filtro-kalman
   ```

3. Desenvolver o trabalho, fazendo commits de acordo com a convenção
   descrita abaixo.

4. Enviar a branch para o GitHub:

   ```bash
   git push -u origin romov/filtro-kalman
   ```

5. Abrir um Pull Request para `main`, com pelo menos 1 aprovação de
   outro elemento do grupo.

6. Fazer squash merge do Pull Request.

7. Apagar a branch depois do merge (é feito automaticamente pelo GitHub).

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
