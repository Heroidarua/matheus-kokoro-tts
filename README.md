# Matheus Kokoro TTS — teste pm_alex

Branch experimental para avaliar a voz masculina brasileira `pm_alex` do Kokoro-82M. A branch `main` permanece intacta com o serviço Piper atual.

## Modelo e voz

- Motor: Kokoro-82M via `kokoro-onnx`
- Voz: `pm_alex` (masculina, português brasileiro)
- Idioma/G2P: `pt-br` via Misaki/espeak-ng
- Modelo: FP16, 163.527.961 bytes (~163,5 MB)
- Pacote de embeddings: `voices-v1.0.bin`, 28.214.398 bytes (~28,2 MB)
- Total dos dois artefatos: ~191,7 MB
- Saída: WAV PCM 16-bit
- API compatível com `POST /v1/audio/speech`

Os arquivos são baixados durante o build e verificados por SHA-256. O arquivo de vozes contém vários perfis; o servidor só seleciona `pm_alex`.

## Deploy experimental no Render

Crie um Web Service separado (ou um serviço de teste) apontando para esta branch:

`test/kokoro-pm-alex`

Runtime: Docker. Plano Free pode não ter memória suficiente para o modelo e as dependências durante a inferência; confirme o consumo nos logs e métricas. Não substitua o serviço Piper de produção antes de validar o teste.

Variáveis opcionais:
- `TTS_API_KEY`: chave Bearer para proteger o endpoint.
- `KOKORO_SPEED`: velocidade padrão (1.0).

## Endpoints

- `GET /`: informações do serviço
- `GET /health`: estado do carregamento
- `POST /v1/audio/speech`: gera WAV
- `GET /docs`: documentação OpenAPI

Exemplo:

```bash
curl -X POST "https://SEU-SERVICO.onrender.com/v1/audio/speech" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SUA_CHAVE" \
  -d '{"model":"kokoro","input":"Olá! Eu sou o Matheus AI. Como posso ajudar você hoje?","voice":"pm_alex","response_format":"wav","speed":1.0}' \
  --output teste-pm-alex.wav
```

A chave é opcional no serviço, mas recomendada em produção. Não coloque segredos no GitHub nem no frontend.

## Segurança e estabilidade

- Um worker e uma síntese por vez para limitar memória.
- Limite de 3.000 caracteres por requisição.
- Velocidade permitida: 0,7 a 1,3.
- O serviço Piper em `main` não é alterado por esta branch.
