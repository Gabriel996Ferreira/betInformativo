from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuração do Banco de Dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bet_informativo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==========================================
# MODELO DO BANCO DE DADOS
# ==========================================
class Time(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    posicao = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    pontos = db.Column(db.Integer, nullable=False)
    forma_letras = db.Column(db.String(20), nullable=False)  # Ex: "V,V,E,V,D"
    placares = db.Column(db.String(50), nullable=False)      # Ex: "3-1,2-0,1-1,3-0,0-1"

# ==========================================
# LÓGICA DE CÁLCULO DAS PORCENTAGENS
# ==========================================
def processar_dados_times(times_do_banco):
    lista_times_formatados = []
    
    for time in times_do_banco:
        lista_ultimos_5 = time.forma_letras.split(',')
        lista_placares = time.placares.split(',')
        
        jogos_mais_1_5 = 0
        jogos_ambas_marcam = 0
        total_jogos = len(lista_placares) if lista_placares else 1

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

# ==========================================
# ROTAS PÚBLICAS (VISITANTE)
# ==========================================
@app.route('/')
def index():
    times_banco = Time.query.order_by(Time.posicao).all()
    times_processados = processar_dados_times(times_banco)
    return render_template('index.html', times=times_processados)

# ==========================================
# ROTAS ADMINISTRATIVAS (CRUD)
# ==========================================

# 1. Tela de gerenciamento (Lista times e exibe o formulário)
@app.route('/admin')
def admin():
    # Busca todos os times para listar no painel
    times_banco = Time.query.order_by(Time.posicao).all()
    return render_template('admin.html', times=times_banco)

# 2. Recebe os dados do formulário e salva no Banco de Dados (Adiciona ou Edita)
@app.route('/admin/salvar', methods=['POST'])
def salvar_time():
    posicao = int(request.form['posicao'])
    nome = request.form['nome']
    pontos = int(request.form['pontos'])
    
    # Tratamento simples para remover espaços e padronizar letras maiúsculas
    forma_letras = request.form['forma_letras'].upper().replace(" ", "")
    placares = request.form['placares'].replace(" ", "")

    # Regra: Se a posição já existir, vamos atualizar o time existente. Caso contrário, criamos um novo.
    time_existente = Time.query.filter_by(posicao=posicao).first()
    
    if time_existente:
        time_existente.nome = nome
        time_existente.pontos = pontos
        time_existente.forma_letras = forma_letras
        time_existente.placares = placares
    else:
        novo_time = Time(
            posicao=posicao, 
            nome=nome, 
            pontos=pontos, 
            forma_letras=forma_letras, 
            placares=placares
        )
        db.session.add(novo_time)

    db.session.commit()
    return redirect(url_for('admin'))

# 3. Rota rápida para remover um time do banco
@app.route('/admin/deletar/<int:id>')
def deletar_time(id):
    time_para_deletar = Time.query.get_or_404(id)
    db.session.delete(time_para_deletar)
    db.session.commit()
    return redirect(url_for('admin'))

# ==========================================
# INICIALIZAÇÃO
# ==========================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Popula o banco com dados padrão na primeira execução
        if Time.query.count() == 0:
            botafogo = Time(posicao=1, nome="Botafogo", pontos=12, forma_letras="V,V,E,V,D", placares="3-1,2-0,1-1,3-0,0-1")
            palmeiras = Time(posicao=2, nome="Palmeiras", pontos=10, forma_letras="V,E,V,V,E", placares="1-0,0-0,2-1,2-0,1-1")
            flamengo = Time(posicao=3, nome="Flamengo", pontos=9, forma_letras="D,V,D,V,V", placares="1-2,4-1,0-2,3-2,2-1")
            
            db.session.add_all([botafogo, palmeiras, flamengo])
            db.session.commit()

    app.run(debug=True)