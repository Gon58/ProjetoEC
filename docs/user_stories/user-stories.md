## US01 - Analisar tendências de preços

**Como** analista  
**Quero** visualizar a evolução dos preços ao longo do tempo  
**Para** identificar tendências e tomar decisões de investimento

### Critérios de Aceitação:
- [ ] O sistema apresenta gráficos de evolução temporal
- [ ] Os dados são obtidos a partir da base de dados SQL
- [ ] É possível selecionar intervalos de tempo
- [ ] A resposta é gerada em menos de 10 segundos

---

## US02 - Fazer perguntas em linguagem natural

**Como** utilizador  
**Quero** fazer perguntas em linguagem natural  
**Para** obter insights sobre o mercado de skins

### Critérios de Aceitação:
- [ ] O sistema responde com base em dados estruturados e não estruturados
- [ ] Utiliza RAG para contexto textual
- [ ] Utiliza SQL para cálculos exatos
- [ ] A resposta é coerente e contextualizada

---

## US03 - Interagir com o dashboard através do chat

**Como** utilizador  
**Quero** que o chat altere o dashboard  
**Para** explorar dados de forma dinâmica

### Critérios de Aceitação:
- [ ] O chat pode aplicar filtros aos dados
- [ ] O dashboard atualiza automaticamente
- [ ] O sistema indica ações (ex: "Consultando SQL...")

---

## US04 - Visualizar métricas e KPIs

**Como** analista  
**Quero** visualizar métricas relevantes  
**Para** compreender o estado do mercado

### Critérios de Aceitação:
- [ ] O sistema apresenta KPIs claros
- [ ] Os dados vêm diretamente do SQL
- [ ] Os gráficos são atualizados com filtros

---

## US05 - Obter dados exatos do sistema

**Como** utilizador  
**Quero** obter valores exatos (ex: médias, totais)  
**Para** tomar decisões baseadas em dados concretos

### Critérios de Aceitação:
- [ ] O sistema executa queries SQL
- [ ] Os resultados são corretos
- [ ] O LLM não inventa valores

---

## US06 - Obter contexto do mercado

**Como** utilizador  
**Quero** aceder a opiniões e contexto do mercado  
**Para** complementar dados quantitativos

### Critérios de Aceitação:
- [ ] O sistema utiliza dados de Reddit/Steam
- [ ] O RAG retorna informação relevante
- [ ] A resposta inclui contexto textual

---

## US07 - Pesquisar informação semanticamente

**Como** utilizador  
**Quero** pesquisar por significado e não apenas palavras-chave  
**Para** encontrar informação relevante

### Critérios de Aceitação:
- [ ] O sistema usa embeddings
- [ ] A pesquisa é baseada em similaridade vetorial
- [ ] Os resultados são relevantes

---

## US08 - Utilizar o sistema completo

**Como** utilizador  
**Quero** que o sistema funcione do dado até à resposta  
**Para** obter valor real do sistema

### Critérios de Aceitação:
- [ ] O sistema executa pipeline completo (dados → resposta)
- [ ] API responde corretamente
- [ ] Todas as componentes estão integradas

---

## US09 - Ter dados atualizados

**Como** utilizador  
**Quero** que os dados sejam atualizados regularmente  
**Para** garantir decisões atuais

### Critérios de Aceitação:
- [ ] O sistema executa ingestão diária
- [ ] O ETL processa os dados corretamente
- [ ] Os dados refletem atualizações recentes

---

## US10 - Validar comportamento do sistema

**Como** equipa de desenvolvimento  
**Quero** testar o sistema com perguntas de controlo  
**Para** garantir qualidade das respostas

### Critérios de Aceitação:
- [ ] Existe um script eval.py
- [ ] O sistema responde corretamente a perguntas definidas
- [ ] Os resultados são consistentes

---

