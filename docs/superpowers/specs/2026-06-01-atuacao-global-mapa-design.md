# Atuação Global do Tauá — Mapa-múndi + reposicionamento de textos

**Data:** 2026-06-01
**Status:** Aprovado para implementação

## Problema

O site (`index.html`, página única estática) está fortemente focado em Salvador/Brasil,
mas o Tauá já tem alunos em **6 países**: Brasil, Estados Unidos, Inglaterra, Japão,
Austrália e Nova Zelândia. O posicionamento precisa refletir o alcance global do
atendimento **online**, mantendo o **presencial como exclusivo de Salvador**.

## Decisões (validadas com o cliente)

- **Mapa:** estilo *pontilhado* com os continentes desenhados a partir do mapa-múndi
  real (Natural Earth), em faixa dedicada de largura total logo após o texto da seção
  "Sobre", com título próprio ("De Salvador para o mundo").
- **Presencial:** continua **exclusivo de Salvador** em todos os pontos do site.
- **Online:** reposicionado como **global** (alunos nos 6 países).
- **SEO:** abordagem em **camadas** — mantém os sinais locais de Salvador (que rankeiam
  o presencial) e **soma** o alcance global em title/description/OG/JSON-LD.
- **Depoimentos:** trocar apenas a **cidade** do depoimento de treino online
  (Rafael Costa) para uma cidade internacional; sem inventar texto novo.
- **Continentes:** 6 países = 5 continentes (Am. do Sul, Am. do Norte, Europa, Ásia, Oceania).

## Arquitetura do componente de mapa

Fiel à arquitetura atual (HTML único, sem build, sem dependências externas):

1. **Dados de terra:** máscara binária de terra (land/ocean) pré-computada a partir do
   GeoJSON `ne_110m_land` (Natural Earth), projeção equiretangular, grade 200×81,
   recorte de latitude `[85, -60]` (sem Antártida). Serializada como base64 (~2.7KB) e
   **embutida inline** no `index.html`.
2. **Render dos continentes:** `<canvas>` desenhado **uma vez** quando a seção entra na
   viewport (IntersectionObserver, padrão `reveal`/`cv-auto` já usado no site). Pontos
   em tom cinza-quente (`#46413a`), `devicePixelRatio` para nitidez em retina,
   `aspect-ratio` travado (1000:403).
3. **Marcadores + arcos:** camada `<svg>` sobreposta com:
   - 6 marcadores nas coordenadas reais (lat/lon → projeção equiretangular idêntica).
   - Salvador como marcador "home" (dourado, maior); demais países em laranja.
   - Halos pulsantes (SVG `<animate>`), arcos quadráticos ligando cada país a Salvador
     (gradiente laranja→dourado), rótulos com o nome do país.
4. **Faixa de números** abaixo do mapa: "6 países · 5 continentes · acompanhamento em
   tempo real".

### Coordenadas dos marcadores (lat, lon)

| País | lat | lon |
|---|---|---|
| Brasil (Salvador, home) | -12.97 | -38.5 |
| Estados Unidos | 39 | -98 |
| Inglaterra | 52.5 | -1.5 |
| Japão | 36.5 | 138 |
| Austrália | -33.5 | 148 |
| Nova Zelândia | -41 | 174 |

Projeção: `x = (lon+180)/360 * 1000`, `y = (85 - lat)/(85 - (-60)) * 403`.

### Acessibilidade e performance

- `role="img"` + `aria-label` na figura; **lista de países visualmente oculta** para
  leitores de tela (a informação não pode depender só do canvas).
- `@media (prefers-reduced-motion: reduce)` desliga halos/pulsos.
- Desenho adiado até a seção entrar na viewport; `content-visibility:auto` na seção.
- **Mobile:** mapa reflui mantendo proporção; nomes dos países viram legenda em chips
  abaixo do mapa quando a largura é pequena.

## Mudanças de texto (alcance global)

| Local (linha aprox.) | Depois |
|---|---|
| Hero tag (983) | "Presencial em Salvador, online no mundo todo — seu resultado não tem fronteira." |
| Sobre p2 (1061) | "…consultoria online para alunos no Brasil, Estados Unidos, Inglaterra, Japão, Austrália e Nova Zelândia." |
| Serviço Online (1109) | "…sem sair de casa, onde quer que você esteja no mundo." |
| FAQ "Onde atende" (1232) | "…consultoria online para alunos no mundo todo — hoje em 6 países: Brasil, EUA, Inglaterra, Japão, Austrália e Nova Zelândia." |
| Contato lead (1314) | "…consultoria online para alunos no mundo todo." |
| Rodapé (1343) | + menção "Alunos em 6 países" |

O presencial permanece **exclusivo de Salvador** (badge "Exclusivo Salvador", card
presencial, `photo-tag` "Salvador · BA").

## SEO / dados estruturados (camadas local + global)

- `<title>`, `meta description`, OG, Twitter: mantêm "Salvador-BA" e **somam** o alcance
  online global.
- JSON-LD `LocalBusiness.areaServed`: mantém Salvador + Bahia + Brasil e **acrescenta**
  Estados Unidos, Reino Unido, Japão, Austrália, Nova Zelândia.
- Offer "Consultoria Online" `areaServed`: `"Brasil"` → lista global.
- `FAQPage` answer "Onde atende" sincronizada com o texto visível.
- **Não alterar** `address`/`geo` de Salvador (âncora do ranking local presencial).
- Nota: no schema usa-se "Reino Unido"; no texto visível mantém-se "Inglaterra".

## Depoimento internacional

- Rafael Costa (depoimento do treino online): cidade `São Paulo, SP` → `Londres, Inglaterra`.
- Nome e texto preservados; `JSON-LD review` não precisa mudar (review não tem localidade).

## Fora de escopo

- Não criar item de navegação novo para a faixa do mapa.
- Não traduzir o site para outros idiomas.
- Não substituir os depoimentos por reais (segue como placeholder, conforme comentário já existente).

## Verificação

Sem framework de testes no repo (site estático, sem build). Verificação por render no
navegador (Playwright): mapa desenha os continentes, 6 marcadores nas posições corretas,
layout responsivo (mobile/desktop), `prefers-reduced-motion` desliga animação, e os
textos atualizados aparecem nas seções.
