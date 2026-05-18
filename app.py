from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'chave_secreta_para_alertas_flash'

# Configuração da Base de Dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bet_informativo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==============================================================================
# MODELOS DA BASE DE DADOS
# ==============================================================================
class Time(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    posicao = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    pontos = db.Column(db.Integer, nullable=False)
    forma_letras = db.Column(db.String(20), nullable=False)  # Guarda como "V,V,E,V,D"
    placares = db.Column(db.String(50), nullable=False)      # Guarda como "3-1,2-0,1-1,3-0,0-1"

# Nova Tabela para controlar o histórico de atualizações automáticas
class ControleAtualizacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ultima_atualizacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Inicialização segura da base de dados
with app.app_context():
    db.create_all()
    # Se a base de dados estiver vazia, popula com dados iniciais de teste
    if Time.query.count() == 0:
        t1 = Time(posicao=1, nome="Botafogo", pontos=12, forma_letras="V,V,E,V,D", placares="3-1,2-0,1-1,3-0,0-1")
        t2 = Time(posicao=2, nome="Palmeiras", pontos=10, forma_letras="V,E,V,V,E", placares="1-0,0-0,2-1,2-0,1-1")
        t3 = Time(posicao=3, nome="Flamengo", pontos=9, forma_letras="D,V,D,V,V", placares="1-2,4-1,0-2,3-2,2-1")
        db.session.add_all([t1, t2, t3])
        
        # Cria o primeiro registo de data da atualização
        registro_tempo = ControleAtualizacao(ultima_atualizacao=datetime.utcnow() - timedelta(hours=3)) # Força uma data antiga para teste
        db.session.add(registro_tempo)
        
        db.session.commit()

# ==============================================================================
# SISTEMA DE SINCRONIZAÇÃO AUTOMÁTICA (O Coração do Passo 2)
# ==============================================================================
def executar_sincronizacao_silenciosa():
    """Busca os dados de futebol da nuvem e atualiza a base de dados sem intervenção humana"""
    try:
        print("🔄 [AUTOMAÇÃO] A procurar novos dados de futebol na API...")
        # Chamada à API externa para capturar os dados novos
        response = requests.get('https://api.jsonbin.io/v3/b/65678a9c12a5d376599ff012', timeout=5)
        
        if response.status_code == 200:
            dados_api = response.json().get('record', {}).get('times', [])
            
            # Limpa os dados antigos e salva os novos recebidos da internet
            Time.query.delete()
            for time_data in dados_api:
                novo_time = Time(
                    posicao=time_data["posicao"],
                    nome=time_data["nome"],
                    pontos=time_data["pontos"],
                    forma_letras=time_data["forma"],
                    placares=time_data["placares"]
                )
                db.session.add(novo_time)
            
            # Atualiza a data de controlo para a hora atual de sucesso
            registro = ControleAtualizacao.query.first()
            if registro:
                registro.ultima_atualizacao = datetime.utcnow()
            else:
                db.session.add(ControleAtualizacao(ultima_atualizacao=datetime.utcnow()))
                
            db.session.commit()
            print("✅ [AUTOMAÇÃO] Sincronização executada automaticamente com sucesso!")
            return True
    except Exception as e:
        print(f"❌ [AUTOMAÇÃO] Erro ao sincronizar automaticamente: {e}")
        return False

# ==============================================================================
# LÓGICA DE NEGÓCIO (Cálculo de Estatísticas)
# ==============================================================================
def processar_dados_times(times_do_banco):
    lista_times_formatados = []
    for time in times_do_banco:
        lista_ultimos_5 = time.forma_letras.split(',')
        lista_placares = time.placares.split(',')
        
        jogos_mais_1_5 = 0
        jogos_ambas_marcam = 0
        total_jogos = len(lista_placares) if len(lista_placares) > 0 else 1

        for placar in lista_placares:
            if '-' in placar:
                try:
                    gols_pro, gols_contra = map(int, placar.split('-'))
                    if (gols_pro + gols_contra) > 1.5:
                        jogos_mais_1_5 += 1
                    if gols_pro > 0 and gols_contra > 0:
                        jogos_ambas_marcam += 1
                except ValueError:
                    continue

        time_formatado = {
            "id": time.id,
            "posicao": time.posicao,
            "nome": time.nome,
            "pontos": time.pontos,
            "ultimos_5": lista_ultimos_5,
            "estatisticas": {
                "mais_1_5_gols": f"{int((jogos_mais_1_5 / total_jogos) * 100)}%",
                "ambas_marcam": f"{int((jogos_ambas_marcam / total_jogos) * 100)}%"
            }
        }
        lista_times_formatados.append(time_formatado)
        
    return lista_times_formatados

# ==============================================================================
# ROTAS DO APLICATIVO
# ==============================================================================
@app.route('/')
def index():
    # 🕵️‍♂️ VERIFICAÇÃO AUTOMÁTICA: O utilizador acabou de entrar na página principal
    registro = ControleAtualizacao.query.first()
    
    # Se os dados foram atualizados há mais de 2 horas (para testes você pode mudar para minutos ou segundos)
    tempo_limite = datetime.utcnow() - timedelta(hours=2)
    
    if not registro or registro.ultima_atualizacao < tempo_limite:
        # Chamar a função de sincronização em segundo plano automaticamente!
        executar_sincronizacao_silenciosa()

    # Pega a data da última atualização para exibir no rodapé
    registro_atualizado = ControleAtualizacao.query.first()
    data_formatada = ""
    if registro_atualizado:
        # Formata a hora de gravação da base de dados para exibir no ecrã
        data_formatada = registro_atualizado.ultima_atualizacao.strftime('%d/%m/%Y %H:%M:%S')

    times_banco = Time.query.order_by(Time.posicao).all()
    times_processados = processar_dados_times(times_banco)
    return render_template('index.html', times=times_processados, ultima_sinc=data_formatada)

@app.route('/admin')
def admin():
    times_banco = Time.query.order_by(Time.posicao).all()
    times_processados = processar_dados_times(times_banco)
    return render_template('admin.html', times=times_processados)

@app.route('/admin/salvar', methods=['POST'])
def admin_salvar():
    posicao = request.form.get('posicao')
    nome = request.form.get('nome')
    pontos = request.form.get('pontos')
    forma = request.form.get('forma').upper().replace(' ', '')
    placares = request.form.get('placares').replace(' ', '')

    if not all([posicao, nome, pontos, forma, placares]):
        flash('Erro: Todos os campos do formulário devem ser preenchidos!', 'error')
        return redirect(url_for('admin'))

    time_existente = Time.query.filter_by(posicao=posicao).first()
    if time_existente:
        time_existente.nome = nome
        time_existente.pontos = pontos
        time_existente.forma_letras = forma
        time_existente.placares = placares
        flash(f'Equipa "{nome}" atualizada com sucesso!', 'success')
    else:
        novo_time = Time(posicao=posicao, nome=nome, pontos=pontos, forma_letras=forma, placares=placares)
        db.session.add(novo_time)
        flash(f'Equipa "{nome}" guardada com sucesso!', 'success')

    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/excluir/<int:id>', methods=['POST'])
def admin_excluir(id):
    time_para_deletar = Time.query.get_or_404(id)
    nome_time = time_para_deletar.nome
    db.session.delete(time_para_deletar)
    db.session.commit()
    flash(f'Equipa "{nome_time}" removida com sucesso!', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)