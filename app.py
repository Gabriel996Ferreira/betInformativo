from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import requests
import traceback  # Importado para podermos ver o erro exato no terminal se algo falhar

app = Flask(__name__)
app.secret_key = 'chave_secreta_para_bet_informativo'

# Configuração da Base de Dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bet_informativo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==============================================================================
# MODELO DA BASE DE DADOS (Estrutura da Tabela)
# ==============================================================================
class Time(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    posicao = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    pontos = db.Column(db.Integer, nullable=False)
    forma_letras = db.Column(db.String(20), nullable=False)  # Guarda como "V,V,E,V,D"
    placares = db.Column(db.String(50), nullable=False)      # Guarda como "3-1,2-0,1-1,3-0,0-1"

# Inicialização segura da base de dados (Funciona localmente e no Render)
with app.app_context():
    try:
        db.create_all()
        # Se a base de dados estiver vazia, popula com dados iniciais de teste
        if Time.query.count() == 0:
            t1 = Time(posicao=1, nome="Botafogo", pontos=15, forma_letras="V,V,E,V,V", placares="3-1,2-0,1-1,3-0,2-1")
            t2 = Time(posicao=2, nome="Palmeiras", pontos=13, forma_letras="V,V,V,V,E", placares="2-0,1-0,2-1,3-0,1-1")
            t3 = Time(posicao=3, nome="Flamengo", pontos=12, forma_letras="V,V,D,V,V", placares="2-1,4-1,0-2,3-2,2-1")
            db.session.add_all([t1, t2, t3])
            db.session.commit()
            print("🔋 [BD] Base de dados inicializada com dados padrão!")
    except Exception as e:
        print("❌ [ERRO BD] Erro ao inicializar a base de dados:")
        traceback.print_exc()

# ==============================================================================
# LÓGICA DE NEGÓCIO (Cálculo de Estatísticas)
# ==============================================================================
def processar_dados_times(times_do_banco):
    lista_times_formatados = []
    for time in times_do_banco:
        lista_ultimos_5 = time.forma_letras.split(',') if time.forma_letras else []
        lista_placares = time.placares.split(',') if time.placares else []
        
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
            "forma_letras": time.forma_letras,
            "placares_raw": time.placares,
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
    try:
        times_banco = Time.query.order_by(Time.posicao).all()
        times_processados = processar_dados_times(times_banco)
        return render_template('index.html', times=times_processados)
    except Exception as e:
        print("❌ [ERRO INDEX] Falha ao carregar a página principal:")
        traceback.print_exc()
        return f"Erro Interno do Servidor na Página Principal. Verifique o terminal do VS Code para detalhes.", 500

@app.route('/admin')
def admin():
    try:
        times_banco = Time.query.order_by(Time.posicao).all()
        times_processados = processar_dados_times(times_banco)
        return render_template('admin.html', times=times_processados)
    except Exception as e:
        print("❌ [ERRO ADMIN] Falha ao carregar a página administrativa:")
        traceback.print_exc()  # Isto vai imprimir no seu terminal o motivo exato do erro!
        return f"Erro Interno do Servidor ao carregar o Painel Admin. Verifique o terminal do VS Code para detalhes.", 500

@app.route('/admin/salvar', methods=['POST'])
def admin_salvar():
    try:
        time_id = request.form.get('time_id')
        posicao = request.form.get('posicao')
        nome = request.form.get('nome')
        pontos = request.form.get('pontos')
        forma = request.form.get('forma').upper().replace(' ', '')
        placares = request.form.get('placares').replace(' ', '')

        if not all([posicao, nome, pontos, forma, placares]):
            flash('Erro: Todos os campos do formulário devem ser preenchidos!', 'error')
            return redirect(url_for('admin'))

        if time_id:
            time_existente = Time.query.get(time_id)
            if time_existente:
                time_existente.posicao = posicao
                time_existente.nome = nome
                time_existente.pontos = pontos
                time_existente.forma_letras = forma
                time_existente.placares = placares
                flash(f'Equipa "{nome}" atualizada com sucesso!', 'success')
            else:
                flash('Erro: Equipa não encontrada para edição.', 'error')
        else:
            novo_time = Time(posicao=posicao, nome=nome, pontos=pontos, forma_letras=forma, placares=placares)
            db.session.add(novo_time)
            flash(f'Equipa "{nome}" guardada com sucesso!', 'success')

        db.session.commit()
    except Exception as e:
        print("❌ [ERRO SALVAR] Falha ao gravar dados:")
        traceback.print_exc()
        flash('Erro interno ao salvar os dados.', 'error')
        
    return redirect(url_for('admin'))

@app.route('/admin/excluir/<int:id>', methods=['POST'])
def admin_excluir(id):
    try:
        time_para_deletar = Time.query.get_or_404(id)
        nome_time = time_para_deletar.nome
        db.session.delete(time_para_deletar)
        db.session.commit()
        flash(f'Equipa "{nome_time}" removida com sucesso!', 'success')
    except Exception as e:
        print("❌ [ERRO EXCLUIR] Falha ao remover equipa:")
        traceback.print_exc()
        flash('Erro interno ao tentar remover a equipa.', 'error')
        
    return redirect(url_for('admin'))

@app.route('/admin/sincronizar')
def admin_sincronizar():
    try:
        response = requests.get('https://api.jsonbin.io/v3/b/65678a9c12a5d376599ff012', timeout=5)
        if response.status_code == 200:
            dados_api = response.json().get('record', {}).get('times', [])
        else:
            raise Exception("Falha na API externa")
            
    except Exception:
        dados_api = [
            {"posicao": 1, "nome": "Botafogo", "pontos": 15, "forma": "V,V,E,V,V", "placares": "3-1,2-0,1-1,3-0,2-1"},
            {"posicao": 2, "nome": "Palmeiras", "pontos": 13, "forma": "V,V,V,V,E", "placares": "2-0,1-0,2-1,3-0,1-1"},
            {"posicao": 3, "nome": "Flamengo", "pontos": 12, "forma": "V,V,D,V,V", "placares": "2-1,4-1,0-2,3-2,2-1"},
            {"posicao": 4, "nome": "Fortaleza", "pontos": 10, "forma": "E,V,V,D,E", "placares": "1-1,2-0,3-1,0-1,0-0"},
            {"posicao": 5, "nome": "São Paulo", "pontos": 8, "forma": "D,E,V,D,V", "placares": "0-1,2-2,3-1,1-2,1-0"}
        ]

    try:
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
        db.session.commit()
        flash("Sincronização com a API de Futebol realizada com sucesso! 5 Equipas carregadas.", "success")
    except Exception as e:
        print("❌ [ERRO SINCRONIZAR] Falha na gravação em lote:")
        traceback.print_exc()
        flash('Erro interno ao sincronizar os dados.', 'error')
        
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)