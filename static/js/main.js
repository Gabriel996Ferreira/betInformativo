// Aguarda todo o HTML da página carregar antes de rodar o script
document.addEventListener('DOMContentLoaded', () => {
    
    // Seleciona todas as linhas (tr) que estão dentro do corpo da tabela (tbody)
    const linhasTimes = document.querySelectorAll('tbody tr');

    // Para cada linha de time encontrada, adicionamos um evento de clique
    linhasTimes.forEach(linha => {
        linha.addEventListener('click', () => {
            
            // Pega o nome do time e as estatísticas direto do texto das células da tabela
            const nomeTime = linha.querySelector('.nome-time').innerText;
            const maisGols = linha.querySelectorAll('.stat-value')[0].innerText;
            const ambasMarcam = linha.querySelectorAll('.stat-value')[1].innerText;

            // Criando uma lógica simples de palpite baseada nos números
            let palpiteSugerido = "";
            
            // Converte a porcentagem (ex: "80%") em número inteiro (80) para fazer a lógica
            const porcentagemGols = parseInt(maisGols);

            if (porcentagemGols >= 80) {
                palpiteSugerido = `🔥 Forte tendência para o mercado de 'Mais de 1.5 Gols' (${maisGols} dos jogos).`;
            } else {
                palpiteSugerido = `⚖️ Jogo equilibrado. Ambas Marcam está em ${ambasMarcam}.`;
            }

            // Exibe um alerta personalizado na tela
            alert(`
📊 INSIGHT DE APOSTA: ${nomeTime.toUpperCase()}
--------------------------------------------------
• Mais de 1.5 Gols: ${maisGols}
• Ambas Marcam: ${ambasMarcam}

💡 Palpite do betInformativo:
${palpiteSugerido}
            `);
        });
    });
});