# meec

Repositório para unidades curriculares do mestrado de Sistemas Autónomos.

## Objetivo

Este repositório reúne o trabalho desenvolvido pelo grupo (3 pessoas) ao
longo do mestrado, organizando por unidade curricular o código, os testes
e outros materiais das diferentes disciplinas.

## Convenção de branches

As branches seguem o formato:

```
<unidade-curricular>/<tipo>/<descricao-curta>
```

Exemplo: `sad/feat/filtro-kalman`

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
automaticamente em cada Pull Request e em cada push para `main`. Só são
executados os jobs correspondentes às linguagens que tiverem ficheiros
alterados.

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
