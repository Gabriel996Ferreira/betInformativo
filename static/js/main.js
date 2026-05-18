/**
 * Script de controlo para análise dinâmica do betInformativo
 */
document.addEventListener('DOMContentLoaded', () => {
    const rows = document.querySelectorAll('.clickable-row');
    const tipBox = document.getElementById('tip-box');
    const tipTitle = document.getElementById('tip-title');
    const tipMessage = document.getElementById('tip-message');

    rows.forEach(row => {
        row.addEventListener('click', () => {
            // Extração de dados da linha clicada
            const name = row.getAttribute('data-name');
            const over15 = parseFloat(row.getAttribute('data-over'));
            const btts = parseFloat(row.getAttribute('data-btts'));

            // Construção personalizada do conselho de aposta em tempo real
            let advice = "";
            if (over15 >= 70 && btts >= 60) {
                advice = `Excelente cenário para gols! O ${name} apresenta ${over15}% de frequência para +1.5 Gols e ${btts}% em Ambas Marcam. Sugere-se uma entrada combinada de over + btts.`;
            } else if (over15 >= 70) {
                advice = `Análise forte para mercado de gols. O ${name} mantém uma consistência de ${over15}% de partidas com mais de 1.5 gols. Excelente para acumuladores de gols.`;
            } else if (btts >= 60) {
                advice = `Mercado de Ambas Marcam está atrativo. Com ${btts}% de ocorrência nos jogos do ${name}, a expectativa é de gols de ambos os lados neste confronto.`;
            } else {
                advice = `Tendência de jogo equilibrado e fechado. O ${name} apresenta médias modestas de gols (${over15}% para +1.5). Uma aposta em gols tem risco elevado.`;
            }

            // Atualização visual do painel de recomendação desportiva
            tipTitle.innerHTML = `<i class="fa-solid fa-calculator"></i> Análise de Aposta: <strong>${name}</strong>`;
            tipMessage.textContent = advice;
            
            // Exibição do painel oculto com efeito suave
            tipBox.classList.remove('hidden');
            tipBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        });
    });
});